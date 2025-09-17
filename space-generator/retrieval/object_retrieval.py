import os
import json
from typing import List, Dict, Optional

import os
import json
from typing import List, Dict, Optional

# 후보 스타일, 재질, 카테고리 테이블
_ATTR_STYLE = [
    {'id': 0, 'category': 'Modern'}, {'id': 1, 'category': 'Chinoiserie'}, {'id': 2, 'category': 'Kids'},
    {'id': 3, 'category': 'European'}, {'id': 4, 'category': 'Japanese'}, {'id': 5, 'category': 'Southeast Asia'},
    {'id': 6, 'category': 'Industrial'}, {'id': 7, 'category': 'American Country'}, {'id': 8, 'category': 'Vintage/Retro'},
    {'id': 9, 'category': 'Light Luxury'}, {'id': 10, 'category': 'Mediterranean'}, {'id': 11, 'category': 'Korean'},
    {'id': 12, 'category': 'New Chinese'}, {'id': 13, 'category': 'Nordic'}, {'id': 14, 'category': 'European Classic'},
    {'id': 15, 'category': 'Others'}, {'id': 16, 'category': 'Ming Qing'}, {'id': 17, 'category': 'Neoclassical'},
    {'id': 18, 'category': 'Minimalist'}
]

_ATTR_MATERIAL = [
    {'id': 5, 'category': 'Solid Wood'}, {'id': 12, 'category': 'Wood'},
    {'id': 11, 'category': 'Rough Cloth'}, {'id': 1, 'category': 'Cloth'},
    {'id': 2, 'category': 'Leather'}, {'id': 4, 'category': 'Metal'},
]

_CATEGORIES_3D = [
    {'id': 13, 'category': 'King-size Bed'}, {'id': 14, 'category': 'Bunk Bed'},
    {'id': 15, 'category': 'Bed Frame'}, {'id': 16, 'category': 'Single bed'},
    {'id': 25, 'category': 'Desk'}, {'id': 4, 'category': 'Wardrobe'},
    {'id': 10, 'category': 'Drawer Chest / Corner cabinet'}, {'id': 35, 'category': 'Shoe Cabinet'},
    {'id': 19, 'category': 'Lounge Chair / Cafe Chair / Office Chair'},
    {'id': 20, 'category': 'Dressing Chair'}, {'id': 11, 'category': 'Shelf'},
]

def load_all_model_info(root_dirs: List[str]) -> List[Dict]:
    all_data = []
    for root in root_dirs:
        info_path = os.path.join(root, "model_info.json")
        if os.path.exists(info_path):
            with open(info_path, "r") as f:
                all_data.extend(json.load(f))
    return all_data

def find_best_match(keywords: List[str], candidates: List[Dict], key: str = "category") -> Optional[str]:
    for kw in keywords:
        for c in candidates:
            if kw.lower() in c[key].lower():
                return c[key]
    return None

def extract_keywords_from_description(desc: str) -> Dict:
    return {
        "category_keywords": ["bed", "platform"],
        "style_keywords": ["modern", "minimalist"],
        "material_keywords": ["wood", "upholstered"],
    }

def retrieve_by_metadata(
    dataset: List[Dict],
    category: Optional[str] = None,
    style: Optional[str] = None,
    material: Optional[str] = None
) -> List[Dict]:
    results = []
    for obj in dataset:
        if category and category.lower() not in (obj.get('category') or '').lower():
            continue
        if style and style.lower() != (obj.get('style') or '').lower():
            continue
        if material and material.lower() != (obj.get('material') or '').lower():
            continue
        results.append(obj)
    return results

def structured_retrieval_from_description(desc: str, dataset: List[Dict]) -> List[Dict]:
    kw = extract_keywords_from_description(desc)
    category = find_best_match(kw["category_keywords"], _CATEGORIES_3D)
    style = find_best_match(kw["style_keywords"], _ATTR_STYLE)
    material = find_best_match(kw["material_keywords"], _ATTR_MATERIAL)
    return retrieve_by_metadata(dataset, category=category, style=style, material=material)
