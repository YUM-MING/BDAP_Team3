import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import json
import ast
import geopandas as gpd


@st.cache_data
def load(total_df):
    disaster_df = total_df["alerts"]

    def safe_eval(val):
        try:
            return ast.literal_eval(val)
        except:
            return []

    disaster_df['재난유형_리스트'] = disaster_df['재난유형_리스트'].apply(safe_eval)
    disaster_df['연도'] = pd.to_datetime(disaster_df['날짜']).dt.year

    exploded_df = disaster_df.explode('재난유형_리스트')
    exploded_df.rename(columns={'지역': '지역명', '재난유형_리스트': '재난유형'}, inplace=True)

    # GeoJSON -> GeoDataFrame으로 로드
    geo_df = gpd.read_file("geo/korea_regions.geojson")
    geo_df = geo_df[["geometry", "CTP_KOR_NM"]].rename(columns={"CTP_KOR_NM": "지역명"})
    geo_df['지역명'] = geo_df['지역명'].str.strip()

    return exploded_df, geo_df


def run_hitmap(total_df):

    df, geo_df = load(total_df)

    with st.sidebar:
        st.header("🔎 필터 선택")
        year_options = sorted(df['연도'].unique())
        disaster_types = df['재난유형'].dropna().unique().tolist()

        # 기본값 설정: 2023년 한파
        default_year = 2023 if 2023 in year_options else year_options[0]
        default_type = "한파" if "한파" in disaster_types else disaster_types[0]

        selected_year = st.selectbox("연도 선택", year_options, index=year_options.index(default_year))
        selected_type = st.selectbox("재난 유형 선택", sorted(disaster_types), index=sorted(disaster_types).index(default_type))

    # 필터링 및 병합
    filtered_df = df[(df['연도'] == selected_year) & (df['재난유형'] == selected_type)]
    grouped_df = filtered_df.groupby('지역명').size().reset_index(name='건수')
    grouped_df['지역명'] = grouped_df['지역명'].str.strip()
    merged = geo_df.merge(grouped_df, on='지역명', how='left').fillna(0)

    # 시각화
    st.subheader(f"▶ {selected_year}년 {selected_type} 발생 히트맵")
    fig, ax = plt.subplots(figsize=(6, 8))
    cmap = plt.cm.PuBu
    norm = mcolors.Normalize(vmin=0, vmax=max(10, merged['건수'].max()))

    merged_plot = merged.plot(column='건수', cmap=cmap, linewidth=0.2, edgecolor='grey', legend=False, ax=ax)

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm._A = []
    cbar = fig.colorbar(sm, ax=ax, orientation='vertical', shrink=0.3)
    # cbar.set_label('재난 발생 건수', fontsize=10)

    ax.axis('off')
    st.pyplot(fig)

