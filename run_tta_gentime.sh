#!/usr/bin/env bash
set -euo pipefail

PROMPTS=(
  "A 4x4 living room in modern style"
  "A 4x4 bedroom in minimalist style"
  "A 4x4 study room in contemporary style"
  "A 5x5 dining space in Scandinavian style"
  "A 4x4 guest room in classic style"
  "A 4x4 home office in industrial style"
  "A 4x4 reading corner in cozy style"
  "A 4x4 children’s bedroom in colorful style"
  "A 5x5 family lounge in warm modern style"
  "A 4x4 small living room in simple style"
)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 결과를 한 폴더에 모은다
TTA_ROOT="${1:-${SCRIPT_DIR}/tta_results}"
ITERATIONS="${2:-300}"
DATASET_BASE_PATH_ARG="${3:-}"

CONFIG_FILE="$SCRIPT_DIR/config.env"

# DATASET_BASE_PATH 설정
if [ -z "${DATASET_BASE_PATH:-}" ]; then
  if [ -n "$DATASET_BASE_PATH_ARG" ]; then
    export DATASET_BASE_PATH="$DATASET_BASE_PATH_ARG"
  elif [ -f "$CONFIG_FILE" ]; then
    # shellcheck disable=SC1090
    source "$CONFIG_FILE"
  fi
fi

if [ -z "${DATASET_BASE_PATH:-}" ]; then
  echo "[ERROR] DATASET_BASE_PATH is not set." >&2
  exit 1
fi

if [ ! -d "$DATASET_BASE_PATH" ]; then
  echo "[ERROR] DATASET_BASE_PATH directory not found: $DATASET_BASE_PATH" >&2
  exit 1
fi

if ! [[ "$ITERATIONS" =~ ^[0-9]+$ ]]; then
  echo "[ERROR] Iterations must be a positive integer (given: $ITERATIONS)" >&2
  exit 1
fi

mkdir -p "$TTA_ROOT"

PROMPTS_FILE="$TTA_ROOT/prompts.txt"
LOG_FILE="$TTA_ROOT/Log.txt"
TIME_SUMMARY_FILE="$TTA_ROOT/time_summary.txt"

: > "$PROMPTS_FILE"
: > "$LOG_FILE"
: > "$TIME_SUMMARY_FILE"

printf '[%s] START LOG\n' "$(date '+%Y-%m-%d-%H-%M-%S')" >> "$LOG_FILE"

command_exists() { command -v "$1" >/dev/null 2>&1; }

if command_exists python3; then
  PYTHON_BIN="python3"
elif command_exists python; then
  PYTHON_BIN="python"
else
  echo "[ERROR] python3/python not found" >&2
  exit 1
fi

hash_file() {
  local f="$1"
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$f" | awk '{print $1}'
  else
    shasum -a 256 "$f" | awk '{print $1}'
  fi
}

