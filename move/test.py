import pandas as pd

# 데이터 불러오기
alerts = pd.read_csv("alerts.csv")
weather = pd.read_csv("weather.csv")

# 날짜 형식 변환
alerts["날짜"] = pd.to_datetime(alerts["날짜"], errors="coerce")
weather["일자"] = pd.to_datetime(weather["일자"], errors="coerce")

# 2023년도 + 폭염 필터링
alerts_2023 = alerts[alerts["날짜"].dt.year == 2023]
heatwave_alerts = alerts_2023[alerts_2023["재난유형_리스트"].str.contains("폭염", na=False)]

weather_2023 = weather[weather["일자"].dt.year == 2023]
heatwave_weather = weather_2023[weather_2023["평균기온"] >= 30]

print("폭염 재난문자 수:", len(heatwave_alerts))
print("폭염 기상일 수:", len(heatwave_weather))
