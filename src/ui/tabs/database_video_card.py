import streamlit as st
import os
import re
import urllib.parse
import requests
from typing import Dict, Any, List
from storage.db_manager import VideoAnalysisDB
from utils.logger import get_logger
from ui.tabs.database_edit import render_editable_card_info, save_edited_data, toggle_edit_mode
from streamlit_extras.stylable_container import stylable_container
import time  # 여기에 추가




logger = get_logger(__name__)


def render_video_cards_section(videos: List[Dict[str, Any]], items_per_page: int = 10):
    """비디오 카드 섹션 전체 렌더링"""
    # 컨테이너에 클래스 추가
    st.markdown('<div class="db-card-container">', unsafe_allow_html=True) 
    if not videos:
        st.info("검색 결과가 없습니다")
        return
    
    # 페이지네이션 설정
    if 'db_page' not in st.session_state:
        st.session_state.db_page = 1
    
    total_pages = (len(videos) + items_per_page - 1) // items_per_page
    current_page = st.session_state.db_page
    
    # 현재 페이지의 비디오들
    start_idx = (current_page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    page_videos = videos[start_idx:end_idx]
    

    # 비디오 카드 렌더링
    for video in page_videos:
        render_single_video_card(video)
    
    # 무한 스크롤 시뮬레이션 (더 보기 버튼)
    if end_idx < len(videos):
        if st.button("🔽 더 보기", use_container_width=True, key="load_more_videos"):
            st.session_state.db_page += 1
            st.rerun()


def sanitize_filename(title: str, max_length: int = 100) -> str:
    """파일명으로 사용 가능한 문자열로 변환"""
    safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
    safe_title = re.sub(r'_+', '_', safe_title)
    safe_title = safe_title.strip('_ ')
    return safe_title[:max_length]


def render_single_video_card(video: Dict[str, Any]):
    """단일 비디오 카드 렌더링"""
    video_id = video.get('video_id', 'unknown')
    
    # 편집 모드 확인
    is_edit_mode = st.session_state.get('edit_mode') == video_id
    
    # 고정 스타일 (선택 상태 제거)
    card_style = """
    {
        border: 1px solid #303842;
        border-radius: 10px;
        padding: 1.5rem 1rem 3rem 1rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    &:hover {
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-color: #c0c0c0;
    }
    """
    
    # stylable_container로 카드 감싸기
    with stylable_container(
        key=f"video_card_{video_id}",
        css_styles=card_style
    ):
        # 카드 내용 - 칼럼 비율 조정 (col3 제거하고 col2 비율 증가)
        col1, col2, col3 = st.columns([2, 6, 1])  # 태그 컬럼 제거, 정보 컬럼 확장
        
        # 썸네일 및 태그
        with col1:
            render_thumbnail(video)
            # 썸네일 하단에 태그 추가
            if not is_edit_mode:  # 편집 모드가 아닐 때만 태그 표시
                render_video_tags(video)
        
        # 정보 - 편집 모드 확인
        with col2:
            if is_edit_mode:
                render_editable_card_info(video)
            else:
                render_video_info(video)
        
        # 액션 버튼
        with col3:
            render_card_actions(video_id, video)
    
    # 무드보드가 열려있는지 확인하고 렌더링
    if (st.session_state.get('show_moodboard_modal') and 
        st.session_state.get('moodboard_video_id') == video_id):
        # 무드보드를 카드 바로 아래에 렌더링
        from ui.tabs.database_moodboard import render_inline_moodboard
        render_inline_moodboard(video_id)


def render_thumbnail(video: Dict[str, Any]):
    """비디오 썸네일 렌더링"""
    video_id = video.get('video_id', '')
    
    # 웹 서버 URL 설정
    base_url = "https://sof.greatminds.kr"
    session_id = video_id  # video_id가 session_id와 동일
    
    # 썸네일 URL
    thumbnail_url = f"{base_url}/{session_id}/{session_id}_Thumbnail.jpg"
    
    # 썸네일 표시
    try:
        st.image(thumbnail_url, use_container_width=True)
    except Exception as e:
        # 썸네일 로드 실패 시 첫 번째 씬 이미지 시도
        try:
            # 첫 번째 씬 이미지 URL
            first_scene_url = f"{base_url}/{session_id}/scene_0000.jpg"
            st.image(first_scene_url, use_container_width=True)
        except:
            st.markdown('<div class="thumbnail-placeholder">📹</div>', unsafe_allow_html=True)
            logger.error(f"썸네일 로드 실패: {thumbnail_url}")


def render_video_info(video: Dict[str, Any]):
    """비디오 정보 표시 (읽기 모드)"""
    # 제목
    title = video.get('title', 'Unknown')
    st.markdown(f"**{title}**")
    
    # 메타 정보 (업로더, 장르, 표현형식, 길이)
    uploader = video.get('uploader', 'Unknown')
    duration = video.get('duration', 0)
    duration_str = f"{duration//60}:{duration%60:02d}"
    
    analysis = video.get('analysis_result')
    
    # 첫 번째 줄: 업로더, 장르, 표현형식, 길이
    meta_parts = [f"👤 {uploader}"]
    
    if analysis:
        genre = analysis.get('genre', '')
        expression_style = analysis.get('expression_style', '')
        if genre:
            meta_parts.append(f"🎬 {genre}")
        if expression_style:
            meta_parts.append(f"📐 {expression_style}")
    
    meta_parts.append(f"⏱️ {duration_str}")
    
    st.caption(" • ".join(meta_parts))
    
    # 분석 정보가 있는 경우
    if analysis:
        # 판단 이유
        reasoning = analysis.get('reasoning', '')
        if reasoning:
            st.text_area(
                "💭 판단 이유",
                value=reasoning,
                key=f"view_reasoning_{video.get('video_id')}",
                height=120,
                disabled=True,
                label_visibility="visible"
            )
        
        # 특징
        features = analysis.get('features', '')
        if features:
            st.text_area(
                "✨ 특징",
                value=features,
                key=f"view_features_{video.get('video_id')}",
                height=120,
                disabled=True,
                label_visibility="visible"
            )

        # 분위기
        mood = analysis.get('mood_tone', '')
        if mood:
            st.text_area(
                "🎭 분위기",
                value=mood,
                key=f"view_mood_{video.get('video_id')}",
                height=90,
                disabled=True,
                label_visibility="visible"
            )
        
        # 타겟 고객층
        target = analysis.get('target_audience', '')
        if target:
            st.text_area(
                "🎯 타겟 고객층",
                value=target,
                key=f"view_target_{video.get('video_id')}",
                height=90,
                disabled=True,
                label_visibility="visible"
            )
    else:
        st.write("⚠️ 분석 미완료")


def render_video_tags(video: Dict[str, Any]):
    """비디오 태그 표시 - 전체 태그"""
    analysis = video.get('analysis_result')
    
    # YouTube 태그
    youtube_tags = video.get('tags', [])
    
    # AI 분석 태그
    ai_tags = []
    if analysis and analysis.get('tags'):
        ai_tags = analysis['tags']
    
    # 태그 HTML 생성
    if youtube_tags or ai_tags:
        tags_html = '<div class="tags-container">'
        
        # YouTube 태그 (파란색) - 전체 표시
        for tag in youtube_tags:
            if tag and len(tag) > 1:
                tags_html += f'<span class="tag-youtube">#{tag}</span>'
        
        # AI 태그 (초록색) - 전체 표시
        for tag in ai_tags:
            if tag and tag not in youtube_tags:
                tags_html += f'<span class="tag-ai">#{tag}</span>'
        
        tags_html += '</div>'
        st.markdown(tags_html, unsafe_allow_html=True)
    else:
        st.caption("태그 없음")

def render_card_actions(video_id: str, video: Dict[str, Any]):
    """카드 액션 버튼들 - 세로 배치, 아웃라인 스타일"""
    
    # 버튼 스타일 적용
    st.markdown(f"""
    <style>
    /* 액션 버튼 컨테이너 스타일 */
    div[data-testid="column"]:has(button[key^="vc_download_{video_id}"],
                                   button[key^="vc_mood_{video_id}"],
                                   button[key^="vc_edit_{video_id}"],
                                   button[key^="vc_save_{video_id}"],
                                   button[key^="vc_delete_{video_id}"]) button {{
        background-color: transparent !important;
        border: 1px solid #4a4a52 !important;
        color: #fafafa !important;
        font-size: 12px !important;
        padding: 4px 8px !important;
        height: 32px !important;
        transition: all 0.2s ease !important;
    }}
    
    div[data-testid="column"]:has(button[key^="vc_download_{video_id}"],
                                   button[key^="vc_mood_{video_id}"],
                                   button[key^="vc_edit_{video_id}"],
                                   button[key^="vc_save_{video_id}"],
                                   button[key^="vc_delete_{video_id}"]) button:hover {{
        border-color: #1f77b4 !important;
        background-color: rgba(31, 119, 180, 0.1) !important;
    }}
    
    /* 삭제 버튼 특별 스타일 */
    button[key^="delete_{video_id}"]:not([data-testid*="secondary"]) {{
        border-color: #ff4444 !important;
        color: #ff4444 !important;
    }}
    
    button[key^="delete_{video_id}"]:not([data-testid*="secondary"]):hover {{
        background-color: rgba(255, 68, 68, 0.1) !important;
    }}
    </style>
    """, unsafe_allow_html=True)
    
    # 다운로드 버튼 - 향상된 로직
    render_download_button(video_id, video)

    # 무드보드 버튼
    if st.button("🎨 무드보드", key=f"vc_mood_{video_id}", help="무드보드", use_container_width=True):
        st.session_state.show_moodboard_modal = True
        st.session_state.moodboard_video_id = video_id
        st.rerun()
    
    # 편집/저장 버튼
    is_edit_mode = st.session_state.get('edit_mode') == video_id
    if is_edit_mode:
        # 저장 버튼
        if st.button("✅ 완료", key=f"vc_save_{video_id}", help="저장", use_container_width=True):
            from ui.tabs.database_edit import save_edited_data
            if save_edited_data(video_id):
                st.success("✅ 저장되었습니다!")
                st.session_state.edit_mode = None
                st.rerun()
    else:
        # 편집 버튼
        if st.button("✏️ 수정", key=f"vc_edit_{video_id}", help="수정", use_container_width=True):
            from ui.tabs.database_edit import toggle_edit_mode
            toggle_edit_mode(video_id)
            st.rerun()
    
    # 삭제 버튼 - 두 번 클릭 방식
    try:
        from ui.tabs.database_delete import delete_manager, get_delete_button_text, get_delete_button_type
        
        button_text = get_delete_button_text(video_id)
        button_type = get_delete_button_type(video_id)
        
        # 라벨 추가
        if button_text == "❌":
            button_label = "❌ 확인"
        else:
            button_label = "🗑️ 삭제"
        
        if st.button(
            button_label, 
            key=f"vc_delete_{video_id}", 
            help="삭제 (한 번 더 클릭하면 삭제)" if button_text == "❌" else "삭제",
            type=button_type if button_text == "❌" else "secondary",
            use_container_width=True
        ):
            # 삭제 핸들러 호출
            if delete_manager.handle_delete_button(video_id):
                # 두 번째 클릭 - 실제 삭제 실행
                with st.spinner(f"..."):
                    success, message = delete_manager.delete_video_complete(
                        video_id, 
                        delete_notion=True,  # Notion에서도 삭제
                        delete_files=False   # 파일은 보존
                    )
                    
                    if success:
                        st.success(f"✅ {message}")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
            else:
                # 첫 번째 클릭 - 상태만 변경되고 rerun으로 버튼 텍스트 변경
                st.rerun()
                
    except ImportError as e:
        # database_delete 모듈이 없는 경우 기존 방식으로 fallback
        if st.button("🗑️ 삭제", key=f"delete_{video_id}", help="삭제", use_container_width=True):
            st.session_state.delete_target = video_id
            st.session_state.show_delete_single = True
            st.rerun()


def render_download_button(video_id: str, video: Dict[str, Any]):
    """다운로드 버튼 렌더링 - 향상된 로직"""
    base_url = "https://sof.greatminds.kr"
    
    # 비디오 제목 가져오기
    video_title = video.get('title', 'video')
    
    # 파일명 생성
    sanitized_title = sanitize_filename(video_title)
    video_filename = f"{video_id}_{sanitized_title}.mp4"
    encoded_filename = urllib.parse.quote(video_filename)
    video_url = f"{base_url}/{video_id}/{encoded_filename}"
    download_filename = f"{sanitized_title}_{video_id}.mp4"
    
    # 다운로드 상태 관리 (각 비디오별)
    download_state_key = f'download_state_{video_id}'
    video_content_key = f'video_content_{video_id}'
    
    if download_state_key not in st.session_state:
        st.session_state[download_state_key] = 'idle'  # idle, loading, ready
    if video_content_key not in st.session_state:
        st.session_state[video_content_key] = None
    
    # 버튼 텍스트 결정
    if st.session_state[download_state_key] == 'idle':
        button_text = "💾 저장"
    elif st.session_state[download_state_key] == 'loading':
        button_text = "⏳ 준비중..."
    else:  # ready
        button_text = "📥 다시 눌러 저장"
    
    # 단일 버튼으로 처리
    if st.session_state[download_state_key] == 'ready' and st.session_state[video_content_key]:
        # 다운로드 준비 완료 상태 - download_button 표시
        st.download_button(
            label=button_text,
            data=st.session_state[video_content_key],
            file_name=download_filename,
            mime="video/mp4",
            key=f"vc_download_video_final_{video_id}",
            use_container_width=True,
            on_click=lambda: (
                setattr(st.session_state, download_state_key, 'idle'),
                setattr(st.session_state, video_content_key, None)
            )
        )
    else:
        # 일반 버튼
        if st.button(button_text, 
                    use_container_width=True, 
                    key=f"vc_download_{video_id}",
                    disabled=(st.session_state[download_state_key] == 'loading')):
            if st.session_state[download_state_key] == 'idle':
                # 다운로드 시작
                st.session_state[download_state_key] = 'loading'
                st.rerun()
    
    # 로딩 중일 때 처리
    if st.session_state[download_state_key] == 'loading':
        try:
            with st.spinner("비디오 다운로드 준비 중..."):
                response = requests.get(video_url, stream=True)
                response.raise_for_status()
                st.session_state[video_content_key] = response.content
                st.session_state[download_state_key] = 'ready'
                st.rerun()
        except Exception as e:
            st.error(f"다운로드 준비 실패: {str(e)}")
            logger.error(f"다운로드 실패 - URL: {video_url}, Error: {str(e)}")
            st.session_state[download_state_key] = 'idle'
            st.session_state[video_content_key] = None