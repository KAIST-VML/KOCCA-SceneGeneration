
import json
import re
import os
from typing import List, Dict, Tuple, Set
from collections import defaultdict, Counter
from difflib import SequenceMatcher
import math
import argparse


# 데이터베이스 카테고리 정의
_ATTR_STYLE = [
    {'id': 0, 'category': 'Modern'},
    {'id': 1, 'category': 'Chinoiserie'},
    {'id': 2, 'category': 'Kids'},
    {'id': 3, 'category': 'European'},
    {'id': 4, 'category': 'Japanese'},
    {'id': 5, 'category': 'Southeast Asia'},
    {'id': 6, 'category': 'Industrial'},
    {'id': 7, 'category': 'American Country'},
    {'id': 8, 'category': 'Vintage/Retro'},
    {'id': 9, 'category': 'Light Luxury'},
    {'id': 10, 'category': 'Mediterranean'},
    {'id': 11, 'category': 'Korean'},
    {'id': 12, 'category': 'New Chinese'},
    {'id': 13, 'category': 'Nordic'},
    {'id': 14, 'category': 'European Classic'},
    {'id': 15, 'category': 'Others'},
    {'id': 16, 'category': 'Ming Qing'},
    {'id': 17, 'category': 'Neoclassical'},
    {'id': 18, 'category': 'Minimalist'},
]

_ATTR_MATERIAL = [
    {'id': 0, 'category': 'Composition'},
    {'id': 1, 'category': 'Cloth'},
    {'id': 2, 'category': 'Leather'},
    {'id': 3, 'category': 'Glass'},
    {'id': 4, 'category': 'Metal'},
    {'id': 5, 'category': 'Solid Wood'},
    {'id': 6, 'category': 'Stone'},
    {'id': 7, 'category': 'Plywood'},
    {'id': 8, 'category': 'Others'},
    {'id': 9, 'category': 'Suede'},
    {'id': 10, 'category': 'Bamboo Rattan'},
    {'id': 11, 'category': 'Rough Cloth'},
    {'id': 12, 'category': 'Wood'},
    {'id': 13, 'category': 'Composite Board'},
    {'id': 14, 'category': 'Marble'},
    {'id': 15, 'category': 'Smooth Leather'},
]

_ATTR_THEME = [
    {'id': 0, 'category': 'Smooth Net'},
    {'id': 1, 'category': 'Lines'},
    {'id': 2, 'category': 'Wrought Iron'},
    {'id': 3, 'category': 'Cartoon'},
    {'id': 4, 'category': 'Granite Texture'},
    {'id': 5, 'category': 'Floral'},
    {'id': 6, 'category': 'Inlay Gold Carve'},
    {'id': 7, 'category': 'Texture Mark'},
    {'id': 8, 'category': 'Striped Grid'},
    {'id': 9, 'category': 'Chinese Pattern'},
    {'id': 10, 'category': 'Gold Foil'},
    {'id': 11, 'category': 'Rivet'},
    {'id': 12, 'category': 'Soft Case'},
    {'id': 13, 'category': 'Wooden Vertical Texture'},
    {'id': 14, 'category': 'Graffiti Ink Stain'},
    {'id': 15, 'category': 'Linen Texture'},
]

_SUPER_CATEGORIES_3D = [
    {'id': 1, 'category': 'Cabinet/Shelf/Desk'},
    {'id': 2, 'category': 'Bed'},
    {'id': 3, 'category': 'Chair'},
    {'id': 4, 'category': 'Table'},
    {'id': 5, 'category': 'Sofa'},
    {'id': 6, 'category': 'Pier/Stool'},
    {'id': 7, 'category': 'Lighting'},
    {'id': 8, 'category': 'Other'},
]

