import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def plot_time_series(df):
    """
    기후 현상, 재난문자 시계열 그래프 (감정 반응 제외)
    """
    df_long = df.melt(
        id_vars="date",
        value_vars=["climate", "alerts"],  # ✅ negative_emotion 제거
        var_name="variable",
        value_name="value"
    )

    df_long["value"] = pd.to_numeric(df_long["value"], errors="coerce")

    fig = px.line(
        df_long,
        x="date",
        y="value",
        color="variable",
        labels={
            "date": "날짜",
            "value": "수치",
            "variable": "항목"
        },
        title="기후 현상 → 재난문자 시계열"
    )

    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.12,
            xanchor="center",
            x=0.5,
            font=dict(size=12)
        ),
        margin=dict(t=70, b=50),
        height=500
    )

    return fig


def plot_emotion_heatmap(emotion_df):
    """
    긍정/중립/부정 감정 반응 시계열 (7일 이동 평균 smoothing)
    """
    if emotion_df.empty:
        return go.Figure().update_layout(
            title="😐 선택한 조건에 해당하는 감정 데이터가 없습니다.",
            xaxis_title="날짜",
            yaxis_title="감정 점수"
        )

    df = emotion_df.copy().sort_values("date")

    # 이동 평균 smoothing
    df["positive_smoothed"] = df["positive_emotion"].rolling(window=7, min_periods=1).mean()
    df["neutral_smoothed"] = df["neutral_emotion"].rolling(window=7, min_periods=1).mean()
    df["negative_smoothed"] = df["negative_emotion"].rolling(window=7, min_periods=1).mean()

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["date"], y=df["positive_smoothed"],
        mode='lines', name="긍정 감정", line=dict(color="green")
    ))

    fig.add_trace(go.Scatter(
        x=df["date"], y=df["neutral_smoothed"],
        mode='lines', name="중립 감정", line=dict(color="gray")
    ))

    fig.add_trace(go.Scatter(
        x=df["date"], y=df["negative_smoothed"],
        mode='lines', name="부정 감정", line=dict(color="red")
    ))

    fig.update_layout(
        title="📊 지역별 감정 반응 시계열",
        xaxis_title="날짜",
        yaxis_title="감정 점수",
        yaxis=dict(range=[0, 1]),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.15,
            xanchor="center",
            x=0.5,
            font=dict(size=12)
        ),
        margin=dict(t=70, b=50),
        height=500
    )

    return fig
