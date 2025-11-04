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
import re
import hashlib
import json
from dotenv import load_dotenv

# Load environment variables from config.env
load_dotenv('config.env')

# FastAPI 앱 생성
app = FastAPI(title="Scene Synthesis API", version="1.0.0")

# 요청 모델
class SceneRequest(BaseModel):
    scene_descriptor: str
    iterations: int = 300
    openai_api_key: str = None

# 전역 API 키 (환경변수에서 로드 시도)
global_openai_api_key = os.getenv('OPENAI_API_KEY')

# 작업 상태 저장
tasks = {}

def prompt_to_folder_name(prompt: str, max_length: int = 50) -> str:
    """
    프롬프트를 안전한 폴더명으로 변환
    예: "A compact 4x4 study space" -> "a_compact_4x4_study_space"
    """
    # 소문자 변환 및 특수문자 제거
    safe_name = re.sub(r'[^\w\s-]', '', prompt.lower())
    # 공백을 언더스코어로 변환
    safe_name = re.sub(r'[-\s]+', '_', safe_name)
    # 연속된 언더스코어 제거
    safe_name = re.sub(r'_+', '_', safe_name)
    # 앞뒤 언더스코어 제거
    safe_name = safe_name.strip('_')
    # 최대 길이 제한
    if len(safe_name) > max_length:
        # 해시를 추가하여 고유성 보장
        hash_suffix = hashlib.md5(prompt.encode()).hexdigest()[:8]
        safe_name = safe_name[:max_length-9] + '_' + hash_suffix

    return safe_name

def load_checkpoint(checkpoint_path: str) -> dict:
    """체크포인트 파일 로드"""
    if os.path.exists(checkpoint_path):
        try:
            with open(checkpoint_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load checkpoint: {e}")
    return {}

def save_checkpoint(checkpoint_path: str, checkpoint_data: dict):
    """체크포인트 파일 저장"""
    try:
        os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
        with open(checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
        print(f"✓ Checkpoint saved: {checkpoint_path}")
    except Exception as e:
        print(f"Warning: Failed to save checkpoint: {e}")

def run_scene_synthesis(task_id: str, scene_descriptor: str, iterations: int, api_key: str):
    """백그라운드에서 씬 생성 실행"""
    try:
        tasks[task_id]["status"] = "processing"

        # 출력 경로 생성 (프롬프트 기반 폴더명 사용)
        output_base = os.getenv('SCENE_OUTPUT_DIR', './outputs')
        folder_name = prompt_to_folder_name(scene_descriptor)
        output_path = f"{output_base}/{folder_name}"
        os.makedirs(output_path, exist_ok=True)

        # 체크포인트 파일 경로
        checkpoint_path = f"{output_path}/checkpoint.json"

        # 기존 체크포인트 로드
        checkpoint = load_checkpoint(checkpoint_path)

        # 체크포인트가 있고 이미 완료된 경우
        if checkpoint.get('status') == 'completed' and checkpoint.get('iterations') == iterations:
            print(f"Task {task_id}: Found completed checkpoint, skipping generation...")
            glb_file = checkpoint.get('glb_file')
            if glb_file and os.path.exists(glb_file):
                tasks[task_id]["status"] = "completed"
                tasks[task_id]["file_path"] = glb_file
                tasks[task_id]["output_path"] = output_path
                print(f"Task {task_id}: Loaded from checkpoint - {glb_file}")
                return

        # 체크포인트 초기화 (재개 또는 새 시작)
        if not checkpoint:
            checkpoint = {
                "scene_descriptor": scene_descriptor,
                "iterations": iterations,
                "started_at": datetime.now().isoformat(),
                "status": "processing",
                "stages": {
                    "layout_generation": "pending",
                    "text_retrieval": "pending",
                    "clip_retrieval": "pending",
                    "scene_composition": "pending"
                }
            }
            save_checkpoint(checkpoint_path, checkpoint)
        
        # 스크립트 실행 (환경변수 또는 현재 디렉토리 기준)
        script_path = os.getenv('SCENE_SCRIPT_PATH', './layout_scene_api.sh')

        env = os.environ.copy()
        env['OPENAI_API_KEY'] = api_key

        # 체크포인트 경로를 환경변수로 전달
        env['CHECKPOINT_PATH'] = checkpoint_path

        print(f"Task {task_id}: Starting scene synthesis with {iterations} iterations...")
        print(f"Task {task_id}: Output path: {output_path}")
        print(f"Task {task_id}: Checkpoint: {checkpoint_path}")

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
                tasks[task_id]["output_path"] = output_path

                # 최종 체크포인트 업데이트
                checkpoint["status"] = "completed"
                checkpoint["completed_at"] = datetime.now().isoformat()
                checkpoint["glb_file"] = glb_file
                save_checkpoint(checkpoint_path, checkpoint)

                print(f"Task {task_id}: Completed successfully")
            else:
                tasks[task_id]["status"] = "failed"
                tasks[task_id]["error"] = "GLB file not found"

                # 실패 체크포인트 저장
                checkpoint["status"] = "failed"
                checkpoint["error"] = "GLB file not found"
                save_checkpoint(checkpoint_path, checkpoint)

                print(f"Task {task_id}: GLB file not found")
        else:
            tasks[task_id]["status"] = "failed"
            tasks[task_id]["error"] = f"Script failed with return code {process.returncode}"

            # 실패 체크포인트 저장
            checkpoint["status"] = "failed"
            checkpoint["error"] = f"Script failed with return code {process.returncode}"
            save_checkpoint(checkpoint_path, checkpoint)

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

    # 파일 스트리밍 (삭제하지 않음 - 재사용을 위해 보존)
    def file_stream():
        with open(file_path, "rb") as f:
            yield from f

    # 파일명에 프롬프트 기반 폴더명 사용
    output_path = task.get("output_path", "")
    folder_name = Path(output_path).name if output_path else task_id

    return StreamingResponse(
        file_stream(),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={folder_name}.glb"}
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