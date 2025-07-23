# web/pages/dashboard.py
"""
실시간 분석 대시보드 - Phase 2 구현
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import Dict, Any
import psutil
import os

from utils.session_manager import get_session_manager
from core.queue.task_queue import get_task_queue
from utils.cache_manager import get_cache_manager
from core.database.concurrent_db import get_database
from utils.logger import get_logger

logger = get_logger(__name__)


def render_dashboard_tab():
    """대시보드 탭 메인 렌더링"""
    st.markdown("# 📊 실시간 분석 대시보드")
    st.markdown("---")
    
    # 자동 새로고침 설정
    refresh_interval = st.sidebar.selectbox(
        "자동 새로고침 (초)", 
        [5, 10, 30, 60], 
        index=1
    )
    
    # 실시간 메트릭 카드들
    render_metrics_cards()
    
    st.markdown("---")
    
    # 차트 섹션
    col1, col2 = st.columns(2)
    
    with col1:
        render_system_resources_chart()
        render_analysis_timeline()
    
    with col2:
        render_queue_status_chart()
        render_performance_metrics()
    
    # 자동 새로고침
    if st.sidebar.button("🔄 수동 새로고침"):
        st.rerun()
    
    # 자동 새로고침 스크립트
    st.markdown(f"""
    <script>
        setTimeout(function(){{
            window.location.reload();
        }}, {refresh_interval * 1000});
    </script>
    """, unsafe_allow_html=True)


def render_metrics_cards():
    """실시간 메트릭 카드 렌더링"""
    # 데이터 수집
    session_manager = get_session_manager()
    task_queue = get_task_queue()
    cache_manager = get_cache_manager()
    db = get_database()
    
    session_stats = session_manager.get_session_stats()
    queue_stats = task_queue.get_queue_status()
    cache_stats = cache_manager.get_stats()
    db_stats = db.get_statistics()
    
    # 메트릭 카드 4개
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card animate-fadeInUp">
            <div class="metric-icon">👥</div>
            <div class="metric-value">{}</div>
            <div class="metric-label">활성 사용자</div>
            <div class="metric-change">+{} 처리중</div>
        </div>
        """.format(
            session_stats['active_sessions'],
            session_stats['processing_sessions']
        ), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card animate-fadeInUp" style="animation-delay: 0.1s">
            <div class="metric-icon">⚙️</div>
            <div class="metric-value">{}</div>
            <div class="metric-label">대기 작업</div>
            <div class="metric-change">{} 실행중</div>
        </div>
        """.format(
            queue_stats['queue_size'],
            queue_stats['running_tasks']
        ), unsafe_allow_html=True)
    
    with col3:
        memory_stats = cache_stats.get('memory_cache', {})
        hit_rate = memory_stats.get('hit_rate', 0) * 100
        st.markdown("""
        <div class="metric-card animate-fadeInUp" style="animation-delay: 0.2s">
            <div class="metric-icon">💾</div>
            <div class="metric-value">{:.1f}%</div>
            <div class="metric-label">캐시 적중률</div>
            <div class="metric-change">Redis: {}</div>
        </div>
        """.format(
            hit_rate,
            "✅" if cache_stats.get('redis_available') else "❌"
        ), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card animate-fadeInUp" style="animation-delay: 0.3s">
            <div class="metric-icon">📊</div>
            <div class="metric-value">{}</div>
            <div class="metric-label">총 분석 완료</div>
            <div class="metric-change">오늘 {} 건</div>
        </div>
        """.format(
            db_stats.get('total_videos', 0),
            get_today_analysis_count()
        ), unsafe_allow_html=True)


