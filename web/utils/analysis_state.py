# web/utils/analysis_state.py
"""분석 상태 관리 유틸리티"""

import streamlit as st
from web.state import set_analysis_state


def reset_analysis_state():
    """분석 상태 초기화"""
    set_analysis_state('idle')
    st.session_state.analysis_result = None
    st.session_state.current_video_url = None
    st.session_state.show_moodboard = False
    st.session_state.show_precision_modal = False
    if 'moodboard_selected' in st.session_state:
        del st.session_state.moodboard_selected