_CATEGORIES_3D = [
    {'id': 1, 'super-category': 'Cabinet/Shelf/Desk', 'category': 'Children Cabinet'},
    {'id': 2, 'super-category': 'Cabinet/Shelf/Desk', 'category': 'Nightstand'},
    {'id': 3, 'super-category': 'Cabinet/Shelf/Desk', 'category': 'Bookcase / jewelry Armoire'},
    {'id': 4, 'super-category': 'Cabinet/Shelf/Desk', 'category': 'Wardrobe'},
    {'id': 5, 'super-category': 'Cabinet/Shelf/Desk', 'category': 'Coffee Table'},
    {'id': 6, 'super-category': 'Cabinet/Shelf/Desk', 'category': 'Corner/Side Table'},
    {'id': 7, 'super-category': 'Cabinet/Shelf/Desk', 'category': 'Sideboard / Side Cabinet / Console Table'},
    {'id': 8, 'super-category': 'Cabinet/Shelf/Desk', 'category': 'Wine Cabinet'},
    {'id': 9, 'super-category': 'Cabinet/Shelf/Desk', 'category': 'TV Stand'},
    {'id': 10, 'super-category': 'Cabinet/Shelf/Desk', 'category': 'Drawer Chest / Corner cabinet'},
    {'id': 11, 'super-category': 'Cabinet/Shelf/Desk', 'category': 'Shelf'},
    {'id': 12, 'super-category': 'Cabinet/Shelf/Desk', 'category': 'Round End Table'},
    {'id': 13, 'super-category': 'Bed', 'category': 'King-size Bed'},
    {'id': 14, 'super-category': 'Bed', 'category': 'Bunk Bed'},
    {'id': 15, 'super-category': 'Bed', 'category': 'Bed Frame'},
    {'id': 16, 'super-category': 'Bed', 'category': 'Single bed'},
    {'id': 17, 'super-category': 'Bed', 'category': 'Kids Bed'},
    {'id': 18, 'super-category': 'Chair', 'category': 'Dining Chair'},
    {'id': 19, 'super-category': 'Chair', 'category': 'Lounge Chair / Cafe Chair / Office Chair'},
    {'id': 20, 'super-category': 'Chair', 'category': 'Dressing Chair'},
    {'id': 21, 'super-category': 'Chair', 'category': 'Classic Chinese Chair'},
    {'id': 22, 'super-category': 'Chair', 'category': 'Barstool'},
    {'id': 23, 'super-category': 'Table', 'category': 'Dressing Table'},
    {'id': 24, 'super-category': 'Table', 'category': 'Dining Table'},
    {'id': 25, 'super-category': 'Table', 'category': 'Desk'},
    {'id': 26, 'super-category': 'Sofa', 'category': 'Three-Seat / Multi-seat Sofa'},
    {'id': 27, 'super-category': 'Sofa', 'category': 'armchair'},
    {'id': 28, 'super-category': 'Sofa', 'category': 'Loveseat Sofa'},
    {'id': 29, 'super-category': 'Sofa', 'category': 'L-shaped Sofa'},
    {'id': 30, 'super-category': 'Sofa', 'category': 'Lazy Sofa'},
    {'id': 31, 'super-category': 'Sofa', 'category': 'Chaise Longue Sofa'},
    {'id': 32, 'super-category': 'Pier/Stool', 'category': 'Footstool / Sofastool / Bed End Stool / Stool'},
    {'id': 33, 'super-category': 'Lighting', 'category': 'Pendant Lamp'},
    {'id': 34, 'super-category': 'Lighting', 'category': 'Ceiling Lamp'},
    {'id': 35, 'super-category': 'Cabinet/Shelf/Desk', 'category': 'Shoe Cabinet'},
    {'id': 36, 'super-category': 'Bed', 'category': 'Couch Bed'},
    {'id': 37, 'super-category': 'Chair', 'category': 'Hanging Chair'},
    {'id': 38, 'super-category': 'Chair', 'category': 'Folding chair'},
    {'id': 39, 'super-category': 'Table', 'category': 'Bar'},
    {'id': 40, 'super-category': 'Sofa', 'category': 'U-shaped Sofa'},
    {'id': 41, 'super-category': 'Lighting', 'category': 'Floor Lamp'},
    {'id': 42, 'super-category': 'Lighting', 'category': 'Wall Lamp'},
]

