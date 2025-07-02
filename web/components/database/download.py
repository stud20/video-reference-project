# web/components/database/download.py
"""
Database 탭의 다운로드 기능
"""

import streamlit as st
import requests
import urllib.parse
from utils.logger import get_logger

logger = get_logger(__name__)


def handle_download(video_id: str, video_data: dict):
    """
    비디오 다운로드 처리
    
    Args:
        video_id: 비디오 ID
        video_data: 비디오 정보 딕셔너리
    """
    # 이 함수는 video_card.py에서 직접 구현되어 있으므로
    # 여기서는 공통 유틸리티만 제공
    pass


def sanitize_filename(title: str, max_length: int = 100) -> str:
    """파일명으로 사용 가능한 문자열로 변환"""
    import re
    safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
    safe_title = re.sub(r'_+', '_', safe_title)
    safe_title = safe_title.strip('_ ')
    return safe_title[:max_length]


def prepare_download_url(video_id: str, title: str) -> tuple:
    """
    다운로드 URL 준비
    
    Returns:
        (video_url, download_filename)
    """
    base_url = "https://ref.greatminds.kr"
    
    # 파일명 생성
    sanitized_title = sanitize_filename(title)
    video_filename = f"{video_id}_{sanitized_title}.mp4"
    encoded_filename = urllib.parse.quote(video_filename)
    video_url = f"{base_url}/{video_id}/{encoded_filename}"
    download_filename = f"{sanitized_title}_{video_id}.mp4"
    
    return video_url, download_filename
