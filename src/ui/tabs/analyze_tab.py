# src/ui/tabs/analyze_tab.py
"""
Analyze 탭 - 영상 분석 UI (정리된 버전)
"""

import streamlit as st
import time
import os
import base64
import urllib.parse
import re
from typing import Optional, Dict, Any
from handlers.enhanced_video_handler import handle_video_analysis_enhanced
from utils.session_state import get_analysis_state, set_analysis_state
from utils.logger import get_logger
from streamlit_extras.grid import grid
from streamlit_modal import Modal

logger = get_logger(__name__)


def render_analyze_tab():
    """Analyze 탭 렌더링"""
    # 모달 처리
    render_modals()
    
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
    if not video_url:
        st.error("비디오 URL이 존재하지 않습니다.")
        return

    # 비디오 임베드
    render_video_embed(video_url)

    # 콘솔창
    st.markdown("### 💻 처리 상황")
    console_container = st.container()
    
    with console_container:
        console_placeholder = st.empty()
    
    # 로그 라인 저장용
    if 'console_logs' not in st.session_state:
        st.session_state.console_logs = []
    
    def update_console(message: str):
        """콘솔 업데이트"""
        st.session_state.console_logs.append(f"> {message}")
        if len(st.session_state.console_logs) > 3:
            st.session_state.console_logs.pop(0)
        
        console_text = "\n".join(st.session_state.console_logs)
        console_placeholder.markdown(
            f"""
            <div style="
                background-color: #1e1e1e;
                color: #00ff00;
                padding: 15px;
                border-radius: 5px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 14px;
                height: 150px;
                overflow-y: auto;
                white-space: pre-wrap;
            ">
{console_text}
            </div>
            """,
            unsafe_allow_html=True
        )

    try:
        st.session_state.console_logs = []
        precision_level = st.session_state.get('precision_level', 5)

        video = handle_video_analysis_enhanced(
            video_url=video_url,
            precision_level=precision_level,
            console_callback=update_console
        )

        st.session_state.analysis_result = video
        st.session_state.console_logs = []
        set_analysis_state('completed')
        st.rerun()

    except Exception as e:
        st.error(f"분석 중 오류 발생: {str(e)}")
        st.session_state.console_logs = []
        set_analysis_state('idle')
        st.rerun()


def render_results_section():
    """결과 표시 섹션"""
    video = st.session_state.get('analysis_result')
    if not video:
        set_analysis_state('idle')
        st.rerun()
        return
    
    # 비디오 임베드
    render_video_embed(video.url)
    
    # 필름 스트립
    render_film_strip(video)
    
    # 분석 결과
    render_analysis_results(video)
    
    # 액션 버튼들
    render_action_buttons(video)


def render_video_embed(url: str):
    """비디오 임베드"""
    video_id = extract_video_id(url)
    platform = detect_platform(url)
    
    if platform == "youtube":
        st.markdown(f"""
        <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden;">
            <iframe style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"
                    src="https://www.youtube.com/embed/{video_id}"
                    frameborder="0" allowfullscreen>
            </iframe>
        </div>
        """, unsafe_allow_html=True)
    elif platform == "vimeo":
        st.markdown(f"""
        <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden;">
            <iframe style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"
                    src="https://player.vimeo.com/video/{video_id}"
                    frameborder="0" allowfullscreen>
            </iframe>
        </div>
        """, unsafe_allow_html=True)


def render_film_strip(video):
    """필름 스트립 표시"""
    if not video.scenes:
        return
    
    base_url = "https://sof.greatminds.kr"
    
    # 4열 그리드
    film_grid = grid(4, vertical_align="center")
    
    # 썸네일
    thumbnail_url = f"{base_url}/{video.session_id}/{video.session_id}_Thumbnail.jpg"
    with film_grid.container():
        st.image(thumbnail_url, caption="📌 썸네일", use_container_width=True)
    
    # 씬 이미지들
    for i, scene in enumerate(video.scenes):
        scene_filename = os.path.basename(scene.frame_path)
        scene_url = f"{base_url}/{video.session_id}/{scene_filename}"
        
        with film_grid.container():
            st.image(
                scene_url, 
                caption=f"Scene {i+1} ({scene.timestamp:.1f}s)", 
                use_container_width=True
            )


