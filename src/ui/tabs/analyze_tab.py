# src/ui/tabs/analyze_tab.py
"""
Analyze 탭 - 영상 분석 UI
"""

import streamlit as st
import time
import os
from typing import Optional
from handlers.enhanced_video_handler import handle_video_analysis_enhanced
from utils.session_state import get_analysis_state, set_analysis_state
from utils.logger import get_logger

logger = get_logger(__name__)


def render_analyze_tab():
    """Analyze 탭 렌더링"""
    # 분석 상태 확인
    analysis_state = get_analysis_state()
    
    if analysis_state == 'idle':
        render_input_section()
    elif analysis_state == 'processing':
        render_processing_section()
    elif analysis_state == 'completed':
        render_results_section()


def render_input_section():
    """URL 입력 섹션"""
    st.markdown("""
    <div class="analyze-input-container">
        <div class="analyze-input-wrapper">
    """, unsafe_allow_html=True)
    
    # 타이틀
    st.markdown("### 🎬 영상 분석 시작하기")
    st.markdown("YouTube 또는 Vimeo 링크를 입력해주세요")
    
    # URL 입력
    col1, col2 = st.columns([4, 1])
    
    with col1:
        video_url = st.text_input(
            "URL",
            placeholder="https://www.youtube.com/watch?v=...",
            label_visibility="collapsed",
            key="analyze_url_input"
        )
    
    with col2:
        analyze_button = st.button(
            "🚀 분석",
            type="primary",
            use_container_width=True,
            key="analyze_start_button"
        )
    
    # Enter 키로도 분석 시작 (JavaScript 추가)
    st.markdown("""
    <script>
        const input = document.querySelector('input[type="text"]');
        if (input) {
            input.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    const button = document.querySelector('button[kind="primary"]');
                    if (button) button.click();
                }
            });
        }
    </script>
    """, unsafe_allow_html=True)
    
    # 예시 링크
    st.markdown("---")
    st.markdown("#### 💡 예시 링크")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📺 YouTube 예시", use_container_width=True):
            st.session_state.analyze_url_input = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            st.rerun()
    
    with col2:
        if st.button("🎬 Vimeo 예시", use_container_width=True):
            st.session_state.analyze_url_input = "https://vimeo.com/347119375"
            st.rerun()
    
    st.markdown("</div></div>", unsafe_allow_html=True)
    
    # 분석 시작 처리
    if analyze_button and video_url:
        set_analysis_state('processing')
        st.session_state.current_video_url = video_url
        st.rerun()
    elif analyze_button:
        st.error("URL을 입력해주세요!")


def render_processing_section():
    """처리 중 섹션"""
    video_url = st.session_state.get('current_video_url')
    
    # 임베드 비디오 표시
    render_video_embed(video_url)
    
    # 콘솔 창
    console_container = st.container()
    with console_container:
        st.markdown('<div class="console-window" id="console">', unsafe_allow_html=True)
        
        # 실시간 콘솔 메시지 (실제로는 handle_video_analysis_enhanced에서 처리)
        console_placeholder = st.empty()
        
        # 분석 프로세스 시작
        try:
            # 정밀도 레벨 가져오기
            precision_level = st.session_state.get('precision_level', 5)
            
            # 분석 실행
            video = handle_video_analysis_enhanced(
                video_url, 
                precision_level,
                console_placeholder
            )
            
            # 결과 저장
            st.session_state.analysis_result = video
            set_analysis_state('completed')
            st.rerun()
            
        except Exception as e:
            st.error(f"분석 중 오류 발생: {str(e)}")
            set_analysis_state('idle')
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_results_section():
    """결과 표시 섹션"""
    video = st.session_state.get('analysis_result')
    if not video:
        set_analysis_state('idle')
        st.rerun()
        return
    
    # 비디오 임베드 유지
    render_video_embed(video.url)
    
    # 필름 스트립
    render_film_strip(video)
    
    # 분석 결과
    render_analysis_results(video)
    
    # 액션 버튼들
    render_action_buttons(video)


