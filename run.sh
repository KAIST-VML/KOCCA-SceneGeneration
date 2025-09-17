#!/bin/bash

# 환경변수 로드
if [ -f "config.env" ]; then
    echo "Loading environment variables from config.env..."
    source config.env
else
    echo "Warning: config.env not found. Using default values."
fi

# 필요한 디렉토리 생성
mkdir -p "${SCENE_OUTPUT_DIR:-./outputs}"

# 서버 실행
echo "Starting Scene Generation API server..."
echo "Base Path: ${SCENE_BASE_PATH:-./stylin}"
echo "Output Dir: ${SCENE_OUTPUT_DIR:-./outputs}"
echo "Script Path: ${SCENE_SCRIPT_PATH:-./layout_scene_api.sh}"
echo ""

python main.py
