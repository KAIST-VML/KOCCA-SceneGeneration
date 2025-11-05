#!/usr/bin/env python3
"""
CLIP Similarity 계산 스크립트
프롬프트 텍스트와 렌더링된 이미지 간의 CLIP similarity를 계산합니다.
"""

import os
import sys
import argparse
import torch
import numpy as np
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
from pathlib import Path
import json


class CLIPSimilarityCalculator:
    def __init__(self, model_name="openai/clip-vit-base-patch16", device=None):
        """
        CLIP 모델 초기화

        Args:
            model_name: 사용할 CLIP 모델 이름
            device: 사용할 디바이스 (None이면 자동 선택)
        """
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        print(f"🔧 CLIP 모델 로딩 중: {model_name} (디바이스: {self.device})")
        self.model = CLIPModel.from_pretrained(model_name).to(self.device)
        self.processor = CLIPProcessor.from_pretrained(model_name)
        print("✅ CLIP 모델 로딩 완료")

    def get_text_embedding(self, text):
        """
        텍스트의 CLIP embedding을 계산합니다.

        Args:
            text: 입력 텍스트

        Returns:
            정규화된 텍스트 embedding (numpy array)
        """
        inputs = self.processor(text=[text], return_tensors="pt", padding=True, truncation=True, max_length=77)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            text_features = self.model.get_text_features(**inputs)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)

        return text_features.cpu().numpy()[0]

    def get_image_embedding(self, image_path):
        """
        이미지의 CLIP embedding을 계산합니다.

        Args:
            image_path: 이미지 파일 경로

        Returns:
            정규화된 이미지 embedding (numpy array)
        """
        image = Image.open(image_path).convert("RGB")
        inputs = self.processor(images=image, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            image_features = self.model.get_image_features(**inputs)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)

        return image_features.cpu().numpy()[0]

    def calculate_similarity(self, text, image_path):
        """
        텍스트와 이미지 간의 cosine similarity를 계산합니다.

        Args:
            text: 프롬프트 텍스트
            image_path: 렌더링된 이미지 경로

        Returns:
            similarity 점수 (0~1 사이의 값)
        """
        print(f"\n📝 프롬프트: {text}")
        print(f"🖼️  이미지: {image_path}")

        # Embedding 계산
        text_emb = self.get_text_embedding(text)
        image_emb = self.get_image_embedding(image_path)

        # Cosine similarity 계산
        similarity = np.dot(text_emb, image_emb)

        print(f"📊 CLIP Similarity: {similarity:.4f}")

        return float(similarity)


def calculate_batch_similarity(prompts_file, renders_dir, output_file=None, view_type="top_view", model_name="openai/clip-vit-base-patch16"):
    """
    여러 프롬프트-이미지 쌍의 similarity를 일괄 계산합니다.

    Args:
        prompts_file: 프롬프트 목록이 담긴 파일 (한 줄에 하나씩)
        renders_dir: 렌더링된 이미지들이 있는 디렉토리
        output_file: 결과를 저장할 JSON 파일 경로 (None이면 저장하지 않음)
        view_type: 사용할 뷰 타입 ('top_view' 또는 'back_wall')
        model_name: 사용할 CLIP 모델 이름 (Hugging Face 기준)
    """
    # view_type에 따라 렌더링 파일 이름 결정
    view_filename_map = {
        "top_view": "render_01_top_view.png",
        "back_wall": "render_02_from_back_wall.png"
    }

    if view_type not in view_filename_map:
        raise ValueError(f"지원하지 않는 view_type: {view_type}. 'top_view' 또는 'back_wall'을 사용하세요.")

    render_filename = view_filename_map[view_type]

    # ⭐️ 수정된 부분: model_name을 전달받아 Calculator 생성
    calculator = CLIPSimilarityCalculator(model_name=model_name)

    # 프롬프트 읽기
    with open(prompts_file, 'r', encoding='utf-8') as f:
        prompts = [line.strip() for line in f if line.strip()]

    results = []
    total_similarity = 0.0

    print("\n" + "=" * 80)
    print("🚀 일괄 CLIP Similarity 계산 시작")
    print(f"📷 뷰 타입: {view_type} ({render_filename})")
    print(f"✅ 사용 모델: {model_name}")
    print("=" * 80)

    renders_path = Path(renders_dir)

    for i, prompt in enumerate(prompts, 1):
        print(f"\n{'='*80}")
        print(f"진행: {i}/{len(prompts)}")

        # 해당 프롬프트에 대한 이미지 찾기
        # automating_script.sh의 명명 규칙을 따름
        filename_base = prompt.lower().replace(' ', '_')
        filename_base = ''.join(c for c in filename_base if c.isalnum() or c == '_')
        filename_base = filename_base[:50]

        # 렌더링 이미지 경로 찾기
        # 두 가지 패턴 지원:
        # 1. scene_N_*/render_XX_*.png (기본 렌더링 구조)
        # 2. images/scene_N_*.png (TTA 구조)

        image_path = None

        # TTA 구조 확인 (images/scene_N_back_wall.png 또는 images/scene_N_top_view.png)
        if (renders_path / "images").exists():
            # TTA 구조
            if view_type == "back_wall":
                tta_image = renders_path / "images" / f"scene_{i-1}_back_wall.png"
            else:  # top_view
                tta_image = renders_path / "images" / f"scene_{i-1}_top_view.png"

            if tta_image.exists():
                image_path = tta_image

        # 기본 구조 확인
        if image_path is None:
            matching_dirs = list(renders_path.glob(f"scene_{i-1}_*"))
            if matching_dirs:
                image_path = matching_dirs[0] / render_filename

        # 이미지를 찾지 못한 경우
        if image_path is None:
            print(f"⚠️  경고: scene_{i-1} 이미지를 찾을 수 없습니다")
            results.append({
                "index": i - 1,
                "prompt": prompt,
                "image_path": None,
                "similarity": None,
                "error": "Image not found"
            })
            continue

        if not image_path.exists():
            print(f"⚠️  경고: 이미지 파일을 찾을 수 없습니다: {image_path}")
            results.append({
                "index": i - 1,
                "prompt": prompt,
                "image_path": str(image_path),
                "similarity": None,
                "error": "Image file not found"
            })
            continue

        try:
            similarity = calculator.calculate_similarity(prompt, str(image_path))
            total_similarity += similarity

            results.append({
                "index": i - 1,
                "prompt": prompt,
                "image_path": str(image_path),
                "similarity": similarity,
                "error": None
            })
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            results.append({
                "index": i - 1,
                "prompt": prompt,
                "image_path": str(image_path),
                "similarity": None,
                "error": str(e)
            })

    # 통계 계산
    valid_results = [r for r in results if r["similarity"] is not None]
    avg_similarity = total_similarity / len(valid_results) if valid_results else 0.0

    summary = {
        "model_name": model_name,
        "view_type": view_type,
        "total_prompts": len(prompts),
        "successful": len(valid_results),
        "failed": len(prompts) - len(valid_results),
        "average_similarity": avg_similarity,
        "results": results
    }

    # 결과 출력
    print("\n" + "=" * 80)
    print("📊 최종 결과")
    print("=" * 80)
    print(f"모델: {summary['model_name']}")
    print(f"뷰 타입: {summary['view_type']}")
    print(f"총 프롬프트: {summary['total_prompts']}개")
    print(f"성공: {summary['successful']}개")
    print(f"실패: {summary['failed']}개")
    print(f"평균 CLIP Similarity: {avg_similarity:.4f}")
    print("\n개별 결과:")
    print("-" * 80)

    for result in results:
        status = "✅" if result["similarity"] is not None else "❌"
        sim_str = f"{result['similarity']:.4f}" if result["similarity"] is not None else "N/A"
        print(f"{status} [{result['index']}] {sim_str} - {result['prompt'][:60]}...")

    # 결과 저장
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        print(f"\n💾 결과가 저장되었습니다: {output_file}")

    return summary


