import streamlit as st
import os
from typing import Dict, Any, List
from storage.db_manager import VideoAnalysisDB
from utils.logger import get_logger
from ui.tabs.database_edit import render_editable_card_info, save_edited_data, toggle_edit_mode
from streamlit_extras.stylable_container import stylable_container
import time  # 여기에 추가

logger = get_logger(__name__)


def render_video_cards_section(videos: List[Dict[str, Any]], items_per_page: int = 10):
    """비디오 카드 섹션 전체 렌더링"""
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
    
    # 통계 표시
    st.markdown(f"### 📹 영상 목록 (총 {len(videos)}개)")
    
    # 텍스트 영역 패딩 줄이기 위한 CSS
    st.markdown("""
        <style>
        .stTextArea > div > div > textarea {
            padding: 0.5rem;
        }
        .stTextInput > div > div > input {
            padding: 0.5rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # 전체 선택 체크박스
    render_select_all_checkbox(page_videos)
    
    # 비디오 카드 렌더링
    for video in page_videos:
        render_single_video_card(video)
    
    # 무한 스크롤 시뮬레이션 (더 보기 버튼)
    if end_idx < len(videos):
        if st.button("🔽 더 보기", use_container_width=True, key="load_more_videos"):
            st.session_state.db_page += 1
            st.rerun()


def render_select_all_checkbox(page_videos: List[Dict[str, Any]]):
    """전체 선택 체크박스"""
    col1, col2 = st.columns([1, 10])
    with col1:
        # 현재 페이지의 모든 비디오가 선택되었는지 확인
        all_selected = all(
            video['video_id'] in st.session_state.get('selected_videos', [])
            for video in page_videos
        )
        
        select_all = st.checkbox("전체", value=all_selected, key="select_all_db")
        
        if select_all:
            # 현재 페이지의 모든 비디오 선택
            if 'selected_videos' not in st.session_state:
                st.session_state.selected_videos = []
            
            for video in page_videos:
                if video['video_id'] not in st.session_state.selected_videos:
                    st.session_state.selected_videos.append(video['video_id'])
        else:
            # 현재 페이지의 모든 비디오 선택 해제
            if 'selected_videos' in st.session_state:
                for video in page_videos:
                    if video['video_id'] in st.session_state.selected_videos:
                        st.session_state.selected_videos.remove(video['video_id'])


def render_single_video_card(video: Dict[str, Any]):
    """단일 비디오 카드 렌더링"""
    video_id = video.get('video_id', 'unknown')
    
    # 선택 상태 확인
    if 'selected_videos' not in st.session_state:
        st.session_state.selected_videos = []
    
    is_selected = video_id in st.session_state.selected_videos
    
    # 편집 모드 확인
    is_edit_mode = st.session_state.get('edit_mode') == video_id
    
    # 선택 상태에 따른 스타일 정의
    if is_selected:
        card_style = """
        {
            border: 1px solid #2196f3;
            border-radius: 10px;
            padding: 1.5rem 1rem 3rem 1rem;
            margin-bottom: 1rem;
        }
        """
    else:
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
        # 카드 내용 - 칼럼 비율 조정
        col1, col2, col3, col4, col5 = st.columns([0.2, 1.5, 5, 1.5, 0.3])
        
        # 체크박스
        with col1:
            if st.checkbox("", value=is_selected, key=f"select_{video_id}", label_visibility="collapsed"):
                if video_id not in st.session_state.selected_videos:
                    st.session_state.selected_videos.append(video_id)
                    st.rerun()
            else:
                if video_id in st.session_state.selected_videos:
                    st.session_state.selected_videos.remove(video_id)
                    st.rerun()
        
        # 썸네일
        with col2:
            render_thumbnail(video)
        
        # 정보 - 편집 모드 확인
        with col3:
            if is_edit_mode:
                render_editable_card_info(video)
            else:
                render_video_info(video)
        
        # 태그
        with col4:
            if not is_edit_mode:  # 편집 모드가 아닐 때만 태그 표시
                render_video_tags(video)
            else:
                st.write("")  # 편집 모드일 때는 빈 공간
        
        # 액션 버튼
        with col5:
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
            # 모든 이미지 로드 실패 시 기본 아이콘 표시
            st.markdown("""
            <div style="width: 100%; height: 80px; background: #444; 
                        border-radius: 8px; display: flex; align-items: center; 
                        justify-content: center; color: #888; font-size: 24px;">
                📹
            </div>
            """, unsafe_allow_html=True)
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
                height=100,
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
                height=100,
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
                height=70,
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
                height=70,
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
        tags_html = '<div style="display: flex; flex-wrap: wrap; gap: 4px; max-height: 120px; overflow-y: auto;">'
        
        # YouTube 태그 (파란색) - 전체 표시
        for tag in youtube_tags:
            if tag and len(tag) > 1:
                tags_html += f'<span style="background-color: #007ACC; color: white; padding: 2px 6px; border-radius: 10px; font-size: 11px; white-space: nowrap;">#{tag}</span>'
        
        # AI 태그 (초록색) - 전체 표시
        for tag in ai_tags:
            if tag and tag not in youtube_tags:
                tags_html += f'<span style="background-color: #28a745; color: white; padding: 2px 6px; border-radius: 10px; font-size: 11px; white-space: nowrap;">#{tag}</span>'
        
        tags_html += '</div>'
        st.markdown(tags_html, unsafe_allow_html=True)
    else:
        st.caption("태그 없음")

def render_card_actions(video_id: str, video: Dict[str, Any]):
    """카드 액션 버튼들 - 세로 배치"""
    # 다운로드 버튼
    if st.button("💾", key=f"download_{video_id}", help="다운로드", use_container_width=True):
        from ui.tabs.database_download import handle_video_download
        handle_video_download(video_id, video)
    
    # 무드보드 버튼
    if st.button("🎨", key=f"mood_{video_id}", help="무드보드", use_container_width=True):
        st.session_state.show_moodboard_modal = True
        st.session_state.moodboard_video_id = video_id
        st.rerun()
    
    # 편집/저장 버튼
    is_edit_mode = st.session_state.get('edit_mode') == video_id
    if is_edit_mode:
        # 저장 버튼
        if st.button("💾", key=f"save_{video_id}", help="저장", type="primary", use_container_width=True):
            from ui.tabs.database_edit import save_edited_data
            if save_edited_data(video_id):
                st.success("✅ 저장되었습니다!")
                st.session_state.edit_mode = None
                st.rerun()
    else:
        # 편집 버튼
        if st.button("✏️", key=f"edit_{video_id}", help="수정", use_container_width=True):
            from ui.tabs.database_edit import toggle_edit_mode
            toggle_edit_mode(video_id)
            st.rerun()
    
    # 삭제 버튼 - 두 번 클릭 방식
    try:
        from ui.tabs.database_delete import delete_manager, get_delete_button_text, get_delete_button_type
        
        button_text = get_delete_button_text(video_id)
        button_type = get_delete_button_type(video_id)
        
        if st.button(
            button_text, 
            key=f"delete_{video_id}", 
            help="삭제 (한 번 더 클릭하면 삭제)" if button_text == "❌" else "삭제",
            type=button_type,
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
                        # 선택 목록에서 제거
                        if video_id in st.session_state.get('selected_videos', []):
                            st.session_state.selected_videos.remove(video_id)
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
            else:
                # 첫 번째 클릭 - 상태만 변경되고 rerun으로 버튼 텍스트 변경
                st.rerun()
                
    except ImportError as e:
        # database_delete 모듈이 없는 경우 기존 방식으로 fallback
        if st.button("🗑️", key=f"delete_{video_id}", help="삭제", use_container_width=True):
            st.session_state.delete_target = video_id
            st.session_state.show_delete_single = True
            st.rerun()