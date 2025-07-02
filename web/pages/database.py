# web/pages/database.py
"""
Database 탭 - 영상 데이터베이스 관리 (리팩토링)
"""

import streamlit as st
from typing import List, Dict, Any
from core.database.repository import VideoAnalysisDB as VideoDatabase
from utils.logger import get_logger

from web.components.database.video_card import render_video_cards_section
from web.components.database.delete import delete_manager
import time

logger = get_logger(__name__)


def render_database_tab():
    """Database 탭 메인 렌더링"""
    # 검색 및 필터 섹션
    render_search_section()
    
    # 필터링된 비디오 목록 가져오기
    videos = get_filtered_videos()
    
    # 비디오 카드 목록 렌더링
    render_video_cards_section(videos)
    
    # 모달 처리
    handle_modals()
    
    # 액션 처리
    handle_actions()


def render_search_section():
    st.markdown("### 🔍 검색 및 필터")
    
    col1, col2 = st.columns([4, 1])  # 2개 칼럼으로 변경
    
    with col1:
        # 실시간 검색
        search_query = st.text_input(
            "검색",
            placeholder="제목, 업로더, 태그, 장르 등...",
            key="db_search_input",
            label_visibility="collapsed"
        )
        
        # 검색 쿼리가 변경되면 자동으로 필터링
        if 'last_search_query' not in st.session_state:
            st.session_state.last_search_query = ""
        
        if search_query != st.session_state.last_search_query:
            st.session_state.last_search_query = search_query
            st.session_state.db_page = 1  # 검색 시 첫 페이지로
    
    with col2:
        if st.button("🔄 새로고침", use_container_width=True):
            st.rerun()


def get_filtered_videos() -> List[Dict[str, Any]]:
    db = VideoDatabase()
    
    try:
        # 모든 비디오 가져오기
        all_videos = db.get_all_videos()
        
        # 검색 필터
        search_query = st.session_state.get('db_search_input', '').lower()
        if search_query:
            filtered = []
            for video in all_videos:
                # 제목, 업로더, 장르, 태그에서 검색
                if (search_query in video.get('title', '').lower() or
                    search_query in video.get('uploader', '').lower() or
                    (video.get('analysis_result') and 
                     (search_query in video['analysis_result'].get('genre', '').lower() or
                      any(search_query in tag.lower() for tag in video['analysis_result'].get('tags', []))))):
                    filtered.append(video)
            all_videos = filtered
        
        # 태그 필터
        selected_tags = st.session_state.get('selected_tags', [])
        if selected_tags:
            filtered = []
            for video in all_videos:
                video_tags = []
                if video.get('tags'):
                    video_tags.extend(video['tags'])
                if video.get('analysis_result', {}).get('tags'):
                    video_tags.extend(video['analysis_result']['tags'])
                
                if any(tag in video_tags for tag in selected_tags):
                    filtered.append(video)
            all_videos = filtered
        
        # 최신순 정렬
        all_videos.sort(key=lambda x: x.get('download_date', ''), reverse=True)
        
        return all_videos
        
    except Exception as e:
        logger.error(f"Error getting filtered videos: {str(e)}")
        return []


def handle_modals():
    """모달 처리"""
    # 삭제 확인 다이얼로그
    if st.session_state.get('show_delete_confirm'):
        render_delete_confirmation()
    
    if st.session_state.get('show_delete_single'):
        render_single_delete_confirmation()
    
    # 무드보드는 video_card에서 인라인으로 처리되므로 여기서는 처리하지 않음


def handle_actions():
    """액션 처리"""
    # 비디오 다운로드
    if st.session_state.get('download_video_id'):
        video_id = st.session_state.download_video_id
        st.info(f"다운로드 기능 준비 중... (Video ID: {video_id})")
        del st.session_state.download_video_id
    
    # 재분석
    if st.session_state.get('reanalyze_video_id'):
        video_id = st.session_state.reanalyze_video_id
        st.info(f"재분석 기능 준비 중... (Video ID: {video_id})")
        del st.session_state.reanalyze_video_id
    
    # 선택된 이미지로 재분석
    if st.session_state.get('reanalyze_with_images'):
        st.info("선택된 이미지로 재분석 기능 준비 중...")
        del st.session_state.reanalyze_with_images
    
    # 선택된 이미지 다운로드
    if st.session_state.get('download_selected_images'):
        st.info("선택된 이미지 다운로드 기능 준비 중...")
        del st.session_state.download_selected_images


def render_delete_confirmation():
    """일괄 삭제 확인 다이얼로그"""
    selected_count = len(st.session_state.selected_videos)
    
    st.warning(f"⚠️ 선택된 {selected_count}개 항목을 삭제하시겠습니까?")
    
    # 삭제 옵션
    col1, col2 = st.columns(2)
    with col1:
        delete_notion = st.checkbox("Notion에서도 삭제", value=True, key="delete_notion_option")
    with col2:
        delete_files = st.checkbox("로컬 파일도 삭제", value=False, key="delete_files_option")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ 삭제", type="primary", key="confirm_bulk_delete"):
            # DeleteManager를 통한 일괄 삭제
            success_count, fail_count, errors = delete_manager.bulk_delete(
                st.session_state.selected_videos,
                delete_notion=delete_notion,
                delete_files=delete_files
            )
            
            if errors:
                st.error(f"❌ 일부 항목 삭제 실패:")
                for error in errors[:5]:  # 최대 5개까지만 표시
                    st.error(f"  • {error}")
                if len(errors) > 5:
                    st.error(f"  ... 외 {len(errors) - 5}개")
            
            if success_count > 0:
                st.success(f"✅ {success_count}개 항목 삭제 완료")
            
            st.session_state.selected_videos = []
            st.session_state.show_delete_confirm = False
            time.sleep(2)
            st.rerun()
    
    with col2:
        if st.button("❌ 취소", key="cancel_bulk_delete"):
            st.session_state.show_delete_confirm = False
            st.rerun()


def render_single_delete_confirmation():
    """단일 삭제 확인 다이얼로그"""
    video_id = st.session_state.get('delete_target')
    
    if video_id:
        st.warning(f"⚠️ 영상 {video_id}를 삭제하시겠습니까?")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ 삭제", type="primary", key="confirm_single_delete"):
                success, message = delete_manager.delete_video_complete(
                    video_id,
                    delete_notion=True,
                    delete_files=False
                )
                
                if success:
                    st.success("✅ 삭제되었습니다")
                    # 선택 목록에서도 제거
                    if video_id in st.session_state.get('selected_videos', []):
                        st.session_state.selected_videos.remove(video_id)
                else:
                    st.error(f"❌ 삭제 실패: {message}")
                
                st.session_state.delete_target = None
                st.session_state.show_delete_single = False
                time.sleep(1)
                st.rerun()
        
        with col2:
            if st.button("❌ 취소", key="cancel_single_delete"):
                st.session_state.delete_target = None
                st.session_state.show_delete_single = False
                st.rerun()
