import time, os, cv2, numpy as np, json, asyncio, base64, psutil, threading
from queue import Queue
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
from ultralytics import YOLO
import pandas as pd

app = FastAPI()
frame_queue = Queue(maxsize=1)
DATA_DIR = "data/final"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs("analysis/system_health", exist_ok=True)

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

# Конфигурация
with open("configs/iphone-01.json", "r") as f: CONFIG = json.load(f)
DANGER_ZONE = np.array(CONFIG["danger_zone"], dtype=np.int32)

def ml_worker():
    model = YOLO('yolov8n.pt'); model.to('mps')
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Инициализация Heatmap (черное изображение)
    heatmap = np.zeros((480, 640), dtype=np.float32)

    while True:
        try:
            item = frame_queue.get(timeout=1)
            raw_img, cam_id, start_ts = item
            
            # Важно: работаем с копией для стабильной отрисовки
            draw_img = raw_img.copy()
            
            results = model(draw_img, verbose=False, conf=0.4, classes=[0])
            violations = 0
            
            # Логика детекции
            for box in results[0].boxes:
                xyxy = box.xyxy[0].cpu().numpy().astype(int)
                # Точка ног
                p_base = (int((xyxy[0] + xyxy[2]) / 2), int(xyxy[3]))
                
                # Проверка зоны
                is_inside = cv2.pointPolygonTest(DANGER_ZONE.astype(np.float32), 
                                                (float(p_base[0]), float(p_base[1])), False) >= 0
                
                if is_inside:
                    violations += 1
                    # Обновляем Heatmap (добавляем "жара" в точку нарушения)
                    cv2.circle(heatmap, p_base, 20, 0.5, -1)
                
                # Рисуем бокс
                color = (0, 0, 255) if is_inside else (255, 255, 255)
                cv2.rectangle(draw_img, (xyxy[0], xyxy[1]), (xyxy[2], xyxy[3]), color, 1)

            # ЭФФЕКТ ГОРЯЩЕЙ ЗОНЫ
            if violations > 0:
                overlay = draw_img.copy()
                cv2.fillPoly(overlay, [DANGER_ZONE], (0, 0, 255))
                cv2.addWeighted(overlay, 0.3, draw_img, 0.7, 0, draw_img)
            
            # Рисуем контур зоны всегда
            cv2.polylines(draw_img, [DANGER_ZONE], True, (255, 255, 255), 2)

            # Наложение Heatmap (опционально, слабым слоем)
            heatmap_color = cv2.applyColorMap((heatmap * 255).astype(np.uint8), cv2.COLORMAP_JET)
            draw_img = cv2.addWeighted(heatmap_color, 0.2, draw_img, 0.8, 0)
            # Охлаждение Heatmap (постепенное затухание)
            heatmap *= 0.99

            e2e_lat = (time.time() - start_ts) * 1000
            _, buffer = cv2.imencode('.jpg', draw_img, [cv2.IMWRITE_JPEG_QUALITY, 70])
            img_b64 = base64.b64encode(buffer).decode('utf-8')

            payload = json.dumps({
                "v": violations, "lat": round(e2e_lat, 1), 
                "cpu": psutil.cpu_percent(), "img": img_b64
            })
            loop.run_until_complete(manager.broadcast(payload))
        except: continue

threading.Thread(target=ml_worker, daemon=True).start()

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    with open('dashboard/index.html', 'r') as f: return f.read()

@app.get("/edge", response_class=HTMLResponse)
async def get_edge():
    with open('edge/index.html', 'r') as f: return f.read()

@app.websocket("/ws/data")
async def ws_data(websocket: WebSocket):
    await manager.connect(websocket)
    try: 
        while True: await websocket.receive_text()
    except: manager.disconnect(websocket)

@app.websocket("/ws/{camera_id}")
async def ws_ingest(websocket: WebSocket, camera_id: str):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_bytes()
            ts = time.time(); nparr = np.frombuffer(data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is not None:
                if frame_queue.full():
                    try: frame_queue.get_nowait()
                    except: pass
                frame_queue.put((img, camera_id, ts))
    except: pass