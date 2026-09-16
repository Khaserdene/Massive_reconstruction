import os
import time
import base64
import numpy as np
import cv2
import json
import asyncio
import shutil
import glob
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow CORS for web viewers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="../client"), name="static")

DATA_DIR = "../data/raw_frames"
os.makedirs(DATA_DIR, exist_ok=True)
SETTINGS_FILE = "../data/settings.json"

settings = {
    "python_path": "python"
}

if os.path.exists(SETTINGS_FILE):
    try:
        with open(SETTINGS_FILE, "r") as f:
            saved = json.load(f)
            if "python_path" in saved:
                settings["python_path"] = saved["python_path"]
    except:
        pass
else:
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f)

active_process_logs = []
process_task = None

class SettingsModel(BaseModel):
    python_path: str
    colmap_path: Optional[str] = ""
    gs_script_dir: Optional[str] = ""

@app.get("/")
async def get_client():
    with open("../client/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/admin")
async def get_admin():
    with open("../client/admin.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/api/sessions")
async def get_sessions():
    sessions = []
    if os.path.exists(DATA_DIR):
        for s in os.listdir(DATA_DIR):
            s_path = os.path.join(DATA_DIR, s)
            if os.path.isdir(s_path):
                frames = len([f for f in os.listdir(s_path) if f.endswith(".jpg")])
                has_sparse = os.path.exists(os.path.join(s_path, "sparse"))
                output_dir = os.path.join(s_path, "output")
                
                # Check for iteration 7000 or 30000 model
                model_path_7k = os.path.join(output_dir, "point_cloud", "iteration_7000", "point_cloud.ply")
                model_path_30k = os.path.join(output_dir, "point_cloud", "iteration_30000", "point_cloud.ply")
                
                model_url = None
                if os.path.exists(model_path_30k):
                    model_url = f"/api/model/{s}/iteration_30000"
                elif os.path.exists(model_path_7k):
                    model_url = f"/api/model/{s}/iteration_7000"
                    
                sessions.append({
                    "id": s,
                    "frames": frames,
                    "has_sparse": has_sparse,
                    "model_url": model_url,
                    "created_at": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(s))) if s.isdigit() else s
                })
    return JSONResponse(sorted(sessions, key=lambda x: x["id"], reverse=True))

@app.get("/api/model/{session_id}/{iteration}")
async def get_model(session_id: str, iteration: str):
    path = os.path.join(DATA_DIR, session_id, "output", "point_cloud", iteration, "point_cloud.ply")
    if os.path.exists(path):
        return FileResponse(path, media_type="application/octet-stream", filename=f"{session_id}.ply")
    return JSONResponse({"error": "Model not found"}, status_code=404)

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    session_dir = os.path.join(DATA_DIR, session_id)
    if os.path.exists(session_dir) and os.path.isdir(session_dir):
        try:
            shutil.rmtree(session_dir)
            return {"status": "success"}
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)
    return JSONResponse({"error": "Session not found"}, status_code=404)

@app.post("/api/settings")
async def save_settings(s: SettingsModel):
    global settings
    settings.update(s.dict())
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f)
    return {"status": "success"}

@app.get("/api/settings")
async def get_settings():
    return JSONResponse(settings)

async def run_subprocess_and_log(cmd, cwd):
    global active_process_logs
    try:
        env = os.environ.copy()
        colmap_base = os.path.abspath("../tools/COLMAP")
        colmap_paths = glob.glob(os.path.join(colmap_base, "**", "COLMAP.bat"), recursive=True)
        if colmap_paths:
            colmap_dir = os.path.dirname(colmap_paths[0])
            env["PATH"] = colmap_dir + os.pathsep + env.get("PATH", "")
        else:
            env["PATH"] = colmap_base + os.pathsep + env.get("PATH", "")

        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=cwd,
            env=env
        )
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            decoded_line = line.decode('utf-8', errors='replace').strip()
            active_process_logs.append(decoded_line)
            if len(active_process_logs) > 2000:
                active_process_logs.pop(0)
        
        await process.wait()
        return process.returncode
    except Exception as e:
        active_process_logs.append(f"System Error: {str(e)}")
        return -1

