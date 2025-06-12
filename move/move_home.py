import streamlit as st

st.set_page_config(page_title="시간 흐름 분석", layout="wide")
st.title("📈 기후 현상 → 문자 발송 → 감정 반응 시간 흐름 분석")

st.markdown("""
본 분석은 재난 문자 발송 이후, SNS상의 감정 반응이 어떤 시간 차이를 두고 발생하는지를 시각적으로 분석합니다.
- 기후 현상 발생 시각
- 재난 문자 발송 시각
- SNS 감정 반응 시각 및 변화 추이

사건별 분석 결과는 좌측 사이드바 메뉴를 통해 확인 가능합니다.
""")
