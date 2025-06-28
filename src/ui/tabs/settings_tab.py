# src/ui/tabs/settings_tab.py
"""
Settings 탭 - 시스템 설정 메인 UI
"""

import streamlit as st
from utils.logger import get_logger

# 각 기능별 모듈 임포트
from ui.tabs.settings_precision import render_precision_settings
from ui.tabs.settings_cache import render_cache_management
from ui.tabs.settings_prompt import render_prompt_tuning
from ui.tabs.settings_notion import render_notion_settings, init_notion_stats

logger = get_logger(__name__)


def render_settings_tab():
    """Settings 탭 메인 렌더링"""
    # Notion 통계 초기화
    init_notion_stats()
    
    st.header("⚙️ 시스템 설정")
    
    # 탭 생성
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 분석 정밀도",
        "🗑️ 캐시 관리", 
        "🤖 AI 프롬프트",
        "📝 Notion 연동"
    ])
    
    # 분석 정밀도 설정
    with tab1:
        render_precision_settings()
    
    # 캐시 관리
    with tab2:
        render_cache_management()
    
    # AI 프롬프트 튜닝
    with tab3:
        render_prompt_tuning()
    
    # Notion 설정
    with tab4:
        render_notion_settings()