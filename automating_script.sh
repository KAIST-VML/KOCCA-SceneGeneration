#!/bin/bash

# 방 크기, 스타일, 목적에 초점을 맞춘 프롬프트들을 배열로 정의합니다.
PROMPTS=(
    "A compact 4x4 study space with a clean and functional Scandinavian design."
    "A long 6x3 gallery-style hallway for displaying art, with a bright and neutral theme."
    "A large 8x6 open-plan area for family gatherings, with a comfortable and casual style."
    "A 4x5 child room for a child's creative play, with a vibrant and colorful theme."
    "A moody and dark 5x5 room for a home theater, with an industrial-chic style."
    "A bright 4x3 sunroom for relaxation and plants, with a bohemian and natural vibe."
    "A formal 6x6 dining space for elegant dinners, with a classic and traditional decor."
)

# 결과물을 저장할 디렉토리를 지정합니다. (없으면 생성)
OUTPUT_DIR="./style_renders_robust2"
mkdir -p "$OUTPUT_DIR"

# 배열의 각 프롬프트를 순회하며 client.py를 실행합니다.
for i in "${!PROMPTS[@]}"; do
    PROMPT="${PROMPTS[$i]}"
    
    # 파일 이름으로 사용하기 위해 프롬프트를 간단하게 변환합니다.
    FILENAME=$(echo "$PROMPT" | tr '[:upper:]' '[:lower:]' | tr ' ' '_' | sed 's/[^a-z0-9_]//g' | cut -c1-50)
    
    # 최종 파일 경로를 설정합니다.
    OUTPUT_FILE="$OUTPUT_DIR/scene_${i}_${FILENAME}.glb"
    
    echo "=================================================="
    echo "Starting render #$((i+1))/${#PROMPTS[@]}"
    echo "Prompt: $PROMPT"
    echo "Output file: $OUTPUT_FILE"
    echo "=================================================="
    
    # client.py 스크립트를 실행하고, 성공/실패 여부를 확인합니다.
    python client.py "$PROMPT" "$OUTPUT_FILE"
    
    # ★★★ 이 부분이 핵심입니다 ★★★
    # 바로 직전에 실행한 명령어(python client.py)가 실패했는지 확인합니다.
    # ($?는 직전 명령어의 종료 코드를 의미하며, 0이 아니면 실패입니다.)
    if [ $? -ne 0 ]; then
        echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
        echo "!!! Render #$((i+1)) FAILED. Continuing to the next one. !!!"
        echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    else
        echo "Render #$((i+1)) finished successfully."
    fi
    
    echo ""
done

echo "All render jobs are complete. Check the '$OUTPUT_DIR' directory for results."