def render_analysis_results(video):
    """분석 결과 표시"""
    if not video.analysis_result:
        return
    
    st.markdown("### 📊 분석 결과")
    
    # 커스텀 CSS
    st.markdown("""
    <style>
    .result-subtitle {
        color: #ffffff;
        font-size: 0.9rem;
        font-weight: 600;
        margin-bottom: 8px;
        padding-bottom: 6px;
        border-bottom: 2px solid #4a9eff;
        display: inline-block;
    }
    
    .result-content {
        color: #e0e0e0;
        font-size: 0.95rem;
        line-height: 1.6;
        margin-bottom: 20px;
        padding: 12px;
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        border-left: 3px solid transparent;
        transition: all 0.3s ease;
    }
    
    .result-content:hover {
        background-color: rgba(255, 255, 255, 0.08);
        border-left-color: #4a9eff;
    }
    
    .tag-container {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 10px;
    }
    
    .tag-item {
        display: inline-block;
        background: linear-gradient(135deg, #4a9eff 0%, #3d8ce6 100%);
        color: white;
        padding: 6px 16px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
        box-shadow: 0 2px 4px rgba(74, 158, 255, 0.3);
        transition: transform 0.2s ease;
    }
    
    .tag-item:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(74, 158, 255, 0.4);
    }
    
    .info-item {
        padding: 8px 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        font-size: 0.9rem;
    }
    
    .info-item:last-child {
        border-bottom: none;
    }
    </style>
    """, unsafe_allow_html=True)
    
    result = video.analysis_result
    metadata = video.metadata if video.metadata else None
    
    # 2컬럼 레이아웃
    col1, col2 = st.columns([35, 65])
    
    # 왼쪽 컬럼 - 메타데이터
    with col1:
        # 제목
        st.markdown('<p class="result-subtitle">📹 제목</p>', unsafe_allow_html=True)
        st.markdown(f'<div class="result-content">{metadata.title if metadata else "Unknown"}</div>', unsafe_allow_html=True)
        
        # 업로드 채널
        st.markdown('<p class="result-subtitle">👤 업로드 채널</p>', unsafe_allow_html=True)
        st.markdown(f'<div class="result-content">{metadata.uploader if metadata else "Unknown"}</div>', unsafe_allow_html=True)
        
        # 설명
        if metadata and metadata.description:
            st.markdown('<p class="result-subtitle">📝 설명</p>', unsafe_allow_html=True)
            description = metadata.description[:200] + '...' if len(metadata.description) > 200 else metadata.description
            st.markdown(f'<div class="result-content">{description}</div>', unsafe_allow_html=True)
        
        # 기타 정보
        st.markdown('<p class="result-subtitle">📊 상세 정보</p>', unsafe_allow_html=True)
        info_html = '<div class="result-content">'
        
        if metadata:
            if metadata.view_count:
                info_html += f'<div class="info-item">👁️ 조회수: <strong>{metadata.view_count:,}회</strong></div>'
            if metadata.duration:
                info_html += f'<div class="info-item">⏱️ 길이: <strong>{int(metadata.duration//60)}분 {int(metadata.duration%60)}초</strong></div>'
            if metadata.upload_date:
                upload_date = metadata.upload_date[:10] if len(metadata.upload_date) >= 10 else metadata.upload_date
                info_html += f'<div class="info-item">📅 업로드: <strong>{upload_date}</strong></div>'
            if metadata.like_count:
                info_html += f'<div class="info-item">👍 좋아요: <strong>{metadata.like_count:,}</strong></div>'
            if metadata.comment_count:
                info_html += f'<div class="info-item">💬 댓글: <strong>{metadata.comment_count:,}</strong></div>'
        
        info_html += '</div>'
        st.markdown(info_html, unsafe_allow_html=True)
    
    # 오른쪽 컬럼 - AI 분석 결과
    with col2:
        # 장르 & 표현형식
        st.markdown('<p class="result-subtitle">🎭 장르 & 표현형식</p>', unsafe_allow_html=True)
        genre_text = f"{result.get('genre', 'Unknown')} • {result.get('expression_style', 'Unknown')}"
        st.markdown(f'<div class="result-content"><strong>{genre_text}</strong></div>', unsafe_allow_html=True)
        
        # 판단이유
        st.markdown('<p class="result-subtitle">💡 판단이유</p>', unsafe_allow_html=True)
        reasoning = result.get('reasoning', 'Unknown')
        st.markdown(f'<div class="result-content">{reasoning}</div>', unsafe_allow_html=True)
        
        # 특징
        st.markdown('<p class="result-subtitle">✨ 특징</p>', unsafe_allow_html=True)
        features = result.get('features', 'Unknown')
        st.markdown(f'<div class="result-content">{features}</div>', unsafe_allow_html=True)
        
        # 분위기
        st.markdown('<p class="result-subtitle">🌈 분위기</p>', unsafe_allow_html=True)
        mood = result.get('mood_tone', 'Unknown')
        st.markdown(f'<div class="result-content">{mood}</div>', unsafe_allow_html=True)
        
        # 타겟 고객층
        st.markdown('<p class="result-subtitle">👥 타겟 고객층</p>', unsafe_allow_html=True)
        target = result.get('target_audience', 'Unknown')
        st.markdown(f'<div class="result-content">{target}</div>', unsafe_allow_html=True)
        
        # 태그
        st.markdown('<p class="result-subtitle">🏷️ 태그</p>', unsafe_allow_html=True)
        tags = result.get('tags', [])
        if tags:
            tags_html = '<div class="tag-container">'
            for tag in tags[:20]:
                tags_html += f'<span class="tag-item">#{tag}</span>'
            tags_html += '</div>'
            st.markdown(tags_html, unsafe_allow_html=True)
        else:
            st.markdown('<div class="result-content">태그 없음</div>', unsafe_allow_html=True)