class FurnitureSearchEngine:
    def __init__(self):
        self.style_categories = {item['category'].lower(): item['id'] for item in _ATTR_STYLE}
        self.material_categories = {item['category'].lower(): item['id'] for item in _ATTR_MATERIAL}
        self.theme_categories = {item['category'].lower(): item['id'] for item in _ATTR_THEME}
        self.super_categories = {item['category'].lower(): item['id'] for item in _SUPER_CATEGORIES_3D}
        
        # TF-IDF를 위한 문서 컬렉션 구축
        self.category_documents = [item['category'].lower() for item in _CATEGORIES_3D]
        self.build_tfidf_vectors()
        
    def build_tfidf_vectors(self):
        """TF-IDF 벡터 구축"""
        # 전체 단어 집합 구축
        all_words = set()
        document_words = []
        
        for doc in self.category_documents:
            words = self.tokenize(doc)
            document_words.append(words)
            all_words.update(words)
        
        self.vocabulary = sorted(all_words)
        self.word_to_idx = {word: idx for idx, word in enumerate(self.vocabulary)}
        
        # IDF 계산
        self.idf = {}
        total_docs = len(self.category_documents)
        
        for word in self.vocabulary:
            doc_freq = sum(1 for words in document_words if word in words)
            self.idf[word] = math.log(total_docs / (doc_freq + 1))
        
        # 각 문서의 TF-IDF 벡터 계산
        self.tfidf_vectors = []
        for words in document_words:
            vector = self.compute_tfidf_vector(words)
            self.tfidf_vectors.append(vector)
    
    def tokenize(self, text: str) -> List[str]:
        """텍스트 토큰화 (가구 도메인 특화)"""
        text = text.lower()
        # 슬래시, 하이픈 등을 공백으로 변환
        text = re.sub(r'[/\-_]', ' ', text)
        # 알파벳과 숫자만 추출
        words = re.findall(r'\b\w+\b', text)
        
        # 불용어 제거 (크기 관련 수식어)
        stopwords = {'small', 'large', 'big', 'mini', 'tiny', 'huge', 'size'}
        words = [w for w in words if w not in stopwords and len(w) > 1]
        
        return words
    
    def compute_tfidf_vector(self, words: List[str]) -> List[float]:
        """단어 리스트로부터 TF-IDF 벡터 계산"""
        word_count = Counter(words)
        total_words = len(words)
        
        vector = []
        for word in self.vocabulary:
            tf = word_count.get(word, 0) / total_words if total_words > 0 else 0
            idf = self.idf.get(word, 0)
            tfidf = tf * idf
            vector.append(tfidf)
        
        return vector
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """코사인 유사도 계산"""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def calculate_semantic_similarity(self, query_text: str, category_text: str) -> float:
        """의미론적 유사도 계산 (TF-IDF + 코사인 유사도)"""
        query_words = self.tokenize(query_text)
        category_words = self.tokenize(category_text)
        
        query_vector = self.compute_tfidf_vector(query_words)
        category_vector = self.compute_tfidf_vector(category_words)
        
        return self.cosine_similarity(query_vector, category_vector)
    
    def jaccard_similarity(self, text1: str, text2: str) -> float:
        """Jaccard 유사도 계산 (보조 지표)"""
        words1 = set(self.tokenize(text1))
        words2 = set(self.tokenize(text2))
        
        if not words1 and not words2:
            return 1.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def find_category_match(self, query_text: str) -> Tuple[str, str, float, str]:
        """개선된 카테고리 매칭 (TF-IDF 기반)"""
        query_lower = query_text.lower().strip()
        
        # 1단계: Detail category에서 정확한 문자열 매칭
        for item in _CATEGORIES_3D:
            category_lower = item['category'].lower()
            if query_lower == category_lower:
                print(f"✅ 정확한 매칭: '{query_text}' → {item['super-category']} / {item['category']}")
                return item['super-category'].lower(), item['category'], 1.0, "exact_match"
        
        # 2단계: TF-IDF + 코사인 유사도 기반 매칭
        best_match = None
        best_score = 0.0
        best_super = None
        best_method = None
        
        for i, item in enumerate(_CATEGORIES_3D):
            # TF-IDF 코사인 유사도
            tfidf_similarity = self.calculate_semantic_similarity(query_text, item['category'])
            
            # Jaccard 유사도 (보조)
            jaccard_sim = self.jaccard_similarity(query_text, item['category'])
            
            # 특별 매칭 점수
            special_score = self.get_special_match_score(query_text, item['category'])
            
            # 종합 점수 계산 (TF-IDF 중심, 특별 매칭 보강)
            if special_score > 0.8:  # 특별 매칭이 강한 경우
                total_score = special_score * 0.7 + tfidf_similarity * 0.3
                method = "special+tfidf"
            else:  # 일반적인 경우
                total_score = tfidf_similarity * 0.8 + jaccard_sim * 0.2
                method = "tfidf+jaccard"
            
            if total_score > best_score:
                best_score = total_score
                best_match = item['category']
                best_super = item['super-category'].lower()
                best_method = method
        
        # 유사도가 충분히 높으면 사용
        if best_score >= 0.25:  # 임계값 조정
            print(f"✅ 의미론적 매칭: '{query_text}' → {best_super} / {best_match}")
            print(f"   └── 점수: {best_score:.3f} (방법: {best_method})")
            return best_super, best_match, best_score, "semantic_match"
        
        # 3단계: Super category에서 키워드 매칭
        query_words = set(self.tokenize(query_text))
        for super_item in _SUPER_CATEGORIES_3D:
            super_category = super_item['category'].lower()
            super_words = set(self.tokenize(super_category))
            
            # 키워드 교집합 확인
            if query_words & super_words:
                matched_keywords = query_words & super_words
                print(f"✅ Super 키워드 매칭: '{query_text}' → {super_category}")
                print(f"   └── 매칭된 키워드: {matched_keywords}")
                return super_category, None, 0.6, "super_keyword_match"
        
        # 4단계: Other로 fallback
        print(f"⚠️ '{query_text}' → Other로 분류")
        return 'other', None, 0.1, "other_fallback"
    
    def get_special_match_score(self, query: str, category: str) -> float:
        """특별한 매칭 케이스들 처리"""
        query_lower = query.lower()
        category_lower = category.lower()
        
        # 직접적인 포함 관계
        if 'chair' in query_lower and 'chair' in category_lower:
            return 1.0
        elif 'table' in query_lower and 'table' in category_lower:
            return 1.0
        elif 'cabinet' in query_lower and 'cabinet' in category_lower:
            return 1.0
        elif 'shelf' in query_lower and ('shelf' in category_lower or 'bookcase' in category_lower):
            return 1.0
        elif 'lamp' in query_lower and 'lamp' in category_lower:
            return 1.0
        elif 'bed' in query_lower and 'bed' in category_lower:
            return 1.0
        elif 'sofa' in query_lower and 'sofa' in category_lower:
            return 1.0
        elif 'stool' in query_lower and 'stool' in category_lower:
            return 1.0
        
        # 특별한 의미론적 매칭
        elif 'bookshelf' in query_lower and ('bookcase' in category_lower or 'shelf' in category_lower):
            return 0.9
        elif 'filing' in query_lower and 'cabinet' in category_lower:
            return 0.8
        elif 'storage' in query_lower and ('cabinet' in category_lower or 'chest' in category_lower):
            return 0.7
        elif 'meeting' in query_lower and 'chair' in category_lower:
            return 0.6
        
        return 0.0
    
