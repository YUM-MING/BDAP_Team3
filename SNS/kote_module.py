# kote_module.py
import torch
import torch.nn as nn
import pytorch_lightning as pl
from transformers import ElectraModel, AutoTokenizer
import streamlit as st
from SNS.config import LABELS, KOTE_MODEL_PATH # config.py에서 상수 가져오기

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class KOTEtagger(pl.LightningModule):
    def __init__(self):
        super().__init__()
        # Electra 모델과 토크나이저 로드 시 revision 명시
        self.electra = ElectraModel.from_pretrained("beomi/KcELECTRA-base", revision='v2021')
        self.tokenizer = AutoTokenizer.from_pretrained("beomi/KcELECTRA-base", revision='v2021')
        self.classifier = nn.Linear(self.electra.config.hidden_size, len(LABELS))

    def forward(self, text: str):
        encoding = self.tokenizer.encode_plus(
            text,
            add_special_tokens=True,
            max_length=512,
            return_token_type_ids=False,
            padding="max_length",
            truncation=True,
            return_attention_mask=True,
            return_tensors='pt',
        ).to(device)

        with torch.no_grad():
            output = self.electra(encoding["input_ids"], attention_mask=encoding["attention_mask"])
            # ELECTRA의 CLS 토큰 임베딩 사용
            output = output.last_hidden_state[:, 0, :]
            output = self.classifier(output)
            output = torch.sigmoid(output) # 멀티 레이블 분류를 위한 시그모이드

        if device.type == 'cuda':
            torch.cuda.empty_cache() # GPU 메모리 정리
        return output

@st.cache_resource # 리소스 캐싱으로 모델 재로드 방지
def load_trained_kote_model(show_message=True):
    """
    사전 학습된 KOTE 모델을 로드합니다.
    성공 또는 실패 메시지를 Streamlit UI에 표시할 수 있습니다.
    """
    model_instance = None
    try:
        model_instance = KOTEtagger().to(device)
        # strict=False 옵션은 모델 구조가 약간 다르더라도 유연하게 로드하도록 허용 (필요시 사용)
        model_instance.load_state_dict(torch.load(KOTE_MODEL_PATH, map_location=device), strict=False)
        model_instance.eval() # 평가 모드로 설정
        
            
    except FileNotFoundError:
        if show_message:
            st.error(f"KOTE 모델 파일({KOTE_MODEL_PATH})을 찾을 수 없습니다. 파일 경로를 확인하세요.")
        # 예외를 다시 발생시켜 호출한 곳에서 처리하도록 할 수도 있습니다.
        # raise
    except Exception as e:
        if show_message:
            st.error(f"KOTE 모델 로드 중 예상치 못한 오류 발생: {e}")
        # raise
    return model_instance

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

@st.cache_data(show_spinner="텍스트 감성 분석 중... (KOTE)") # 데이터 캐싱 및 스피너 메시지
def analyze_sentiment_kote_batch(texts, _model_instance, threshold=0.4): # <--- 여기를 수정했습니다.
    """
    여러 텍스트에 대해 KOTE 모델을 사용하여 감성 분석을 일괄 수행합니다.
    _model_instance: Streamlit 캐싱에서 해시되지 않도록 밑줄로 시작하는 이름으로 변경
    """
    if not _model_instance or not texts: # <--- 여기를 수정했습니다.
        return [[] for _ in texts] # 빈 입력에 대한 처리

    all_emotions = []
    # 텍스트를 작은 배치로 나누어 처리 (메모리 관리 및 안정성)
    for text_chunk in chunks(texts, 32): # 배치 크기는 시스템 환경에 따라 조절
        chunk_emotions = []
        for text_item in text_chunk:
            if isinstance(text_item, str) and text_item.strip(): # 유효한 문자열인지 확인
                try:
                    preds = _model_instance(text_item)[0] # 모델 예측  # <--- 여기를 수정했습니다.
                    # 임계값(threshold)보다 높은 확률을 가진 감성 레이블만 선택
                    emotions = [LABELS[i] for i, p_val in enumerate(preds) if p_val > threshold]
                    chunk_emotions.append(emotions if emotions else []) # 감정이 없으면 빈 리스트
                except Exception as e:
                    # 개별 텍스트 분석 오류 시 로그를 남기거나 빈 결과 반환
                    # print(f"Warning: Error analyzing sentiment for text: '{text_item[:50]}...' - {e}")
                    chunk_emotions.append([])
            else:
                chunk_emotions.append([]) # 비어 있거나 유효하지 않은 텍스트
        all_emotions.extend(chunk_emotions)
    return all_emotions