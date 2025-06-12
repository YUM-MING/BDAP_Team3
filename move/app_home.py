import streamlit as st
import pandas as pd
from .loader import load_all_data
from .processor import analyze_time_flow
from .visualizer import plot_time_series, plot_emotion_heatmap

st.set_page_config(page_title="기후 위기 체감도 대시보드", layout="wide")

st.title("📊 기후 위기 체감도 대시보드")
st.markdown("기후 현상 발생 → 재난 문자 발송 → SNS 감정 반응까지의 흐름을 시계열로 시각화합니다.")

# ✅ 사이드바 필터
with st.sidebar:
    st.header("🔍 필터 선택")
    selected_year = st.selectbox("연도 선택", [2023, 2024, 2025])
    disaster_type = st.selectbox("재난 유형 선택", ["전체", "폭염", "미세먼지", "호우", "한파", "기타"])
    region_filter = st.selectbox("지역 선택", ["전체", "서울특별시", "부산광역시", "경상남도", "제주특별자치도"])
    show_emotion = st.checkbox("감정 데이터 포함", value=True)

# ✅ 데이터 불러오기
with st.spinner("데이터 불러오는 중..."):
    weather_df, alert_df, emotion_df = load_all_data()

# ✅ 날짜 형식 강제 변환
weather_df["date"] = pd.to_datetime(weather_df["date"], errors="coerce")
alert_df["date"] = pd.to_datetime(alert_df["date"], errors="coerce")
if not emotion_df.empty and "date" in emotion_df.columns:
    emotion_df["date"] = pd.to_datetime(emotion_df["date"], errors="coerce")
else:
    emotion_df = pd.DataFrame(columns=["date", "region", "negative_emotion"])

# ✅ 연도 필터
weather_df = weather_df[weather_df["date"].dt.year == selected_year]
alert_df = alert_df[alert_df["date"].dt.year == selected_year]
if show_emotion and not emotion_df.empty:
    emotion_df = emotion_df[emotion_df["date"].dt.year == selected_year]
else:
    emotion_df = pd.DataFrame(columns=["date", "region", "negative_emotion"])

# ✅ 지역 필터
if region_filter != "전체":
    weather_df = weather_df[weather_df["region"] == region_filter]
    alert_df = alert_df[alert_df["region"] == region_filter]
    emotion_df = emotion_df[emotion_df["region"] == region_filter]

# ✅ 재난유형 필터 (alert)
if disaster_type != "전체" and "type" in alert_df.columns:
    alert_df = alert_df[alert_df["type"].str.contains(disaster_type, na=False)]

# ✅ 기후 지표 결정 및 필터링
indicator_col = "temperature"
if disaster_type == "폭염":
    weather_df = weather_df[weather_df["temperature"] >= 30]
elif disaster_type == "한파":
    weather_df = weather_df[weather_df["temperature"] <= 0]
elif disaster_type == "미세먼지" and "pm10" in weather_df.columns:
    weather_df = weather_df[weather_df["pm10"] >= 80]
    indicator_col = "pm10"
elif disaster_type == "호우" and "rainfall" in weather_df.columns:
    weather_df = weather_df[weather_df["rainfall"] >= 20]
    indicator_col = "rainfall"

# ✅ 날짜 교집합 필터
common_dates = set(weather_df["date"]) & set(alert_df["date"])
weather_df = weather_df[weather_df["date"].isin(common_dates)]
alert_df = alert_df[alert_df["date"].isin(common_dates)]
emotion_df = emotion_df[emotion_df["date"].isin(common_dates)]

# ✅ 시계열 분석
st.header("1️⃣ 시간 흐름 분석")
if weather_df.empty or alert_df.empty:
    st.warning("⚠️ 선택한 조건에 해당하는 기후 및 재난문자 데이터가 없어 시계열 그래프를 표시할 수 없습니다.")
else:
    flow_df = analyze_time_flow(weather_df, alert_df, emotion_df, indicator_col)
    if flow_df.empty:
        st.warning("⚠️ 시계열 분석 결과가 없습니다. 조건을 다시 확인해주세요.")
    else:
        st.plotly_chart(plot_time_series(flow_df), use_container_width=True)

# ✅ 감정 반응 히트맵
st.header("2️⃣ 지역별 감정 반응")
if emotion_df.empty:
    st.info("😐 선택한 조건에 해당하는 감정 데이터가 없습니다.")
else:
    st.plotly_chart(plot_emotion_heatmap(emotion_df), use_container_width=True)
