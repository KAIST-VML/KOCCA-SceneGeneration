from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import subprocess
import uuid
import os
from datetime import datetime
from pathlib import Path
import threading
import shutil

# FastAPI 앱 생성
app = FastAPI(title="Scene Synthesis API", version="1.0.0")

# 요청 모델
class SceneRequest(BaseModel):
    scene_descriptor: str
    iterations: int = 300
    openai_api_key: str = None

# 전역 API 키
global_openai_api_key = None

# 작업 상태 저장
tasks = {}

def run_scene_synthesis(task_id: str, scene_descriptor: str, iterations: int, api_key: str):
    """백그라운드에서 씬 생성 실행"""
    try:
        tasks[task_id]["status"] = "processing"
        
        # 출력 경로 생성 (환경변수 또는 현재 디렉토리 기준)
        output_base = os.getenv('SCENE_OUTPUT_DIR', './outputs')
        output_path = f"{output_base}/scene_output_{task_id}"
        os.makedirs(output_path, exist_ok=True)
        
        # 스크립트 실행 (환경변수 또는 현재 디렉토리 기준)
        script_path = os.getenv('SCENE_SCRIPT_PATH', './layout_scene_api.sh')
        
        env = os.environ.copy()
        env['OPENAI_API_KEY'] = api_key
        
        print(f"Task {task_id}: Starting scene synthesis with {iterations} iterations...")
        
        # 스크립트 실행 (kocca 디렉토리에서 실행하도록 절대 경로 사용)
        kocca_dir = os.path.dirname(os.path.abspath(__file__))
        
        process = subprocess.run([
            "bash", script_path, scene_descriptor, output_path, str(iterations)
        ], 
        cwd=kocca_dir,  # kocca 폴더에서 실행
        env=env,
        # capture_output=True,  # 이걸 주석처리해서 출력을 볼 수 있게 함
        # text=True
        )
        
        if process.returncode == 0:
            # GLB 파일 찾기
            glb_file = None
            result_dir = f"{output_path}/Result"
            if os.path.exists(result_dir):
                for file in Path(result_dir).glob("**/*.glb"):
                    glb_file = str(file)
                    break
            
            if glb_file:
                tasks[task_id]["status"] = "completed"
                tasks[task_id]["file_path"] = glb_file
                print(f"Task {task_id}: Completed successfully")
            else:
                tasks[task_id]["status"] = "failed"
                tasks[task_id]["error"] = "GLB file not found"
                print(f"Task {task_id}: GLB file not found")
        else:
            tasks[task_id]["status"] = "failed"
            tasks[task_id]["error"] = f"Script failed: {process.stderr}"
            print(f"Task {task_id}: Script failed")
            
    except Exception as e:
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = str(e)
        print(f"Task {task_id}: Exception - {str(e)}")

@app.get("/")
async def root():
    return {"message": "Scene Synthesis API", "version": "1.0.0"}

@app.post("/api/set-api-key")
async def set_api_key(request: dict):
    """API 키 설정"""
    global global_openai_api_key
    
    api_key = request.get("openai_api_key", "").strip()
    if not api_key or not api_key.startswith('sk-'):
        raise HTTPException(status_code=400, detail="Invalid API key")
    
    global_openai_api_key = api_key
    return {"message": "API key set successfully"}

@app.post("/api/generate-scene")
async def generate_scene(request: SceneRequest):
    """씬 생성 요청"""
    if not request.scene_descriptor.strip():
        raise HTTPException(status_code=400, detail="Scene descriptor required")
    
    if request.iterations <= 0 or request.iterations > 1000:
        raise HTTPException(status_code=400, detail="Iterations must be 1-1000")
    
    api_key = request.openai_api_key or global_openai_api_key
    if not api_key:
        raise HTTPException(status_code=400, detail="OpenAI API key required")
    
    task_id = str(uuid.uuid4())
    
    tasks[task_id] = {
        "status": "queued",
        "scene_descriptor": request.scene_descriptor,
        "iterations": request.iterations,
        "created_at": datetime.now().isoformat()
    }
    
    # 백그라운드 실행
    thread = threading.Thread(
        target=run_scene_synthesis,
        args=(task_id, request.scene_descriptor, request.iterations, api_key)
    )
    thread.daemon = True
    thread.start()
    
    return {"task_id": task_id, "status": "queued"}

@app.get("/api/status/{task_id}")
async def get_status(task_id: str):
    """작업 상태 확인"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks[task_id]
    result = {
        "task_id": task_id,
        "status": task["status"],
        "scene_descriptor": task["scene_descriptor"],
        "iterations": task["iterations"],
        "created_at": task["created_at"]
    }
    
    if task["status"] == "completed":
        result["download_url"] = f"/download/{task_id}"
    elif task["status"] == "failed":
        result["error"] = task.get("error", "Unknown error")
    
    return result

@app.get("/download/{task_id}")
async def download_file(task_id: str):
    """GLB 파일 다운로드"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks[task_id]
    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail="Task not completed")
    
    file_path = task.get("file_path")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # 파일 스트리밍 후 정리
    output_dir = str(Path(file_path).parent.parent)
    
    def file_stream_and_cleanup():
        with open(file_path, "rb") as f:
            yield from f
        try:
            shutil.rmtree(output_dir)
            print(f"Cleaned up: {output_dir}")
        except Exception as e:
            print(f"Cleanup failed: {e}")
    
    return StreamingResponse(
        file_stream_and_cleanup(),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename=scene_{task_id}.glb"}
    )

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "active_tasks": len([t for t in tasks.values() if t["status"] == "processing"]),
        "api_key_status": "Set" if global_openai_api_key else "Not Set"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)