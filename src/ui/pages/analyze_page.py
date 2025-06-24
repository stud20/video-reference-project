# src/ui/pages/analyze_page.py
"""
분석 페이지 - 비디오 임베드 및 필름스트립 UI 포함
"""

import streamlit as st
import time
import re
from typing import Dict, Any, List, Optional
from handlers.video_handler import handle_video_analysis


def get_video_embed_html(url: str) -> Optional[str]:
    """비디오 URL에서 임베드 HTML 생성"""
    if not url:
        return None
    
    # YouTube URL 처리
    if "youtube.com" in url or "youtu.be" in url:
        # 다양한 YouTube URL 형식 처리
        video_id = None
        
        # youtu.be 형식
        if "youtu.be" in url:
            match = re.search(r'youtu\.be/([a-zA-Z0-9_-]+)', url)
            if match:
                video_id = match.group(1)
        # youtube.com/watch 형식
        else:
            match = re.search(r'[?&]v=([a-zA-Z0-9_-]+)', url)
            if match:
                video_id = match.group(1)
        
        if video_id:
            return f'<iframe width="100%" height="400" src="https://www.youtube.com/embed/{video_id}" frameborder="0" allowfullscreen></iframe>'
    
    # Vimeo URL 처리
    elif "vimeo.com" in url:
        match = re.search(r'vimeo\.com/(\d+)', url)
        if match:
            video_id = match.group(1)
            return f'<iframe width="100%" height="400" src="https://player.vimeo.com/video/{video_id}" frameborder="0" allowfullscreen></iframe>'
    
    return None


def create_filmstrip_html(scenes: List[Dict[str, Any]], thumbnail_path: Optional[str] = None) -> str:
    """씬 이미지들로 필름스트립 HTML 생성"""
    if not scenes and not thumbnail_path:
        return ""
    
    filmstrip_html = '<div class="filmstrip-container">'
    
    # 썸네일 추가 (있는 경우)
    if thumbnail_path:
        filmstrip_html += f'''
        <div class="filmstrip-item">
            <img src="{thumbnail_path}" alt="썸네일" onerror="this.src='https://via.placeholder.com/200x120/667eea/ffffff?text=썸네일'">
            <div class="filmstrip-label">썸네일</div>
        </div>
        '''
    
    # 씬 이미지들 추가
    for i, scene in enumerate(scenes):
        # scene이 dict인 경우와 객체인 경우 모두 처리
        if isinstance(scene, dict):
            frame_path = scene.get('frame_path', '')
            timestamp = scene.get('timestamp', 0)
        else:
            frame_path = getattr(scene, 'frame_path', '')
            timestamp = getattr(scene, 'timestamp', 0)
        
        # 로컬 경로를 웹에서 접근 가능한 URL로 변환 (실제 구현시 필요)
        # 여기서는 placeholder 이미지 사용
        img_src = f"https://via.placeholder.com/200x120/764ba2/ffffff?text=씬+{i+1}"
        
        filmstrip_html += f'''
        <div class="filmstrip-item">
            <img src="{img_src}" alt="씬 {i+1} ({timestamp:.1f}초)">
            <div class="filmstrip-label">씬 {i+1} ({timestamp:.1f}초)</div>
        </div>
        '''
    
    filmstrip_html += '</div>'
    return filmstrip_html