def render_action_buttons(video):
    """액션 버튼들"""
    base_url = "https://sof.greatminds.kr"
    video_id = video.session_id
    
    # 파일명 정리
    def sanitize_filename(title: str, max_length: int = 100) -> str:
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
        safe_title = re.sub(r'_+', '_', safe_title)
        safe_title = safe_title.strip('_ ')
        return safe_title[:max_length]
    
    video_title = video.metadata.title if video.metadata else "video"
    sanitized_title = sanitize_filename(video_title)
    video_filename = f"{video_id}_{sanitized_title}.mp4"
    
    encoded_filename = urllib.parse.quote(video_filename)
    video_url = f"{base_url}/{video_id}/{encoded_filename}"
    download_filename = f"{sanitized_title}_{video_id}.mp4"
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <a href="{video_url}" download="{download_filename}" style="text-decoration: none; display: block;">
            <div style="
                background-color: #262730;
                color: white;
                padding: 0.5rem;
                border: 1px solid rgba(250, 250, 250, 0.2);
                border-radius: 0.5rem;
                cursor: pointer;
                text-align: center;
                font-size: 14px;
                font-weight: 400;
                transition: all 0.3s;
            " onmouseover="this.style.backgroundColor='#464646'" 
               onmouseout="this.style.backgroundColor='#262730'">
                💾 다운로드
            </div>
        </a>
        """, unsafe_allow_html=True)

    with col2:
        if st.button("🎨 무드보드 보기", use_container_width=True, key="view_moodboard"):
            show_moodboard_dialog()  # 직접 함수 호출
    
    with col3:
        if st.button("🔄 재추론하기", use_container_width=True, key="reanalyze"):
            st.session_state.analysis_result = None
            set_analysis_state('processing')
            st.rerun()
    
    with col4:
        if st.button("🎚️ 다른 정밀도로", use_container_width=True, key="change_precision"):
            st.session_state.show_precision_modal = True
            st.rerun()
    
    st.markdown("---")
    if st.button("🆕 새로운 영상 분석", type="secondary", use_container_width=True):
        reset_analysis_state()
        st.rerun()


def render_modals():
    """모달 창들 렌더링"""
    if st.session_state.get('show_moodboard'):
        show_moodboard_dialog()
    
    if st.session_state.get('show_precision_modal'):
        show_precision_dialog()


@st.dialog("🎨 무드보드", width="large")
def show_moodboard_dialog():
    """Streamlit의 네이티브 dialog 사용"""
    video = st.session_state.get('analysis_result')
    if not video:
        return
    
    # 비디오 정보
    if video.metadata:
        cols = st.columns(5)
        with cols[0]:
            st.metric("🎬 영상", video.metadata.title[:20] + "...")
        with cols[1]:
            st.metric("🎭 장르", video.analysis_result.get('genre', 'Unknown'))
        with cols[2]:
            st.metric("🎨 표현형식", video.analysis_result.get('expression_style', 'Unknown'))
        with cols[3]:
            st.metric("🖼️ 씬 수", f"{len(video.scenes)}개")
        with cols[4]:
            duration = video.metadata.duration if video.metadata else 0
            st.metric("⏱️ 길이", f"{int(duration//60)}:{int(duration%60):02d}")
    
    # 탭
    tab1, tab2, tab3 = st.tabs(["📸 그리드 뷰", "📋 리스트 뷰", "🎞️ 필름스트립"])
    
    base_url = "https://sof.greatminds.kr"
    
    with tab1:
        render_grid_view(video, base_url)
    
    with tab2:
        render_list_view(video, base_url)
    
    with tab3:
        render_filmstrip_view(video, base_url)


def render_moodboard_modal():
    """무드보드 모달"""
    video = st.session_state.get('analysis_result')
    if not video:
        st.session_state.show_moodboard = False
        st.rerun()
        return
    
    # CSS 스타일
    st.markdown("""
    <style>
    .Modal {
        max-width: 80vw !important;
        width: 80vw !important;
        max-height: 80vh !important;
        margin: auto !important;
    }
    
    .Modal > div:first-child {
        max-height: 80vh !important;
        overflow-y: auto !important;
    }
    
    .scene-image-container {
        overflow: hidden;
        border-radius: 8px;
        transition: transform 0.3s ease;
    }
    
    .scene-image-container:hover {
        transform: scale(1.02);
        box-shadow: 0 8px 16px rgba(0,0,0,0.3);
    }
    
    .info-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        backdrop-filter: blur(10px);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 모달 생성
    modal = Modal(
        title="", 
        key="moodboard-modal",
        max_width=None,
        padding=0,
    )
    
    if st.session_state.get('show_moodboard', False):
        modal.open()
    
    if modal.is_open():
        with modal.container():
            # 헤더
            header_col1, header_col2 = st.columns([10, 1])
            with header_col1:
                st.markdown("# 🎨 무드보드")
            with header_col2:
                if st.button("✖", key="close_moodboard_btn", help="닫기"):
                    st.session_state.show_moodboard = False
                    modal.close()
                    st.rerun()
            
            # 비디오 정보
            if video.metadata:
                st.markdown('<div class="info-card">', unsafe_allow_html=True)
                
                info_cols = st.columns(5)
                with info_cols[0]:
                    st.metric("🎬 영상", video.metadata.title[:30] + "..." if len(video.metadata.title) > 30 else video.metadata.title)
                with info_cols[1]:
                    st.metric("🎭 장르", video.analysis_result.get('genre', 'Unknown'))
                with info_cols[2]:
                    st.metric("🎨 표현형식", video.analysis_result.get('expression_style', 'Unknown'))
                with info_cols[3]:
                    st.metric("🖼️ 씬 수", f"{len(video.scenes)}개")
                with info_cols[4]:
                    duration = video.metadata.duration if video.metadata else 0
                    st.metric("⏱️ 길이", f"{int(duration//60)}:{int(duration%60):02d}")
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # 탭
            tab1, tab2, tab3 = st.tabs(["📸 그리드 뷰", "📋 리스트 뷰", "🎞️ 필름스트립"])
            
            base_url = "https://sof.greatminds.kr"
            
            with tab1:
                render_grid_view(video, base_url)
            
            with tab2:
                render_list_view(video, base_url)
            
            with tab3:
                render_filmstrip_view(video, base_url)
            
            # 액션 버튼들
            st.markdown("---")
            render_moodboard_actions(video, base_url)