# 전역 함수들을 클래스 외부에 정의
def parse_llm_furniture_text(text: str) -> List[Dict]:
    """LLM 결과에서 카테고리명만 유연하게 추출"""
    items = []
    
    # 1. 숫자로 시작하는 아이템들 찾기 (매우 유연한 패턴)
    # "1.", "1)", "1 -", "1:" 등 다양한 형식 지원
    pattern = re.compile(r'^\s*(\d+)[\.\)\-:\s]+(.+?)(?=^\s*\d+[\.\)\-:\s]|\Z)', re.MULTILINE | re.DOTALL)
    matches = list(pattern.finditer(text))
    
    print(f"🔍 발견된 아이템: {len(matches)}개")
    
    for match in matches:
        item_number = match.group(1)
        item_content = match.group(2).strip()
        
        # 2. 카테고리 추출 (첫 번째 줄에서 *와 : 제거)
        lines = item_content.split('\n')
        first_line = lines[0].strip()
        
        # *와 :를 모두 제거하고 순수 카테고리명만 추출
        category_name = re.sub(r'[\*\:]+', '', first_line).strip()
        
        print(f"  {item_number}: '{category_name}'")
        
        # 3. 전체 아이템 텍스트 (속성 추출용)
        item_data = {
            'item_number': int(item_number),
            'category_name': category_name,
            'full_text': item_content  # 기존 _extract_section_keywords에서 사용
        }
        
        items.append(item_data)
    
    return items

def extract_section_keywords_simple(text: str, section_name: str, style_categories: dict, material_categories: dict, theme_categories: dict) -> set:
    """간단한 방식으로 섹션 키워드 추출"""
    found_keywords = set()
    
    # 줄별로 나누어서 처리
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line.startswith('-'):
            continue
            
        # '-' 제거
        content = line[1:].strip()
        
        # section_name이 포함된 줄인지 확인 (대소문자 무시)
        if section_name.lower() not in content.lower():
            continue
            
        # 특수기호와 section_name 제거
        # 모든 특수기호(*:) 제거하고 section_name도 제거
        clean_content = re.sub(r'[\*\:]+', '', content)  # 특수기호 제거
        clean_content = re.sub(section_name, '', clean_content, flags=re.IGNORECASE)  # section_name 제거
        clean_content = clean_content.strip().lower()
        
        print(f"    📝 {section_name} 정리된 텍스트: {clean_content[:50]}...")
        
        if not clean_content:
            continue
            
        # 키워드 매칭
        for keyword in style_categories.keys():
            if keyword in clean_content:
                found_keywords.add(f"style:{keyword}")
        
        for keyword in material_categories.keys():
            if keyword in clean_content:
                found_keywords.add(f"material:{keyword}")
        
        for keyword in theme_categories.keys():
            if keyword in clean_content:
                found_keywords.add(f"theme:{keyword}")
    
    return found_keywords

