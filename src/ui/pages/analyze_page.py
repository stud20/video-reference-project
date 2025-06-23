# src/ui/pages/analyze_page.py
"""
Analyze 페이지 - 영상 분석 인터페이스
"""

import streamlit as st
import time
from datetime import datetime


def render_analyze_page():
    """Analyze 페이지 렌더링"""
    
    # 페이지 상태 관리
    if 'analyzing' not in st.session_state:
        st.session_state.analyzing = False
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False
    if 'show_input' not in st.session_state:
        st.session_state.show_input = True
    
    # 페이드 애니메이션을 위한 컨테이너
    animation_container = st.empty()
    
    # 상태에 따른 렌더링
    if st.session_state.show_input and not st.session_state.analyzing and not st.session_state.analysis_complete:
        # 입력 UI 표시
        with animation_container.container():
            render_input_ui()
    
    elif st.session_state.analyzing:
        # 진행 상황 표시
        with animation_container.container():
            render_progress_ui()
    
    elif st.session_state.analysis_complete:
        # 결과 표시
        with animation_container.container():
            render_results_ui()


def render_input_ui():
    """입력 UI 렌더링"""
    # 빈 공간으로 수직 중앙 정렬
    for _ in range(10):
        st.write("")
    
    # 중앙 정렬을 위한 컬럼 사용
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # 페이드인 애니메이션
        st.markdown("""
        <style>
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }
            .fade-in-form {
                animation: fadeIn 0.5s ease-out;
            }
        </style>
        <div class="fade-in-form">
        """, unsafe_allow_html=True)
        
        # Form으로 Enter 키와 버튼 클릭 모두 처리
        with st.form(key="analyze_form", clear_on_submit=False):
            # 입력 필드와 버튼을 한 줄에 배치
            input_col, btn_col = st.columns([4, 1], gap="small")
            
            with input_col:
                video_url = st.text_input(
                    "URL",
                    placeholder="Enter YouTube or Vimeo URL...",
                    key="video_url_input",
                    label_visibility="collapsed"
                )
            
            with btn_col:
                submitted = st.form_submit_button("Analyze", type="primary", use_container_width=True)
            
            if submitted and video_url:
                st.session_state.video_url = video_url
                st.session_state.show_input = False
                st.session_state.analyzing = True
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)


