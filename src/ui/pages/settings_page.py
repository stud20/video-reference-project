# src/ui/pages/settings_page.py
"""
Settings 페이지 - 설정 관리
"""

import streamlit as st


def render_settings_page():
    """Settings 페이지 렌더링"""
    st.markdown("## ⚙️ Settings")
    
    # 임시 메시지
    st.markdown("""
    <div class="custom-card">
        <p>Settings will be implemented here...</p>
    </div>
    """, unsafe_allow_html=True)