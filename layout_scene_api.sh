#!/bin/bash
# 스크립트 설정
set -e  # 에러 발생 시 스크립트 중단

# 디버깅 정보
echo "=== DEBUG INFO ==="
echo "Script execution directory: $(pwd)"
echo "Script arguments: $@"
echo "==================="

# 매개변수 받기
SCENE_DESCRIPTOR="$1"
OUTPUT_BASE="$2"
ITERATIONS="${3:-300}"  # 3번째 매개변수가 없으면 기본값 300

# 매개변수 확인
if [ -z "$SCENE_DESCRIPTOR" ] || [ -z "$OUTPUT_BASE" ]; then
    echo "사용법: $0 <scene_descriptor> <output_base> [iterations]"
    exit 1
fi

# 체크포인트 관련 함수들
CHECKPOINT_FILE="${CHECKPOINT_PATH:-$OUTPUT_BASE/checkpoint.json}"

# 체크포인트에서 특정 단계 상태 읽기
get_stage_status() {
    local stage_name="$1"
    if [ -f "$CHECKPOINT_FILE" ]; then
        python3 -c "
import json, sys
try:
    with open('$CHECKPOINT_FILE', 'r') as f:
        data = json.load(f)
        print(data.get('stages', {}).get('$stage_name', 'pending'))
except:
    print('pending')
"
    else
        echo "pending"
    fi
}

