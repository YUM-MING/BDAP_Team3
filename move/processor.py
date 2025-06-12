import pandas as pd

def analyze_time_flow(weather_df, alert_df, emotion_df, indicator_col="temperature"):
    # ✅ 날짜 타입 명확히 통일
    weather_df["date"] = pd.to_datetime(weather_df["date"], errors="coerce")
    alert_df["date"] = pd.to_datetime(alert_df["date"], errors="coerce")
    emotion_df["date"] = pd.to_datetime(emotion_df["date"], errors="coerce")

    # ✅ 날짜 기준 병합
    df = pd.merge(weather_df[["date", indicator_col]], alert_df[["date", "count"]], on="date", how="outer")
    df = df.rename(columns={indicator_col: "climate", "count": "alerts"})

    if not emotion_df.empty:
        emotion_grouped = emotion_df.groupby("date")["negative_emotion"].mean().reset_index()
        df = pd.merge(df, emotion_grouped, on="date", how="left")
    else:
        df["negative_emotion"] = None

    df = df.sort_values("date")
    return df
