#!/usr/bin/env bash
set -euo pipefail

# Text-to-Asset post-processing automation script.
# 1. Looks for pre-generated layout outputs for each prompt.
# 2. Runs retrieval + composition only when matching outputs already exist.
# 3. Renders the generated GLB from a top view and measures CLIP similarity.

PROMPTS=(
    "A 4x4 living room in Scandinavian style with warm wood tones and neutral colors."
    "A 5x5 bedroom in contemporary minimalist style with white walls and calm natural tones."
    "A 4x4 dining space in modern rustic style with natural wood texture and soft earthy palette."
    "A 4x4 study room in industrial style with gray walls and subtle warm color accents."
    "A 5x5 guest room in minimalist style with simple neutral design and balanced composition."
    "A 4x4 living room in mid-century modern style with warm wooden palette and clean geometry."
    "A 4x4 bedroom in bohemian style with organic materials and natural color harmony."
    "A 5x5 home office in Scandinavian style with balanced composition and light wood interior."
    "A 4x4 reading corner in cottagecore style with gentle color palette and cozy atmosphere."
    "A 5x5 family lounge in modern farmhouse style with neutral tones and wooden interior design."
)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_OUTPUT_DIR="${1:-${SCRIPT_DIR}/outputs}"
RENDER_OUTPUT_DIR="${2:-${SCRIPT_DIR}/renders_tta}"
CLIP_MODEL_NAME="${3:-laion/CLIP-ViT-H-14-laion2B-s32B-b79K}"
DATASET_BASE_PATH_ARG="${4:-}"

CONFIG_FILE="$SCRIPT_DIR/config.env"

# Source config.env when available so DATASET_BASE_PATH and other shared
# settings are consistent with the rest of the project. Allow callers to
# override by passing the dataset path explicitly or exporting the variable
# ahead of time.
if [ -z "${DATASET_BASE_PATH:-}" ]; then
  if [ -n "$DATASET_BASE_PATH_ARG" ]; then
    export DATASET_BASE_PATH="$DATASET_BASE_PATH_ARG"
  elif [ -f "$CONFIG_FILE" ]; then
    # shellcheck disable=SC1090
    source "$CONFIG_FILE"
  fi
fi

if [ -z "${DATASET_BASE_PATH:-}" ]; then
  echo "[ERROR] DATASET_BASE_PATH is not set. Provide it as the 4th argument or export the variable." >&2
  exit 1
fi

if [ ! -d "$DATASET_BASE_PATH" ]; then
  echo "[ERROR] DATASET_BASE_PATH directory not found: $DATASET_BASE_PATH" >&2
  exit 1
fi

export DATASET_BASE_PATH

if [ ! -d "$BASE_OUTPUT_DIR" ]; then
  echo "[ERROR] Base output directory not found: $BASE_OUTPUT_DIR" >&2
  exit 1
fi

mkdir -p "$RENDER_OUTPUT_DIR"

PROMPTS_FILE="$BASE_OUTPUT_DIR/prompts.txt"
CLIP_SUMMARY_FILE="$RENDER_OUTPUT_DIR/clip_summary.csv"

: > "$PROMPTS_FILE"
echo "index,prompt,image_path,clip_similarity" > "$CLIP_SUMMARY_FILE"

echo "[INFO] Using dataset base: $DATASET_BASE_PATH"

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

dir_has_content() {
  local target_dir="$1"
  if [ -d "$target_dir" ]; then
    local first_entry
    first_entry=$(find "$target_dir" -mindepth 1 -print -quit)
    [[ -n "$first_entry" ]]
  else
    return 1
  fi
}

if command_exists python3; then
  PYTHON_BIN="python3"
elif command_exists python; then
  PYTHON_BIN="python"
else
  echo "[ERROR] python3/python not found" >&2
  exit 1
fi

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
SKIPPED=0