# 체크포인트에 특정 단계 상태 저장
update_stage_status() {
    local stage_name="$1"
    local status="$2"
    python3 -c "
import json, os
from datetime import datetime

checkpoint_file = '$CHECKPOINT_FILE'
os.makedirs(os.path.dirname(checkpoint_file) if os.path.dirname(checkpoint_file) else '.', exist_ok=True)

data = {}
if os.path.exists(checkpoint_file):
    try:
        with open(checkpoint_file, 'r') as f:
            data = json.load(f)
    except:
        pass

if 'stages' not in data:
    data['stages'] = {}

data['stages']['$stage_name'] = '$status'
data['last_updated'] = datetime.now().isoformat()

with open(checkpoint_file, 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print('✓ Checkpoint updated: $stage_name = $status')
"
}

# 기본 경로 설정 (스크립트 실행 위치 기준으로 절대 경로 생성)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_PATH="${SCRIPT_DIR}/space-generator"

echo "=== 경로 정보 ==="
echo "스크립트 디렉토리: $SCRIPT_DIR"
echo "베이스 경로: $BASE_PATH"
if [ -d "$BASE_PATH/Scene_Synthesis" ]; then
    echo "Scene_Synthesis 존재 여부: YES"
else
    echo "Scene_Synthesis 존재 여부: NO"
fi
if [ -d "$BASE_PATH/retrieval" ]; then
    echo "retrieval 존재 여부: YES"
else
    echo "retrieval 존재 여부: NO"
fi
echo "================"

echo "=== Scene Synthesis Pipeline 시작 ==="
echo "Scene Description: $SCENE_DESCRIPTOR"
echo "Base Path: $BASE_PATH"
echo "Output Base: $OUTPUT_BASE"
echo "Iterations: $ITERATIONS"
echo ""

# 출력 디렉토리 생성
mkdir -p "$OUTPUT_BASE"

# 절대 경로로 변환
OUTPUT_BASE_ABS="$(readlink -f "$OUTPUT_BASE")"
echo "출력 경로 (절대): $OUTPUT_BASE_ABS"

# 1단계: Layout 및 공간 내 object text 생성
echo "[1/4] Layout 및 object text 생성 중..."

STAGE_STATUS=$(get_stage_status "layout_generation")
LAYOUT_TXT="$OUTPUT_BASE_ABS/Result_txt/layout.txt"

if [ "$STAGE_STATUS" = "completed" ] && [ -f "$LAYOUT_TXT" ]; then
    echo "⏭️  Stage 1 already completed, skipping..."
    echo "   Using existing layout: $LAYOUT_TXT"
else
    echo "🔄 Running layout generation..."
    cd "$BASE_PATH/Scene_Synthesis"
    python scene_synthesis.py --scene_descriptor "$SCENE_DESCRIPTOR" --save_path "$OUTPUT_BASE_ABS/Result_txt" --iterations $ITERATIONS

    if [ $? -eq 0 ]; then
        echo "✓ Layout 생성 완료"

        # 생성된 파일들 확인
        echo "=== 생성된 파일 확인 ==="
        echo "Result_txt 디렉토리 내용:"
        ls -la "$OUTPUT_BASE_ABS/Result_txt/" 2>/dev/null || echo "Result_txt 디렉토리 없음"

        if [ -f "$LAYOUT_TXT" ]; then
            echo "layout.txt 파일 존재: YES"
            LINE_COUNT=$(wc -l < "$LAYOUT_TXT")
            echo "layout.txt 파일 크기: $LINE_COUNT lines"
            echo "layout.txt 처음 5줄:"
            head -5 "$LAYOUT_TXT"

            # 체크포인트 업데이트
            update_stage_status "layout_generation" "completed"
        else
            echo "layout.txt 파일 존재: NO"
        fi
        echo "========================"
    else
        echo "✗ Layout 생성 실패"
        update_stage_status "layout_generation" "failed"
        exit 1
    fi
fi

# 2단계: Object text를 기반으로 layout
echo "[2/4] Text 기반 retrieval 수행 중..."

# 경로 확인
LAYOUT_FILE="$OUTPUT_BASE_ABS/Result_txt/layout.txt"
TEXT_RETRIEVAL_DIR="$OUTPUT_BASE_ABS/Result_retrieval/text_retrieval"

if [ ! -f "$LAYOUT_FILE" ]; then
    echo "✗ layout.txt 파일이 없어서 2단계를 진행할 수 없습니다."
    exit 1
fi

STAGE_STATUS=$(get_stage_status "text_retrieval")

if [ "$STAGE_STATUS" = "completed" ] && [ -d "$TEXT_RETRIEVAL_DIR" ] && [ "$(ls -A $TEXT_RETRIEVAL_DIR)" ]; then
    echo "⏭️  Stage 2 already completed, skipping..."
    echo "   Using existing text retrieval results: $TEXT_RETRIEVAL_DIR"
else
    echo "🔄 Running text retrieval..."
    cd "$BASE_PATH/retrieval"
    python test_retrieval.py --layout_path "$LAYOUT_FILE" --output_dir "$TEXT_RETRIEVAL_DIR"

    if [ $? -eq 0 ]; then
        echo "✓ Text retrieval 완료"
        update_stage_status "text_retrieval" "completed"
    else
        echo "✗ Text retrieval 실패"
        update_stage_status "text_retrieval" "failed"
        exit 1
    fi
fi

# 3단계: 1차 검색된 결과를 바탕으로 CLIP retrieval
echo "[3/4] CLIP 기반 retrieval 수행 중..."

CLIP_RETRIEVAL_DIR="$OUTPUT_BASE_ABS/Result_retrieval/clip_retrieval"
STAGE_STATUS=$(get_stage_status "clip_retrieval")

if [ "$STAGE_STATUS" = "completed" ] && [ -d "$CLIP_RETRIEVAL_DIR" ] && [ "$(ls -A $CLIP_RETRIEVAL_DIR)" ]; then
    echo "⏭️  Stage 3 already completed, skipping..."
    echo "   Using existing CLIP retrieval results: $CLIP_RETRIEVAL_DIR"
else
    echo "🔄 Running CLIP retrieval..."
    cd "$BASE_PATH/retrieval"
    python retrieval_clip.py --layout_path "$LAYOUT_FILE" --candidate_folder "$TEXT_RETRIEVAL_DIR" --output_dir "$CLIP_RETRIEVAL_DIR"

    if [ $? -eq 0 ]; then
        echo "✓ CLIP retrieval 완료"
        update_stage_status "clip_retrieval" "completed"
    else
        echo "✗ CLIP retrieval 실패"
        update_stage_status "clip_retrieval" "failed"
        exit 1
    fi
fi

# 4단계: 검색된 object와 layout을 기반으로 scene 완성
echo "[4/4] Scene composition 수행 중..."

RESULT_DIR="$OUTPUT_BASE_ABS/Result"
STAGE_STATUS=$(get_stage_status "scene_composition")

# GLB 파일 존재 여부 확인
GLB_FILE=$(find "$RESULT_DIR" -name "*.glb" -type f 2>/dev/null | head -1)

if [ "$STAGE_STATUS" = "completed" ] && [ -n "$GLB_FILE" ] && [ -f "$GLB_FILE" ]; then
    echo "⏭️  Stage 4 already completed, skipping..."
    echo "   Using existing scene: $GLB_FILE"
else
    echo "🔄 Running scene composition..."
    cd "$BASE_PATH/retrieval"
    python scene_composition.py --root "$OUTPUT_BASE_ABS/Result_txt" --clip-results "$CLIP_RETRIEVAL_DIR" --output "$RESULT_DIR"

    if [ $? -eq 0 ]; then
        echo "✓ Scene composition 완료"
        update_stage_status "scene_composition" "completed"
    else
        echo "✗ Scene composition 실패"
        update_stage_status "scene_composition" "failed"
        exit 1
    fi
fi

echo ""
echo "=== 모든 단계 완료! ==="
echo "최종 결과 위치: $RESULT_DIR"

# GLB 파일 확인 및 경로 출력
GLB_FILE=$(find "$RESULT_DIR" -name "*.glb" -type f | head -1)
if [ -n "$GLB_FILE" ]; then
    echo "GLB 파일 생성 완료: $GLB_FILE"
else
    echo "경고: GLB 파일을 찾을 수 없습니다."
    exit 1
fi