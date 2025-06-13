import pandas as pd
from util import load_data
import streamlit as st

st.set_page_config(page_title="재난 문자 인식 대시보드", layout="wide")

def run_home():
    # 데이터 불러오기
    total_df = load_data()

    # 🏠 메인 타이틀
    st.title("🌍 재난 문자 인식 대시보드")

    # 💬 설명문 + 이모지 활용
    st.markdown("""
    ### 📢 우리는 매일 재난문자를 받습니다.
    그러나 정말 **체감하고 있나요?**  
    이 대시보드는 다양한 데이터를 바탕으로  
    **기후 위기와 재난 알림 간의 연관성**을 시각적으로 보여줍니다.
    """)

    st.markdown("---")  # 구분선

    # 📅 데이터 기간 안내
    st.info("📅 데이터 기간: 2023년 9월 ~ 2025년 5월")
    
    # 📊 데이터 개요
    st.success(f"📦 총 수집된 재난문자 수: 22515건")
    st.success(f"🌤 총 수집된 기상 데이터 수: 10488건")

    # 📌 앞으로 보여질 기능 예고
    with st.expander("💡 대시보드에서 확인할 수 있는 기능들"):
        st.markdown("""
        - 📈 **재난문자 추이 분석**
        - 📍 **기상현상과 발송 관계 분석**
        - 🧠 **SNS 감정 분석 기반 체감 변화 추이**
        - 🗺️ **지역별 재난 발생 유형 분석**
        - ⏳ **시간 흐름에 따른 재난 반응 변화**
        """)

    # 🚀 빠르게 탐색하도록 안내 버튼
    st.markdown("⬅️ 왼쪽 메뉴에서 원하는 분석 기능을 선택해주세요.")