def render_grid_view(video, base_url):
    """그리드 뷰"""
    st.markdown("### 📸 씬 이미지 그리드")
    
    col_option = st.radio(
        "그리드 열 수",
        [2, 3, 4],
        index=1,
        horizontal=True,
        key="grid_columns"
    )
    
    # 썸네일 포함
    include_thumbnail = st.checkbox("썸네일 포함", value=True, key="include_thumb_grid")
    
    images = []
    
    if include_thumbnail:
        thumbnail_url = f"{base_url}/{video.session_id}/{video.session_id}_Thumbnail.jpg"
        images.append(("썸네일", thumbnail_url, None))
    
    for i, scene in enumerate(video.scenes):
        scene_filename = os.path.basename(scene.frame_path)
        scene_url = f"{base_url}/{video.session_id}/{scene_filename}"
        images.append((f"Scene {i+1}", scene_url, scene))
    
    # 그리드 렌더링
    rows = (len(images) + col_option - 1) // col_option
    
    for row in range(rows):
        cols = st.columns(col_option)
        for col_idx in range(col_option):
            img_idx = row * col_option + col_idx
            if img_idx < len(images):
                title, url, scene = images[img_idx]
                with cols[col_idx]:
                    st.markdown(f'<div class="scene-image-container">', unsafe_allow_html=True)
                    st.image(url, use_container_width=True)
                    
                    if scene:
                        st.caption(f"{title} - {scene.timestamp:.1f}s")
                    else:
                        st.caption(title)
                    
                    st.markdown('</div>', unsafe_allow_html=True)


