#!/bin/bash
# 전체 프롬프트를 순회하며 Layout 생성까지 실행하는 스크립트
# API를 사용하지 않고 Python 파일을 직접 background로 실행

set -e  # 에러 발생 시 스크립트 중단


# 스크립트 디렉토리 확인
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# config.env 파일 로드
if [ -f "$SCRIPT_DIR/config.env" ]; then
    source "$SCRIPT_DIR/config.env"
    echo "Loaded config.env"
else
    echo "Warning: config.env not found, using existing environment variables"
fi

# API 키 확인
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: OPENAI_API_KEY is not set"
    echo "Please set it in config.env or as an environment variable"
    exit 1
fi

# 프롬프트 배열 정의 (automating_script.sh와 동일)
PROMPTS=(
    "A modern 4x4 living room interior shot in Scandinavian style, with a beige sofa, light wood coffee table, and large window letting in daylight.",
    "A cozy 4x5 bedroom in bohemian style, with warm ambient light, woven rug, rattan chair, and soft pastel fabrics.",
    "A minimalist 6x6 open-plan living room in contemporary style, with white walls, sleek furniture, and natural sunlight.",
    "A 4x5 dining space in modern rustic style, with a solid oak table, pendant lamps, and green indoor plants.",
    "A spacious 6x6 living-dining room in mid-century modern style, with walnut furniture, leather chairs, and a bright airy atmosphere.",
    "A 4x4 children’s bedroom in Scandinavian style, with light wood furniture, colorful toys, and a soft rug on the floor.",
    "A calm 4x5 guest room in minimalist style, with a single bed, linen bedding, and a neutral beige palette.",
    "A 6x6 home office in industrial style, with a metal desk, exposed brick wall, and hanging warm lights.",
    "A cozy 4x4 reading corner in cottagecore style, with a wooden armchair, bookshelf, floral patterns, and sunlight from a nearby window.",
    "A 4x5 family lounge in modern farmhouse style, with white shiplap walls, wooden beams, and comfortable beige sofas."

)
# 결과물을 저장할 베이스 디렉토리
OUTPUT_DIR="./outputs"
mkdir -p "$OUTPUT_DIR"

# 기본 경로 설정
BASE_PATH="${SCRIPT_DIR}/space-generator"
SCENE_SYNTHESIS_PATH="${BASE_PATH}/Scene_Synthesis"

