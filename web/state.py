# web/state.py
"""
Streamlit 세션 상태 관리 (최적화된 버전)
"""

import streamlit as st
import os
from utils.logger import get_logger
from utils.session_manager import get_current_session

logger = get_logger(__name__)


def init_session_state():
    """세션 상태 초기화"""
    # 최적화된 세션 관리 사용
    if 'session_initialized' not in st.session_state:
        try:
            # 사용자 세션 생성/가져오기
            current_session = get_current_session()
            st.session_state.user_session = current_session
            
            logger.info(f"세션 초기화 완료: {current_session.session_id[:8]}...")
            
        except Exception as e:
            logger.error(f"세션 초기화 실패: {e}")
            st.error(f"세션 초기화 중 오류가 발생했습니다: {e}")
    
    # VideoService 초기화는 나중에 지연 로딩
    if 'video_service' not in st.session_state:
        try:
            # 여기서 import하여 순환 참조 방지
            from core.workflow.coordinator import VideoProcessor
            
            # 환경변수에서 AI Provider 읽기
            ai_provider = os.getenv("AI_PROVIDER", "openai")
            
            # VideoProcessor 초기화
            st.session_state.video_service = VideoProcessor(ai_provider=ai_provider)
            st.session_state.ai_provider = ai_provider
            
            st.session_state.session_initialized = True
            logger.info(f"VideoService 초기화 완료: {ai_provider}")
            
        except Exception as e:
            logger.error(f"VideoService 초기화 실패: {e}")
            # 대체 서비스 제공 (기본 기능은 유지)
            st.session_state.video_service = None
            st.session_state.ai_provider = "openai"
    
    # 처리 이력
    if 'processing_history' not in st.session_state:
        st.session_state.processing_history = []
    
    # 분석 상태
    if 'analysis_state' not in st.session_state:
        st.session_state.analysis_state = 'idle'  # idle, processing, completed
    
    # 정밀도 레벨
    if 'precision_level' not in st.session_state:
        st.session_state.precision_level = 5
    
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


def get_analysis_state():
    """분석 상태 반환"""
    return st.session_state.get('analysis_state', 'idle')


def set_analysis_state(state: str):
    """분석 상태 설정"""
    st.session_state.analysis_state = state


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