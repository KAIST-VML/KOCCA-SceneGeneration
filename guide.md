# 3D Scene Generation API 설치 및 실행 가이드

텍스트 설명을 입력하면 3D 씬을 생성하는 API 서버입니다.

## 📋 시스템 요구사항

- **Python**: 3.8 이상
- **운영체제**: Linux (Ubuntu 권장)
- **GPU**: CUDA 지원 GPU (권장)
- **메모리**: 최소 16GB RAM

## 🚀 빠른 시작

### 1. 의존성 설치

```bash
# Python 패키지 설치
pip install -r requirements.txt
```

### 2. 환경변수 설정

```bash
# config.env 파일 편집
nano config.env

# OpenAI API 키 설정 (필수)
export OPENAI_API_KEY="your-openai-api-key-here"
```

### 3. 서버 실행

```bash
# 환경변수 로드 및 서버 시작
bash run.sh

# 또는 직접 실행
source config.env
python main.py
```

### 4. 클라이언트 사용

```bash
# 기본 사용법
python client.py "씬 설명" "출력파일경로.glb"

# 예시
python client.py "A 4x4 cozy bedroom" "./bedroom.glb"
```

## 📁 폴더 구조

```
kocca/
├── main.py                 # 서버 메인 코드
├── client.py               # 클라이언트 코드
├── config.env              # 환경변수 설정
├── run.sh                  # 서버 실행 스크립트
├── layout_scene_api.sh     # 씬 생성 파이프라인
├── requirements.txt        # Python 패키지 목록
├── space-generator/        # 씬 생성 알고리즘
│   ├── Scene_Synthesis/    # 레이아웃 생성
│   └── retrieval/          # 객체 검색 및 배치
├── dataset/                # 3D 객체 데이터셋
│   ├── 3D-FUTURE-model-part1/
│   ├── 3D-FUTURE-model-part2/
│   ├── 3D-FUTURE-model-part3/
│   └── 3D-FUTURE-model-part4/
└── outputs/                # 생성된 파일 저장소
```

## ⚙️ 설정 파일 (config.env)

```bash
# OpenAI API 키 (필수)
export OPENAI_API_KEY="sk-your-api-key-here"

# 프로젝트 경로
export SCENE_BASE_PATH="./space-generator"
export SCENE_SCRIPT_PATH="./layout_scene_api.sh"
export SCENE_WORK_DIR="."
export SCENE_OUTPUT_DIR="./outputs"
```

## 💻 클라이언트 사용법

### 기본 사용

```bash
python client.py "A 5x5 modern kitchen" "./kitchen.glb"
```

### 고급 옵션

```bash
python client.py "A bedroom" "./bedroom.glb" \
  --iterations 500 \
  --server-url http://localhost:8000 \
  --api-key sk-your-key \
  --check-interval 10
```

### 매개변수 설명

- `input_prompt`: 생성할 씬의 텍스트 설명
- `save_dir`: GLB 파일을 저장할 경로
- `--iterations`: 생성 반복 횟수 (기본값: 300)
- `--server-url`: 서버 주소 (기본값: http://localhost:8000)
- `--api-key`: OpenAI API 키 (환경변수 우선)
- `--check-interval`: 상태 확인 간격(초) (기본값: 10)

## 🌐 API 엔드포인트

### 서버 상태 확인
```bash
curl http://localhost:8000/health
```

### API 키 설정
```bash
curl -X POST http://localhost:8000/api/set-api-key \
  -H "Content-Type: application/json" \
  -d '{"openai_api_key": "sk-your-key"}'
```

### 씬 생성 요청
```bash
curl -X POST http://localhost:8000/api/generate-scene \
  -H "Content-Type: application/json" \
  -d '{
    "scene_descriptor": "A cozy bedroom",
    "iterations": 300,
    "openai_api_key": "sk-your-key"
  }'
```

### 작업 상태 확인
```bash
curl http://localhost:8000/api/status/{task_id}
```

### 파일 다운로드
```bash
curl http://localhost:8000/download/{task_id} -o scene.glb
```
## 📊 실행 예시

### 서버 실행 성공시 출력
```
Loading environment variables from config.env...
Starting Scene Generation API server...
Base Path: ./space-generator
Output Dir: ./outputs
Script Path: ./layout_scene_api.sh

INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 클라이언트 실행 성공시 출력
```
🎨 3D Scene Generation Client
📝 씬 설명: A 4x4 cozy bedroom
💾 저장 경로: ./bedroom.glb
🔄 반복 횟수: 300
🌐 서버: http://localhost:8000
--------------------------------------------------
🟢 서버 상태: healthy
   활성 작업: 0개
   API 키 상태: Set
✅ API 키가 성공적으로 설정되었습니다.
🚀 씬 생성 요청이 접수되었습니다. Task ID: abc123...
⏳ 씬 생성 중...
📊 상태: processing | 단계: scene_synthesis | 진행률: 25%
📊 상태: processing | 단계: text_retrieval | 진행률: 50%
📊 상태: processing | 단계: clip_retrieval | 진행률: 75%
📊 상태: processing | 단계: scene_composition | 진행률: 90%
🎉 씬 생성이 완료되었습니다!
📁 파일 다운로드 중...
✅ 파일이 성공적으로 저장되었습니다: ./bedroom.glb
🎉 모든 작업이 완료되었습니다!
```