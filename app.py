# 홈화면 코드 구성
import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
from utils import load_data
## 호출
from home import run_home
from message.message_home import run_message
from relationship.relationship_home import run_relationship
from SNS.app import run_sns
from hitmap.hitmap_home import run_hitmap
from move.main import run_move

st.set_page_config(page_title="빅데이터 분석 프로젝트 3조", layout="wide")

from utils.download_model import download_model_from_huggingface

# Hugging Face 모델 URL
MODEL_URL = "https://huggingface.co/eunanim/BDAP-model/resolve/main/kote_pytorch_lightning.bin"
LOCAL_PATH = "SNS/kote_pytorch_lightning.bin"

# 자동 다운로드
download_model_from_huggingface(MODEL_URL, LOCAL_PATH)

# 이후 PyTorch 등으로 모델 로드
# import torch
# model = torch.load(LOCAL_PATH, map_location=torch.device('cpu'))


def main():
    
    with st.sidebar:
        sidebar_selected = option_menu(
            "재난 문자/경보 데이터 분석 - 기후 위기 체감 분석", ["Home", "재난문자 추이 분석", "기상현상과 발송 관계 분석", "SNS 감정 변화 분석", "지역별 재난 발생 유형 분석", "시간 흐름 분석"],
                                              icons = ["house", "bar_chart", "chart_with_upwards_trend", "left_speech_bubble", "world_map", "stopwatch"],
                                              menu_icon = "cast", default_index = 0
        )

    total_df = load_data()
    
    if sidebar_selected == "Home":
        run_home()
    elif sidebar_selected == "재난문자 추이 분석":
        run_message(total_df)
    elif sidebar_selected == "기상현상과 발송 관계 분석":
        run_relationship(total_df)
    elif sidebar_selected == "SNS 감정 변화 분석":
        run_sns()
    elif sidebar_selected == "지역별 재난 발생 유형 분석":
        run_hitmap(total_df)
    elif sidebar_selected == "시간 흐름 분석":
        run_move(total_df)
    else:
        print("error")

if __name__ == '__main__':
    main()