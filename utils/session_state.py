# src/utils/session_state.py
"""
Streamlit 세션 상태 관리
"""

import streamlit as st
import os
from utils.logger import get_logger

logger = get_logger(__name__)


def init_session_state():
    """세션 상태 초기화"""
    # VideoService 초기화는 나중에 지연 로딩
    if 'video_service' not in st.session_state:
        # 여기서 import하여 순환 참조 방지
        from src.services.video_service import VideoService
        from src.storage.storage_manager import StorageType
        
        # 환경변수에서 스토리지 타입 읽기
        storage_type_str = os.getenv("STORAGE_TYPE", "sftp")
        try:
            storage_type = StorageType[storage_type_str.upper()]
        except KeyError:
            storage_type = StorageType.SFTP
            logger.warning(f"알 수 없는 스토리지 타입: {storage_type_str}, SFTP 사용")
        
        # VideoService 초기화
        st.session_state.video_service = VideoService(storage_type=storage_type)
        st.session_state.storage_type = storage_type
    
    # 처리 이력
    if 'processing_history' not in st.session_state:
        st.session_state.processing_history = []
    
    # 데이터베이스 모달 관련
    init_database_modal_state()


def init_database_modal_state():
    """데이터베이스 모달 관련 상태 초기화"""
    if 'show_db_modal' not in st.session_state:
        st.session_state.show_db_modal = False
    if 'selected_videos' not in st.session_state:
        st.session_state.selected_videos = []
    if 'db_page' not in st.session_state:
        st.session_state.db_page = 1
    if 'db_filter' not in st.session_state:
        st.session_state.db_filter = 'all'
    if 'db_search' not in st.session_state:
        st.session_state.db_search = ''
    if 'edit_video_id' not in st.session_state:
        st.session_state.edit_video_id = None
    if 'confirm_delete' not in st.session_state:
        st.session_state.confirm_delete = None
    if 'show_video_details' not in st.session_state:
        st.session_state.show_video_details = None


def add_to_processing_history(video_url: str, title: str, precision_level: int):
    """처리 이력에 추가"""
    from datetime import datetime
    
    st.session_state.processing_history.append({
        'time': datetime.now().strftime("%H:%M"),
        'title': title,
        'url': video_url,
        'precision_level': precision_level
    })


def clear_delete_confirmation():
    """삭제 확인 상태 초기화"""
    st.session_state.confirm_delete = None


def clear_modal_states():
    """모달 관련 모든 상태 초기화"""
    st.session_state.show_db_modal = False
    st.session_state.confirm_delete = None
    st.session_state.show_video_details = None
    st.session_state.edit_video_id = None