class FurnitureSearchEngine:
    def __init__(self):
        self.style_categories = {item['category'].lower(): item['id'] for item in _ATTR_STYLE}
        self.material_categories = {item['category'].lower(): item['id'] for item in _ATTR_MATERIAL}
        self.theme_categories = {item['category'].lower(): item['id'] for item in _ATTR_THEME}
        self.super_categories = {item['category'].lower(): item['id'] for item in _SUPER_CATEGORIES_3D}
        
        # TF-IDF를 위한 문서 컬렉션 구축
        self.category_documents = [item['category'].lower() for item in _CATEGORIES_3D]
        self.build_tfidf_vectors()
        
    def build_tfidf_vectors(self):
        """TF-IDF 벡터 구축"""
        # 전체 단어 집합 구축
        all_words = set()
        document_words = []
        
        for doc in self.category_documents:
            words = self.tokenize(doc)
            document_words.append(words)
            all_words.update(words)
        
        self.vocabulary = sorted(all_words)
        self.word_to_idx = {word: idx for idx, word in enumerate(self.vocabulary)}
        
        # IDF 계산
        self.idf = {}
        total_docs = len(self.category_documents)
        
        for word in self.vocabulary:
            doc_freq = sum(1 for words in document_words if word in words)
            self.idf[word] = math.log(total_docs / (doc_freq + 1))
        
        # 각 문서의 TF-IDF 벡터 계산
        self.tfidf_vectors = []
        for words in document_words:
            vector = self.compute_tfidf_vector(words)
            self.tfidf_vectors.append(vector)
    
    def tokenize(self, text: str) -> List[str]:
        """텍스트 토큰화 (가구 도메인 특화)"""
        text = text.lower()
        # 슬래시, 하이픈 등을 공백으로 변환
        text = re.sub(r'[/\-_]', ' ', text)
        # 알파벳과 숫자만 추출
        words = re.findall(r'\b\w+\b', text)
        
        # 불용어 제거 (크기 관련 수식어)
        stopwords = {'small', 'large', 'big', 'mini', 'tiny', 'huge', 'size'}
        words = [w for w in words if w not in stopwords and len(w) > 1]
        
        return words
    
    def compute_tfidf_vector(self, words: List[str]) -> List[float]:
        """단어 리스트로부터 TF-IDF 벡터 계산"""
        word_count = Counter(words)
        total_words = len(words)
        
        vector = []
        for word in self.vocabulary:
            tf = word_count.get(word, 0) / total_words if total_words > 0 else 0
            idf = self.idf.get(word, 0)
            tfidf = tf * idf
            vector.append(tfidf)
        
        return vector
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """코사인 유사도 계산"""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def calculate_semantic_similarity(self, query_text: str, category_text: str) -> float:
        """의미론적 유사도 계산 (TF-IDF + 코사인 유사도)"""
        query_words = self.tokenize(query_text)
        category_words = self.tokenize(category_text)
        
        query_vector = self.compute_tfidf_vector(query_words)
        category_vector = self.compute_tfidf_vector(category_words)
        
        return self.cosine_similarity(query_vector, category_vector)
    
    def jaccard_similarity(self, text1: str, text2: str) -> float:
        """Jaccard 유사도 계산 (보조 지표)"""
        words1 = set(self.tokenize(text1))
        words2 = set(self.tokenize(text2))
        
        if not words1 and not words2:
            return 1.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def find_category_match(self, query_text: str) -> Tuple[str, str, float, str]:
        """개선된 카테고리 매칭 (TF-IDF 기반)"""
        query_lower = query_text.lower().strip()
        
        # 1단계: Detail category에서 정확한 문자열 매칭
        for item in _CATEGORIES_3D:
            category_lower = item['category'].lower()
            if query_lower == category_lower:
                print(f"✅ 정확한 매칭: '{query_text}' → {item['super-category']} / {item['category']}")
                return item['super-category'].lower(), item['category'], 1.0, "exact_match"
        
        # 2단계: TF-IDF + 코사인 유사도 기반 매칭
        best_match = None
        best_score = 0.0
        best_super = None
        best_method = None
        
        for i, item in enumerate(_CATEGORIES_3D):
            # TF-IDF 코사인 유사도
            tfidf_similarity = self.calculate_semantic_similarity(query_text, item['category'])
            
            # Jaccard 유사도 (보조)
            jaccard_sim = self.jaccard_similarity(query_text, item['category'])
            
            # 특별 매칭 점수
            special_score = self.get_special_match_score(query_text, item['category'])
            
            # 종합 점수 계산 (TF-IDF 중심, 특별 매칭 보강)
            if special_score > 0.8:  # 특별 매칭이 강한 경우
                total_score = special_score * 0.7 + tfidf_similarity * 0.3
                method = "special+tfidf"
            else:  # 일반적인 경우
                total_score = tfidf_similarity * 0.8 + jaccard_sim * 0.2
                method = "tfidf+jaccard"
            
            if total_score > best_score:
                best_score = total_score
                best_match = item['category']
                best_super = item['super-category'].lower()
                best_method = method
        
        # 유사도가 충분히 높으면 사용
        if best_score >= 0.25:  # 임계값 조정
            print(f"✅ 의미론적 매칭: '{query_text}' → {best_super} / {best_match}")
            print(f"   └── 점수: {best_score:.3f} (방법: {best_method})")
            return best_super, best_match, best_score, "semantic_match"
        
        # 3단계: Super category에서 키워드 매칭
        query_words = set(self.tokenize(query_text))
        for super_item in _SUPER_CATEGORIES_3D:
            super_category = super_item['category'].lower()
            super_words = set(self.tokenize(super_category))
            
            # 키워드 교집합 확인
            if query_words & super_words:
                matched_keywords = query_words & super_words
                print(f"✅ Super 키워드 매칭: '{query_text}' → {super_category}")
                print(f"   └── 매칭된 키워드: {matched_keywords}")
                return super_category, None, 0.6, "super_keyword_match"
        
        # 4단계: Other로 fallback
        print(f"⚠️ '{query_text}' → Other로 분류")
        return 'other', None, 0.1, "other_fallback"
    
    def get_special_match_score(self, query: str, category: str) -> float:
        """특별한 매칭 케이스들 처리"""
        query_lower = query.lower()
        category_lower = category.lower()
        
        # 직접적인 포함 관계
        if 'chair' in query_lower and 'chair' in category_lower:
            return 1.0
        elif 'table' in query_lower and 'table' in category_lower:
            return 1.0
        elif 'cabinet' in query_lower and 'cabinet' in category_lower:
            return 1.0
        elif 'shelf' in query_lower and ('shelf' in category_lower or 'bookcase' in category_lower):
            return 1.0
        elif 'lamp' in query_lower and 'lamp' in category_lower:
            return 1.0
        elif 'bed' in query_lower and 'bed' in category_lower:
            return 1.0
        elif 'sofa' in query_lower and 'sofa' in category_lower:
            return 1.0
        elif 'stool' in query_lower and 'stool' in category_lower:
            return 1.0
        
        # 특별한 의미론적 매칭
        elif 'bookshelf' in query_lower and ('bookcase' in category_lower or 'shelf' in category_lower):
            return 0.9
        elif 'filing' in query_lower and 'cabinet' in category_lower:
            return 0.8
        elif 'storage' in query_lower and ('cabinet' in category_lower or 'chest' in category_lower):
            return 0.7
        elif 'meeting' in query_lower and 'chair' in category_lower:
            return 0.6
        
        return 0.0
    
    def parse_structured_text_simple(self, text: str) -> List[Dict]:
        """LLM 결과의 간단한 파싱"""
        llm_items = parse_llm_furniture_text(text)
        items = []
        
        for llm_item in llm_items:
            category_name = llm_item['category_name']
            item_text = llm_item['full_text']
            
            print(f"\n🔍 처리 중: {category_name}")
            
            # 카테고리 매칭
            super_category, detailed_category, category_score, match_type = self.find_category_match(category_name)
            
            # 간단한 키워드 추출
            style_matches = extract_section_keywords_simple(
                item_text, "Style", 
                self.style_categories, self.material_categories, self.theme_categories
            )
            
            color_matches = extract_section_keywords_simple(
                item_text, "Color", 
                self.style_categories, self.material_categories, self.theme_categories
            )
            
            colour_matches = extract_section_keywords_simple(
                item_text, "Colour", 
                self.style_categories, self.material_categories, self.theme_categories
            )
            
            material_matches = extract_section_keywords_simple(
                item_text, "Material", 
                self.style_categories, self.material_categories, self.theme_categories
            )
            
            all_keywords = style_matches | color_matches | colour_matches | material_matches
            
            item_data = {
                'target_category': category_name,
                'super_category': super_category,
                'detailed_category': detailed_category,
                'category_score': category_score,
                'match_type': match_type,
                'style_keywords': style_matches,
                'color_keywords': color_matches | colour_matches,
                'material_keywords': material_matches,
                'all_keywords': all_keywords
            }
            
            items.append(item_data)
            
            if all_keywords:
                print(f"    🎯 키워드: {', '.join(all_keywords)}")
            else:
                print(f"    ⚠️ 키워드 없음")
        
        return items
    
    def parse_structured_text(self, text: str) -> List[Dict]:
        """메인 파싱 함수 - 호환성을 위해 추가"""
        return self.parse_structured_text_simple(text)
    
    def calculate_item_score(self, db_item: Dict, parsed_item: Dict) -> Tuple[float, Dict]:
        """간소화된 점수 계산"""
        score = 0.0
        score_details = {}
        
        # Bed Frame 제외
        if (parsed_item['target_category'].lower() == 'bed' and 
            'bed frame' in db_item.get('category', '').lower()):
            return 0.0, {}
        
        db_super_category = db_item.get('super-category', '').lower()
        parsed_super_category = parsed_item['super_category']
        
        # Super category 매칭 확인
        if db_super_category == parsed_super_category:
            # 1. 카테고리 매칭 점수
            if parsed_item['match_type'] == 'exact_match':
                category_score = 25.0  # 정확한 매칭
            elif parsed_item['match_type'] == 'semantic_match':  # 수정: similarity_match → semantic_match
                category_score = 15.0 + (parsed_item['category_score'] * 10.0)  # 유사도 기반
            elif parsed_item['match_type'] == 'super_keyword_match':
                category_score = 10.0  # Super 키워드 매칭
            else:
                category_score = 5.0  # Other 카테고리
            
            score += category_score
            score_details['category_score'] = category_score
            
            # 2. Detail category 매칭 추가 점수
            if (parsed_item['detailed_category'] and 
                parsed_item['detailed_category'].lower() in db_item.get('category', '').lower()):
                detail_bonus = 15.0
                score += detail_bonus
                score_details['detail_bonus'] = detail_bonus
            
            # 3. Style, Material, Theme 점수 추가
            style_score, material_score, theme_score = self._calculate_attribute_scores(db_item, parsed_item)
            score += style_score + material_score + theme_score
            
            if style_score > 0:
                score_details['style_score'] = style_score
            if material_score > 0:
                score_details['material_score'] = material_score  
            if theme_score > 0:
                score_details['theme_score'] = theme_score
                
        elif parsed_super_category == 'other':
            # Other 카테고리인 경우 - 속성만으로 점수 계산
            base_score = 3.0
            score += base_score
            score_details['other_base'] = base_score
            
            # Style, Material, Theme 점수만 계산
            style_score, material_score, theme_score = self._calculate_attribute_scores(db_item, parsed_item)
            score += style_score + material_score + theme_score
            
            if style_score > 0:
                score_details['style_score'] = style_score
            if material_score > 0:
                score_details['material_score'] = material_score
            if theme_score > 0:
                score_details['theme_score'] = theme_score
            
            # Other인데 속성 매칭이 없으면 0점
            if style_score + material_score + theme_score == 0:
                return 0.0, {}
        
        return score, score_details
    
    def _calculate_attribute_scores(self, db_item: Dict, parsed_item: Dict) -> Tuple[float, float, float]:
        """Style, Material, Theme 점수 계산"""
        style_matches = 0
        material_matches = 0
        theme_matches = 0
        
        for keyword in parsed_item['all_keywords']:
            if ':' not in keyword:
                continue
                
            category_type, category_name = keyword.split(':', 1)
            
            if category_type == 'style' and category_name in db_item.get('style', '').lower():
                style_matches += 1
            elif category_type == 'material' and category_name in db_item.get('material', '').lower():
                material_matches += 1
            elif category_type == 'theme' and category_name in db_item.get('theme', '').lower():
                theme_matches += 1
        
        # 점수 계산
        style_score = style_matches * 3.0
        material_score = material_matches * 2.0
        theme_score = theme_matches * 2.0
        
        return style_score, material_score, theme_score