# 프롬프트를 폴더명으로 변환하는 함수
prompt_to_folder_name() {
    local prompt="$1"
    local max_length=50

    # 소문자 변환 및 특수문자 제거
    local safe_name=$(echo "$prompt" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9 _-]//g')
    # 공백을 언더스코어로 변환
    safe_name=$(echo "$safe_name" | tr ' ' '_' | tr '-' '_')
    # 연속된 언더스코어 제거
    safe_name=$(echo "$safe_name" | sed 's/_\+/_/g')
    # 앞뒤 언더스코어 제거
    safe_name=$(echo "$safe_name" | sed 's/^_//; s/_$//')

    # 최대 길이 제한
    if [ ${#safe_name} -gt $max_length ]; then
        # 해시를 추가하여 고유성 보장
        local hash_suffix=$(echo -n "$prompt" | md5sum | cut -c1-8)
        safe_name="${safe_name:0:$((max_length-9))}_${hash_suffix}"
    fi

    echo "$safe_name"
}

# 로그 디렉토리 생성
LOG_DIR="${OUTPUT_DIR}/logs"
mkdir -p "$LOG_DIR"

# PID 추적용 배열
declare -a PIDS=()
declare -a FOLDERS=()

echo "=================================================="
echo "Scene Layout Generation Pipeline"
echo "=================================================="
echo "Total prompts: ${#PROMPTS[@]}"
echo "Output directory: $OUTPUT_DIR"
echo "Logs directory: $LOG_DIR"
echo ""

# 각 프롬프트에 대해 작업 시작
for i in "${!PROMPTS[@]}"; do
    PROMPT="${PROMPTS[$i]}"

    # 프롬프트를 폴더명으로 변환
    FOLDER_NAME=$(prompt_to_folder_name "$PROMPT")
    OUTPUT_PATH="${OUTPUT_DIR}/${FOLDER_NAME}"
    RESULT_TXT_PATH="${OUTPUT_PATH}/Result_txt"

    # 출력 디렉토리 생성
    mkdir -p "$RESULT_TXT_PATH"

    # 절대 경로로 변환
    OUTPUT_PATH="$(cd "$OUTPUT_PATH" && pwd)"
    RESULT_TXT_PATH="${OUTPUT_PATH}/Result_txt"

    # 로그 파일 경로 (절대 경로로 변환)
    LOG_FILE="$(cd "$LOG_DIR" && pwd)/${FOLDER_NAME}.log"

    echo "=================================================="
    echo "Starting job #$((i+1))/${#PROMPTS[@]}"
    echo "Prompt: $PROMPT"
    echo "Folder: $FOLDER_NAME"
    echo "Output: $RESULT_TXT_PATH"
    echo "Log: $LOG_FILE"
    echo "=================================================="

    # Layout.txt가 이미 존재하는지 확인
    LAYOUT_FILE="${RESULT_TXT_PATH}/layout.txt"
    if [ -f "$LAYOUT_FILE" ]; then
        echo "⏭️  Layout already exists, skipping: $LAYOUT_FILE"
        echo ""
        continue
    fi

    # Background로 Python 스크립트 실행
    (
        # 로그 디렉토리가 존재하는지 확인 및 생성
        mkdir -p "$(dirname "$LOG_FILE")"

        cd "$SCENE_SYNTHESIS_PATH"
        echo "=== Starting layout generation ===" > "$LOG_FILE"
        echo "Time: $(date)" >> "$LOG_FILE"
        echo "Prompt: $PROMPT" >> "$LOG_FILE"
        echo "Output: $RESULT_TXT_PATH" >> "$LOG_FILE"
        echo "" >> "$LOG_FILE"

        python scene_synthesis.py \
            --scene_descriptor "$PROMPT" \
            --save_path "$RESULT_TXT_PATH" \
            --iterations 300 \
            >> "$LOG_FILE" 2>&1

        EXIT_CODE=$?
        echo "" >> "$LOG_FILE"
        echo "=== Completed ===" >> "$LOG_FILE"
        echo "Exit code: $EXIT_CODE" >> "$LOG_FILE"
        echo "Time: $(date)" >> "$LOG_FILE"

        if [ $EXIT_CODE -eq 0 ]; then
            echo "✓ Layout generation successful" >> "$LOG_FILE"
            # 성공 마커 파일 생성
            touch "${OUTPUT_PATH}/.success"
        else
            echo "✗ Layout generation failed" >> "$LOG_FILE"
            # 실패 마커 파일 생성
            touch "${OUTPUT_PATH}/.failed"
        fi
    ) &

    # PID 저장
    PID=$!
    PIDS+=($PID)
    FOLDERS+=("$FOLDER_NAME")

    echo "🔄 Started background process (PID: $PID)"
    echo ""

    # 너무 많은 프로세스가 동시에 실행되지 않도록 제한
    # 최대 3개까지만 동시 실행
    if [ ${#PIDS[@]} -ge 3 ]; then
        echo "⏳ Waiting for some processes to complete..."
        wait ${PIDS[0]}
        echo "✓ Process ${PIDS[0]} (${FOLDERS[0]}) completed"
        # 배열에서 첫 번째 항목 제거
        PIDS=("${PIDS[@]:1}")
        FOLDERS=("${FOLDERS[@]:1}")
        echo ""
    fi
done

# 모든 background 프로세스가 완료될 때까지 대기
if [ ${#PIDS[@]} -gt 0 ]; then
    echo "=================================================="
    echo "Waiting for all remaining processes to complete..."
    echo "Remaining processes: ${#PIDS[@]}"
    echo "=================================================="

    for i in "${!PIDS[@]}"; do
        PID=${PIDS[$i]}
        FOLDER=${FOLDERS[$i]}
        echo "⏳ Waiting for PID $PID ($FOLDER)..."
        wait $PID
        EXIT_CODE=$?
        if [ $EXIT_CODE -eq 0 ]; then
            echo "✓ Process $PID ($FOLDER) completed successfully"
        else
            echo "✗ Process $PID ($FOLDER) failed with exit code $EXIT_CODE"
        fi
    done
fi

echo ""
echo "=================================================="
echo "All jobs completed!"
echo "=================================================="
echo ""

# 결과 요약
echo "=== Results Summary ==="
TOTAL=${#PROMPTS[@]}
SUCCESS_COUNT=0
FAILED_COUNT=0
SKIPPED_COUNT=0

for i in "${!PROMPTS[@]}"; do
    PROMPT="${PROMPTS[$i]}"
    FOLDER_NAME=$(prompt_to_folder_name "$PROMPT")
    OUTPUT_PATH="${OUTPUT_DIR}/${FOLDER_NAME}"
    LAYOUT_FILE="${OUTPUT_PATH}/Result_txt/layout.txt"

    if [ -f "${OUTPUT_PATH}/.success" ]; then
        echo "✓ #$((i+1)): $FOLDER_NAME (SUCCESS)"
        ((SUCCESS_COUNT++))
    elif [ -f "${OUTPUT_PATH}/.failed" ]; then
        echo "✗ #$((i+1)): $FOLDER_NAME (FAILED)"
        ((FAILED_COUNT++))
    elif [ -f "$LAYOUT_FILE" ]; then
        echo "⏭️  #$((i+1)): $FOLDER_NAME (SKIPPED - already exists)"
        ((SKIPPED_COUNT++))
    else
        echo "? #$((i+1)): $FOLDER_NAME (UNKNOWN)"
    fi
done

echo ""
echo "Total: $TOTAL"
echo "Success: $SUCCESS_COUNT"
echo "Failed: $FAILED_COUNT"
echo "Skipped: $SKIPPED_COUNT"
echo ""
echo "Check logs in: $LOG_DIR"
echo "Check results in: $OUTPUT_DIR"
echo "=================================================="