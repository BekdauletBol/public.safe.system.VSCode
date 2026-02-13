import time, os, cv2, numpy as np, json, asyncio, base64, psutil, threading
from queue import Queue
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
from ultralytics import YOLO
import pandas as pd
import matplotlib.pyplot as plt

# --- ПУТИ (Абсолютные) ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT_PATH = os.path.join(BASE_DIR, "analysis", "final_report.png")
CSV_PATH = os.path.join(BASE_DIR, "data", "final", "session_data.csv")

os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)

app = FastAPI()
frame_queue = Queue(maxsize=1)

# Инициализация лога
if not os.path.exists(CSV_PATH):
    with open(CSV_PATH, "w") as f:
        f.write("timestamp,people_count,latency,cpu,is_violation\n")

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
CONFIG_FILE = os.path.join(BASE_DIR, "configs", "iphone-01.json")
with open(CONFIG_FILE, "r") as f: CONFIG = json.load(f)
DANGER_ZONE = np.array(CONFIG["danger_zone"], dtype=np.int32)

def ml_worker():
    model = YOLO('yolov8n.pt'); model.to('mps')
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    while True:
        try:
            item = frame_queue.get(timeout=1)
            img, cam_id, start_ts = item
            results = model(img, verbose=False, conf=0.3, classes=[0])
            
            violations = 0
            people_in_frame = len(results[0].boxes)
            
            # Рендеринг детекций
            for box in results[0].boxes:
                xyxy = box.xyxy[0].cpu().numpy().astype(int)
                pts = [(xyxy[0], xyxy[3]), (xyxy[2], xyxy[3]), (int((xyxy[0]+xyxy[2])/2), xyxy[3])]
                is_inside = any(cv2.pointPolygonTest(DANGER_ZONE.astype(np.float32), (float(p[0]), float(p[1])), False) >= 0 for p in pts)
                
                if is_inside: violations += 1
                color = (0, 0, 255) if is_inside else (255, 255, 255)
                cv2.rectangle(img, (xyxy[0], xyxy[1]), (xyxy[2], xyxy[3]), color, 1)

            # Отрисовка зоны (Заливка при нарушении)
            z_color = (0, 0, 255) if violations > 0 else (255, 255, 255)
            if violations > 0:
                overlay = img.copy()
                cv2.fillPoly(overlay, [DANGER_ZONE], (0, 0, 255))
                cv2.addWeighted(overlay, 0.2, img, 0.8, 0, img)
            cv2.polylines(img, [DANGER_ZONE], True, z_color, 1)

            # Научное логирование
            lat_raw = (time.time() - start_ts) * 1000
            cpu = psutil.cpu_percent()
            # Формула взвешенной нагрузки для графика (Spike logic)
            weighted_load = lat_raw + (violations * 60) 

            with open(CSV_PATH, "a") as f:
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"{ts},{people_in_frame},{round(weighted_load, 1)},{cpu},{1 if violations>0 else 0}\n")

            _, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 65])
            img_b64 = base64.b64encode(buffer).decode('utf-8')
            
            # Отправляем взвешенную нагрузку как 'lat'
            payload = json.dumps({"v": violations, "lat": round(weighted_load, 1), "cpu": cpu, "img": img_b64})
            loop.run_until_complete(manager.broadcast(payload))
        except: continue

threading.Thread(target=ml_worker, daemon=True).start()

# --- ROUTES ---

@app.get("/")
async def serve_dashboard():
    return FileResponse(os.path.join(BASE_DIR, "dashboard", "index.html"))

@app.get("/edge")
async def serve_edge():
    return FileResponse(os.path.join(BASE_DIR, "edge", "index.html"))

@app.get("/api/build_analytics")
async def build_analytics():
    if not os.path.exists(CSV_PATH): return {"status": "error"}
    try:
        df = pd.read_csv(CSV_PATH)
        if len(df) < 2: return {"status": "error", "msg": "Insufficient data"}
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(10, 5), facecolor='#0b0c0e')
        ax.set_facecolor('#0b0c0e')
        
        # Рисуем график активности
        ax.plot(df['timestamp'], df['people_count'], color='#00ff41', linewidth=2)
        ax.fill_between(df['timestamp'], df['people_count'], color='#00ff41', alpha=0.1)
        
        ax.grid(color='#222', linestyle='--')
        plt.title("SESSION INTELLIGENCE REPORT", color='white')
        
        # Сохранение с гарантией записи
        plt.savefig(REPORT_PATH, facecolor='#0b0c0e', bbox_inches='tight')
        plt.close(fig)
        return {"status": "success", "url": "/api/download_report"}
    except Exception as e:
        return {"status": "error", "msg": str(e)}

@app.get("/api/download_report")
async def dl_report():
    if os.path.exists(REPORT_PATH):
        return FileResponse(REPORT_PATH)
    return {"error": "File not generated"}

@app.get("/api/download_csv")
async def dl_csv(): return FileResponse(CSV_PATH)

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