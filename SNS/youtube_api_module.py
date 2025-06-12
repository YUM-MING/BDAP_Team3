# youtube_api_module.py
import streamlit as st
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime
from SNS.config import YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION # config.py에서 상수 가져오기

# Streamlit의 secrets에서 API 키를 가져옵니다.
# 이 모듈이 로드될 때 한 번만 실행됩니다.

try:
    YOUTUBE_API_KEY_VALUE = "AIzaSyBPSD9lGwsxGOihqH77MOlBHRHbGv_Y1dw"
except KeyError:
    YOUTUBE_API_KEY_VALUE = None
    # app.py에서 API 키 존재 여부를 확인하므로 여기서는 오류를 발생시키지 않을 수 있음
    # 또는 여기서 st.error를 호출하고 None을 반환하여 app.py에서 처리

@st.cache_data(ttl=3600, show_spinner="YouTube에서 영상 검색 중...") # 1시간 캐시, 스피너
def search_youtube_videos(query, order="relevance", max_results=25, region_code="KR", lang="ko"):
    """
    YouTube API를 사용하여 특정 쿼리로 비디오를 검색합니다.
    """
    if not YOUTUBE_API_KEY_VALUE:
        st.error("YouTube API 키가 설정되지 않았습니다. API 호출을 할 수 없습니다.")
        return []

    videos = []
    try:
        youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=YOUTUBE_API_KEY_VALUE)
        search_response = youtube.search().list(
            q=query,
            part="id,snippet",
            maxResults=max_results,
            type="video",
            order=order,
            regionCode=region_code,
            relevanceLanguage=lang
        ).execute()

        for item in search_response.get("items", []):
            video_id = item.get("id", {}).get("videoId")
            snippet = item.get("snippet", {})
            if video_id and snippet:
                videos.append({
                    "id": video_id,
                    "title": snippet.get("title", "제목 없음"),
                    "thumbnail": snippet.get("thumbnails", {}).get("default", {}).get("url", ""),
                    "published_at": snippet.get("publishedAt", "")
                })
    except HttpError as e:
        st.error(f"YouTube API 오류 (영상 검색): {e.resp.status} - {e._get_reason()}")
        # 추가적인 오류 정보 로깅 또는 사용자에게 안내
        # print(f"Error content: {e.content}")
    except Exception as e:
        st.error(f"영상 검색 중 예상치 못한 오류 발생: {e}")
    return videos

@st.cache_data(ttl=3600, show_spinner=False) # 댓글 수집은 개별 영상마다 호출되므로 스피너는 app.py에서 관리
def get_video_comments(video_id, max_results_per_call=100, total_max_comments=100):
    """
    특정 비디오 ID에 대한 댓글을 수집합니다.
    """
    if not YOUTUBE_API_KEY_VALUE:
        # 이 함수는 반복 호출될 수 있으므로, API 키 오류는 search_youtube_videos에서 주로 처리
        # st.warning("YouTube API 키가 없어 댓글을 수집할 수 없습니다.")
        return []

    comments_data = []
    next_page_token = None
    try:
        youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=YOUTUBE_API_KEY_VALUE)
        while len(comments_data) < total_max_comments:
            current_max_results = min(max_results_per_call, total_max_comments - len(comments_data))
            if current_max_results <= 0:
                break

            response = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=current_max_results,
                textFormat="plainText", # HTML 태그 제거
                order="relevance", # 또는 "time"
                pageToken=next_page_token
            ).execute()

            for item in response.get("items", []):
                top_level_comment = item.get("snippet", {}).get("topLevelComment", {})
                comment_snippet = top_level_comment.get("snippet", {})
                if comment_snippet:
                    try:
                        published_at_dt = datetime.strptime(comment_snippet.get("publishedAt", ""), "%Y-%m-%dT%H:%M:%SZ")
                    except ValueError:
                        published_at_dt = None # 날짜 파싱 실패 시

                    comments_data.append({
                        "video_id": video_id,
                        "comment_id": top_level_comment.get("id", ""),
                        "text": comment_snippet.get("textDisplay", ""),
                        "author": comment_snippet.get("authorDisplayName", "익명"),
                        "published_at": published_at_dt,
                        "like_count": comment_snippet.get("likeCount", 0)
                    })

            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break
        # 요청한 최대 댓글 수만큼만 반환
        return comments_data[:total_max_comments]

    except HttpError as e:
        # 댓글 수집 오류는 영상별로 발생할 수 있으므로 st.warning 사용
        st.warning(f"댓글 수집 중 API 오류 (영상 ID: {video_id}, 오류: {e.resp.status} - {e._get_reason()}). 수집된 댓글만 반환합니다.")
    except Exception as e:
        st.warning(f"댓글 수집 중 예상치 못한 오류 (영상 ID: {video_id}): {e}. 수집된 댓글만 반환합니다.")
    return comments_data[:total_max_comments] # 오류 발생 시에도 현재까지 수집된 데이터 반환