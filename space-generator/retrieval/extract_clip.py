from transformers import CLIPProcessor, CLIPModel
import torch
from PIL import Image
import os

clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch16").cuda()
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch16")

import os
import numpy as np
from tqdm import tqdm

def extract_clip_image_embedding(image_path):
    image = Image.open(image_path).convert("RGB")
    inputs = clip_processor(images=image, return_tensors="pt")
    inputs = {k: v.cuda() for k, v in inputs.items()}
    with torch.no_grad():
        image_features = clip_model.get_image_features(**inputs)
        image_features = image_features / image_features.norm(dim=-1, keepdim=True)  # normalize
    return image_features.cpu().numpy()[0]  # shape: (512,)

def collect_model_image_embeddings(root_dirs, save_path="clip_image_embeddings.npy"):
    embedding_dict = {}
    for root_dir in root_dirs:
        for model_id in tqdm(os.listdir(root_dir), desc=f"Folder: {root_dir}"):
            if model_id in embedding_dict:    # 이미 임베딩이 있으면 skip!
                continue
            sub_dir = os.path.join(root_dir, model_id)
            image_path = os.path.join(sub_dir, "image.jpg")
            if not os.path.isfile(image_path):
                continue
            try:
                emb = extract_clip_image_embedding(image_path)
                embedding_dict[model_id] = emb
            except Exception as e:
                print(f"Failed: {model_id} ({image_path}) - {e}")
    np.save(save_path, embedding_dict)
    print(f"Done! Total embeddings: {len(embedding_dict)}")

# 사용 예시:
base_path = os.environ.get('DATASET_BASE_PATH', '../../dataset')
root_folders = [
    os.path.join(base_path, "3D-FUTURE-model-part1"),
    os.path.join(base_path, "3D-FUTURE-model-part2"),
    os.path.join(base_path, "3D-FUTURE-model-part3"),
    os.path.join(base_path, "3D-FUTURE-model-part4")
]
collect_model_image_embeddings(root_folders, save_path="clip_image_embeddings.npy")