def render_video_embed(url: str):
    """비디오 임베드"""
    st.markdown('<div style="animation: slideDown 0.5s ease-out;">', unsafe_allow_html=True)
    
    # YouTube/Vimeo 판별
    if "youtube.com" in url or "youtu.be" in url:
        # YouTube ID 추출
        if "watch?v=" in url:
            video_id = url.split("watch?v=")[1].split("&")[0]
        else:
            video_id = url.split("/")[-1]
        
        st.markdown(f"""
        <iframe width="100%" height="400" 
                src="https://www.youtube.com/embed/{video_id}"
                frameborder="0" allowfullscreen>
        </iframe>
        """, unsafe_allow_html=True)
    
    elif "vimeo.com" in url:
        # Vimeo ID 추출
        video_id = url.split("/")[-1]
        st.markdown(f"""
        <iframe width="100%" height="400" 
                src="https://player.vimeo.com/video/{video_id}"
                frameborder="0" allowfullscreen>
        </iframe>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_film_strip(video):
    """필름 스트립 표시"""
    if not video.scenes:
        return
    
    st.markdown('<div class="film-strip-container">', unsafe_allow_html=True)
    st.markdown("#### 🎞️ 추출된 주요 장면")
    
    # 이미지 개수에 따른 동적 레이아웃
    num_scenes = len(video.scenes)
    if num_scenes <= 5:
        cols = st.columns(num_scenes)
    else:
        # 스크롤 가능한 필름 스트립
        st.markdown('<div class="film-strip">', unsafe_allow_html=True)
        
        # HTML로 직접 렌더링
        html_content = ""
        for i, scene in enumerate(video.scenes):
            if os.path.exists(scene.frame_path):
                html_content += f"""
                <div class="film-frame">
                    <img src="data:image/jpeg;base64,{get_base64_image(scene.frame_path)}" 
                         alt="Scene {i+1}" />
                </div>
                """
        
        st.markdown(html_content, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 5개 이하일 때는 컬럼 사용
    if num_scenes <= 5:
        for i, (col, scene) in enumerate(zip(cols, video.scenes)):
            with col:
                if os.path.exists(scene.frame_path):
                    st.image(scene.frame_path, caption=f"Scene {i+1}")
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_analysis_results(video):
    """분석 결과 표시"""
    if not video.analysis_result:
        return
    
    st.markdown('<div class="result-section">', unsafe_allow_html=True)
    st.markdown("### 📊 분석 결과")
    
    result = video.analysis_result
    
    # 결과 아이템들
    items = [
        ("장르", result.get('genre', 'Unknown')),
        ("표현형식", result.get('expression_style', 'Unknown')),
        ("판단이유", result.get('reasoning', 'Unknown')),
        ("특징", result.get('features', 'Unknown')),
        ("분위기", result.get('mood_tone', 'Unknown')),
        ("타겟 고객층", result.get('target_audience', 'Unknown'))
    ]
    
    for label, value in items:
        st.markdown(f"""
        <div class="result-item">
            <div class="result-label">{label}</div>
            <div class="result-value">{value}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # 태그
    tags = result.get('tags', [])
    if tags:
        st.markdown("""
        <div class="result-item">
            <div class="result-label">태그</div>
            <div class="result-value">
                <div class="tag-container">
        """, unsafe_allow_html=True)
        
        for tag in tags:
            st.markdown(f'<span class="tag">#{tag}</span>', unsafe_allow_html=True)
        
        st.markdown("</div></div></div>", unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_action_buttons(video):
    """액션 버튼들"""
    st.markdown("### 🎯 추가 작업")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("💾 다른 이름으로 저장", use_container_width=True):
            # TODO: 구현
            st.info("저장 기능 준비 중...")
    
    with col2:
        if st.button("🎨 무드보드 보기", use_container_width=True):
            st.session_state.show_moodboard = True
            st.rerun()
    
    with col3:
        if st.button("🔄 재추론하기", use_container_width=True):
            set_analysis_state('processing')
            st.rerun()
    
    with col4:
        if st.button("🎚️ 다른 정밀도로", use_container_width=True):
            st.session_state.show_precision_modal = True
            st.rerun()
    
    # 새로운 분석 버튼
    st.markdown("---")
    if st.button("🆕 새로운 영상 분석", type="secondary", use_container_width=True):
        # 상태 초기화
        set_analysis_state('idle')
        st.session_state.analysis_result = None
        st.session_state.current_video_url = None
        st.rerun()


def get_base64_image(image_path):
    """이미지를 base64로 변환"""
    import base64
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()


# 무드보드 모달 처리
def render_moodboard_modal():
    """무드보드 모달 (별도 함수로 분리)"""
    if st.session_state.get('show_moodboard'):
        # TODO: 구현
        st.info("무드보드 기능 준비 중...")
        if st.button("닫기"):
            st.session_state.show_moodboard = False
            st.rerun()