import streamlit as st
import pandas as pd
from .loader import load_all_data
from .processor import analyze_time_flow
from .visualizer import plot_time_series, plot_emotion_heatmap
from .preprocessing import prepare_dataset
import plotly.express as px

def run_move(total_df):


    # ✅ 분석 유형 선택
    selected_view = st.sidebar.radio("🧭 분석 유형 선택", ["📈 시계열 흐름 분석", "⏱ 사건별 시간 분석"])

    # =====================================================================================
    # 📈 1. 시계열 흐름 분석 페이지
    # =====================================================================================
    if selected_view == "📈 시계열 흐름 분석":
        st.title("📊 기후 위기 체감도 대시보드")
        st.markdown("기후 현상 발생 → 재난 문자 발송 → SNS 감정 반응까지의 흐름을 시계열로 시각화합니다.")

        with st.sidebar:
            st.header("🔍 필터 선택")
            selected_year = st.selectbox("연도 선택", [2023, 2024, 2025])
            disaster_type = st.selectbox("재난 유형 선택", ["전체", "폭염", "미세먼지", "호우", "한파", "기타"])
            region_filter = st.selectbox("지역 선택", ["전체", "서울특별시", "부산광역시", "경상남도", "제주특별자치도"])
            show_emotion = st.checkbox("감정 데이터 포함", value=True)

        with st.spinner("데이터 불러오는 중..."):
            weather_df, alert_df, emotion_df = load_all_data(total_df)

        # ✅ 날짜 변환
        weather_df["date"] = pd.to_datetime(weather_df["date"], errors="coerce")
        alert_df["date"] = pd.to_datetime(alert_df["date"], errors="coerce")
        if not emotion_df.empty:
            emotion_df["date"] = pd.to_datetime(emotion_df["date"], errors="coerce")

        # ✅ 연도 필터링
        weather_df = weather_df[weather_df["date"].dt.year == selected_year]
        alert_df = alert_df[alert_df["date"].dt.year == selected_year]
        if show_emotion:
            emotion_df = emotion_df[emotion_df["date"].dt.year == selected_year]

        # ✅ 지역 필터링
        if region_filter != "전체":
            weather_df = weather_df[weather_df["region"] == region_filter]
            alert_df = alert_df[alert_df["region"] == region_filter]
            emotion_df = emotion_df[emotion_df["region"] == region_filter]

        # ✅ 재난유형 필터링
        if disaster_type != "전체" and "type" in alert_df.columns:
            alert_df = alert_df[alert_df["type"].str.contains(disaster_type, na=False)]

        # ✅ 기후 조건 설정
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

        # ✅ 공통 날짜 필터링
        common_dates = set(weather_df["date"]) & set(alert_df["date"])
        weather_df = weather_df[weather_df["date"].isin(common_dates)]
        alert_df = alert_df[alert_df["date"].isin(common_dates)]
        emotion_df = emotion_df[emotion_df["date"].isin(common_dates)]

        # ✅ 시각화
        st.header("📈 시간 흐름 분석")
        if weather_df.empty or alert_df.empty:
            st.warning("⚠️ 선택한 조건에 해당하는 기후 및 재난문자 데이터가 없어 시계열 그래프를 표시할 수 없습니다.")
        else:
            flow_df = analyze_time_flow(weather_df, alert_df, emotion_df, indicator_col)
            if flow_df.empty:
                st.warning("⚠️ 시계열 분석 결과가 없습니다. 조건을 다시 확인해주세요.")
            else:
                st.plotly_chart(plot_time_series(flow_df), use_container_width=True)

        st.header("📊 지역별 감정 반응")
        if emotion_df.empty:
            st.info("😐 선택한 조건에 해당하는 감정 데이터가 없습니다.")
        else:
            st.plotly_chart(plot_emotion_heatmap(emotion_df), use_container_width=True)

    # =====================================================================================
    # ⏱ 2. 사건별 시간 분석 페이지
    # =====================================================================================
    elif selected_view == "⏱ 사건별 시간 분석":
        st.title("⏱ 사건별 시간 흐름 분석")
        st.markdown("""
        - 기후 현상 발생 → 재난 문자 발송 → 감정 반응까지 얼마나 걸렸는지를 시각적으로 분석합니다.
        """)

        df = prepare_dataset()

        # ✅ 긴 포맷으로 변환 (bar 시각화용)
        df_long = df.melt(
            id_vars="event",
            value_vars=["alert_delay_min", "emotion_delay_min"],
            var_name="delay_type",
            value_name="delay_min"
        )

        fig = px.bar(
            df_long,
            x="event",
            y="delay_min",
            color="delay_type",
            barmode="group",
            labels={"event": "사건명", "delay_min": "지연 시간(분)", "delay_type": "지연 유형"},
            title="사건별 재난문자 및 감정 반응 지연 시간"
        )

        fig.update_layout(
            xaxis_tickangle=-45,
            legend=dict(orientation="h", x=0.5, xanchor="center", y=1.12),
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### 사건별 시간 상세 테이블")
        st.dataframe(df.style.format({
            "alert_delay_min": "{:.0f}분",
            "emotion_delay_min": "{:.0f}분"
        }))
