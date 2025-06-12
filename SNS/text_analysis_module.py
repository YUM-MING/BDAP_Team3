# text_analysis_module.py
import re
from collections import Counter
import streamlit as st # Okt 로드 시 캐시 사용 및 get_okt_instance 데코레이터에 필요
from konlpy.tag import Okt
from SNS.config import DISASTER_SYNONYMS, DEFAULT_STOPWORDS # config.py에서 상수 가져오기

# Okt 객체를 캐시하는 함수는 그대로 둡니다.
# 이 함수는 get_analyzer() 내부에서 처음 필요할 때 한 번만 호출됩니다.
@st.cache_resource
def get_okt_instance():
    """Okt 형태소 분석기 인스턴스를 반환합니다. (캐시됨)"""
    # print("DEBUG: get_okt_instance() called to create and cache Okt object.") # 디버깅 필요시 주석 해제
    return Okt()

# 모듈 레벨에서 Okt 분석기 인스턴스를 저장할 변수 (초기값은 None)
# 이 변수는 get_analyzer() 함수를 통해 접근하고 관리됩니다.
_okt_analyzer_instance = None

def get_analyzer():
    """
    Okt 형태소 분석기 인스턴스를 반환합니다.
    필요한 경우 생성하고 캐시된 인스턴스를 사용하며, 이미 생성된 경우 그것을 반환합니다.
    (일종의 지연 초기화 + 싱글톤 패턴)
    """
    global _okt_analyzer_instance # 모듈 레벨 변수를 수정하기 위해 global 키워드 사용
    if _okt_analyzer_instance is None:
        # print("DEBUG: _okt_analyzer_instance is None. Calling get_okt_instance().") # 디버깅 필요시 주석 해제
        _okt_analyzer_instance = get_okt_instance() # 여기서 Okt 객체가 생성되고 캐시됨
    # else:
        # print("DEBUG: _okt_analyzer_instance already exists. Returning cached instance.") # 디버깅 필요시 주석 해제
    return _okt_analyzer_instance

def label_disaster(comment_text):
    """
    주어진 텍스트에서 DISASTER_SYNONYMS를 기반으로 재난 유형을 라벨링합니다.
    하나의 댓글에 여러 재난 유형이 언급될 수 있습니다.
    """
    labels = set() # 중복 방지를 위해 set 사용
    if not isinstance(comment_text, str) or not comment_text.strip():
        return [] # 빈 문자열이나 유효하지 않은 입력은 빈 리스트 반환

    # 효율성을 위해 미리 소문자 변환 등을 고려할 수 있으나, 현재는 원문 대조
    for disaster_category, synonyms in DISASTER_SYNONYMS.items():
        for synonym in synonyms:
            if synonym in comment_text:
                labels.add(disaster_category)
                # 특정 재난 카테고리에서 동의어가 하나라도 발견되면,
                # 해당 카테고리에 대한 검색은 더 이상 진행하지 않고 다음 카테고리로 넘어갈 수 있습니다.
                # (성능 향상을 위한 선택적 최적화. 주석 처리되어 있음)
                # break
    return list(labels)

def extract_keywords(text, num_keywords=10, custom_stopwords=None):
    """
    주어진 텍스트에서 명사를 추출하고, 불용어를 제거한 후 상위 키워드를 반환합니다.
    Okt 형태소 분석기를 사용합니다.
    """
    if not isinstance(text, str) or not text.strip():
        return [] # 빈 문자열이나 유효하지 않은 입력은 빈 리스트 반환

    # Okt 분석기 인스턴스를 가져옵니다 (필요시 생성 및 캐시됨).
    analyzer = get_analyzer()

    # 1. 특수문자 및 숫자 제거 (선택적: 분석 목적에 따라 다를 수 있음)
    # 기본적인 비-단어(non-word), 비-공백(non-whitespace) 문자 제거
    processed_text = re.sub(r"[^\w\s]", "", text)
    processed_text = re.sub(r"\d+", "", processed_text)   # 모든 숫자 제거

    # 2. 명사 추출
    # Okt.nouns()는 리스트를 반환합니다.
    nouns = analyzer.nouns(processed_text)

    # 3. 불용어 처리 및 단어 길이 필터링
    # 사용할 불용어 목록을 구성합니다. (기본 불용어 + 사용자 정의 불용어)
    stopwords_to_use = DEFAULT_STOPWORDS + (custom_stopwords if custom_stopwords is not None else [])
    meaningful_nouns = [
        noun for noun in nouns
        if len(noun) > 1 and noun not in stopwords_to_use # 한 글자 단어 및 불용어 목록에 없는 단어만 선택
    ]

    if not meaningful_nouns:
        return [] # 의미 있는 명사가 없으면 빈 리스트 반환

    # 4. 빈도수 계산 및 상위 키워드 반환
    # Counter 객체는 (요소, 빈도수) 튜플의 리스트를 반환합니다.
    count = Counter(meaningful_nouns)
    return count.most_common(num_keywords)