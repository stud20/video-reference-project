# web/pages/settings.py
"""
Settings 탭 - 시스템 설정 메인 UI
"""

import streamlit as st
from utils.logger import get_logger

# 각 기능별 모듈 임포트
from web.components.settings.cache import render_cache_management
from web.components.settings.prompt import render_prompt_settings
from web.components.settings.notion import render_notion_settings, init_notion_stats

logger = get_logger(__name__)


def render_settings_tab():
    """설정 탭 렌더링"""
    # Notion 통계 초기화
    init_notion_stats()
    
    st.header("⚙️ 시스템 설정")
    
    # 탭 생성
    tab1, tab2, tab3 = st.tabs([
        "🗑️ 캐시 관리",
        "🤖 AI 프롬프트",
        "📝 Notion 연동"
    ])
    
    # 캐시 관리
    with tab1:
        render_cache_management()
    
    # AI 프롬프트 설정
    with tab2:
        render_prompt_settings()
    
    # Notion 설정
    with tab3:
        render_notion_settings()