async def process_pipeline(session_id: str):
    global active_process_logs, process_task
    active_process_logs.clear()
    session_dir = os.path.abspath(os.path.join(DATA_DIR, session_id))
    
    gs_dir = os.path.abspath("../tools/gaussian-splatting")
    convert_script = os.path.join(gs_dir, "convert.py")
    train_script = os.path.join(gs_dir, "train.py")
    python_cmd = settings.get("python_path", "python")
    
    colmap_base = os.path.abspath("../tools/COLMAP")
    colmap_paths = glob.glob(os.path.join(colmap_base, "**", "COLMAP.bat"), recursive=True)
    colmap_executable = colmap_paths[0] if colmap_paths else "colmap"
    
    if not os.path.exists(convert_script):
        active_process_logs.append(f"ERROR: convert.py not found in {gs_dir}. Please set the correct 'Gaussian Splatting Folder' in settings.")
        return
        
    active_process_logs.append(f"[{time.strftime('%H:%M:%S')}] --- Starting Pipeline for Session: {session_id} ---")
    active_process_logs.append(f"[{time.strftime('%H:%M:%S')}] Step 1: Running COLMAP (convert.py)...")
    
    cmd_colmap = f'"{python_cmd}" "{convert_script}" -s "{session_dir}" --colmap_executable "{colmap_executable}"'
    code = await run_subprocess_and_log(cmd_colmap, cwd=gs_dir)
    
    if code != 0:
        active_process_logs.append(f"[{time.strftime('%H:%M:%S')}] COLMAP processing failed! Check logs above.")
        return
        
    active_process_logs.append(f"[{time.strftime('%H:%M:%S')}] Step 1 Complete. Starting Step 2: 3DGS Training (train.py)...")
    
    output_dir = os.path.join(session_dir, "output")
    cmd_train = f'"{python_cmd}" "{train_script}" -s "{session_dir}" -m "{output_dir}"'
    
    code = await run_subprocess_and_log(cmd_train, cwd=gs_dir)
    if code != 0:
        active_process_logs.append(f"[{time.strftime('%H:%M:%S')}] 3DGS Training failed! Check logs above.")
    else:
        active_process_logs.append(f"[{time.strftime('%H:%M:%S')}] --- Pipeline Finished Successfully! ---")
        active_process_logs.append(f"[{time.strftime('%H:%M:%S')}] Model saved to {output_dir}. You can now view it.")
    process_task = None

@app.post("/api/process/{session_id}")
async def start_processing(session_id: str):
    global process_task
    if process_task is not None and not process_task.done():
        return JSONResponse({"status": "error", "message": "Another process is currently running. Please wait."})
    
    process_task = asyncio.create_task(process_pipeline(session_id))
    return {"status": "started"}

@app.websocket("/ws/logs")
async def logs_websocket(websocket: WebSocket):
    await websocket.accept()
    last_idx = 0
    try:
        while True:
            if len(active_process_logs) > last_idx:
                new_logs = active_process_logs[last_idx:]
                await websocket.send_json({"logs": new_logs})
                last_idx = len(active_process_logs)
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        pass

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Keep legacy for old clients just in case
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        pass

@app.websocket("/ws_realtime")
async def websocket_realtime_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Real-time Camera Client connected!")
    
    session_id = str(int(time.time()))
    session_dir = os.path.join(DATA_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)
    
    # Benchmarking state
    benchmark_frames = 0
    benchmark_start_time = None
    
    # Training state
    train_frames = 0
    
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            
            msg_type = payload.get("type")
            img_data_str = payload.get("image", "")
            pose = payload.get("pose", [])
            resolution = payload.get("resolution", 360)
            
            if img_data_str.startswith("data:image"):
                header, encoded = img_data_str.split(",", 1)
                img_data = base64.b64decode(encoded)
                nparr = np.frombuffer(img_data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if msg_type == "benchmark_frame":
                    if benchmark_start_time is None:
                        benchmark_start_time = time.time()
                    
                    # Simulate GPU load (matrix operations relative to resolution)
                    dummy_load = np.dot(np.random.rand(resolution, resolution), np.random.rand(resolution, resolution))
                    
                    benchmark_frames += 1
                    
                    # After 20 frames, return result
                    if benchmark_frames >= 20:
                        elapsed = time.time() - benchmark_start_time
                        fps = round(benchmark_frames / elapsed, 1)
                        
                        rec = "Keep current settings."
                        if fps < 10:
                            rec = "Your GPU is struggling. Lower resolution to 240p or reduce FPS."
                        elif fps > 20:
                            rec = "Your GPU handles this well! You can increase resolution."
                            
                        await websocket.send_json({
                            "type": "benchmark_result",
                            "fps": fps,
                            "resolution": resolution,
                            "recommendation": rec
                        })
                        benchmark_frames = 0
                        benchmark_start_time = None
                        
                elif msg_type == "train_frame":
                    # Save frame and pose for Real-time incremental trainer
                    frame_name = f"frame_{train_frames:05d}.jpg"
                    filepath = os.path.join(session_dir, frame_name)
                    cv2.imwrite(filepath, img)
                    
                    pose_path = os.path.join(session_dir, f"pose_{train_frames:05d}.json")
                    with open(pose_path, "w") as f:
                        json.dump(pose, f)
                    
                    train_frames += 1
                    
                    # Simulate sending status back to client
                    await websocket.send_json({
                        "type": "training_status",
                        "loss": np.random.uniform(0.01, 0.5),
                        "points": train_frames * 150
                    })
                    
    except WebSocketDisconnect:
        print("Camera Client disconnected.")
    except Exception as e:
        print(f"WebSocket error: {e}")