for i in "${!PROMPTS[@]}"; do
  PROMPT="${PROMPTS[$i]}"
  printf '%s\n' "$PROMPT" >> "$PROMPTS_FILE"

  FOLDER_NAME=$(prompt_to_folder_name "$PROMPT")
  SCENE_DIR="$BASE_OUTPUT_DIR/$FOLDER_NAME"
  RESULT_TXT_DIR="$SCENE_DIR/Result_txt"
  RETRIEVAL_ROOT="$SCENE_DIR/Result_retrieval"
  RESULT_DIR="$SCENE_DIR/Result"
  RENDER_DIR="$RENDER_OUTPUT_DIR/$FOLDER_NAME"

  echo "============================================================"
  echo "Processing prompt $((i+1))/$TOTAL"
  echo "Prompt: $PROMPT"
  echo "Scene directory: $SCENE_DIR"
  echo "Render directory: $RENDER_DIR"
  echo "============================================================"

  mkdir -p "$RENDER_DIR"

  LAYOUT_FILE="$RESULT_TXT_DIR/layout.txt"

  if [ ! -f "$LAYOUT_FILE" ]; then
    echo "  - layout.txt not found, skipping prompt." >&2
    SKIPPED=$((SKIPPED + 1))
    continue
  fi

  echo "layout file: $LAYOUT_FILE"

  RETRIEVAL_DIR="$SCRIPT_DIR/space-generator/retrieval"
  if [ ! -d "$RETRIEVAL_DIR" ]; then
    echo "✗ Retrieval pipeline directory not found: $RETRIEVAL_DIR" >&2
    FAIL=$((FAIL + 1))
    continue
  fi

  TEXT_RETRIEVAL_DIR="$RETRIEVAL_ROOT/text_retrieval"
  CLIP_RETRIEVAL_DIR="$RETRIEVAL_ROOT/clip_retrieval"

  mkdir -p "$RETRIEVAL_ROOT"

  echo "[1/3] Text retrieval"
  if dir_has_content "$TEXT_RETRIEVAL_DIR"; then
    echo "  - Existing text retrieval detected, refreshing directory."
    rm -rf "$TEXT_RETRIEVAL_DIR"
  fi
  mkdir -p "$TEXT_RETRIEVAL_DIR"
  if (cd "$RETRIEVAL_DIR" && "$PYTHON_BIN" test_retrieval.py --layout_path "$LAYOUT_FILE" --output_dir "$TEXT_RETRIEVAL_DIR"); then
    echo "  ✓ Text retrieval completed."
  else
    echo "  ✗ Text retrieval failed." >&2
    FAIL=$((FAIL + 1))
    continue
  fi

  echo "[2/3] CLIP retrieval"
  if dir_has_content "$CLIP_RETRIEVAL_DIR"; then
    echo "  - Existing CLIP retrieval detected, refreshing directory."
    rm -rf "$CLIP_RETRIEVAL_DIR"
  fi
  mkdir -p "$CLIP_RETRIEVAL_DIR"
  if (cd "$RETRIEVAL_DIR" && "$PYTHON_BIN" retrieval_clip.py --layout_path "$LAYOUT_FILE" --candidate_folder "$TEXT_RETRIEVAL_DIR" --output_dir "$CLIP_RETRIEVAL_DIR"); then
    echo "  ✓ CLIP retrieval completed."
  else
    echo "  ✗ CLIP retrieval failed." >&2
    FAIL=$((FAIL + 1))
    continue
  fi

  echo "[3/3] Scene composition"
  if dir_has_content "$RESULT_DIR"; then
    echo "  - Existing scene artifacts detected, refreshing directory."
    rm -rf "$RESULT_DIR"
  fi
  mkdir -p "$RESULT_DIR"
  if (cd "$RETRIEVAL_DIR" && "$PYTHON_BIN" scene_composition.py --root "$RESULT_TXT_DIR" --clip-results "$CLIP_RETRIEVAL_DIR" --output "$RESULT_DIR"); then
    echo "  ✓ Scene composition completed."
  else
    echo "  ✗ Scene composition failed." >&2
    FAIL=$((FAIL + 1))
    continue
  fi

  GLB_FILE=$(find "$RESULT_DIR" -maxdepth 1 -type f -name '*.glb' | head -n1)
  if [ -z "$GLB_FILE" ]; then
    echo "✗ GLB file not found for prompt: $PROMPT" >&2
    FAIL=$((FAIL + 1))
    continue
  fi

  echo "GLB file: $GLB_FILE"

  if ! $PYTHON_BIN "$SCRIPT_DIR/complete_render.py" --glb "$GLB_FILE" --output "$RENDER_DIR"; then
    echo "✗ Rendering failed for prompt: $PROMPT" >&2
    FAIL=$((FAIL + 1))
    continue
  fi

  TOP_VIEW_IMAGE="$RENDER_DIR/render_01_top_view.png"

  if [ ! -f "$TOP_VIEW_IMAGE" ]; then
    echo "✗ Top view image not found: $TOP_VIEW_IMAGE" >&2
    FAIL=$((FAIL + 1))
    continue
  fi

  echo "Top view image: $TOP_VIEW_IMAGE"

  CLIP_OUTPUT=$($PYTHON_BIN "$SCRIPT_DIR/calculate_clip_similarity.py" \
    --text "$PROMPT" \
    --image "$TOP_VIEW_IMAGE" \
    --model-name "$CLIP_MODEL_NAME" 2>&1)

  printf '%s\n' "$CLIP_OUTPUT"

  SIMILARITY=$(printf '%s' "$CLIP_OUTPUT" | $PYTHON_BIN - <<'PY'
import re, sys
text = sys.stdin.read()
match = re.search(r"similarity:\s*([0-9.]+)", text)
print(match.group(1) if match else "")
PY
)

  if [ -z "$SIMILARITY" ]; then
    echo "✗ Failed to parse CLIP similarity" >&2
    FAIL=$((FAIL + 1))
    continue
  fi

  ESCAPED_PROMPT=$(printf '%s' "$PROMPT" | sed 's/"/""/g')
  printf '%s,"%s","%s",%s\n' "$i" "$ESCAPED_PROMPT" "$TOP_VIEW_IMAGE" "$SIMILARITY" >> "$CLIP_SUMMARY_FILE"

  SUCCESS=$((SUCCESS + 1))
  echo "✓ Completed pipeline for prompt $((i+1))/$TOTAL"
  echo ""
done

echo "============================================================"
echo "Summary"
echo "  Total prompts : $TOTAL"
echo "  Success        : $SUCCESS"
echo "  Failed         : $FAIL"
echo "  Skipped        : $SKIPPED"
echo "Outputs"
echo "  Layout base    : $BASE_OUTPUT_DIR"
echo "  Renders        : $RENDER_OUTPUT_DIR"
echo "  Prompts file   : $PROMPTS_FILE"
echo "  CLIP summary   : $CLIP_SUMMARY_FILE"
echo "  Dataset base   : $DATASET_BASE_PATH"
echo "Done."