def render_analyze_page():
    """분석 페이지 렌더링"""
    # 메인 컨테이너
    with st.container():
        st.markdown('<div class="main-container">', unsafe_allow_html=True)
        
        # 헤더
        st.markdown('<h1 class="main-header">🎬 AI 영상 분석</h1>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">YouTube 또는 Vimeo 영상의 장르와 특성을 AI가 분석합니다</p>', unsafe_allow_html=True)
        
        # 입력 섹션
        st.markdown('<div class="input-section">', unsafe_allow_html=True)
        
        # URL 입력
        video_url = st.text_input(
            "영상 URL을 입력하세요",
            placeholder="https://www.youtube.com/watch?v=... 또는 https://vimeo.com/...",
            help="YouTube와 Vimeo 영상을 지원합니다",
            key="video_url_input"
        )
        
        # 예시 URL 버튼
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📺 YouTube 예시", use_container_width=True):
                st.session_state.example_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
                st.rerun()
        
        with col2:
            if st.button("🎬 Vimeo 예시", use_container_width=True):
                st.session_state.example_url = "https://vimeo.com/347119375"
                st.rerun()
        
        with col3:
            if st.button("🎯 샘플 분석", use_container_width=True):
                st.session_state.show_sample = True
                st.rerun()
        
        # 예시 URL 적용
        if 'example_url' in st.session_state:
            video_url = st.session_state.example_url
            del st.session_state.example_url
        
        # 정밀도 설정
        st.markdown("### ⚙️ 분석 설정")
        precision_level = st.slider(
            "분석 정밀도",
            min_value=1,
            max_value=10,
            value=5,
            help="높을수록 더 정확하지만 시간이 오래 걸립니다"
        )
        
        st.markdown('</div>', unsafe_allow_html=True)  # input-section 닫기
        
        # 분석 버튼
        if st.button("🚀 분석 시작", type="primary", use_container_width=True):
            if video_url:
                # 비디오 임베드 표시
                embed_html = get_video_embed_html(video_url)
                if embed_html:
                    st.markdown('<div class="video-container">', unsafe_allow_html=True)
                    st.markdown(embed_html, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # 분석 진행
                with st.spinner("영상을 분석하고 있습니다..."):
                    try:
                        # 실제 분석 수행
                        video = handle_video_analysis(video_url, precision_level)
                        
                        if video:
                            # 필름스트립 표시 (썸네일 + 씬 이미지들)
                            st.markdown("### 🎞️ 추출된 씬")
                            
                            # 썸네일 경로 가져오기
                            thumbnail_path = None
                            if hasattr(video, 'metadata') and video.metadata:
                                thumbnail_path = getattr(video.metadata, 'thumbnail', None)
                            
                            # 씬 리스트 가져오기
                            scenes = getattr(video, 'scenes', [])
                            
                            filmstrip_html = create_filmstrip_html(scenes, thumbnail_path)
                            st.markdown(filmstrip_html, unsafe_allow_html=True)
                            
                            # 분석 결과 표시
                            display_analysis_results(video)
                    except Exception as e:
                        st.error(f"분석 중 오류가 발생했습니다: {str(e)}")
            else:
                st.error("❌ 영상 URL을 입력해주세요!")
        
        # 샘플 분석 결과 표시
        if st.session_state.get('show_sample', False):
            show_sample_analysis()
            del st.session_state['show_sample']
        
        st.markdown('</div>', unsafe_allow_html=True)  # main-container 닫기


def display_analysis_results(video):
    """분석 결과 표시"""
    if not video or not hasattr(video, 'analysis_result') or not video.analysis_result:
        st.warning("분석 결과가 없습니다.")
        return
    
    st.markdown("---")
    st.markdown("### 📊 분석 결과")
    
    result = video.analysis_result
    
    # 주요 정보 메트릭
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("장르", result.get('genre', 'N/A'))
    with col2:
        st.metric("표현 형식", result.get('expression_style', 'N/A'))
    with col3:
        st.metric("분위기", result.get('mood_tone', 'N/A'))
    
    # 상세 분석 결과
    analysis_sections = [
        ("🎯", "장르 판단 이유", result.get('reasoning', '')),
        ("✨", "영상의 특징", result.get('features', '')),
        ("👥", "타겟 고객층", result.get('target_audience', ''))
    ]
    
    for icon, title, content in analysis_sections:
        if content:
            st.markdown(f'''
            <div class="analysis-card">
                <div class="analysis-header">
                    <div class="analysis-icon">{icon}</div>
                    <div class="analysis-title">{title}</div>
                </div>
                <div class="analysis-content">{content}</div>
            </div>
            ''', unsafe_allow_html=True)
    
    # 태그 표시
    if result.get('tags'):
        st.markdown("### 🏷️ 태그")
        tags_html = '<div class="tag-container">'
        for tag in result['tags']:
            tags_html += f'<span class="tag">#{tag}</span>'
        tags_html += '</div>'
        st.markdown(tags_html, unsafe_allow_html=True)


def show_sample_analysis():
    """샘플 분석 결과 표시"""
    st.markdown("---")
    st.markdown("### 📊 샘플 분석 결과")
    
    # 샘플 비디오 임베드
    sample_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    sample_embed = get_video_embed_html(sample_url)
    
    if sample_embed:
        st.markdown('<div class="video-container">', unsafe_allow_html=True)
        st.markdown(sample_embed, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 샘플 필름스트립
    st.markdown("### 🎞️ 추출된 씬")
    sample_scenes = [
        {'frame_path': '', 'timestamp': 0.0},
        {'frame_path': '', 'timestamp': 15.5},
        {'frame_path': '', 'timestamp': 30.2},
        {'frame_path': '', 'timestamp': 45.8},
        {'frame_path': '', 'timestamp': 60.0}
    ]
    filmstrip_html = create_filmstrip_html(sample_scenes, "thumbnail")
    st.markdown(filmstrip_html, unsafe_allow_html=True)
    
    # 샘플 분석 결과
    sample_result = get_sample_analysis_result()
    
    # 주요 정보 메트릭
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("장르", sample_result['genre'])
    with col2:
        st.metric("표현 형식", sample_result['expression_style'])
    with col3:
        st.metric("분위기", sample_result['mood_tone'])
    
    # 상세 분석 결과
    analysis_sections = [
        ("🎯", "장르 판단 이유", sample_result['reasoning']),
        ("✨", "영상의 특징", sample_result['features']),
        ("👥", "타겟 고객층", sample_result['target_audience'])
    ]
    
    for icon, title, content in analysis_sections:
        st.markdown(f'''
        <div class="analysis-card">
            <div class="analysis-header">
                <div class="analysis-icon">{icon}</div>
                <div class="analysis-title">{title}</div>
            </div>
            <div class="analysis-content">{content}</div>
        </div>
        ''', unsafe_allow_html=True)
    
    # 태그 표시
    st.markdown("### 🏷️ 태그")
    tags_html = '<div class="tag-container">'
    for tag in sample_result['tags']:
        tags_html += f'<span class="tag">#{tag}</span>'
    tags_html += '</div>'
    st.markdown(tags_html, unsafe_allow_html=True)


def get_sample_analysis_result():
    """샘플 분석 결과 반환"""
    return {
        'genre': '코미디/엔터테인먼트',
        'expression_style': '실사',
        'mood_tone': '유쾌하고 활기찬',
        'reasoning': '''이 영상은 전형적인 코미디/엔터테인먼트 장르의 특징을 보여줍니다. 
        밝고 경쾌한 음악과 함께 리드미컬한 편집이 특징적이며, 
        시청자들에게 즐거움과 재미를 전달하는 것을 주 목적으로 하고 있습니다.''',
        'features': '''• 빠른 템포의 편집과 전환 효과
        • 밝고 채도 높은 색감 사용
        • 반복적인 리듬과 멜로디로 중독성 있는 구성
        • 단순하지만 임팩트 있는 시각적 요소''',
        'target_audience': '10대~30대의 젊은 층, 가벼운 엔터테인먼트를 즐기는 시청자',
        'tags': ['코미디', '엔터테인먼트', '음악', '댄스', '바이럴', '유머', '팝컬처']
    }