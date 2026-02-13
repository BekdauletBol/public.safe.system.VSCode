import time, os, cv2, numpy as np, json, asyncio, base64, psutil
import threading
from queue import Queue
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from ultralytics import YOLO

app = FastAPI()
DATA_DIR = "data/final"
os.makedirs(DATA_DIR, exist_ok=True)

frame_queue = Queue(maxsize=1)
metrics_log = f"{DATA_DIR}/system_stats.csv"

# Инициализация лога с новой колонкой CPU
if not os.path.exists(metrics_log):
    with open(metrics_log, "w") as f:
        f.write("timestamp,latency_ms,fps,cpu_usage,violations\n")

class ConnectionManager:
    def __init__(self): self.active_connections = []
    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active_connections.append(ws)
    def disconnect(self, ws: WebSocket):
        if ws in self.active_connections: self.active_connections.remove(ws)
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try: await connection.send_text(message)
            except: pass

manager = ConnectionManager()
with open("configs/iphone-01.json", "r") as f: CONFIG = json.load(f)
DANGER_ZONE = np.array(CONFIG["danger_zone"], dtype=np.int32)

def ml_worker():
    model = YOLO('yolov8n.pt'); model.to('mps')
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    while True:
        try:
            item = frame_queue.get(timeout=1)
            img, cam_id, start_ts = item
            
            results = model(img, verbose=False, conf=0.4, classes=[0])
            violations = 0
            
            # --- ОТРИСОВКА (Оптимизировано для M1/M2) ---
            # 1. Рисуем опасную зону (полигон)
            cv2.polylines(img, [DANGER_ZONE], True, (0, 0, 255), 3)
            
            for box in results[0].boxes:
                xyxy = box.xyxy[0].cpu().numpy().astype(int)
                p_base = (int((xyxy[0] + xyxy[2]) / 2), int(xyxy[3]))
                
                # Проверка вхождения
                is_inside = cv2.pointPolygonTest(DANGER_ZONE, p_base, False) >= 0
                color = (0, 0, 255) if is_inside else (0, 255, 0)
                if is_inside: violations += 1
                
                # Рисуем рамку человека и точку ног
                cv2.rectangle(img, (xyxy[0], xyxy[1]), (xyxy[2], xyxy[3]), color, 2)
                cv2.circle(img, p_base, 5, (255, 255, 0), -1)

            # --- СБОР МЕТРИК ---
            e2e_lat = (time.time() - start_ts) * 1000
            cpu = psutil.cpu_percent()
            
            with open(metrics_log, "a") as f:
                f.write(f"{datetime.utcnow().isoformat()},{e2e_lat:.2f},{1.0/(time.time()-start_ts):.2f},{cpu},{violations}\n")

            # --- ПОДГОТОВКА КАДРА ДЛЯ DASHBOARD ---
            _, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 60])
            img_base64 = base64.b64encode(buffer).decode('utf-8')

            payload = json.dumps({
                "cam": cam_id, 
                "v": violations, 
                "lat": round(e2e_lat, 1),
                "cpu": cpu,
                "img": img_base64 # Передаем само изображение
            })
            loop.run_until_complete(manager.broadcast(payload))
        except: continue

threading.Thread(target=ml_worker, daemon=True).start()

@app.get("/", response_class=HTMLResponse)
async def get_client():
    with open('edge/index.html', 'r') as f: return f.read()

@app.get("/dash", response_class=HTMLResponse)
async def get_dashboard():
    with open('dashboard/index.html', 'r') as f: return f.read()

@app.websocket("/ws/data")
async def ws_dashboard(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True: await websocket.receive_text()
    except WebSocketDisconnect: manager.disconnect(websocket)

@app.websocket("/ws/{camera_id}")
async def ws_ingest(websocket: WebSocket, camera_id: str):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_bytes()
            ts = time.time()
            nparr = np.frombuffer(data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is not None:
                if frame_queue.full():
                    try: frame_queue.get_nowait()
                    except: pass
                frame_queue.put((img, camera_id, ts))
    except: pass