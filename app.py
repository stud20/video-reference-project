# app.py
"""
AI 기반 광고 영상 콘텐츠 추론 시스템 - 개선된 UI
"""

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import sys
import os

# src 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

# utils 디렉토리도 Python 경로에 추가 (프로젝트 루트의 utils)
sys.path.insert(0, current_dir)

# 컴포넌트 임포트
from ui.styles import get_enhanced_styles
from ui.tabs.analyze_tab import render_analyze_tab
from ui.tabs.database_tab import render_database_tab
from ui.tabs.settings_tab import render_settings_tab
from utils.session_state import init_session_state
from utils.logger import get_logger

logger = get_logger(__name__)


def setup_page():
    """페이지 설정 및 스타일 적용"""
    st.set_page_config(
        page_title="AI 영상 레퍼런스 분석기",
        page_icon="🎥",
        layout="wide",
        initial_sidebar_state="collapsed"  # 사이드바 숨김
    )
    
    # 향상된 CSS 스타일 적용
    st.markdown(get_enhanced_styles(), unsafe_allow_html=True)
    
    # 세션 상태 초기화
    init_session_state()


def render_header():
    """헤더 렌더링"""
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.markdown("""
        <div class="main-header">
            <h1>🎬 AI Video Reference Analyzer</h1>
            <p>영상 콘텐츠 자동 분석 및 분류 시스템</p>
        </div>
        """, unsafe_allow_html=True)


def main():
    """메인 앱 함수"""
    # 페이지 설정
    setup_page()
    
    # 헤더
    render_header()
    
    # 탭 생성
    tab1, tab2, tab3 = st.tabs(["🎯 Analyze", "📊 Database", "⚙️ Settings"])
    
    with tab1:
        render_analyze_tab()
    
    with tab2:
        render_database_tab()
    
    with tab3:
        render_settings_tab()


if __name__ == "__main__":
    main()