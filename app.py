# app.py
"""
AI 기반 광고 영상 콘텐츠 추론 시스템 - 메인 앱
간소화 버전 (~200줄)
"""

from dotenv import load_dotenv
load_dotenv()  # .env 파일 로드

import streamlit as st
import sys
import os

# src 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

# 컴포넌트 임포트
from ui.styles import get_app_styles
from ui.components.sidebar import render_sidebar
from ui.components.database_modal import render_database_modal
from ui.components.analysis_display import display_search_results
from handlers.video_handler import render_video_input_section, render_system_status
from utils.session_state import init_session_state, init_database_modal_state

# 로거 설정
from utils.logger import get_logger
logger = get_logger(__name__)


def setup_page():
    """페이지 설정 및 스타일 적용"""
    st.set_page_config(
        page_title="AI 영상 레퍼런스 분석기",
        page_icon="🎥",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 다크 테마 강제 적용을 위한 스크립트
    st.markdown("""
        <script>
            // 다크 테마 강제 적용
            if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
                document.documentElement.setAttribute('data-theme', 'dark');
            }
            
            // 테마 변경 감지 및 다크 테마 유지
            window.matchMedia('(prefers-color-scheme: light)').addEventListener('change', e => {
                document.documentElement.setAttribute('data-theme', 'dark');
            });
        </script>
    """, unsafe_allow_html=True)
    
    # CSS 스타일 적용
    st.markdown(get_app_styles(), unsafe_allow_html=True)


def main():
    """메인 앱 함수"""
    # 페이지 설정
    setup_page()
    
    # 세션 상태 초기화
    init_session_state()
    init_database_modal_state()
    
    # 헤더
    st.title("🎥 AI 기반 광고 영상 콘텐츠 추론 시스템")
    st.markdown("---")
    
    # 데이터베이스 모달 렌더링 (최상단)
    render_database_modal()
    
    # 사이드바 렌더링 및 설정값 가져오기
    with st.sidebar:
        sidebar_settings = render_sidebar()
        current_precision = sidebar_settings['precision_level']
        debug_mode = sidebar_settings['debug_mode']
        
        # 디버그 모드 세션 상태에 저장
        st.session_state['debug_mode'] = debug_mode
    
    # 검색 결과 표시 (메인 영역 상단)
    display_search_results()
    
    # 메인 컨텐츠 영역
    col1, col2 = st.columns([2, 1])
    
    # 좌측: 비디오 입력 및 분석
    with col1:
        render_video_input_section(current_precision)
    
    # 우측: 시스템 상태
    with col2:
        render_system_status(current_precision)


if __name__ == "__main__":
    main()