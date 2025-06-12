import pandas as pd
import random
from datetime import datetime, timedelta

def load_event_data():
    # 사건명 리스트 (2023~2025)
    real_events = [
        "2023 태풍 카눈", "2023 산불 강릉", "2023 집중호우 충청권", "2023 지진 울진", "2023 미세먼지 경보",
        "2023 황사 전국", "2023 폭염 서울", "2024 한파 강원", "2024 폭우 부산", "2024 태풍 하이쿠이",
        "2024 산불 울산", "2024 미세먼지 고농도", "2024 가뭄 충남"
    ]

    data = []

    for i, event_name in enumerate(real_events):
        # 사건명에서 연도 추출
        year = int(event_name.split()[0])
        base_time = datetime(year, 6, 1, 8, 0)  # 각 연도별 6월 1일 08시 시작

        # 랜덤 시간 생성
        weather_time = base_time + timedelta(days=i, hours=random.randint(0, 2), minutes=random.randint(0, 59))
        alert_delay = random.randint(30, 90)  # 문자 발송 지연
        emotion_delay = random.randint(20, 60)  # 감정 피크 지연

        alert_time = weather_time + timedelta(minutes=alert_delay)
        emotion_peak_time = alert_time + timedelta(minutes=emotion_delay)

        data.append({
            "event": event_name,
            "weather_time": weather_time,
            "alert_time": alert_time,
            "emotion_peak_time": emotion_peak_time,
            "peak_emotion": "부정"
        })

    return pd.DataFrame(data)

def calculate_time_delays(df):
    df["alert_delay_min"] = (df["alert_time"] - df["weather_time"]).dt.total_seconds() / 60
    df["emotion_delay_min"] = (df["emotion_peak_time"] - df["alert_time"]).dt.total_seconds() / 60
    return df
