from transformers import CLIPProcessor, CLIPModel
import torch
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import os
import re
import time
import hashlib

clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch16").cuda()
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch16")


def _sanitize_object_name(object_name: str, max_length: int = 100) -> str:
    """Match the filename sanitization used during text retrieval."""

    slug = re.sub(r"[^a-z0-9]+", "_", object_name.lower())
    slug = slug.strip("_")

    if not slug:
        slug = "object"

    if len(slug) > max_length:
        suffix = hashlib.md5(object_name.encode("utf-8")).hexdigest()[:8]
        slug = f"{slug[: max_length - 9]}_{suffix}"

    return slug

def get_clip_text_embedding(text):
    max_length = 77
    inputs = clip_processor(text=[text], return_tensors="pt", padding=True, truncation=True, max_length=max_length)
    inputs = {k: v.cuda() for k, v in inputs.items()}
    with torch.no_grad():
        emb = clip_model.get_text_features(**inputs)
        emb = emb / emb.norm(dim=-1, keepdim=True)
    return emb.cpu().numpy()[0]

def clip_similarity_rerank(candidate_items, query_text, embedding_dict, top_k=1):
    # 1. 쿼리 텍스트를 CLIP text embedding으로
    text_emb = get_clip_text_embedding(query_text).reshape(1, -1)

    # 2. 후보군 embedding 비교
    sims = []
    for item, _score in candidate_items:
        model_id = item['model_id']
        img_emb = embedding_dict.get(model_id)
        if img_emb is not None:
            sim = cosine_similarity(img_emb.reshape(1, -1), text_emb)[0][0]
            sims.append((sim, item))
    
    if not sims:
        return []
        
    sims.sort(reverse=True, key=lambda x: x[0])
    return [item for sim, item in sims[:top_k]]

def create_simple_prompt(object_name, style_line, color_line):
    """간단하고 짧은 프롬프트 생성"""
    keywords = []
    
    if style_line:
        style_words = [w for w in style_line.split() if w.lower() not in ['with', 'a', 'the', 'and', 'bed', 'design']]
        keywords.extend(style_words[:3])
    
    if color_line:
        color_words = [w for w in color_line.split() if w.lower() not in ['with', 'and', 'the', 'a']]
        keywords.extend(color_words[:3])
    
    prompt = f"{object_name.strip()} {' '.join(keywords)}".strip()
    return prompt[:50]

def parse_numbered_blocks(text):
    """
    숫자. **이름** 으로 시작하는 블록을 모두 분리하고 이름 정리
    ex) 1. **Sofa:** ... ~ 2. **TV Stand** ... 형태
    """
    import re
    
    pattern = re.compile(
        r'^\s*(\d+)[\.\)\-:\s]+\*\*([^*]+)\*\*[\s\S]*?(?=^\s*\d+[\.\)\-:\s]+\*\*|$\Z)',
        re.MULTILINE
    )
    blocks = []
    for match in pattern.finditer(text):
        item_number = match.group(1)
        object_name = match.group(2).strip()
        
        # 이름 정리: 콜론과 특수문자 제거, 소문자로 변환
        clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', object_name)  # 특수문자 제거
        clean_name = re.sub(r'\s+', ' ', clean_name)  # 여러 공백을 하나로
        clean_name = clean_name.strip().lower()  # 앞뒤 공백 제거 후 소문자
        
        block = match.group(0).strip()
        blocks.append((clean_name, block))
    return blocks

def clip_rerank_for_all_objects(results_by_object, query_text, embedding_dict, database, top_k=5):
    """모든 object에 대해 CLIP reranking 수행"""
    
    db_by_id = {item['model_id']: item for item in database}
    final_selection = {}

    # [수정] 한 줄로 파싱!
    items = parse_numbered_blocks(query_text)
    
    print(f"🔍 파싱된 object 수: {len(items)}")
    for i, (name, _) in enumerate(items, 1):
        print(f"  {i}. {name}")
    
    print(f"\n🎯 CLIP Reranking 시작 (총 {len(items)}개 object)")
    print("=" * 60)
    
    print(f"🔍 파싱된 object 수: {len(items)}")
    for i, (name, _) in enumerate(items, 1):
        print(f"  {i}. {name}")
    
    print(f"\n🎯 CLIP Reranking 시작 (총 {len(items)}개 object)")
    print("=" * 60)
    
    for object_name, object_block in items:
        obj_start = time.time()
        obj_key = object_name.strip().lower()
        slug_key = _sanitize_object_name(obj_key)

        print(f"\n🔍 처리 중: {object_name.upper()}")

        # 후보 ID 리스트 가져오기
        id_list = results_by_object.get(slug_key)

        if not id_list:
            legacy_keys = {
                obj_key,
                obj_key.replace(" ", "_"),
                slug_key.replace("_", " ")
            }

            for legacy_key in legacy_keys:
                if legacy_key in results_by_object:
                    id_list = results_by_object[legacy_key]
                    break

        if not id_list:
            print(f"❌ {obj_key} 후보 없음 → 전체 DB에서 검색 시도")
            candidate_items = [(item, 0) for item in database]
        else:
            candidate_items = [(db_by_id[mid], 0) for mid in id_list if mid in db_by_id]

        if not candidate_items:
            print(f"❌ {obj_key} 매칭 아이디 없음")
            final_selection[object_name] = []
            continue
            
        print(f"✅ 유효한 후보: {len(candidate_items)}개")
        
        # Style, Color 추출
        style_line = ''
        color_line = ''
        for line in object_block.split('\n'):
            line = line.strip()
            if line.lower().startswith('- **style**:'):
                style_line = line.split(":", 1)[-1].strip()
            if line.lower().startswith('- **color**:'):
                color_line = line.split(":", 1)[-1].strip()

        # 간단한 프롬프트 생성
        prompt = create_simple_prompt(object_name, style_line, color_line)
        print(f"💬 프롬프트: '{prompt}'")

        # CLIP reranking 수행
        try:
            rerank_start = time.time()
            reranked = clip_similarity_rerank(candidate_items, prompt, embedding_dict, top_k=top_k)
            rerank_end = time.time()
            
            if reranked:
                print(f"🎉 CLIP Top-{len(reranked)} 결과 ({rerank_end - rerank_start:.2f}초):")
                for i, item in enumerate(reranked, 1):
                    print(f"   {i}. {item['model_id']}")
                final_selection[object_name] = reranked
            else:
                print(f"❌ CLIP 결과 없음 (임베딩 누락)")
                final_selection[object_name] = []
                
        except Exception as e:
            print(f"❌ CLIP 처리 오류: {e}")
            final_selection[object_name] = []
            
        obj_end = time.time()
        print(f"⏱️ {object_name} 처리 시간: {obj_end - obj_start:.2f}초")

    return final_selection

