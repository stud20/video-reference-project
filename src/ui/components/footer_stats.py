# src/ui/components/footer_stats.py
"""
하단 통계 호버 컴포넌트
"""

import streamlit as st
from storage.db_manager import VideoAnalysisDB
from datetime import datetime


def render_footer_stats():
    """하단 통계 렌더링"""
    # 통계 데이터 가져오기
    stats = get_stats_data()
    
    # HTML/CSS로 호버 영역 구현
    footer_html = f"""
    <div class="footer-stats">
        <div class="footer-content">
            <span class="footer-arrow">▲</span>
            <div class="stats-summary">
                <span>Total Videos: {stats['total_videos']}</span>
                <span> | </span>
                <span>Today: {stats['today_count']}</span>
                <span> | </span>
                <span>Last Analysis: {stats['last_analysis']}</span>
            </div>
        </div>
    </div>
    
    <style>
        .footer-stats {{
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            height: 2rem;
            background-color: #0A0A0B;
            border-top: 1px solid #27272A;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.3s ease;
            z-index: 1000;
        }}
        
        .footer-stats:hover {{
            height: 4rem;
            background-color: #111111;
        }}
        
        .footer-content {{
            text-align: center;
        }}
        
        .footer-arrow {{
            color: #71717A;
            font-size: 0.75rem;
            display: block;
            transition: transform 0.3s ease;
        }}
        
        .footer-stats:hover .footer-arrow {{
            transform: rotate(180deg);
            margin-bottom: 0.5rem;
        }}
        
        .stats-summary {{
            display: none;
            color: #A78BFA;
            font-size: 0.875rem;
        }}
        
        .footer-stats:hover .stats-summary {{
            display: block;
        }}
    </style>
    """
    
    st.markdown(footer_html, unsafe_allow_html=True)


def get_stats_data():
    """통계 데이터 조회"""
    try:
        db = VideoAnalysisDB()
        stats = db.get_statistics()
        
        # 오늘 분석한 수 계산 (실제 구현 필요)
        today_count = len(st.session_state.get('processing_history', []))
        
        # 마지막 분석 시간
        last_analysis = "Never"
        if st.session_state.get('last_analysis_time'):
            last_analysis = st.session_state['last_analysis_time']
        
        db.close()
        
        return {
            'total_videos': stats['total_videos'],
            'today_count': today_count,
            'last_analysis': last_analysis
        }
    except:
        return {
            'total_videos': 0,
            'today_count': 0,
            'last_analysis': 'Never'
        }