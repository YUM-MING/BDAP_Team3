# ui_helpers.py
import streamlit as st
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import numpy as np 
import os
# 💡 [핵심] config 모듈을 임포트하여 색상 맵을 사용합니다.
import SNS.config as config
from io import BytesIO

def create_donut_chart(df, names_col, values_col, title, key_suffix=""):
    """ Plotly Express를 사용하여 도넛 차트를 생성하고 표시합니다. """
    if df.empty or not all(col in df.columns for col in [names_col, values_col]):
        st.info(f"'{title}' 차트를 생성할 데이터가 부족합니다.")
        return

    fig = px.pie(
        df,
        names=names_col,
        values=values_col,
        title=title,
        hole=0.4,
        color=names_col, # 색상을 이름(names_col) 기준으로 설정
        # 💡 [변경] names_col이 감정 관련 컬럼일 경우, 정의된 색상 맵을 사용합니다.
        color_discrete_map=config.EMOTION_COLOR_MAP if names_col in ['sentiment', 'sentiment_labels'] else None
    )
    
    pull_values = [0.05 if i == 0 else 0 for i in range(len(df))]
    fig.update_traces(
        textposition='outside',
        textinfo='percent+label',
        pull=pull_values,
        hovertemplate='<b>%{label}</b><br>값: %{value}<br>비중: %{percent}<extra></extra>'
    )
    fig.update_layout(showlegend=False, margin=dict(t=50, b=0, l=0, r=0))

    st.plotly_chart(fig, use_container_width=True, key=f"donut_chart_{key_suffix}")


def display_dataframe_with_title(df, title, key_suffix=""):
    """ 데이터프레임과 제목을 함께 표시합니다. """
    if not df.empty:
        st.markdown(f"##### {title}")
        st.dataframe(df, use_container_width=True, key=f"df_{key_suffix}")
    else:
        st.info(f"'{title}'에 대한 데이터가 없습니다.")

def create_bar_chart(df, x_col, y_col, title, color_col=None, orientation='v', top_n=None, key_suffix=""):
    """ 
    Plotly Express를 사용하여 막대 차트를 생성하고,
    색상 구분이 없는 모든 기본 막대 차트의 색상을 통일합니다.
    (제목은 Plotly 기본 스타일을 사용합니다.)
    """
    if df.empty or x_col not in df.columns or y_col not in df.columns:
        st.info(f"'{title}' 차트를 생성할 데이터가 부족합니다.")
        return

    # 데이터 정렬 및 상위 N개 필터링
    sort_col = y_col if orientation == 'v' else x_col
    chart_df = df.sort_values(by=sort_col, ascending=False)
    if top_n and len(chart_df) > top_n:
        chart_df = chart_df.head(top_n)

    if orientation == 'h':
        chart_df = chart_df.sort_values(by=x_col, ascending=True)

    # ------------------ [핵심 수정 부분 1] ------------------
    # px.bar 호출 시 title을 다시 원래대로 전달하여 Plotly 기본 제목을 사용합니다.
    fig = px.bar(
        chart_df,
        x=x_col,
        y=y_col,
        title=title, # <-- title을 다시 원래대로 설정
        color=color_col if color_col and color_col in chart_df.columns else None,
        orientation=orientation,
        color_discrete_map=config.EMOTION_COLOR_MAP if color_col in ['sentiment', 'sentiment_labels'] else None
    )

    # 색상 구분이 없을 때, 모든 막대 차트의 기본 색상을 지정합니다. (이 기능은 유지)
    is_color_col_provided = color_col and color_col in chart_df.columns
    if not is_color_col_provided:
        fig.update_traces(marker_color="#6393c8")

    # ------------------ [핵심 수정 부분 2] ------------------
    # 레이아웃 업데이트에서 제목 스타일을 지정하던 dict를 제거했습니다.
    fig.update_layout(
        xaxis_title=x_col.replace('_', ' ').title(),
        yaxis_title=y_col.replace('_', ' ').title(),
        legend_title_text=color_col.replace('_', ' ').title() if color_col and color_col in chart_df.columns else None
    )
    fig.update_yaxes(automargin=True)

    st.plotly_chart(fig, use_container_width=True, key=f"bar_chart_{key_suffix}")