def render_progress_ui():
    """진행 상황 UI 렌더링"""
    # 빈 공간으로 수직 중앙 정렬
    for _ in range(12):
        st.write("")
    
    # 중앙 정렬을 위한 컬럼
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # 진행 상황 컨테이너
        progress_container = st.empty()
        
        # 실제 분석 함수 연결
        try:
            from handlers.video_handler import handle_video_analysis
            from utils.constants import PRECISION_DESCRIPTIONS
            
            # 설정에서 정밀도 레벨 가져오기
            precision_level = st.session_state.get('settings', {}).get('precision_level', 5)
            
            # 진행 상황 콜백
            def progress_callback(step: str, progress: int, message: str):
                with progress_container.container():
                    st.markdown(f"""
                    <div style="text-align: center;">
                        <p class="progress-text fade-in">{message}</p>
                        <div style="width: 100%; height: 4px; background-color: #27272A; border-radius: 2px; margin-top: 1rem;">
                            <div style="width: {progress}%; height: 100%; background: linear-gradient(90deg, #8B5CF6 0%, #A78BFA 100%); border-radius: 2px; transition: width 0.3s ease;"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # 비디오 분석 실행
            handle_video_analysis(st.session_state.video_url, precision_level, progress_callback)
            
            # 분석 완료
            st.session_state.analyzing = False
            st.session_state.analysis_complete = True
            st.session_state.last_analysis_time = datetime.now().strftime("%H:%M")
            st.rerun()
            
        except ImportError:
            # 임시 시뮬레이션 (handler 연결 전)
            progress_messages = [
                ("parsing", 10, "🔍 Analyzing video URL..."),
                ("download", 30, "📥 Downloading video..."),
                ("extract", 50, "🎬 Extracting key scenes..."),
                ("analyze", 80, "🤖 AI analysis in progress..."),
                ("complete", 100, "💾 Saving results...")
            ]
            
            for step, progress, message in progress_messages:
                with progress_container.container():
                    st.markdown(f"""
                    <div style="text-align: center;">
                        <p class="progress-text fade-in">{message}</p>
                        <div style="width: 100%; height: 4px; background-color: #27272A; border-radius: 2px; margin-top: 1rem;">
                            <div style="width: {progress}%; height: 100%; background: linear-gradient(90deg, #8B5CF6 0%, #A78BFA 100%); border-radius: 2px; transition: width 0.3s ease;"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                time.sleep(1)
            
            # 분석 완료
            st.session_state.analyzing = False
            st.session_state.analysis_complete = True
            st.session_state.last_analysis_time = datetime.now().strftime("%H:%M")
            st.rerun()


def render_results_ui():
    """결과 UI 렌더링"""
    # 상단 여백
    st.write("")
    
    # 새 분석 버튼
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("← New Analysis", key="new_analysis"):
            # 상태 초기화
            st.session_state.analysis_complete = False
            st.session_state.show_input = True
            st.session_state.video_url = None
            st.session_state.current_video = None
            st.rerun()
    
    # 결과 표시
    video = st.session_state.get('current_video')
    
    if video and hasattr(video, 'analysis_result') and video.analysis_result:
        # 분석 결과가 있는 경우
        render_analysis_results(video)
    else:
        # 임시 결과 (시뮬레이션)
        render_temp_results()


def render_analysis_results(video):
    """실제 분석 결과 렌더링"""
    st.markdown("### 📊 Analysis Results")
    
    # 메인 결과 카드
    st.markdown(f"""
    <div class="custom-card fade-in" style="margin-top: 2rem;">
        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 1.5rem;">
            <div>
                <h2 style="color: #FAFAFA; margin: 0;">{video.metadata.title if video.metadata else 'Untitled'}</h2>
                <p style="color: #71717A; margin-top: 0.5rem;">{video.metadata.uploader if video.metadata else 'Unknown'}</p>
            </div>
            <div style="text-align: right;">
                <span class="tag" style="background: linear-gradient(135deg, #8B5CF6 0%, #A78BFA 100%); color: white; padding: 0.5rem 1rem; border-radius: 20px; font-weight: 600;">
                    {video.analysis_result.get('genre', 'Unknown')}
                </span>
            </div>
        </div>
        
        <div style="border-top: 1px solid #27272A; padding-top: 1.5rem;">
            <h3 style="color: #A78BFA; font-size: 1.125rem; margin-bottom: 1rem;">🎯 Analysis Summary</h3>
            <p style="color: #E4E4E7; line-height: 1.6;">
                {video.analysis_result.get('reasoning', 'No analysis available')}
            </p>
        </div>
        
        <div style="margin-top: 2rem;">
            <h3 style="color: #A78BFA; font-size: 1.125rem; margin-bottom: 1rem;">✨ Key Features</h3>
            <p style="color: #E4E4E7; line-height: 1.6;">
                {video.analysis_result.get('features', 'No features detected')}
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 추가 정보 그리드
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div class="custom-card fade-in" style="margin-top: 1rem;">
            <h4 style="color: #A78BFA; font-size: 1rem; margin-bottom: 0.5rem;">🎭 Mood & Tone</h4>
            <p style="color: #E4E4E7;">{video.analysis_result.get('mood_tone', 'Not analyzed')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="custom-card fade-in" style="margin-top: 1rem;">
            <h4 style="color: #A78BFA; font-size: 1rem; margin-bottom: 0.5rem;">🎯 Target Audience</h4>
            <p style="color: #E4E4E7;">{video.analysis_result.get('target_audience', 'Not specified')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 태그 표시
    if video.analysis_result.get('tags'):
        st.markdown("""
        <div class="custom-card fade-in" style="margin-top: 1rem;">
            <h4 style="color: #A78BFA; font-size: 1rem; margin-bottom: 1rem;">🏷️ Tags</h4>
            <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
        """, unsafe_allow_html=True)
        
        for tag in video.analysis_result['tags'][:10]:
            st.markdown(f"""
                <span style="background-color: #27272A; color: #A78BFA; padding: 0.25rem 0.75rem; border-radius: 15px; font-size: 0.875rem;">
                    #{tag}
                </span>
            """, unsafe_allow_html=True)
        
        st.markdown("</div></div>", unsafe_allow_html=True)


def render_temp_results():
    """임시 결과 표시 (시뮬레이션)"""
    st.markdown("### 📊 Analysis Results")
    
    st.markdown("""
    <div class="custom-card fade-in" style="margin-top: 2rem;">
        <h3 style="color: #A78BFA;">🎬 Video Analysis Complete</h3>
        <p style="color: #71717A; margin-top: 1rem;">
            Analysis results will appear here when connected to the actual processing system.
        </p>
    </div>
    """, unsafe_allow_html=True)