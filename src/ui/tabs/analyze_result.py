# src/ui/tabs/analyze_result.py
"""
분석 결과 렌더링 - 비디오 임베드, 필름스트립, 분석 결과 표시
"""

import streamlit as st
import os
import re
from streamlit_extras.grid import grid
from utils.session_state import set_analysis_state
from .analyze_function import render_action_buttons
from utils.logger import get_logger

logger = get_logger(__name__)


def render_results_section():
    """결과 표시 섹션"""
    # 세션 상태에서 직접 가져오기
    video = st.session_state.get('analysis_result')
    if not video:
        set_analysis_state('idle')
        st.rerun()
        return
    
    # video 객체 타입 검증
    if not hasattr(video, 'url') or not hasattr(video, 'session_id'):
        st.error("잘못된 분석 결과 형식입니다. 다시 분석해주세요.")
        logger.error(f"Invalid video object type: {type(video)}")
        set_analysis_state('idle')
        st.rerun()
        return
    
    # 디버깅: 현재 분석 결과 확인
    if video.analysis_result:
        logger.info(f"Rendering results - Genre: {video.analysis_result.get('genre', 'N/A')}")
    
    # 비디오 임베드
    render_video_embed(video.url)
    
    # 비디오와 필름스트립 사이 구분선 및 여백
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 필름 스트립
    render_film_strip(video)
    
    # 필름스트립과 분석 결과 사이 여백
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 분석 결과
    render_analysis_results(video)
    
    # 분석 결과와 액션 버튼 사이 여백
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # 액션 버튼들
    render_action_buttons(video)


def render_video_embed(url: str):
    """비디오 임베드"""
    video_id = extract_video_id(url)
    platform = detect_platform(url)
    
    # 중앙 정렬을 위한 컬럼 구조 추가
    col1, col2, col3 = st.columns([1, 2, 1])
        
    with col2:  # 중앙 컬럼에만 비디오 표시
        if platform == "youtube":
            st.markdown(f"""
            <div style="
                max-width: 1200px;
                min-width: 400px;
                margin: 0 auto;
                box-shadow: 0px 0px 75px 0px #000;
                border-radius: 8px;
                overflow: hidden;
            ">
                <div style="
                    position: relative; 
                    padding-bottom: 56.25%; 
                    height: 0; 
                    overflow: hidden;
                ">
                    <iframe style="
                        position: absolute; 
                        top: 0; 
                        left: 0; 
                        width: 100%; 
                        height: 100%;"
                        src="https://www.youtube.com/embed/{video_id}"
                        frameborder="0" 
                        allowfullscreen>
                    </iframe>
                </div>
            </div>
            """, unsafe_allow_html=True)
        elif platform == "vimeo":
            st.markdown(f"""
            <div style="
                max-width: 1200px;
                min-width: 400px;
                margin: 0 auto;
                box-shadow: 0px 0px 75px 0px #000;
                border-radius: 8px;
                overflow: hidden;
            ">
                <div style="
                    position: relative; 
                    padding-bottom: 56.25%; 
                    height: 0; 
                    overflow: hidden;
                ">
                    <iframe style="
                        position: absolute; 
                        top: 0; 
                        left: 0; 
                        width: 100%; 
                        height: 100%;"
                        src="https://player.vimeo.com/video/{video_id}"
                        frameborder="0" 
                        allowfullscreen>
                    </iframe>
                </div>
            </div>
            """, unsafe_allow_html=True)


