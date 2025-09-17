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

cd "$BASE_PATH/Scene_Synthesis"
python scene_synthesis.py --scene_descriptor "$SCENE_DESCRIPTOR" --save_path "$OUTPUT_BASE_ABS/Result_txt" --iterations $ITERATIONS

if [ $? -eq 0 ]; then
    echo "✓ Layout 생성 완료"
    
    # 생성된 파일들 확인
    echo "=== 생성된 파일 확인 ==="
    echo "Result_txt 디렉토리 내용:"
    ls -la "$OUTPUT_BASE_ABS/Result_txt/" 2>/dev/null || echo "Result_txt 디렉토리 없음"
    
    LAYOUT_TXT="$OUTPUT_BASE_ABS/Result_txt/layout.txt"
    if [ -f "$LAYOUT_TXT" ]; then
        echo "layout.txt 파일 존재: YES"
        LINE_COUNT=$(wc -l < "$LAYOUT_TXT")
        echo "layout.txt 파일 크기: $LINE_COUNT lines"
        echo "layout.txt 처음 5줄:"
        head -5 "$LAYOUT_TXT"
    else
        echo "layout.txt 파일 존재: NO"
    fi
    echo "========================"
else
    echo "✗ Layout 생성 실패"
    exit 1
fi

# 2단계: Object text를 기반으로 layout
echo "[2/4] Text 기반 retrieval 수행 중..."

# 경로 확인
LAYOUT_FILE="$OUTPUT_BASE_ABS/Result_txt/layout.txt"
echo "=== 2단계 경로 확인 ==="
echo "Layout 파일 경로: $LAYOUT_FILE"

if [ -f "$LAYOUT_FILE" ]; then
    echo "파일 존재 여부: YES"
else
    echo "파일 존재 여부: NO"
    echo "✗ layout.txt 파일이 없어서 2단계를 진행할 수 없습니다."
    exit 1
fi
echo "====================="

cd "$BASE_PATH/retrieval"
python test_retrieval.py --layout_path "$LAYOUT_FILE" --output_dir "$OUTPUT_BASE_ABS/Result_retrieval/text_retrieval"

if [ $? -eq 0 ]; then
    echo "✓ Text retrieval 완료"
else
    echo "✗ Text retrieval 실패"
    exit 1
fi

# 3단계: 1차 검색된 결과를 바탕으로 CLIP retrieval
echo "[3/4] CLIP 기반 retrieval 수행 중..."
python retrieval_clip.py --layout_path "$LAYOUT_FILE" --candidate_folder "$OUTPUT_BASE_ABS/Result_retrieval/text_retrieval" --output_dir "$OUTPUT_BASE_ABS/Result_retrieval/clip_retrieval"

if [ $? -eq 0 ]; then
    echo "✓ CLIP retrieval 완료"
else
    echo "✗ CLIP retrieval 실패"
    exit 1
fi

# 4단계: 검색된 object와 layout을 기반으로 scene 완성
echo "[4/4] Scene composition 수행 중..."
python scene_composition.py --root "$OUTPUT_BASE_ABS/Result_txt" --clip-results "$OUTPUT_BASE_ABS/Result_retrieval/clip_retrieval" --output "$OUTPUT_BASE_ABS/Result"

if [ $? -eq 0 ]; then
    echo "✓ Scene composition 완료"
else
    echo "✗ Scene composition 실패"
    exit 1
fi

echo ""
echo "=== 모든 단계 완료! ==="
echo "최종 결과 위치: $OUTPUT_BASE_ABS/Result"

# GLB 파일 확인 및 경로 출력
GLB_FILE=$(find "$OUTPUT_BASE_ABS/Result" -name "*.glb" -type f | head -1)
if [ -n "$GLB_FILE" ]; then
    echo "GLB 파일 생성 완료: $GLB_FILE"
else
    echo "경고: GLB 파일을 찾을 수 없습니다."
fi