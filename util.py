import os
import pandas as pd
import streamlit as st

@st.cache_data
def load_data():
    folder_path = "data/"
    data_dict = {}

    for file in os.listdir(folder_path):
        if file.endswith(".csv"):
            file_path = os.path.join(folder_path, file)
            df = pd.read_csv(file_path)
            # 파일 확장자 제거한 이름을 key로 사용
            name = os.path.splitext(file)[0]
            data_dict[name] = df

    return data_dict
