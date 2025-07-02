# integrations/notion/__init__.py
"""
Notion 통합 모듈
"""

from .base import NotionBaseService
from .database import NotionDatabaseService
from .page import NotionPageService
from .client import NotionService
import streamlit as st

# 싱글턴 인스턴스
_notion_service_instance = None

def get_notion_service():
    """
    NotionService 싱글턴 인스턴스 반환
    
    Streamlit의 session_state를 활용하여 세션 내에서 유지
    """
    # Streamlit 환경인지 확인
    try:
        # Streamlit session_state에 저장
        if 'notion_service' not in st.session_state:
            st.session_state.notion_service = NotionService()
        return st.session_state.notion_service
    except:
        # Streamlit이 아닌 환경에서는 일반 싱글턴 사용
        global _notion_service_instance
        if _notion_service_instance is None:
            _notion_service_instance = NotionService()
        return _notion_service_instance

__all__ = [
    'NotionBaseService',
    'NotionDatabaseService', 
    'NotionPageService',
    'NotionService',
    'get_notion_service'
]
