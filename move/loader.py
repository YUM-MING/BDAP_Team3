import pandas as pd
import os

def load_all_data(total_df):
    # ✅ 재난문자 데이터 불러오기
    alerts = total_df["alerts"]
    alerts = alerts.rename(columns={
        "날짜": "date",
        "지역": "region",
        "재난문자_건수": "count",
        "재난유형_리스트": "type"
    })
    alerts["date"] = pd.to_datetime(alerts["date"])
    alerts["count"] = pd.to_numeric(alerts["count"], errors="coerce")
    alerts_daily = alerts[["date", "region", "count", "type"]]  # 🔄 type 포함 유지

    # ✅ 기상청 데이터 불러오기
    weather = total_df["weather"]
    weather = weather.rename(columns={
        "날짜": "date",
        "평균기온": "temperature",
        "강수량": "rainfall",
        "지역": "region"
    })
    weather["date"] = pd.to_datetime(weather["date"])

    # ✅ 감정 데이터 불러오기
    emotion = total_df["emotion_sample"]
    emotion["date"] = pd.to_datetime(emotion["date"])

    return weather, alerts_daily, emotion