def render_system_resources_chart():
    """시스템 리소스 사용률 차트"""
    st.markdown("### 💻 시스템 리소스")
    
    # CPU와 메모리 사용률 가져오기
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    memory_percent = memory.percent
    
    # 게이지 차트 생성
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{'type': 'indicator'}, {'type': 'indicator'}]],
        subplot_titles=('CPU 사용률', '메모리 사용률')
    )
    
    # CPU 게이지
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=cpu_percent,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "CPU %"},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "yellow"},
                    {'range': [80, 100], 'color': "red"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ),
        row=1, col=1
    )
    
    # 메모리 게이지
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=memory_percent,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Memory %"},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkgreen"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 85], 'color': "yellow"},
                    {'range': [85, 100], 'color': "red"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ),
        row=1, col=2
    )
    
    fig.update_layout(
        height=300,
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': 'white'}
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_queue_status_chart():
    """작업 큐 상태 차트"""
    st.markdown("### ⚙️ 작업 큐 상태")
    
    task_queue = get_task_queue()
    queue_stats = task_queue.get_queue_status()
    
    # 도넛 차트 데이터
    labels = ['대기중', '실행중', '완료']
    values = [
        queue_stats['queue_size'],
        queue_stats['running_tasks'],
        queue_stats['stats']['total_completed']
    ]
    colors = ['#ff9999', '#66b3ff', '#99ff99']
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.6,
        marker_colors=colors,
        textinfo='label+percent',
        hovertemplate='<b>%{label}</b><br>개수: %{value}<br>비율: %{percent}<extra></extra>'
    )])
    
    fig.update_layout(
        showlegend=True,
        height=300,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': 'white'},
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_analysis_timeline():
    """분석 타임라인 차트"""
    st.markdown("### 📈 분석 처리량 (최근 24시간)")
    
    # 모의 데이터 생성 (실제로는 DB에서 가져와야 함)
    hours = list(range(24))
    current_hour = datetime.now().hour
    
    # 현실적인 패턴의 모의 데이터
    import random
    analysis_counts = []
    for hour in hours:
        # 업무시간에 더 많은 활동
        if 9 <= hour <= 18:
            count = random.randint(3, 12)
        elif 19 <= hour <= 23 or 7 <= hour <= 8:
            count = random.randint(1, 6)
        else:
            count = random.randint(0, 3)
        analysis_counts.append(count)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=hours,
        y=analysis_counts,
        mode='lines+markers',
        line=dict(color='#4ecdc4', width=3),
        marker=dict(size=8, color='#4ecdc4'),
        fill='tonexty',
        fillcolor='rgba(78, 205, 196, 0.3)',
        name='분석 완료 수',
        hovertemplate='시간: %{x}시<br>완료: %{y}건<extra></extra>'
    ))
    
    fig.update_layout(
        height=300,
        xaxis_title="시간 (24h)",
        yaxis_title="분석 완료 수",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': 'white'},
        xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
        yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_performance_metrics():
    """성능 메트릭 차트"""
    st.markdown("### ⚡ 성능 메트릭")
    
    # 모의 응답시간 데이터
    models = ['GPT-4o', 'Claude Sonnet 4', 'Gemini 2.0']
    avg_times = [45.2, 38.7, 52.1]  # 초 단위
    colors = ['#ff6b6b', '#4ecdc4', '#45b7d1']
    
    fig = go.Figure(data=[
        go.Bar(
            x=models,
            y=avg_times,
            marker_color=colors,
            text=[f'{time:.1f}s' for time in avg_times],
            textposition='auto',
            hovertemplate='<b>%{x}</b><br>평균 응답시간: %{y:.1f}초<extra></extra>'
        )
    ])
    
    fig.update_layout(
        height=300,
        yaxis_title="평균 응답시간 (초)",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': 'white'},
        xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
        yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
    )
    
    st.plotly_chart(fig, use_container_width=True)


def get_today_analysis_count() -> int:
    """오늘 분석 완료 건수 조회"""
    try:
        db = get_database()
        # 실제로는 오늘 날짜 필터링된 쿼리 필요
        return 23  # 모의 데이터
    except:
        return 0


# 메트릭 카드 CSS 추가
def get_dashboard_styles():
    """대시보드 전용 스타일"""
    return """
    <style>
    .metric-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05));
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
        animation: fadeInUp 0.6s ease-out;
        animation-fill-mode: both;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(0,0,0,0.3);
        border-color: rgba(78, 205, 196, 0.5);
    }
    
    .metric-icon {
        font-size: 2.5rem;
        margin-bottom: 12px;
    }
    
    .metric-value {
        font-size: 2.8rem;
        font-weight: bold;
        color: #4ecdc4;
        margin-bottom: 8px;
        animation: countUp 0.8s ease-out;
    }
    
    .metric-label {
        font-size: 1rem;
        color: rgba(255,255,255,0.8);
        margin-bottom: 4px;
        font-weight: 500;
    }
    
    .metric-change {
        font-size: 0.85rem;
        color: rgba(255,255,255,0.6);
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes countUp {
        from {
            opacity: 0;
            transform: scale(0.5);
        }
        to {
            opacity: 1;
            transform: scale(1);
        }
    }
    </style>
    """