def render_film_strip(video):
    """필름 스트립 표시"""
    if not video or not hasattr(video, 'scenes'):
        logger.warning("No scenes available for film strip")
        return
    
    if not video.scenes:
        return
    
    base_url = "https://sof.greatminds.kr"
    
    # session_id 가져오기
    if not hasattr(video, 'session_id'):
        logger.error("Video object missing session_id")
        return
    
    # 재추론 여부 확인
    is_reanalyzed = getattr(video, 'is_reanalyzed', False)
    if is_reanalyzed:
        st.info("🔄 재추론된 이미지들을 표시합니다")
        
    # 4열 그리드
    film_grid = grid(4, vertical_align="center")
    
    # 썸네일 - 재추론 시에도 항상 표시
    thumbnail_url = f"{base_url}/{video.session_id}/{video.session_id}_Thumbnail.jpg"
    with film_grid.container():
        caption = "📌 썸네일"
        if is_reanalyzed and 'thumbnail' in getattr(video, 'reanalyzed_images', []):
            caption += " (재선택됨)"
        st.image(thumbnail_url, caption=caption, use_container_width=True)
    
    # 씬 이미지들
    for i, scene in enumerate(video.grouped_scenes):
        scene_filename = os.path.basename(scene.frame_path)
        scene_url = f"{base_url}/{video.session_id}/{scene_filename}"
        
        with film_grid.container():
            caption = f"Scene {i+1}"
            if hasattr(scene, 'timestamp') and scene.timestamp > 0:
                caption += f" ({scene.timestamp:.1f}s)"
            if is_reanalyzed:
                caption += " ✅"
                
            st.image(
                scene_url, 
                caption=caption, 
                use_container_width=True
            )


def render_analysis_results(video):
    """분석 결과 표시"""
    if not video:
        return
        
    # analysis_result 속성 확인
    if not hasattr(video, 'analysis_result') or not video.analysis_result:
        st.warning("AI 분석 결과가 없습니다.")
        return
    
    # 디버깅: 현재 표시되는 결과 확인
    result = video.analysis_result
    logger.info(f"Displaying analysis - Genre: {result.get('genre')}, Reasoning length: {len(result.get('reasoning', ''))}")
    
    # 강제 새로고침을 위한 키 추가
    st.markdown(f"### 📊 분석 결과 <small style='color: gray;'>(업데이트: {st.session_state.get('last_analysis_time', 'N/A')})</small>", unsafe_allow_html=True)
    
    # CSS 스타일
    st.markdown("""
    <style>
    .result-subtitle {
        font-size: 14px;
        color: #888;
        margin-bottom: 5px;
        font-weight: 600;
    }
    
    .result-content {
        background-color: rgba(255, 255, 255, 0.05);
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .tag-container {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 8px;
    }
    
    .tag-item {
        background-color: rgba(0, 122, 204, 0.3);
        color: #4DA6FF;
        padding: 4px 12px;
        border-radius: 16px;
        font-size: 13px;
        border: 1px solid rgba(77, 166, 255, 0.3);
    }
    
    .info-item {
        margin-bottom: 8px;
        color: rgba(255, 255, 255, 0.8);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 세션 상태에서 최신 데이터 가져오기
    current_video = st.session_state.get('analysis_result', video)
    result = current_video.analysis_result
    metadata = current_video.metadata if hasattr(current_video, 'metadata') else None
    
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
        genre = result.get('genre', 'Unknown')
        expression = result.get('expression_style', 'Unknown')
        genre_text = f"{genre} • {expression}"
        st.markdown(f'<div class="result-content"><strong>{genre_text}</strong></div>', unsafe_allow_html=True)
        
        # 판단이유
        st.markdown('<p class="result-subtitle">💡 판단이유</p>', unsafe_allow_html=True)
        reasoning = result.get('reasoning', result.get('reason', 'Unknown'))
        st.markdown(f'<div class="result-content">{reasoning}</div>', unsafe_allow_html=True)
        
        # 특징
        st.markdown('<p class="result-subtitle">✨ 특징</p>', unsafe_allow_html=True)
        features = result.get('features', 'Unknown')
        st.markdown(f'<div class="result-content">{features}</div>', unsafe_allow_html=True)
        
        # 분위기
        st.markdown('<p class="result-subtitle">🌈 분위기</p>', unsafe_allow_html=True)
        mood = result.get('mood_tone', result.get('mood', 'Unknown'))
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