def render_list_view(video, base_url):
    """리스트 뷰"""
    st.markdown("### 📋 상세 씬 정보")
    
    for i, scene in enumerate(video.scenes):
        scene_filename = os.path.basename(scene.frame_path)
        scene_url = f"{base_url}/{video.session_id}/{scene_filename}"
        
        with st.expander(f"🎬 Scene {i+1}", expanded=False):
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.image(scene_url, use_container_width=True)
            
            with col2:
                st.subheader(f"Scene {i+1}")
                st.write(f"**타임스탬프:** {scene.timestamp:.1f}초")
                st.write(f"**파일명:** {scene_filename}")
                st.write(f"**씬 타입:** {scene.scene_type}")
                
                minutes = int(scene.timestamp // 60)
                seconds = int(scene.timestamp % 60)
                st.write(f"**시간 위치:** {minutes:02d}:{seconds:02d}")


def render_filmstrip_view(video, base_url):
    """필름스트립 뷰"""
    st.markdown("### 🎞️ 필름스트립 뷰")
    
    strip_height = st.slider("스트립 높이", 100, 300, 200, 20, key="strip_height")
    
    st.markdown(f"""
    <style>
    .filmstrip-wrapper {{
        width: 100%;
        overflow-x: auto;
        background: #1e1e1e;
        border-radius: 10px;
        padding: 10px;
    }}
    
    .filmstrip {{
        display: flex;
        gap: 10px;
        height: {strip_height}px;
    }}
    
    .film-frame {{
        flex: 0 0 auto;
        height: 100%;
        position: relative;
        border-radius: 8px;
        overflow: hidden;
        background: #2a2a2a;
    }}
    
    .film-frame img {{
        height: 100%;
        width: auto;
        display: block;
    }}
    
    .film-frame-caption {{
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        background: rgba(0,0,0,0.8);
        color: white;
        padding: 5px;
        font-size: 12px;
        text-align: center;
    }}
    </style>
    
    <div class="filmstrip-wrapper">
        <div class="filmstrip">
    """, unsafe_allow_html=True)
    
    # 썸네일
    thumbnail_url = f"{base_url}/{video.session_id}/{video.session_id}_Thumbnail.jpg"
    st.markdown(f'''
        <div class="film-frame">
            <img src="{thumbnail_url}" alt="썸네일">
            <div class="film-frame-caption">썸네일</div>
        </div>
    ''', unsafe_allow_html=True)
    
    # 씬들
    for i, scene in enumerate(video.scenes):
        scene_filename = os.path.basename(scene.frame_path)
        scene_url = f"{base_url}/{video.session_id}/{scene_filename}"
        
        st.markdown(f'''
            <div class="film-frame">
                <img src="{scene_url}" alt="Scene {i+1}">
                <div class="film-frame-caption">Scene {i+1} ({scene.timestamp:.1f}s)</div>
            </div>
        ''', unsafe_allow_html=True)
    
    st.markdown("</div></div>", unsafe_allow_html=True)


def render_moodboard_actions(video, base_url):
    """무드보드 액션 버튼들"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📥 전체 ZIP 다운로드", use_container_width=True, type="primary"):
            st.info("ZIP 파일 생성 기능은 준비 중입니다.")
    
    with col2:
        if st.button("📄 PDF 무드보드", use_container_width=True):
            st.info("PDF 생성 기능은 준비 중입니다.")
    
    with col3:
        if st.button("🎨 PPT 템플릿", use_container_width=True):
            st.info("PPT 템플릿 기능은 준비 중입니다.")
    
    with col4:
        if st.button("📤 Notion 업로드", use_container_width=True):
            st.info("Notion 연동 기능은 준비 중입니다.")


def render_precision_modal():
    """정밀도 선택 모달"""
    modal = Modal(
        title="🎚️ 정밀도 선택",
        key="precision-modal",
        max_width=600,
        padding=20,
    )
    
    if st.session_state.get('show_precision_modal', False):
        modal.open()
    
    if modal.is_open():
        with modal.container():
            if st.button("✖", key="close_precision_btn", help="닫기"):
                st.session_state.show_precision_modal = False
                modal.close()
                st.rerun()
            
            current_precision = st.session_state.get('precision_level', 5)
            
            st.info(f"현재 정밀도: **레벨 {current_precision}**")
            
            new_precision = st.slider(
                "새로운 정밀도 레벨",
                min_value=1,
                max_value=10,
                value=current_precision,
                help="높은 레벨일수록 더 많은 이미지를 추출하고 정밀한 분석을 수행합니다."
            )
            
            precision_info = {
                1: ("⚡ 초고속", "4개 이미지, 30초-1분", "#28a745"),
                2: ("🏃 고속", "4개 이미지, 1-2분", "#28a745"),
                3: ("🚶 빠름", "5개 이미지, 2-3분", "#17a2b8"),
                4: ("🚶‍♂️ 보통-빠름", "5개 이미지, 3-4분", "#17a2b8"),
                5: ("⚖️ 균형 (권장)", "6개 이미지, 4-6분", "#007bff"),
                6: ("🔍 정밀", "7개 이미지, 6-8분", "#ffc107"),
                7: ("🔬 고정밀", "8개 이미지, 8-12분", "#ffc107"),
                8: ("🎯 매우정밀", "10개 이미지, 12-15분", "#fd7e14"),
                9: ("🏆 초정밀", "10개 이미지, 15-20분", "#dc3545"),
                10: ("💎 최고정밀", "10개 이미지, 20-30분", "#dc3545")
            }
            
            if new_precision in precision_info:
                title, desc, color = precision_info[new_precision]
                st.markdown(f"""
                <div style="background: {color}20; border-left: 4px solid {color}; 
                            padding: 15px; border-radius: 5px; margin: 10px 0;">
                    <strong style="color: {color};">{title}</strong><br>
                    {desc}
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔄 이 정밀도로 재분석", type="primary", use_container_width=True):
                    st.session_state.precision_level = new_precision
                    st.session_state.show_precision_modal = False
                    st.session_state.analysis_result = None
                    set_analysis_state('processing')
                    modal.close()
                    st.rerun()
            
            with col2:
                if st.button("취소", use_container_width=True):
                    st.session_state.show_precision_modal = False
                    modal.close()
                    st.rerun()


# 유틸리티 함수들
def extract_video_id(url: str) -> str:
    """비디오 ID 추출"""
    if "youtube.com" in url or "youtu.be" in url:
        if "watch?v=" in url:
            return url.split("watch?v=")[1].split("&")[0]
        elif "youtu.be" in url:
            return url.split("/")[-1].split("?")[0]
    elif "vimeo.com" in url:
        return url.split("/")[-1].split("?")[0]
    return ""


def detect_platform(url: str) -> str:
    """플랫폼 감지"""
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    elif "vimeo.com" in url:
        return "vimeo"
    return "unknown"


def reset_analysis_state():
    """분석 상태 초기화"""
    set_analysis_state('idle')
    st.session_state.analysis_result = None
    st.session_state.current_video_url = None
    st.session_state.show_moodboard = False
    st.session_state.show_precision_modal = False
    if 'moodboard_selected' in st.session_state:
        del st.session_state.moodboard_selected