class DatabaseLoader:
    """실제 데이터베이스에서 model_info.json 파일들을 로드"""
    
    @staticmethod
    def load_multiple_folders(folder_paths: List[str]) -> List[Dict]:
        """여러 폴더에서 model_info.json 파일들을 로드"""
        database = []
        seen_model_ids = set()  # 중복 체크용
        duplicate_count = 0
        
        for i, folder_path in enumerate(folder_paths, 1):
            if not os.path.exists(folder_path):
                continue
                
            model_info_path = os.path.join(folder_path, "model_info.json")
            
            if os.path.exists(model_info_path):
                try:
                    with open(model_info_path, 'r', encoding='utf-8') as f:
                        model_data = json.load(f)
                    
                    folder_name = os.path.basename(folder_path)
                    
                    if isinstance(model_data, list):
                        for item in model_data:
                            model_id = item.get('model_id')
                            
                            if model_id and model_id in seen_model_ids:
                                duplicate_count += 1
                                continue
                            
                            if model_id:
                                seen_model_ids.add(model_id)
                            
                            item['source_folder'] = folder_name
                            item['source_path'] = folder_path
                            database.append(item)
                    else:
                        model_id = model_data.get('model_id')
                        
                        if model_id and model_id in seen_model_ids:
                            duplicate_count += 1
                        else:
                            if model_id:
                                seen_model_ids.add(model_id)
                            model_data['source_folder'] = folder_name
                            model_data['source_path'] = folder_path
                            database.append(model_data)
                        
                except Exception as e:
                    continue
        
        print(f"✅ 중복 제거 완료: {duplicate_count}개 중복 항목 제거됨")
        return database