def main():
    parser = argparse.ArgumentParser(
        description='CLIP Similarity 계산 - 프롬프트와 렌더링된 이미지 비교'
    )

    # 단일 비교 모드
    parser.add_argument('--text', type=str, help='비교할 텍스트 프롬프트')
    parser.add_argument('--image', type=str, help='비교할 이미지 경로')

    # 일괄 처리 모드
    parser.add_argument('--prompts-file', type=str, help='프롬프트 목록 파일')
    parser.add_argument('--renders-dir', type=str, help='렌더링 결과 디렉토리')
    parser.add_argument('--output', type=str, help='결과 저장 경로 (JSON)')
    parser.add_argument('--view-type', type=str, default='top_view',
                        choices=['top_view', 'back_wall'],
                        help='사용할 뷰 타입 (기본값: top_view)')

    # ⭐️ 수정된 부분: 모델 선택 인자 추가
    parser.add_argument('--model-name', type=str,
                        default='openai/clip-vit-base-patch16',
                        help='사용할 CLIP 모델 이름 (Hugging Face 기준)')

    args = parser.parse_args()
    
    # ⭐️ 수정된 부분: args에서 model_name 가져오기
    model_name = args.model_name

    # 단일 비교 모드
    if args.text and args.image:
        if not os.path.exists(args.image):
            print(f"❌ 이미지 파일을 찾을 수 없습니다: {args.image}")
            sys.exit(1)
        
        # ⭐️ 수정된 부분: model_name 전달
        calculator = CLIPSimilarityCalculator(model_name=model_name)
        similarity = calculator.calculate_similarity(args.text, args.image)
        print(f"\n✅ 최종 similarity: {similarity:.4f}")

    # 일괄 처리 모드
    elif args.prompts_file and args.renders_dir:
        if not os.path.exists(args.prompts_file):
            print(f"❌ 프롬프트 파일을 찾을 수 없습니다: {args.prompts_file}")
            sys.exit(1)

        if not os.path.exists(args.renders_dir):
            print(f"❌ 렌더링 디렉토리를 찾을 수 없습니다: {args.renders_dir}")
            sys.exit(1)

        # ⭐️ 수정된 부분: model_name 전달
        calculate_batch_similarity(args.prompts_file, args.renders_dir, args.output, args.view_type, model_name)

    else:
        parser.print_help()
        print("\n사용 예시:")
        print("  단일 비교:")
        print("    python calculate_clip_similarity.py --text \"A modern living room\" --image render.png")
        print("\n  일괄 처리 (기본 모델):")
        print("    python calculate_clip_similarity.py --prompts-file prompts.txt --renders-dir ./renders --output results.json")
        print("\n  일괄 처리 (모델 지정):")
        print("    python calculate_clip_similarity.py --prompts-file prompts.txt --renders-dir ./renders --output results_large.json --model-name \"openai/clip-vit-large-patch14\"")
        sys.exit(1)


if __name__ == "__main__":
    main()