prompt_to_folder_name() {
  local prompt="$1"
  local max_length=50
  local safe_name
  safe_name=$(echo "$prompt" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9 _-]//g')
  safe_name=$(echo "$safe_name" | tr ' ' '_' | tr '-' '_')
  safe_name=$(echo "$safe_name" | sed 's/_\+/_/g')
  safe_name=$(echo "$safe_name" | sed 's/^_//; s/_$//')
  if [ ${#safe_name} -gt $max_length ]; then
    local hash_suffix
    hash_suffix=$(echo -n "$prompt" | md5sum | cut -c1-8)
    safe_name="${safe_name:0:$((max_length-9))}_${hash_suffix}"
  fi
  echo "$safe_name"
}

TOTAL=${#PROMPTS[@]}
SUCCESS=0
FAIL=0

for i in "${!PROMPTS[@]}"; do
  PROMPT="${PROMPTS[$i]}"
  printf '%s\n' "$PROMPT" >> "$PROMPTS_FILE"

  FOLDER_NAME=$(prompt_to_folder_name "$PROMPT")
  SCENE_DIR="$TTA_ROOT/$FOLDER_NAME"
  RESULT_DIR="$SCENE_DIR/Result"
  mkdir -p "$SCENE_DIR" "$RESULT_DIR"

  echo "============================================================"
  echo "Processing prompt $((i+1))/$TOTAL"
  echo "Prompt         : $PROMPT"
  echo "Scene directory: $SCENE_DIR"
  echo "============================================================"

  # 전체 시간 시작
  PROMPT_START_TS=$(date +%s)

  # 1) layout / scene 생성 시간 측정
  LAYOUT_START_TS=$(date +%s)
  if ! bash "$SCRIPT_DIR/layout_scene_api.sh" "$PROMPT" "$SCENE_DIR" "$ITERATIONS"; then
    echo "✗ Pipeline failed for prompt: $PROMPT" >&2
    FAIL=$((FAIL + 1))
    continue
  fi
  LAYOUT_END_TS=$(date +%s)
  LAYOUT_ELAPSED=$((LAYOUT_END_TS - LAYOUT_START_TS))

  # 2) GLB 찾기
  GLB_FILE=$(find "$RESULT_DIR" -type f -name '*.glb' | head -n1)
  if [ -z "$GLB_FILE" ]; then
    echo "✗ GLB file not found for prompt: $PROMPT" >&2
    FAIL=$((FAIL + 1))
    continue
  fi

  # 루트로 복사 (최종 산출물 모으기)
  ROOT_GLB="$TTA_ROOT/${FOLDER_NAME}.glb"
  cp "$GLB_FILE" "$ROOT_GLB"
  GLB_HASH=$(hash_file "$ROOT_GLB")
  printf '[%s] %s %s\n' "$(date '+%Y-%m-%d-%H-%M-%S')" "$ROOT_GLB" "$GLB_HASH" >> "$LOG_FILE"

  # 3) 렌더 시간 측정
  RENDER_START_TS=$(date +%s)
  if ! $PYTHON_BIN "$SCRIPT_DIR/complete_render.py" --glb "$GLB_FILE" --output "$SCENE_DIR"; then
    echo "✗ Rendering failed for prompt: $PROMPT" >&2
    # 렌더 실패도 기록
    {
      echo "Prompt      : $PROMPT"
      echo "RENDER      : FAILED"
      echo "--------------------------------------------"
    } >> "$LOG_FILE"
    FAIL=$((FAIL + 1))
    continue
  fi
  RENDER_END_TS=$(date +%s)
  RENDER_ELAPSED=$((RENDER_END_TS - RENDER_START_TS))

  TOP_VIEW_IMAGE="$SCENE_DIR/render_01_top_view.png"
  if [ ! -f "$TOP_VIEW_IMAGE" ]; then
    echo "✗ Top view image not found: $TOP_VIEW_IMAGE" >&2
    FAIL=$((FAIL + 1))
    continue
  fi

  # 루트로 png 복사
  ROOT_IMG="$TTA_ROOT/${FOLDER_NAME}.png"
  cp "$TOP_VIEW_IMAGE" "$ROOT_IMG"
  IMG_HASH=$(hash_file "$ROOT_IMG")
  printf '[%s] %s %s\n' "$(date '+%Y-%m-%d-%H-%M-%S')" "$ROOT_IMG" "$IMG_HASH" >> "$LOG_FILE"

  # 전체 시간 끝
  PROMPT_END_TS=$(date +%s)
  PROMPT_ELAPSED=$((PROMPT_END_TS - PROMPT_START_TS))

  # TTA 로그에 시간도 붙이기
  {
    echo "Prompt      : $PROMPT"
    echo "Layout time : ${LAYOUT_ELAPSED}s"
    echo "Render time : ${RENDER_ELAPSED}s"
    echo "Total time  : ${PROMPT_ELAPSED}s"
    echo "--------------------------------------------"
  } >> "$LOG_FILE"

  # 사람용 시간 요약
  {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $PROMPT"
    echo "  layout(s): ${LAYOUT_ELAPSED}"
    echo "  render(s): ${RENDER_ELAPSED}"
    echo "  total(s) : ${PROMPT_ELAPSED}"
    echo
  } >> "$TIME_SUMMARY_FILE"

  SUCCESS=$((SUCCESS + 1))
  echo "✓ Completed pipeline for prompt $((i+1))/$TOTAL in ${PROMPT_ELAPSED}s"
  echo ""
done

printf '[%s] END LOG\n' "$(date '+%Y-%m-%d-%H-%M-%S')" >> "$LOG_FILE"

echo "============================================================"
echo "Summary"
echo "  Total prompts : $TOTAL"
echo "  Success        : $SUCCESS"
echo "  Failed         : $FAIL"
echo "Outputs"
echo "  TTA root       : $TTA_ROOT"
echo "  Log (TTA)      : $LOG_FILE"
echo "  Time summary   : $TIME_SUMMARY_FILE"
echo "Done."