def load_candidate_ids_from_folder(folder_path):
    if not os.path.exists(folder_path):
        print(f"❌ 폴더가 존재하지 않습니다: {folder_path}")
        return {}
        
    candidates_by_object = {}
    for filename in os.listdir(folder_path):
        if not filename.endswith("_results.txt"):
            continue
        object_name = filename.replace("_results.txt", "").lower()
        path = os.path.join(folder_path, filename)
        with open(path, "r", encoding="utf-8") as f:
            ids = [line.strip() for line in f if line.strip()]
        candidates_by_object[object_name] = ids
        print(f"📂 {object_name}: {len(ids)}개 후보 로드됨")
        
    return candidates_by_object

def save_clip_results(final_results, output_dir):
    """CLIP 결과를 파일로 저장"""
    os.makedirs(output_dir, exist_ok=True)
    
    for object_name, items in final_results.items():
        filename = f"{object_name.lower()}.txt"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            for item in items:
                model_id = item['model_id'] if isinstance(item, dict) else item
                f.write(f"{model_id}\n")
        
        print(f"💾 {object_name} CLIP 결과 저장: {filepath} ({len(items)}개)")

def main(query_text_path, candidate_folder, output_dir):
    start_time = time.time()
    print("🚀 CLIP 기반 가구 검색 시작")
    print("=" * 60)

    # 경로 설정
    base_path = os.environ.get('DATASET_BASE_PATH', '../../dataset')
    folder_paths = [
        os.path.join(base_path, "3D-FUTURE-model-part1"),
        os.path.join(base_path, "3D-FUTURE-model-part2"),
        os.path.join(base_path, "3D-FUTURE-model-part3"),
        os.path.join(base_path, "3D-FUTURE-model-part4")
    ]
    embedding_path = "clip_image_embeddings.npy"

    # 1. 쿼리 텍스트 파일에서 읽기
    with open(query_text_path, "r", encoding="utf-8") as f:
        query_text = f.read()

    # 2. 데이터 로딩
    load_start = time.time()
    print("📚 데이터베이스 로딩 중...")
    from object_retrieval import load_all_model_info
    database = load_all_model_info(folder_paths)
    print(f"✅ 데이터베이스: {len(database)}개 아이템 로드")
    
    print("🖼️ CLIP 임베딩 로딩 중...")
    import numpy as np
    embedding_dict = np.load(embedding_path, allow_pickle=True).item()
    print(f"✅ CLIP 임베딩: {len(embedding_dict)}개 로드")
    
    print("📂 후보 ID 파일 로딩 중...")
    candidates_by_object = load_candidate_ids_from_folder(candidate_folder)
    load_end = time.time()
    print(f"⏱️ 데이터 로딩 시간: {load_end - load_start:.2f}초")
    
    # 3. CLIP reranking 수행
    clip_start = time.time()
    final_results = clip_rerank_for_all_objects(
        candidates_by_object, query_text, embedding_dict, database, top_k=5
    )
    clip_end = time.time()
    print(f"\n⏱️ 전체 CLIP 처리 시간: {clip_end - clip_start:.2f}초")
    
    # 4. 결과 저장
    save_start = time.time()
    if final_results:
        save_clip_results(final_results, output_dir)
        save_end = time.time()
        print(f"⏱️ 결과 저장 시간: {save_end - save_start:.2f}초")
        
        print(f"\n🎯 최종 결과 요약:")
        print("=" * 40)
        for obj_name, items in final_results.items():
            print(f"🔸 {obj_name}: {len(items)}개 선정")
    else:
        print("❌ 최종 결과가 없습니다!")
    
    total_time = time.time() - start_time
    print(f"\n⏱️ 총 실행 시간: {total_time:.2f}초")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="CLIP reranking for furniture retrieval")

    parser.add_argument(
        "--layout_path", default="/source/sumin/stylin/Scene_Synthesis/Result_txt/layout.txt", type=str, required=True,
        help="Path to the layout.txt file (LLM prompt result)"
    )
    parser.add_argument(
        "--candidate_folder", default="/source/sumin/stylin/Scene_Synthesis/Result_retrieval/text_retrieval", type=str, required=True,
        help="Folder containing *_results.txt files"
    )
    parser.add_argument(
        "--output_dir", type=str, default="/source/sumin/stylin/Scene_Synthesis/Result_retrieval/clip_retrieval",
        help="Directory where CLIP rerank results will be saved"
    )

    args = parser.parse_args()

    # main 함수에 output_dir 추가 필요
    main(args.layout_path, args.candidate_folder, args.output_dir)
