# src/ui/tabs/database_download.py
"""
Database 탭의 다운로드 관련 기능
"""

import streamlit as st
import streamlit.components.v1 as components
import urllib.parse
import re
from typing import Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)


def handle_video_download(video_id: str, video_data: Dict[str, Any]):
    """비디오 다운로드 처리"""
    base_url = "https://sof.greatminds.kr"
    
    # 파일명 정리 함수
    def sanitize_filename(title: str, max_length: int = 100) -> str:
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
        safe_title = re.sub(r'_+', '_', safe_title)
        safe_title = safe_title.strip('_ ')
        return safe_title[:max_length]
    
    # 비디오 제목 가져오기
    video_title = video_data.get('title', 'video')
    sanitized_title = sanitize_filename(video_title)
    
    # 다운로드 URL 생성
    video_filename = f"{video_id}_{sanitized_title}.mp4"
    encoded_filename = urllib.parse.quote(video_filename)
    video_url = f"{base_url}/{video_id}/{encoded_filename}"
    
    # 세션 상태를 사용하여 다운로드 추적
    if 'download_count' not in st.session_state:
        st.session_state.download_count = 0
    st.session_state.download_count += 1
    
    # JavaScript를 사용하여 새 탭에서 다운로드
    components.html(
        f"""
        <script>
            window.open('{video_url}', '_blank');
        </script>
        <!-- 다운로드 #{st.session_state.download_count} -->
        """,
        height=0
    )
    
    st.toast("✅ 다운로드 페이지가 새 탭에서 열렸습니다!", icon="💾")
    logger.info(f"비디오 다운로드 시작: {video_id} - {video_url}")