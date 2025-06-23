# src/utils/session_state.py
"""
Streamlit 세션 상태 관리 - 간소화 버전
"""

import streamlit as st
from utils.logger import get_logger

logger = get_logger(__name__)


def init_session_state():
    """세션 상태 초기화"""
    # VideoService 초기화
    if 'video_service' not in st.session_state:
        from src.services.video_service import VideoService
        from src.storage.storage_manager import StorageType
        
        storage_type = StorageType.LOCAL  # 일단 로컬로 설정
        st.session_state.video_service = VideoService(storage_type=storage_type)
        st.session_state.storage_type = storage_type
    
    # 분석 관련 상태
    if 'analyzing' not in st.session_state:
        st.session_state.analyzing = False
    
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False
    
    if 'current_video' not in st.session_state:
        st.session_state.current_video = None
    
    # 처리 이력
    if 'processing_history' not in st.session_state:
        st.session_state.processing_history = []
    
    # 설정값 (로컬 스토리지에서 로드)
    if 'settings' not in st.session_state:
        st.session_state.settings = load_settings()


def load_settings():
    """설정값 로드 (추후 구현)"""
    return {
        'precision_level': 5,
        'theme': 'dark',
        'language': 'ko'
    }


def save_settings(settings):
    """설정값 저장 (추후 구현)"""
    st.session_state.settings = settings
    # localStorage나 파일로 저장하는 로직 추가


def add_to_processing_history(video_url: str, title: str, precision_level: int):
    """처리 이력에 추가"""
    from datetime import datetime
    
    st.session_state.processing_history.append({
        'time': datetime.now().strftime("%H:%M"),
        'title': title,
        'url': video_url,
        'precision_level': precision_level
    })
    
    # 마지막 분석 시간 업데이트
    st.session_state['last_analysis_time'] = datetime.now().strftime("%H:%M")


def init_database_modal_state():
    """데이터베이스 모달 관련 상태 초기화 (호환성 유지)"""
    if 'show_db_modal' not in st.session_state:
        st.session_state.show_db_modal = False
    if 'selected_videos' not in st.session_state:
        st.session_state.selected_videos = []
    if 'db_page' not in st.session_state:
        st.session_state.db_page = 1