import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
import os
import matplotlib.pyplot as plt
import seaborn as sns
import platform
import matplotlib
import matplotlib.font_manager as fm

def run_relationship(total_df):

     # ✅ 사용자 폰트 경로 지정 (예: relationship 폴더 내부 NanumGothic-Regular.ttf)
    font_path = os.path.join(os.path.dirname(__file__), "malgun.ttf")

    # ✅ 폰트 등록 및 설정
    if os.path.exists(font_path):
        fm.fontManager.addfont(font_path)
        font_name = fm.FontProperties(fname=font_path).get_name()
        matplotlib.rc('font', family=font_name)
    else:
        if platform.system() == 'Darwin':
            matplotlib.rc('font', family='AppleGothic')
        elif platform.system() == 'Windows':
            matplotlib.rc('font', family='Malgun Gothic')
        else:
            matplotlib.rc('font', family='malgun')

    matplotlib.rcParams['axes.unicode_minus'] = False

    # 데이터 로드
    @st.cache_data
    def load():
        weather_df = total_df["weather"]
        alert_df = total_df["alerts"]

        # 지역명 통일
        alert_df["지역"] = alert_df["지역"].replace({
            "강원특별자치도": "강원도"
        })

        # 날짜 포맷 통일
        weather_df["날짜"] = pd.to_datetime(weather_df["날짜"])
        alert_df["날짜"] = pd.to_datetime(alert_df["날짜"])

        # 날짜 + 지역 기준으로 병합
        merged = pd.merge(weather_df, alert_df, on=["날짜", "지역"], how="left")
        merged["재난문자_건수"] = merged["재난문자_건수"].fillna(0)
        return merged

    df = load()

    st.title("📊 지역별 기상 데이터와 재난 문자 발송량 상관관계 대시보드")

    # 지역 선택
    region = st.selectbox("지역을 선택하세요", sorted(df["지역"].unique()))
    region_df = df[df["지역"] == region]

    # 상관계수 분석
    correlation = region_df[["최고기온", "최저기온", "평균기온", "강수량", "재난문자_건수"]].corr()

    st.subheader(f"🔍 {region}의 기상 요소와 재난문자 발송 상관관계")
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.heatmap(correlation, annot=True, cmap="coolwarm", ax=ax)
    st.pyplot(fig)

    # 📈 선 그래프
    st.subheader(f"📈 {region}의 기상 변화 및 재난문자 발송 추이")
    fig2, ax2 = plt.subplots(figsize=(12, 5))
    ax2.plot(region_df["날짜"], region_df["평균기온"], label="평균기온 (°C)", color="orange")
    ax2.set_ylabel("평균기온 (°C)", color="orange")
    ax2.tick_params(axis='y', labelcolor="orange")

    ax3 = ax2.twinx()
    ax3.plot(region_df["날짜"], region_df["재난문자_건수"], label="재난문자 건수", color="blue")
    ax3.set_ylabel("재난문자 건수", color="blue")
    ax3.tick_params(axis='y', labelcolor="blue")

    fig2.tight_layout()
    st.pyplot(fig2)