def save_results_to_files(results_by_object: Dict, output_dir: str = "./search_results"):
    """검색 결과를 object별로 텍스트 파일에 저장 (ID만)"""
    os.makedirs(output_dir, exist_ok=True)
    
    for object_name, results in results_by_object.items():
        # 파일명에서 특수문자 제거 또는 안전하게 변환
        safe_name = object_name.replace('/', '_').replace('\\', '_').replace('(', '').replace(')', '').replace(':', '_')
        filename = f"{safe_name}_results.txt"
        filepath = os.path.join(output_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                for item, score in results:
                    f.write(f"{item.get('model_id', 'N/A')}\n")
            
            print(f"✅ {object_name} 결과 저장됨: {filepath} ({len(results)}개 ID)")
        except Exception as e:
            print(f"❌ {object_name} 저장 실패: {e}")

def search_furniture_database(folder_paths: List[str], query_text: str, output_dir: str = "./search_results"):
    """실제 데이터베이스를 사용한 가구 검색 (간소화된 버전)"""
    
    # 검색 엔진 초기화
    search_engine = FurnitureSearchEngine()
    
    # 데이터베이스 로드
    print("=== 데이터베이스 로딩 중... ===")
    database = DatabaseLoader.load_multiple_folders(folder_paths)
    
    if not database:
        print("데이터베이스가 비어있습니다!")
        return
    
    print(f"총 {len(database)}개 아이템 로드 완료")
    
    # None 값 정리
    fields_to_clean = ['material', 'style', 'theme', 'super-category', 'category']
    cleaned_count = 0

    for item in database:
        for field in fields_to_clean:
            if item.get(field) is None:
                item[field] = ''
                cleaned_count += 1

    print(f"None 값 {cleaned_count}개 정리 완료")

    # 텍스트 파싱 - 수정된 메서드 이름 사용
    print("\n=== 카테고리 매칭 결과 ===")
    parsed_items = search_engine.parse_structured_text(query_text)  # parse_structured_text 사용
    
    if not parsed_items:
        print("파싱된 아이템이 없습니다.")
        return
    
    print(f"\n총 {len(parsed_items)}개 아이템이 성공적으로 매칭됨")
    
    # 각 object별로 검색 결과 저장
    results_by_object = {}
    
    for parsed_item in parsed_items:
        target_category = parsed_item['target_category']
        
        # 해당 object에 대한 모든 결과 계산
        object_results = []
        matched_count = 0
        
        for db_item in database:
            score, details = search_engine.calculate_item_score(db_item, parsed_item)
            
            if score > 0:
                object_results.append((db_item, score))
                matched_count += 1
        
        # 점수순으로 정렬
        object_results.sort(key=lambda x: x[1], reverse=True)
        
        # 상위 2개 점수대의 모든 아이템 추출
        if object_results:
            unique_scores = list(set(item[1] for item in object_results))
            unique_scores.sort(reverse=True)
            top_2_scores = unique_scores[:2]
            
            top_results = [item for item in object_results if item[1] in top_2_scores]
            
            score_summary = ", ".join([f"{score}점({sum(1 for item in object_results if item[1] == score)}개)" 
                                     for score in top_2_scores])
        else:
            top_results = []
            score_summary = "결과 없음"
        
        results_by_object[target_category] = top_results
        
        print(f"🔍 {target_category.upper()}: 매칭 {matched_count}개 → 상위 2점수대 [{score_summary}] → 결과 {len(top_results)}개")
    
    # 결과를 파일에 저장
    save_results_to_files(results_by_object, output_dir)
    
    # 요약 통계 출력
    total_results = sum(len(results) for results in results_by_object.values())
    print(f"\n{'='*60}")
    print(f"🎯 검색 완료!")
    print(f"📁 결과 저장 위치: {output_dir}")
    print(f"📊 총 {len(parsed_items)}개 Object, {total_results}개 결과")
    for obj_name, results in results_by_object.items():
        print(f"   - {obj_name}: {len(results)}개")
    print(f"{'='*60}")
    
    return results_by_object

# 사용 예시
def demo_search(query_text_path, output_dir):
    # 실제 데이터베이스 폴더 경로들
    DATASET_BASE_PATH = os.environ.get('DATASET_BASE_PATH', '../../dataset')

    folder_paths = [
        os.path.join(DATASET_BASE_PATH, "3D-FUTURE-model-part1"),
        os.path.join(DATASET_BASE_PATH, "3D-FUTURE-model-part2"),
        os.path.join(DATASET_BASE_PATH, "3D-FUTURE-model-part3"),
        os.path.join(DATASET_BASE_PATH, "3D-FUTURE-model-part4")
    ]
    
    with open(query_text_path, "r", encoding="utf-8") as f:
        query_text = f.read()
        
    search_furniture_database(folder_paths, query_text, output_dir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Furniture category & keyword matching")

    parser.add_argument(
        "--layout_path", type=str, default = "Result_txt/test.txt", required=True,
        help="Path to the layout.txt file (LLM prompt result)"
    )

    parser.add_argument(
        "--output_dir", type=str, default = "Result_txt/text_retrieval", required=True,
        help="Directory where the results will be saved"
    )

    args = parser.parse_args()

    demo_search(args.layout_path, args.output_dir)