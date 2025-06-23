# app.py
"""
AI 기반 광고 영상 콘텐츠 추론 시스템 - 미니멀 버전
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

# 페이지 임포트
from ui.pages.analyze_page import render_analyze_page
from ui.pages.database_page import render_database_page
from ui.pages.settings_page import render_settings_page
from ui.components.footer_stats import render_footer_stats
from ui.styles.modern_theme import apply_modern_theme
from utils.session_state import init_session_state


def main():
    # 페이지 설정
    st.set_page_config(
        page_title="AI Video Analyzer",
        page_icon="🎬",
        layout="wide",
        initial_sidebar_state="collapsed"  # 사이드바 숨김
    )
    
    # 세션 상태 초기화
    init_session_state()
    
    # 모던 테마 적용
    apply_modern_theme()
    
    # 메인 컨테이너
    with st.container():
        # 상단 탭 네비게이션
        tab1, tab2, tab3 = st.tabs(["Analyze", "Database", "Settings"])
        
        with tab1:
            render_analyze_page()
        
        with tab2:
            render_database_page()
        
        with tab3:
            render_settings_page()
    
    # 하단 통계 (호버)
    render_footer_stats()


if __name__ == "__main__":
    main()