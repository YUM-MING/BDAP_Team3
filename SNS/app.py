# app.py
import streamlit as st
# --- Streamlit 버전 확인 코드 (디버깅용) ---
# st.write(f"현재 스크립트에서 사용되는 Streamlit 버전: {st.__version__}") # 앱 실행 시 브라우저에 버전 표시
# --------------------------------------------

import pandas as pd
from collections import Counter
# 사용자 정의 모듈 import
import SNS.config as config # 상수 및 설정
import SNS.kote_module as kote_module
import SNS.youtube_api_module as youtube_api_module
import SNS.text_analysis_module as text_analysis_module
import SNS.ui_helpers as ui_helpers# UI 헬퍼 모듈 (선택적)

def run_sns():
    # KOTE 모델 로드 (앱 시작 시 한 번)
    kote_model = kote_module.load_trained_kote_model() # show_message=True는 기본값

    # YouTube API 키 확인
    if not youtube_api_module.YOUTUBE_API_KEY_VALUE:
        st.error("YouTube API 키가 .streamlit/secrets.toml 파일에 설정되지 않았습니다. 애플리케이션을 사용할 수 없습니다.")
        st.stop()

    # --- Streamlit 앱 UI 구성 ---
    st.title("YouTube 재난 영상 댓글 분석기")
    st.markdown(
        "YouTube 영상 댓글을 수집하여 재난 유형을 분류하고, KOTE 감성 분석 모델을 통해 댓글에 나타난 감정을 분석합니다. "
    )
    st.markdown("---")

    # --- 세션 상태 초기화 ---
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    if 'selected_video_ids_titles' not in st.session_state:
        st.session_state.selected_video_ids_titles = {}
    if 'all_comments_df' not in st.session_state:
        st.session_state.all_comments_df = pd.DataFrame()
    if 'main_search_button_clicked' not in st.session_state:
        st.session_state.main_search_button_clicked = False
    if 'main_analyze_button_clicked' not in st.session_state:
        st.session_state.main_analyze_button_clicked = False


    def is_disaster_related(query):
        """
        입력된 검색어가 재난 관련 키워드를 포함하는지 확인합니다.
        """
        # 1. 모든 동의어를 하나의 리스트로 만듭니다.
        all_disaster_keywords = [
            keyword 
            for keywords_list in config.DISASTER_SYNONYMS.values() 
            for keyword in keywords_list
        ]
        
        # 2. 검색어에 키워드 중 하나라도 포함되어 있는지 확인합니다.
        #    any() 함수는 하나라도 True이면 즉시 True를 반환하므로 효율적입니다.
        if any(keyword in query for keyword in all_disaster_keywords):
            return True
        return False
        

    # --- 1. 영상 검색 및 분석 설정 섹션 ---
    with st.container():
        st.subheader("1. YouTube 영상 검색 및 분석 설정")

        search_query = st.text_input(
            "검색어 입력:",
            placeholder="예: 포항 지진 피해, 서울 폭우 상황",
            key="main_search_query"
        )

        col1_search_opts, col2_search_opts = st.columns(2)
        with col1_search_opts:
            sort_order_options = {
                "관련성 높은 순": "relevance",
                "조회수 많은 순": "viewCount",
            }
            sort_order_display = st.selectbox(
                "정렬 방식:",
                list(sort_order_options.keys()),
                key="main_sort_order"
            )
            sort_order = sort_order_options[sort_order_display]
        with col2_search_opts:
            max_search_results = st.slider(
                "검색 결과 수 (최대):", 5, 50,
                config.DEFAULT_MAX_SEARCH_RESULTS,
                key="main_max_search_results"
            )

        if st.button("YouTube 영상 검색", type="primary", key="main_search_button_trigger_v2"):
            st.session_state.main_search_button_clicked = True
            
            # 1. 검색어 입력 여부 확인
            if not search_query:
                st.warning("검색어를 입력해주세요.")
                # 이전 검색 결과가 남아있지 않도록 초기화
                st.session_state.search_results = None 
            
            # 2. 재난 관련 키워드 포함 여부 확인 (가장 중요한 변경점)
            elif not is_disaster_related(search_query):
                st.warning("재난 관련 키워드(예: 지진, 홍수, 태풍 등)를 포함하여 검색해주세요.")
                # 유효하지 않은 검색이므로 이전 결과 초기화
                st.session_state.search_results = None
                
            # 3. 모든 검증 통과 시, 실제 검색 실행
            else:
                with st.spinner("YouTube 영상을 검색 중입니다..."):
                    st.session_state.search_results = youtube_api_module.search_youtube_videos(
                        search_query, sort_order, max_search_results
                    )
                if not st.session_state.search_results:
                    st.warning("검색 결과가 없습니다. 다른 검색어를 시도해보세요.")
                else:
                    st.session_state.selected_video_ids_titles = {}
                    st.session_state.all_comments_df = pd.DataFrame()
                    st.info(f"{len(st.session_state.search_results)}개의 영상을 찾았습니다. 아래에서 분석할 영상을 선택하세요.")

        if st.session_state.search_results:
            st.markdown("##### 분석할 영상 선택 (최대 5개)")
            video_options_dict = {
                f"{idx+1}. {v['title']} (게시일: {v['published_at'][:10] if v['published_at'] else '날짜 정보 없음'})": v['id']
                for idx, v in enumerate(st.session_state.search_results)
            }
            default_selected_display_keys = [
                display_key for display_key, vid_id in video_options_dict.items()
                if vid_id in st.session_state.selected_video_ids_titles.keys()
            ]

            selected_display_keys = st.multiselect(
                "아래 목록에서 분석할 영상을 선택하세요:",
                options=list(video_options_dict.keys()),
                max_selections=5,
                default=default_selected_display_keys,
                key="main_video_multiselect_v2" # 키 변경
            )

            current_selected_temp = {}
            for display_key in selected_display_keys:
                video_id = video_options_dict.get(display_key)
                if video_id:
                    original_video_info = next((v for v in st.session_state.search_results if v['id'] == video_id), None)
                    if original_video_info:
                        current_selected_temp[video_id] = original_video_info['title']
            st.session_state.selected_video_ids_titles = current_selected_temp

            if st.session_state.selected_video_ids_titles:
                st.caption(f"선택된 영상 수: {len(st.session_state.selected_video_ids_titles)}개")
                cols_thumbnails = st.columns(min(len(st.session_state.selected_video_ids_titles), 5))
                search_results_map_by_id = {v['id']: v for v in st.session_state.search_results}
                for i, video_id in enumerate(list(st.session_state.selected_video_ids_titles.keys())[:5]):
                    video_info = search_results_map_by_id.get(video_id)
                    if video_info and video_info.get('thumbnail'):
                        with cols_thumbnails[i]:
                            st.image(video_info['thumbnail'], caption=video_info['title'][:30]+"...", width=150)
                            st.markdown(f"[{video_info['title'][:20]}...](https://www.youtube.com/watch?v={video_id})", unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("2. 댓글 분석 옵션 설정")
        col1_analysis_opts, col2_analysis_opts = st.columns(2)
        with col1_analysis_opts:
            max_comments_per_video = st.slider(
                "영상별 최대 댓글 수집:", 50, 500,
                config.DEFAULT_MAX_COMMENTS_PER_VIDEO,
                step=50,
                key="main_max_comments_per_video_v2" # 키 변경
            )
        with col2_analysis_opts:
            emotion_threshold = st.slider(
                "감정 분류 임계값 (KOTE):", 0.1, 0.9,
                config.DEFAULT_EMOTION_THRESHOLD,
                step=0.05,
                key="main_emotion_threshold_v2" # 키 변경
            )

        if st.button(
            "선택된 영상 댓글 분석 시작",
            type="primary",
            disabled=not st.session_state.selected_video_ids_titles or not kote_model,
            key="main_analyze_button_trigger_v2" # 키 변경
        ):
            st.session_state.main_analyze_button_clicked = True
            if not kote_model:
                st.error("KOTE 감성 분석 모델이 로드되지 않아 분석을 시작할 수 없습니다.")
            elif st.session_state.selected_video_ids_titles:
                all_comments_list_for_df = []
                total_videos_to_analyze = len(st.session_state.selected_video_ids_titles)
                analysis_progress_bar = st.progress(0, text="분석 준비 중...")
                analysis_status_text = st.empty()

                with st.spinner("선택된 영상의 댓글을 수집하고 분석 중입니다. 잠시만 기다려주세요..."):
                    for i, (video_id, video_title) in enumerate(st.session_state.selected_video_ids_titles.items()):
                        progress_value_collect = int(((i + 0.5) / total_videos_to_analyze) * 80)
                        analysis_status_text.info(f"'{video_title}' 영상 댓글 수집 중... ({i+1}/{total_videos_to_analyze})")
                        analysis_progress_bar.progress(progress_value_collect, text=f"댓글 수집: {video_title} ({i+1}/{total_videos_to_analyze})")

                        comments = youtube_api_module.get_video_comments(video_id, total_max_comments=max_comments_per_video)
                        for comment_data in comments:
                            comment_data['video_title'] = video_title
                        all_comments_list_for_df.extend(comments)

                    if not all_comments_list_for_df:
                        st.warning("수집된 댓글이 없습니다. 영상 선택 또는 댓글 수집 설정을 확인해주세요.")
                        st.session_state.all_comments_df = pd.DataFrame()
                        if analysis_progress_bar is not None: analysis_progress_bar.empty()
                        if analysis_status_text is not None: analysis_status_text.empty()
                    else:
                        analysis_status_text.info("댓글 텍스트 전처리 및 감정/재난 라벨링 중...")
                        analysis_progress_bar.progress(80, text="텍스트 분석 중...")

                        df_raw_comments = pd.DataFrame(all_comments_list_for_df)

                        if 'text' in df_raw_comments.columns and not df_raw_comments['text'].isnull().all():
                            df_raw_comments['text'] = df_raw_comments['text'].astype(str)
                            comment_texts_list = df_raw_comments["text"].tolist()

                            df_raw_comments["disaster_labels"] = df_raw_comments["text"].apply(text_analysis_module.label_disaster)
                            df_raw_comments["sentiment_labels"] = kote_module.analyze_sentiment_kote_batch(
                                comment_texts_list, kote_model, emotion_threshold
                            )

                            df_raw_comments["published_at"] = pd.to_datetime(df_raw_comments["published_at"], errors='coerce')
                            df_raw_comments["comment_hour"] = df_raw_comments["published_at"].dt.hour
    
                            st.session_state.all_comments_df = df_raw_comments
                            analysis_progress_bar.progress(100, text="분석 완료!")
                            st.success(f"총 {len(df_raw_comments)}개의 댓글에 대한 분석이 완료되었습니다!")
                        else:
                            st.warning("댓글 데이터에 유효한 'text' 내용이 없어 분석을 진행할 수 없습니다.")
                            st.session_state.all_comments_df = pd.DataFrame()
                        if analysis_status_text is not None: analysis_status_text.empty()
            else:
                st.error("분석할 영상을 먼저 선택해주세요.")

    st.markdown("---")

    # --- 3. 분석 결과 탭 섹션 ---
    if not st.session_state.all_comments_df.empty:
        st.header("댓글 분석 결과")
        df_analysis_results = st.session_state.all_comments_df.copy()

        valid_sentiments_global = df_analysis_results["sentiment_labels"].dropna().apply(
            lambda x: [s for s in x if s != '없음'] if isinstance(x, list) and x else None
        ).dropna()
        sentiment_counts_global = Counter([label for sublist in valid_sentiments_global for label in sublist])

        valid_disasters_global = df_analysis_results["disaster_labels"].dropna().apply(
            lambda x: x if isinstance(x, list) and x else None
        ).dropna()
        disaster_label_counts_global = Counter([label for sublist in valid_disasters_global for label in sublist])

        tab_titles_list = [
            "종합 요약", "전체 감정 분포", "시간대별 감정", "전체 키워드",
            "정별 키워드", "재난 유형별 분석", "항목 간 비교 분석"
        ]
        (tab_summary, tab_sentiment_distribution, tab_sentiment_over_time, tab_all_keywords,
        tab_keywords_by_emotion, tab_analysis_by_disaster, tab_comparative_analysis) = st.tabs(tab_titles_list)

        with tab_summary:
            st.subheader("종합 요약 및 데이터 미리보기")
            total_comments = len(df_analysis_results)
            num_videos = df_analysis_results['video_id'].nunique()
            avg_comments_video = total_comments / num_videos if num_videos > 0 else 0

            sum_col1, sum_col2, sum_col3 = st.columns(3)
            with sum_col1: st.metric("총 분석 댓글 수", f"{total_comments:,} 개")
            with sum_col2: st.metric("분석된 영상 수", f"{num_videos} 개")
            with sum_col3: st.metric("영상당 평균 댓글 수", f"{avg_comments_video:.1f} 개")

            if st.checkbox("수집된 전체 댓글 데이터 미리보기 (상위 5개)", key="show_raw_data_summary_tab_v4"): # 키 변경
                display_cols = ['video_title', 'text', 'sentiment_labels', 'disaster_labels', 'published_at', 'like_count']
                existing_display_cols = [col for col in display_cols if col in df_analysis_results.columns]
                st.dataframe(df_analysis_results[existing_display_cols].head())

        with tab_sentiment_distribution:
            st.subheader("전체 댓글의 감정 분포 (KOTE Multi-label)")
            if sentiment_counts_global:
                df_sentiment_dist = pd.DataFrame(
                    sentiment_counts_global.items(), columns=['sentiment', 'count']
                ).sort_values(by='count', ascending=False)

                # 워드 클라우드는 딕셔너리를 입력으로 받으므로, 데이터프레임을 다시 딕셔너리로 변환
                sentiment_dict = pd.Series(df_sentiment_dist['count'].values, index=df_sentiment_dist['sentiment']).to_dict()
                
                ui_helpers.create_bar_chart(
                df_sentiment_dist, x_col='sentiment', y_col='count',
                title="주요 감정 레이블 빈도 (상위 15개)", color_col='sentiment', top_n=15,
                key_suffix="_global_sent_dist_v4" # 키 변경
                )
                
                if st.checkbox("전체 감정 빈도 데이터 보기", key="show_all_sentiment_data_dist_tab_v4"): # 키 변경
                    ui_helpers.display_dataframe_with_title(df_sentiment_dist, "전체 감정 빈도", "_all_sent_data_v4") # 키 변경
            else:
                st.info("감정 분석 결과가 없거나 '없음' 감정만 존재합니다.")
        
        df_analysis_results['comment_date'] = df_analysis_results['published_at'].dt.date

        df_analysis_results['published_at'] = pd.to_datetime(df_analysis_results['published_at'])
        df_analysis_results['comment_year'] = df_analysis_results['published_at'].dt.year

        def display_sentiment_trend_chart(df_analysis, sentiment_counts, time_unit, top_n=5, title_suffix="", x_axis_type='full'):
            """
            지정된 시간 단위(시간, 연도 등)에 따른 감정 변화 차트를 생성합니다.
            (X축 범위 자동 조절 기능 추가)
            """
            
            # 시간 단위에 따른 설정(Configuration) 정의
            configs = {
                'hour': {
                    'col': 'comment_hour', 'title_prefix': '시간대별', 'x_label': '댓글 작성 시간',
                    'check_unique': lambda df: True, 'fail_msg': "",
                    'get_ticks': lambda df, axis_type: list(range(24)) if axis_type == 'full' else sorted(df['comment_hour'].unique())
                },
                'year': {
                    'col': 'comment_year', 'title_prefix': '연도별', 'x_label': '댓글 작성 연도',
                    'check_unique': lambda df: df['comment_year'].nunique() > 1,
                    'fail_msg': "모든 댓글이 동일한 연도에 작성되어 연도별 추이 분석을 생략합니다.",
                    'get_ticks': lambda df, axis_type: sorted(df['comment_year'].unique())
                }
            }
            
            cfg = configs.get(time_unit)
            if not cfg:
                st.error(f"'{time_unit}'은(는) 지원되지 않는 시간 단위입니다.")
                return

            # [가드 클로즈] 로직 (이전과 동일)
            if cfg['col'] not in df_analysis.columns or not sentiment_counts:
                st.info(f"분석에 필요한 정보(게시 {cfg['title_prefix']} 또는 감정)가 없습니다.")
                return
            if not cfg['check_unique'](df_analysis):
                st.info(cfg['fail_msg'])
                return

            # 데이터 전처리 및 가공
            df_processed = df_analysis.copy().explode('sentiment_labels').dropna(subset=['sentiment_labels']).query("sentiment_labels != '없음'")
            if df_processed.empty:
                st.info(f"{cfg['title_prefix']} 분석을 위한 유효한 감정 데이터가 포함된 댓글이 없습니다.")
                return

            # 상위 N개 감정 필터링 로직
            top_sentiments_df = pd.DataFrame(sentiment_counts.items(), columns=['sentiment', 'count']).sort_values(by='count', ascending=False)
            top_sentiments_list = top_sentiments_df.head(top_n)['sentiment'].tolist()
            if not top_sentiments_list:
                st.info(f"분석된 주요 감정이 없습니다 ({cfg['title_prefix']} 차트).")
                return

            # 최종 차트 데이터 생성
            chart_df = df_processed.query("sentiment_labels in @top_sentiments_list").groupby([cfg['col'], 'sentiment_labels']).size().reset_index(name='count')
            if chart_df.empty:
                st.info(f"선택된 주요 감정(상위 {len(top_sentiments_list)}개)에 대한 {cfg['title_prefix']} 데이터가 충분하지 않습니다.")
                return

            # ------------------ [핵심 수정 부분 시작] ------------------
            # X축 눈금과 범위(range)를 설정
            x_ticks = cfg['get_ticks'](chart_df, x_axis_type)
            xaxis_range = None # 기본값은 None (자동)

            # 시간대 분석이고, x축 자동 설정이며, 데이터가 하나일 때 범위 수동 지정
            if time_unit == 'hour' and x_axis_type == 'auto' and len(x_ticks) == 1:
                center_hour = x_ticks[0]
                # 해당 시간의 좌우 1시간 범위를 보여주되, 0~23시를 벗어나지 않게 함
                range_min = max(0, center_hour - 1)
                range_max = min(23, center_hour + 1)
                xaxis_range = [range_min, range_max]
            # ------------------- [핵심 수정 부분 끝] -------------------

            # 차트 생성
            final_title = f"{cfg['title_prefix']} 주요 감정 빈도 (상위 {len(top_sentiments_list)}개){title_suffix}"
            
            # ui_helpers.create_line_chart 함수가 xaxis_range 인자를 받을 수 있어야 함
            ui_helpers.create_line_chart(
                chart_df,
                x_col=cfg['col'], y_col="count", color_col="sentiment_labels",
                title=final_title,
                x_label=cfg['x_label'], y_label="댓글 수", color_label="감정 레이블",
                x_tickvals=x_ticks,
                xaxis_range=xaxis_range # 새로 추가된 인자
            )


        # ----------------------------------------------------------------------
        # 2. Streamlit UI 렌더링 (호출 부분)
        # ----------------------------------------------------------------------
        with tab_sentiment_over_time:
            
            # ==================================================================
            # 1. 시간대별 감정 변화 분석 (날짜 선택 기능 추가)
            # ==================================================================
            st.subheader("시간대별 댓글 감정 변화 (KOTE Multi-label)")

            analysis_mode = st.radio(
                "분석 범위를 선택하세요:",
                ('전체 기간', '특정 날짜 선택'),
                horizontal=True,
                key='time_analysis_mode'
            )

            if analysis_mode == '전체 기간':
                # 전체 기간 분석 시에는 x축을 0-23시 모두 표시
                display_sentiment_trend_chart(
                    df_analysis_results, 
                    sentiment_counts_global, 
                    time_unit='hour',
                    x_axis_type='full'
                )
            
            elif analysis_mode == '특정 날짜 선택':
                # 데이터에 있는 날짜의 최소/최대값 구하기
                min_date = df_analysis_results['comment_date'].min()
                max_date = df_analysis_results['comment_date'].max()

                # 날짜 선택 위젯
                selected_date = st.date_input(
                    "분석할 날짜를 선택하세요:",
                    value=max_date,
                    min_value=min_date,
                    max_value=max_date,
                    format="YYYY-MM-DD",
                    key='date_selector_for_time'
                )

                if selected_date:
                    # 선택된 날짜로 데이터 필터링
                    df_filtered_by_date = df_analysis_results[df_analysis_results['comment_date'] == selected_date]

                    if df_filtered_by_date.empty:
                        st.info(f"**{selected_date.strftime('%Y-%m-%d')}**에는 작성된 댓글이 없습니다.")
                    else:
                        # 선택된 날짜의 데이터에 대해서만 감정 빈도수 다시 계산
                        filtered_sentiment_counts = (
                            df_filtered_by_date.copy()
                            .explode('sentiment_labels')
                            .dropna(subset=['sentiment_labels'])
                            .query("sentiment_labels != '없음'")
                            ['sentiment_labels'].value_counts().to_dict()
                        )
                        
                        # 특정 날짜 분석 시에는 x축을 데이터에 맞게 자동으로 설정
                        display_sentiment_trend_chart(
                            df_filtered_by_date, 
                            filtered_sentiment_counts, 
                            time_unit='hour',
                            title_suffix=f" - {selected_date.strftime('%Y-%m-%d')}",
                            x_axis_type='auto' # x축을 동적으로 설정
                        )

            st.divider()

            # ==================================================================
            # 2. 연도별 감정 변화 분석 (기존과 동일)
            # ==================================================================
            st.subheader("연도별 댓글 감정 변화 (KOTE Multi-label)")
            display_sentiment_trend_chart(
                df_analysis_results, 
                sentiment_counts_global, 
                time_unit='year'
            )
        with tab_all_keywords:
            st.subheader("주요 키워드 (전체 댓글에서 추출)")
            all_comments_text_combined = ""
            if 'text' in df_analysis_results.columns and not df_analysis_results['text'].isnull().all():
                text_series_all = df_analysis_results["text"].astype(str).str.strip().dropna()
                filtered_text_series_all = text_series_all[
                    (text_series_all != 'nan') & (text_series_all != '')
                ]
                all_comments_text_combined = " ".join(filtered_text_series_all)

            if all_comments_text_combined.strip():
                # extract_keywords가 리스트 [('단어', 빈도), ...]를 반환합니다.
                top_keywords_list = text_analysis_module.extract_keywords(all_comments_text_combined, num_keywords=50)
                
                if top_keywords_list:
                    # 💡 [해결] 리스트를 딕셔너리로 변환합니다.
                    top_keywords_dict = dict(top_keywords_list)
                    
                    # 변환된 딕셔너리를 워드 클라우드 함수로 전달합니다.
                    ui_helpers.create_wordcloud(
                        top_keywords_dict,
                        title="전체 댓글 주요 키워드 빈도" 
                    )
                else:
                    st.info("전체 댓글에서 주요 키워드를 추출할 수 없었습니다.")
            else:
                st.info("키워드 분석을 위한 유효한 텍스트 데이터가 없습니다.")

        with tab_keywords_by_emotion:
            st.subheader("특정 감정 관련 주요 키워드 분석")
            available_emotions_for_kw_analysis = sorted(list(sentiment_counts_global.keys()))

            if not available_emotions_for_kw_analysis:
                st.info("키워드를 분석할 감정이 없습니다. 먼저 댓글 분석을 수행해주세요.")
            else:
                selected_emotion_for_kw = st.selectbox(
                    "키워드를 분석할 감정을 선택하세요:",
                    options=available_emotions_for_kw_analysis,
                    index=0 if available_emotions_for_kw_analysis else None,
                    key="emotion_keyword_selectbox_v4" # 키 변경
                )
                if selected_emotion_for_kw:
                    emotion_specific_comments_df = df_analysis_results[
                        df_analysis_results['sentiment_labels'].apply(
                            lambda x: isinstance(x, list) and selected_emotion_for_kw in x
                        )
                    ]
                    if emotion_specific_comments_df.empty:
                        st.warning(f"'{selected_emotion_for_kw}' 감정이 포함된 댓글이 없습니다.")
                    else:
                        st.markdown(f"#### '{selected_emotion_for_kw}' 감정 관련 주요 키워드 (댓글 {len(emotion_specific_comments_df)}개 대상)")
                        emotion_specific_text_combined = ""
                        if 'text' in emotion_specific_comments_df.columns and not emotion_specific_comments_df['text'].isnull().all():
                            text_series_emotion = emotion_specific_comments_df["text"].astype(str).str.strip().dropna()
                            filtered_text_series_emotion = text_series_emotion[
                                (text_series_emotion != 'nan') & (text_series_emotion != '')
                            ]
                            emotion_specific_text_combined = " ".join(filtered_text_series_emotion)

                        if emotion_specific_text_combined.strip():
                            emotion_keywords = text_analysis_module.extract_keywords(emotion_specific_text_combined, num_keywords=15)
                            if emotion_keywords:
                                df_emotion_kws = pd.DataFrame(emotion_keywords, columns=["keyword", "count"])
                                ui_helpers.create_bar_chart(
                                    df_emotion_kws, x_col='count', y_col='keyword', orientation='h',
                                    title=f"'{selected_emotion_for_kw}' 감정 주요 키워드 (상위 15개)", top_n=15,
                                    key_suffix=f"_kw_v4_{selected_emotion_for_kw.replace('/', '_').replace(' ', '_')}" # 키 변경
                                )
                                if st.checkbox(f"'{selected_emotion_for_kw}' 관련 댓글 일부 보기", key=f"show_comments_for_emotion_kw_v4_{selected_emotion_for_kw.replace(' ', '_')}"): # 키에 공백 제거
                                    st.dataframe(emotion_specific_comments_df[['video_title', 'text', 'sentiment_labels']].head(10))
                            else:
                                st.info(f"'{selected_emotion_for_kw}' 감정 관련 댓글에서 주요 키워드를 추출할 수 없었습니다.")
                        else:
                            st.info(f"'{selected_emotion_for_kw}' 감정 관련 댓글에 분석할 유효한 텍스트가 없습니다.")

        with tab_analysis_by_disaster:
            st.subheader("재난 유형별 심층 분석")
            if not disaster_label_counts_global:
                st.info("댓글에서 식별된 재난 유형이 없습니다.")
            else:
                sorted_disaster_types = sorted(list(disaster_label_counts_global.keys()))

                if len(sorted_disaster_types) == 1:
                    disaster_type = sorted_disaster_types[0]
                    st.markdown(f"#### '{disaster_type}' 관련 댓글 분석")
                    disaster_specific_df = df_analysis_results[
                        df_analysis_results["disaster_labels"].apply(lambda x: isinstance(x, list) and disaster_type in x)
                    ]
                    if disaster_specific_df.empty:
                        st.write(f"'{disaster_type}' 관련 댓글이 없습니다.")
                    else:
                        col_dis_sent, col_dis_kw = st.columns(2)
                        with col_dis_sent:
                            st.markdown("##### 감정 분포 (KOTE)")
                            dis_valid_sents = disaster_specific_df["sentiment_labels"].dropna().apply(
                                lambda x: [s for s in x if s != '없음'] if isinstance(x, list) and x else []
                            ).tolist()
                            dis_valid_sents_flattened = [label for sublist in dis_valid_sents if sublist for label in sublist]
                            if dis_valid_sents_flattened:
                                dis_sent_counts = Counter(dis_valid_sents_flattened)
                                df_dis_sent = pd.DataFrame(dis_sent_counts.items(), columns=['sentiment', 'count']).sort_values(by='count', ascending=False)
                                ui_helpers.create_bar_chart(
                                    df_dis_sent, x_col='sentiment', y_col='count',
                                    title=f"'{disaster_type}' 주요 감정 (상위 10개)", color_col='sentiment', top_n=10,
                                    key_suffix=f"_sent_v4_{disaster_type.replace(' ', '_')}" # 키 변경
                                )
                            else: st.info("해당 재난 유형 관련 댓글에서 감정 분석 결과가 없습니다.")
                        with col_dis_kw:
                            st.markdown("##### 주요 키워드")
                            dis_text = ""
                            if 'text' in disaster_specific_df.columns and not disaster_specific_df['text'].isnull().all():
                                text_series_dis_single = disaster_specific_df["text"].astype(str).str.strip().dropna()
                                filtered_text_series_dis_single = text_series_dis_single[
                                    (text_series_dis_single != 'nan') & (text_series_dis_single != '')
                                ]
                                dis_text = " ".join(filtered_text_series_dis_single)

                            if dis_text.strip():
                                dis_kws = text_analysis_module.extract_keywords(dis_text, num_keywords=10)
                                if dis_kws:
                                    df_dis_kws = pd.DataFrame(dis_kws, columns=["keyword", "count"])
                                    ui_helpers.create_bar_chart(
                                        df_dis_kws, x_col='keyword', y_col='count',
                                        title=f"관련 키워드 (상위 10개)", top_n=10,
                                        key_suffix=f"_kw_v4_{disaster_type.replace(' ', '_')}" # 키 변경
                                    )
                                else: st.info("추출된 키워드 없음")
                            else: st.info("키워드 분석을 위한 유효한 텍스트 없음")
                        if st.checkbox(f"'{disaster_type}' 관련 댓글 보기 ({len(disaster_specific_df)}개)", key=f"show_comments_single_dis_v4_{disaster_type.replace(' ', '_')}"): # 키에 공백 제거
                            st.dataframe(disaster_specific_df[['video_title', 'text', 'sentiment_labels', 'published_at']].head(20))
                else:
                    disaster_sub_tabs = st.tabs([dt.replace(' ', '_') for dt in sorted_disaster_types]) # 탭 이름에 공백 제거
                    for i, disaster_type_in_tab in enumerate(sorted_disaster_types):
                        with disaster_sub_tabs[i]:
                            st.markdown(f"##### '{disaster_type_in_tab}' 관련 댓글 분석")
                            disaster_df_for_tab = df_analysis_results[
                                df_analysis_results["disaster_labels"].apply(lambda x: isinstance(x, list) and disaster_type_in_tab in x)
                            ]
                            if disaster_df_for_tab.empty:
                                st.write(f"'{disaster_type_in_tab}' 관련 댓글이 없습니다.")
                                continue

                            col_tab_sent, col_tab_kw = st.columns(2)
                            with col_tab_sent:
                                st.markdown("###### 감정 분포 (KOTE)")
                                tab_valid_sents = disaster_df_for_tab["sentiment_labels"].dropna().apply(
                                    lambda x: [s for s in x if s != '없음'] if isinstance(x, list) and x else []
                                ).tolist()
                                tab_valid_sents_flattened = [label for sublist in tab_valid_sents if sublist for label in sublist]
                                if tab_valid_sents_flattened:
                                    tab_sent_counts = Counter(tab_valid_sents_flattened)
                                    df_tab_sent = pd.DataFrame(tab_sent_counts.items(), columns=['sentiment', 'count']).sort_values(by='count', ascending=False)
                                    ui_helpers.create_bar_chart(
                                        df_tab_sent, x_col='sentiment', y_col='count',
                                        title=f"주요 감정 (상위 10개)", color_col='sentiment', top_n=10,
                                        key_suffix=f"_sent_tab_v4_{disaster_type_in_tab.replace(' ', '_')}" # 키 변경
                                    )
                                else: st.info("감정 분석 결과 없음")
                            with col_tab_kw:
                                st.markdown("###### 주요 키워드")
                                tab_text = ""
                                if 'text' in disaster_df_for_tab.columns and not disaster_df_for_tab['text'].isnull().all():
                                    text_series_dis_tab = disaster_df_for_tab["text"].astype(str).str.strip().dropna()
                                    filtered_text_series_dis_tab = text_series_dis_tab[
                                        (text_series_dis_tab != 'nan') & (text_series_dis_tab != '')
                                    ]
                                    tab_text = " ".join(filtered_text_series_dis_tab)

                                if tab_text.strip():
                                    tab_kws = text_analysis_module.extract_keywords(tab_text, num_keywords=10)
                                    if tab_kws:
                                        df_tab_kws = pd.DataFrame(tab_kws, columns=["keyword", "count"])
                                        ui_helpers.create_bar_chart(
                                            df_tab_kws, x_col='keyword', y_col='count',
                                            title=f"관련 키워드 (상위 10개)", top_n=10,
                                            key_suffix=f"_kw_tab_v4_{disaster_type_in_tab.replace(' ', '_')}" # 키 변경
                                        )
                                    else: st.info("추출된 키워드 없음")
                                else: st.info("키워드 분석을 위한 유효한 텍스트 없음")

                            if st.checkbox(f"'{disaster_type_in_tab}' 관련 댓글 보기 ({len(disaster_df_for_tab)}개)", key=f"show_tab_comments_v4_{disaster_type_in_tab.replace(' ', '_')}"): # 키에 공백 제거
                                st.dataframe(disaster_df_for_tab[['video_title', 'text', 'sentiment_labels', 'published_at']].head(20))

        # app.py (tab_comparative_analysis 전체 코드)

    # ... (이전 탭들 및 필요한 import, 변수 설정은 이미 완료되었다고 가정) ...
    # df_analysis_results, st.session_state.selected_video_ids_titles, disaster_label_counts_global 등이 사용 가능해야 함

        # --- 탭 7: 항목 간 비교 분석 ---
        with tab_comparative_analysis:
            st.subheader("항목 간 데이터 비교 분석")

            comparison_target_type = st.radio(
                "비교할 대상을 선택하세요:",
                ("영상 간 비교", "재난 유형 간 비교"),
                horizontal=True,
                key="main_comparison_target_type_radio_tab7_v6" # 키 업데이트
            )

            # 비교 UI를 실제로 표시할지 결정하는 플래그
            display_comparison_ui = False
            # 비교 분석에 최종적으로 사용될 아이템 목록 (초기화)
            selected_items_for_final_comparison = []


            if comparison_target_type == "영상 간 비교":
                # "1. 영상 검색 및 분석 설정" 단계에서 사용자가 선택하여
                # 실제로 댓글 분석이 수행된 영상들의 제목 목록을 가져옵니다.
                # st.session_state.selected_video_ids_titles는 분석 시작 시점의 선택 목록이므로,
                # df_analysis_results에 있는 실제 분석된 영상 제목을 사용하는 것이 더 정확할 수 있습니다.
                if 'video_title' in df_analysis_results.columns:
                    analyzed_video_titles_for_comparison_options = sorted(list(df_analysis_results['video_title'].unique()))
                else:
                    analyzed_video_titles_for_comparison_options = [] # 분석 결과에 video_title이 없는 경우

                num_analyzed_videos = len(analyzed_video_titles_for_comparison_options)

                if num_analyzed_videos < 2:
                    st.info(f"영상 간 비교를 위해서는 최소 2개의 영상에 대한 분석 결과가 필요합니다. 현재 분석된 고유 영상은 {num_analyzed_videos}개입니다. '1. 영상 검색 및 분석 설정' 단계에서 더 많은 영상을 선택하고 분석을 실행해주세요.")
                else:
                    # min_selections 인자 없이 multiselect 사용
                    temp_selected_videos = st.multiselect(
                        f"분석된 영상 중 비교할 영상을 선택하세요 (현재 {num_analyzed_videos}개 분석됨, 2개 이상 선택):",
                        options=analyzed_video_titles_for_comparison_options,
                        default=[],
                        key="compare_videos_multiselect_tab7_v6" # 키 업데이트
                    )

                    if not temp_selected_videos:
                        st.info("위 목록에서 비교할 영상을 2개 이상 선택해주세요.")
                    elif len(temp_selected_videos) == 1:
                        st.warning(f"1개의 영상만 선택되었습니다 ('{temp_selected_videos[0]}'). 비교를 위해서는 2개 이상의 영상이 필요합니다.")
                    else: # 2개 이상 선택됨
                        selected_items_for_final_comparison = temp_selected_videos
                        display_comparison_ui = True # 비교 UI 표시 조건 충족
                
                # --- 영상 간 비교 UI 및 데이터 처리 로직 ---
                # --- 영상 간 비교 UI 및 데이터 처리 로직 ---
                if display_comparison_ui and selected_items_for_final_comparison:
                    cols_for_comparison = st.columns(len(selected_items_for_final_comparison))

                    for i, video_title_for_comp in enumerate(selected_items_for_final_comparison):
                        with cols_for_comparison[i]:
                            # 영상 제목이 길 수 있으므로 일부만 표시
                            st.markdown(f"##### {video_title_for_comp[:40]}...")
                            
                            item_df_comp = df_analysis_results[df_analysis_results['video_title'] == video_title_for_comp]
                            
                            if item_df_comp.empty:
                                st.write("해당 영상에 대한 분석 데이터가 없습니다.")
                                st.markdown("---")
                                continue

                            # 1. 감정 분포 비교 (도넛 차트로 변경)
                            st.markdown("**감정 구성비**")
                            item_comp_sents = item_df_comp["sentiment_labels"].dropna().apply(
                                lambda x: [s for s in x if s != '없음'] if isinstance(x, list) and x else []
                            ).tolist()
                            item_comp_sents_flattened = [label for sublist in item_comp_sents if sublist for label in sublist]
                            
                            if item_comp_sents_flattened:
                                item_comp_sent_counts = Counter(item_comp_sents_flattened)
                                df_item_comp_sent = pd.DataFrame(item_comp_sent_counts.items(), columns=['sentiment', 'count']).sort_values(by='count', ascending=False)
                                
                                # 💡 [핵심 변경] 도넛 차트를 위한 데이터 전처리 (상위 5개 + 기타)
                                top_n = 5
                                if len(df_item_comp_sent) > top_n:
                                    top_df = df_item_comp_sent.head(top_n)
                                    others_count = df_item_comp_sent.iloc[top_n:]['count'].sum()
                                    others_df = pd.DataFrame([{'sentiment': '기타', 'count': others_count}])
                                    df_for_donut = pd.concat([top_df, others_df], ignore_index=True)
                                else:
                                    df_for_donut = df_item_comp_sent

                                # 💡 [핵심 변경] 올바른 인자로 도넛 차트 함수 호출
                                ui_helpers.create_donut_chart(
                                    df_for_donut,
                                    names_col='sentiment',
                                    values_col='count',
                                    title="상위 감정 분포",
                                    key_suffix=f"_comp_donut_vid_{i}" 
                                )
                            else: 
                                st.write("감정 데이터 없음")

                            # 2. 주요 키워드 비교
                            st.markdown("**주요 키워드**")
                            item_comp_text_combined = ""
                            if 'text' in item_df_comp.columns and not item_df_comp['text'].isnull().all():
                                text_series_item_comp = item_df_comp["text"].astype(str).str.strip().dropna()
                                filtered_text_series_item_comp = text_series_item_comp[
                                    (text_series_item_comp != 'nan') & (text_series_item_comp != '')
                                ]
                                item_comp_text_combined = " ".join(filtered_text_series_item_comp)

                            if item_comp_text_combined.strip():
                                item_comp_kws = text_analysis_module.extract_keywords(item_comp_text_combined, num_keywords=5)
                                if item_comp_kws:
                                    keyword_display = "\n".join([f"- {kw} ({count_val})" for kw, count_val in item_comp_kws])
                                    st.markdown(keyword_display)
                                else: 
                                    st.write("추출된 키워드 없음")
                            else: 
                                st.write("키워드 분석을 위한 유효한 텍스트 데이터 없음")
                            st.markdown("---") # 각 아이템 비교 컬럼 구분

            elif comparison_target_type == "재난 유형 간 비교":
                # 식별된 전체 재난 유형 목록 (disaster_label_counts_global는 이미 계산되어 있다고 가정)
                available_disasters_for_comparison_options = sorted(list(disaster_label_counts_global.keys()))
                num_analyzed_disasters = len(available_disasters_for_comparison_options)

                if num_analyzed_disasters < 2:
                    st.info(f"재난 유형 간 비교를 위해서는 최소 2개의 재난 유형이 댓글에서 식별되어야 합니다. 현재 식별된 고유 재난 유형은 {num_analyzed_disasters}개입니다.")
                else:
                    # min_selections 인자 없이 multiselect 사용
                    temp_selected_disasters = st.multiselect(
                        f"식별된 재난 유형 중 비교할 유형을 선택하세요 (현재 {num_analyzed_disasters}개 식별됨, 2개 이상 선택):",
                        options=available_disasters_for_comparison_options,
                        default=[],
                        key="main_compare_disaster_multiselect_tab7_v6" # 키 업데이트
                    )

                    if not temp_selected_disasters:
                        st.info("위 목록에서 비교할 재난 유형을 2개 이상 선택해주세요.")
                    elif len(temp_selected_disasters) == 1:
                        st.warning(f"1개의 재난 유형만 선택되었습니다 ('{temp_selected_disasters[0]}'). 비교를 위해서는 2개 이상의 재난 유형이 필요합니다.")
                    else: # 2개 이상 선택됨
                        selected_items_for_final_comparison = temp_selected_disasters
                        display_comparison_ui = True # 비교 UI 표시 조건 충족
                
                # --- 재난 유형 간 비교 UI 및 데이터 처리 로직 ---
                if display_comparison_ui and selected_items_for_final_comparison:
                    st.markdown(f"#### 선택된 재난 유형 비교: **{', '.join(selected_items_for_final_comparison)}**")
                    cols_for_comparison = st.columns(len(selected_items_for_final_comparison))

                    for i, disaster_type_for_comp in enumerate(selected_items_for_final_comparison):
                        with cols_for_comparison[i]:
                            st.markdown(f"##### {disaster_type_for_comp}")
                            # 해당 재난 유형을 포함하는 댓글 필터링
                            item_df_comp = df_analysis_results[
                                df_analysis_results["disaster_labels"].apply(lambda x: isinstance(x, list) and disaster_type_for_comp in x)
                            ]
                            if item_df_comp.empty:
                                st.write("해당 재난 유형에 대한 분석 데이터가 없습니다.")
                                st.markdown("---")
                                continue

                            # 1. 감정 분포 비교
                            st.markdown("**감정 분포**")
                            item_comp_sents = item_df_comp["sentiment_labels"].dropna().apply(
                                lambda x: [s for s in x if s != '없음'] if isinstance(x, list) and x else []
                            ).tolist()
                            item_comp_sents_flattened = [label for sublist in item_comp_sents if sublist for label in sublist]

                            if item_comp_sents_flattened:
                                item_comp_sent_counts = Counter(item_comp_sents_flattened)
                                df_item_comp_sent = pd.DataFrame(item_comp_sent_counts.items(), columns=['sentiment', 'count']).sort_values(by='count', ascending=False)
                                ui_helpers.create_bar_chart(
                                    df_item_comp_sent, x_col='sentiment', y_col='count',
                                    title="상위 5개 감정", color_col='sentiment', top_n=5,
                                    key_suffix=f"_comp_sent_dis_tab7_v6_{disaster_type_for_comp.replace(' ', '_')}_{i}" # 키 업데이트
                                )
                            else: 
                                st.write("감정 데이터 없음")

                            # 2. 주요 키워드 비교
                            st.markdown("**주요 키워드**")
                            item_comp_text_combined = ""
                            if 'text' in item_df_comp.columns and not item_df_comp['text'].isnull().all():
                                text_series_item_comp = item_df_comp["text"].astype(str).str.strip().dropna()
                                filtered_text_series_item_comp = text_series_item_comp[
                                    (text_series_item_comp != 'nan') & (text_series_item_comp != '')
                                ]
                                item_comp_text_combined = " ".join(filtered_text_series_item_comp)
                            
                            if item_comp_text_combined.strip():
                                item_comp_kws = text_analysis_module.extract_keywords(item_comp_text_combined, num_keywords=5)
                                if item_comp_kws:
                                    keyword_display = "\n".join([f"- {kw} ({count_val})" for kw, count_val in item_comp_kws])
                                    st.markdown(keyword_display)
                                else: 
                                    st.write("추출된 키워드 없음")
                            else: 
                                st.write("키워드 분석을 위한 유효한 텍스트 데이터 없음")
                            st.markdown("---") # 각 아이템 비교 컬럼 구분

    elif st.session_state.get('main_analyze_button_clicked') and st.session_state.all_comments_df.empty :
        st.warning("댓글 수집/분석 결과가 없습니다. 상단 설정을 확인하고 '선택된 영상 댓글 분석 시작' 버튼을 다시 눌러주세요.")
    elif not st.session_state.get('main_search_button_clicked') and not st.session_state.get('main_analyze_button_clicked'):
        st.info("페이지 상단에서 검색어를 입력하고 영상을 검색한 후, 분석할 영상을 선택하고 댓글 분석을 시작해주세요.")

    st.markdown("---")
    st.caption("YouTube 재난 영상 댓글 분석기 | KOTE 감성 분석 모델 활용")
    st.caption("API 사용량에는 제한이 있을 수 있습니다. [Google Cloud Console](https://console.cloud.google.com/apis/dashboard)에서 확인하세요.")