def create_line_chart(df, x_col, y_col, color_col, title, x_label, y_label, color_label, markers=True, x_tickvals=None, xaxis_range=None):
    """ 
    Plotly Express를 사용하여 라인 차트를 생성하고 표시합니다.
    x축 범위(range)를 수동으로 설정하는 기능이 추가되었습니다.
    """
    if df.empty or not all(col in df.columns for col in [x_col, y_col, color_col]):
        st.info(f"'{title}' 차트를 생성할 데이터가 부족합니다.")
        return

    fig = px.line(
        df, x=x_col, y=y_col, color=color_col,
        title=title,
        labels={x_col: x_label, y_col: y_label, color_col: color_label},
        markers=markers,
        color_discrete_map=config.EMOTION_COLOR_MAP if color_col in ['sentiment', 'sentiment_labels'] else None
    )

    # ------------------ [핵심 수정 부분 시작] ------------------

    # Case 1: xaxis_range가 지정되었을 때 (특정 날짜 선택 시)
    # X축을 숫자 축으로 취급하고 범위를 직접 설정합니다.
    if xaxis_range is not None:
        fig.update_xaxes(
            range=xaxis_range,
            tickvals=x_tickvals # 눈금은 여전히 명시적으로 표시
        )
    
    # Case 2: xaxis_range가 없고, x_tickvals만 있을 때 (전체 기간 선택 시)
    # 기존과 동일하게 카테고리 축으로 처리합니다.
    elif x_tickvals:
        fig.update_xaxes(
            type='category', 
            tickvals=x_tickvals, 
            ticktext=[str(v) for v in x_tickvals]
        )
        
    # ------------------- [핵심 수정 부분 끝] -------------------
        
    st.plotly_chart(fig, use_container_width=True)

def create_wordcloud(word_counts_dict, title=None):
    """ Matplotlib과 WordCloud를 사용하여 원형 워드 클라우드를 생성하고, 크기를 줄여 가운데 정렬하여 표시합니다. """
    if not word_counts_dict:
        st.info("워드 클라우드를 생성할 키워드가 없습니다.")
        return

    # 1. 원형 마스크 생성 (기존과 동일)
    x, y = np.ogrid[:800, :800]
    mask_shape = (x - 400) ** 2 + (y - 400) ** 2 > 400 ** 2
    mask = 255 * mask_shape.astype(int)

    # 2. 워드 클라우드 생성 (기존과 동일)
    font_path = os.path.join(os.path.dirname(__file__), "malgun.ttf")
    try:
        wc = WordCloud(
            font_path=font_path,
            width=800, height=800,
            background_color='white', colormap='viridis', mask=mask
        ).generate_from_frequencies(word_counts_dict)
    except Exception as e:
        st.warning(f"한글 폰트 파일을 찾을 수 없습니다. (오류: {e}).")
        wc = WordCloud(width=800, height=800, background_color='white', colormap='Set2', mask=mask).generate_from_frequencies(word_counts_dict)

    # 3. Figure를 이미지 Bytes로 변환 (기존과 동일)
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.imshow(wc, interpolation='bilinear')
    ax.axis("off")
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight', pad_inches=0)
    image_bytes = buf.getvalue()

    # ------------------ [핵심 수정 부분 시작] ------------------

    # 4. st.columns를 사용하여 가운데 정렬 및 크기 조절
    if title:
        st.markdown(f"{title}")

    # 페이지를 세 개의 컬럼으로 나눕니다.
    # [2, 5, 2] -> 양쪽 여백을 늘리고 가운데 이미지 공간을 줄여 크기를 작게 만듭니다.
    left_space, image_column, right_space = st.columns([2, 5, 2])

    # 가운데 컬럼(image_column)에만 이미지를 표시합니다.
    with image_column:
        st.image(image_bytes, use_container_width=True)
    