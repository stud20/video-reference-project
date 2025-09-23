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
from integrations.notion.sync_service import NotionSyncService
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

    col1, col2, col3 = st.columns([4, 1, 1])  # 3개 칼럼으로 변경

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

    with col3:
        if st.button("📤 Notion 동기화", use_container_width=True, type="primary"):
            st.session_state.show_notion_sync = True


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

    # Notion 동기화 모달
    if st.session_state.get('show_notion_sync'):
        render_notion_sync_modal()

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


def render_notion_sync_modal():
    """Notion 동기화 모달"""
    with st.container():
        st.markdown("### 📤 Notion 동기화")
        st.markdown("---")

        # 동기화 시작 전 상태
        if 'sync_in_progress' not in st.session_state:
            st.session_state.sync_in_progress = False
            st.session_state.sync_completed = False

        if not st.session_state.sync_in_progress and not st.session_state.sync_completed:
            # 동기화 전 안내
            st.info("""
            **데이터베이스와 Notion 동기화**

            이 기능은 로컬 데이터베이스에 있지만 Notion에 없는 항목을 찾아서 업로드합니다.

            동기화 작업:
            - ✅ 누락된 항목 검색
            - ✅ 중복 항목 체크
            - ✅ 새 항목 Notion에 추가
            """)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🚀 동기화 시작", type="primary", key="start_sync"):
                    st.session_state.sync_in_progress = True
                    st.rerun()

            with col2:
                if st.button("❌ 취소", key="cancel_sync"):
                    st.session_state.show_notion_sync = False
                    st.rerun()

        elif st.session_state.sync_in_progress:
            # 동기화 진행 중
            with st.spinner("Notion과 동기화 중..."):
                sync_service = NotionSyncService()

                # 1단계: 분석
                with st.status("동기화 분석 중...", expanded=True) as status:
                    missing_items, duplicate_ids, stats = sync_service.find_missing_items()

                    st.write(f"📊 로컬 DB 항목: {stats.get('total_local', 0)}개")
                    st.write(f"📊 Notion 항목: {stats.get('total_notion', 0)}개")
                    st.write(f"🔍 누락 항목: {stats.get('missing_count', 0)}개")
                    st.write(f"⚠️ 중복 항목: {stats.get('duplicate_count', 0)}개")

                    if duplicate_ids:
                        st.warning(f"중복된 비디오 ID: {', '.join(duplicate_ids[:5])}")

                    status.update(label="분석 완료!", state="complete")

                # 2단계: 동기화
                if missing_items:
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    def update_progress(current, total, title):
                        progress = current / total if total > 0 else 0
                        progress_bar.progress(progress)
                        status_text.text(f"처리 중 ({current}/{total}): {title[:50]}...")

                    success_count, fail_count, errors = sync_service.sync_missing_items(
                        missing_items,
                        progress_callback=update_progress
                    )

                    # 결과 저장
                    st.session_state.sync_result = {
                        'success_count': success_count,
                        'fail_count': fail_count,
                        'errors': errors,
                        'stats': stats
                    }
                else:
                    st.session_state.sync_result = {
                        'success_count': 0,
                        'fail_count': 0,
                        'errors': [],
                        'stats': stats
                    }

                st.session_state.sync_in_progress = False
                st.session_state.sync_completed = True
                st.rerun()

        elif st.session_state.sync_completed:
            # 동기화 완료
            result = st.session_state.get('sync_result', {})

            if result.get('success_count', 0) > 0:
                st.success(f"✅ {result['success_count']}개 항목을 Notion에 동기화했습니다!")
            elif result.get('stats', {}).get('missing_count', 0) == 0:
                st.success("✅ 모든 항목이 이미 동기화되어 있습니다!")

            if result.get('fail_count', 0) > 0:
                st.error(f"❌ {result['fail_count']}개 항목 동기화 실패")
                if result.get('errors'):
                    with st.expander("오류 상세"):
                        for error in result['errors'][:10]:  # 최대 10개만 표시
                            st.write(f"• {error}")

            # 통계 표시
            stats = result.get('stats', {})
            if stats:
                st.markdown("### 📊 동기화 통계")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("로컬 DB", stats.get('total_local', 0))
                with col2:
                    st.metric("Notion", stats.get('total_notion', 0))
                with col3:
                    st.metric("동기화 완료", result.get('success_count', 0))

            if st.button("✅ 확인", key="confirm_sync_result"):
                # 상태 초기화
                st.session_state.sync_in_progress = False
                st.session_state.sync_completed = False
                st.session_state.show_notion_sync = False
                if 'sync_result' in st.session_state:
                    del st.session_state.sync_result
                st.rerun()
