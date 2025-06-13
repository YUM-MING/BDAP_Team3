import streamlit as st
import pandas as pd
import plotly.express as px
import re

def run_message(total_df):

    # 📌 CSV 파일 불러오기
    data = total_df["alerts"]

    # 날짜 처리 및 연도 추출
    data['연도'] = pd.to_datetime(data['날짜']).dt.year

    # 재난유형 분리 및 정제
    data['재난유형_리스트'] = data['재난유형_리스트'].apply(lambda x: x.split(','))

    expanded_rows = []
    for index, row in data.iterrows():
        for disaster_type in row['재난유형_리스트']:
            disaster_type_cleaned = re.sub(r'[^가-힣a-zA-Z0-9\s]', '', disaster_type.strip())
            expanded_rows.append({
                '연도': row['연도'],
                '재난유형_리스트': disaster_type_cleaned,
                '재난문자_건수': row['재난문자_건수']
            })

    expanded_data = pd.DataFrame(expanded_rows)

    # 데이터 집계
    yearly_counts = data.groupby('연도')['재난문자_건수'].sum().reset_index()
    yearly_counts['연도'] = yearly_counts['연도'].astype(str)
    type_counts = expanded_data.groupby(['연도', '재난유형_리스트'])['재난문자_건수'].sum().reset_index()
    region_counts = data.groupby(['연도', '지역'])['재난문자_건수'].sum().reset_index()

    # Streamlit 레이아웃
    st.title("📊 연도별 재난문자 발송 통계")

    # 연도 선택
    selected_year = st.selectbox("연도를 선택하세요:", sorted(yearly_counts['연도'].unique()))

    # 선 그래프
    fig1 = px.line(yearly_counts, x='연도', y='재난문자_건수',
                title='연도별 재난문자 발송 개수',
                labels={'연도': '연도', '재난문자_건수': '문자 발송 건수'},
                markers=True)
    highlight = yearly_counts[yearly_counts['연도'] == selected_year]
    fig1.add_scatter(x=highlight['연도'], y=highlight['재난문자_건수'],
                    mode='markers',
                    marker=dict(size=12, color='red'),
                    name='선택된 연도')
    st.plotly_chart(fig1)

    # ✅ 재난유형별 막대 그래프 (상세보기 자동 출력)
    filtered_detail = type_counts[type_counts['연도'] == selected_year]
    fig2 = px.bar(filtered_detail, x='재난유형_리스트', y='재난문자_건수',
                title=f'{selected_year}년 재난유형별 재난문자 통계',
                labels={'재난유형_리스트': '재난유형', '재난문자_건수': '문자 개수'},
                color='재난유형_리스트')
    fig2.update_layout(bargap=0.2)
    st.plotly_chart(fig2)

    # ✅ session_state 초기화
    if 'show_top5' not in st.session_state:
        st.session_state['show_top5'] = False
    if 'show_top3' not in st.session_state:
        st.session_state['show_top3'] = False

    # 🔘 버튼: 탑 5 재난유형
    if st.button('🔥 탑 5 재난유형 보기'):
        st.session_state['show_top5'] = True

    # 🔸 탑 5 재난유형 그래프
    if st.session_state['show_top5']:
        top5 = type_counts[type_counts['연도'] == selected_year].sort_values(by='재난문자_건수', ascending=False).head(5)
        fig3 = px.bar(top5, x='재난유형_리스트', y='재난문자_건수',
                    title=f'{selected_year}년 탑 5 재난유형',
                    labels={'재난유형_리스트': '재난유형', '재난문자_건수': '문자 개수'},
                    color='재난유형_리스트')
        st.plotly_chart(fig3)

    # 🔸 도넛 차트: 지역별
    filtered_region = region_counts[region_counts['연도'] == selected_year]
    fig4 = px.pie(filtered_region, names='지역', values='재난문자_건수',
                title=f'{selected_year}년 지역별 재난문자 발송 비율',
                hole=0.4)
    st.plotly_chart(fig4)

    # 🔘 버튼: 상위 3개 지역
    if st.button('📍 상위 3개 지역 보기'):
        st.session_state['show_top3'] = True
        
    # 🔸 상위 3개 지역 그래프
    if st.session_state['show_top3']:
        top3_region = filtered_region.sort_values(by='재난문자_건수', ascending=False).head(3)
        fig5 = px.bar(top3_region, x='재난문자_건수', y='지역', orientation='h',
                    title=f'{selected_year}년 상위 3개 지역 재난문자 발송',
                    labels={'재난문자_건수': '문자 개수', '지역': '지역'},
                    color='지역')
        st.plotly_chart(fig5)