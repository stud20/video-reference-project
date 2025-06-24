# src/ui/components/database_modal.py
"""
데이터베이스 관리 모달 컴포넌트
"""

import streamlit as st
from datetime import datetime
from typing import List, Dict, Any
from storage.db_manager import VideoAnalysisDB
from handlers.db_handler import (
    get_filtered_videos, 
    delete_video_with_confirmation,
    bulk_delete_videos,
    update_video_info,
    update_analysis_result,
    delete_analysis_results,
    export_selected_videos,
    trigger_reanalysis,
    bulk_reanalyze_videos
)
from ui.components.video_cards import render_video_card
from utils.constants import FILTER_OPTIONS, GENRES
from utils.logger import get_logger
from services.notion_service import NotionService

logger = get_logger(__name__)


def render_database_modal():
    """데이터베이스 모달 렌더링"""
    if not st.session_state.get('show_db_modal', False):
        return
    
    db = VideoAnalysisDB()
    
    # 삭제 확인 처리
    handle_delete_confirmation()
    
    # 상세보기 처리
    handle_video_details_display()
    
    # 모달 헤더
    render_modal_header()
    
    # 필터 및 검색 영역
    db_filter, db_search, items_per_page = render_filter_section()
    
    # 데이터 가져오기 및 필터링
    videos = get_filtered_videos(db, db_filter, db_search)
    
    # 통계 정보
    render_statistics(db, videos)
    
    # 일괄 작업 버튼
    if st.session_state.selected_videos:
        render_bulk_actions()
    
    # 페이지네이션 계산
    current_page, page_videos = calculate_pagination(videos, items_per_page)
    
    # 영상 목록 표시
    render_video_list(page_videos)
    
    # 페이지네이션 렌더링
    if len(videos) > items_per_page:
        render_pagination(current_page, len(videos), items_per_page)
    
    # 편집 모달
    if st.session_state.get('edit_video_id'):
        render_edit_modal(db)
    
    db.close()


def render_modal_header():
    """모달 헤더 렌더링"""
    with st.container():
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown("""
            <div class="db-header">
                <h2>📊 데이터베이스 관리자</h2>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            if st.button("✖️ 닫기", key="close_db_modal"):
                st.session_state.show_db_modal = False
                if 'confirm_delete' in st.session_state:
                    st.session_state.confirm_delete = None
                if 'show_video_details' in st.session_state:
                    st.session_state.show_video_details = None
                st.rerun()


def render_filter_section():
    """필터 및 검색 섹션 렌더링"""
    st.markdown("### 🔍 필터 및 검색")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        db_filter = st.selectbox(
            "필터",
            list(FILTER_OPTIONS.keys()),
            format_func=lambda x: FILTER_OPTIONS[x],
            key="db_filter_select"
        )
    
    with col2:
        db_search = st.text_input("검색 (제목, 장르, 태그)", key="db_search_input")
    
    with col3:
        items_per_page = st.selectbox("페이지당 항목", [5, 10, 20, 50], index=1, key="items_per_page")
    
    with col4:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 새로고침", key="refresh_db"):
            st.rerun()
    
    return db_filter, db_search, items_per_page


def render_statistics(db: VideoAnalysisDB, videos: List[Dict[str, Any]]):
    """통계 정보 렌더링"""
    stats = db.get_statistics()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("총 영상", stats['total_videos'])
    with col2:
        st.metric("AI 분석 완료", len([v for v in videos if v.get('analysis_result')]))
    with col3:
        st.metric("검색 결과", len(videos))
    with col4:
        st.metric("선택된 항목", len(st.session_state.selected_videos))


def render_bulk_actions():
    """일괄 작업 버튼 렌더링"""
    st.markdown("### ⚡ 일괄 작업")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("🗑️ 선택 항목 삭제", key="bulk_delete", type="secondary"):
            show_bulk_delete_confirmation()
    
    with col2:
        if st.button("📤 선택 항목 내보내기", key="bulk_export"):
            try:
                export_path = export_selected_videos(st.session_state.selected_videos)
                st.success(f"✅ {len(st.session_state.selected_videos)}개 영상이 내보내기되었습니다!")
                st.info(f"📁 파일 위치: {export_path}")
            except Exception as e:
                st.error(f"내보내기 실패: {str(e)}")
    
    with col3:
        if st.button("🔄 선택 항목 재분석", key="bulk_reanalyze"):
            show_bulk_reanalyze_dialog()
    
    with col4:
        if st.button("📝 Notion 업로드", key="bulk_notion", type="primary"):
            show_bulk_notion_upload()
    
    with col5:
        if st.button("❌ 선택 해제", key="clear_selection"):
            st.session_state.selected_videos = []
            st.rerun()


def calculate_pagination(videos: List[Dict[str, Any]], items_per_page: int):
    """페이지네이션 계산"""
    total_pages = (len(videos) + items_per_page - 1) // items_per_page
    current_page = st.session_state.get('db_page', 1)
    
    if current_page > total_pages and total_pages > 0:
        st.session_state.db_page = total_pages
        current_page = total_pages
    
    start_idx = (current_page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    page_videos = videos[start_idx:end_idx]
    
    return current_page, page_videos


def render_video_list(page_videos: List[Dict[str, Any]]):
    """영상 목록 렌더링"""
    st.markdown("### 📹 영상 목록")
    
    if not page_videos:
        st.info("검색 조건에 맞는 영상이 없습니다.")
    else:
        # 전체 선택/해제 체크박스
        col1, col2 = st.columns([1, 10])
        with col1:
            select_all = st.checkbox(
                "전체", 
                key="select_all_videos",
                label_visibility="visible"
            )
            if select_all:
                st.session_state.selected_videos = [v['video_id'] for v in page_videos]
            elif not select_all and st.session_state.get('was_select_all', False):
                st.session_state.selected_videos = []
            st.session_state.was_select_all = select_all
        
        # 영상 카드들
        for video in page_videos:
            render_video_card(video)


def render_pagination(current_page: int, total_items: int, items_per_page: int):
    """페이지네이션 렌더링"""
    total_pages = (total_items + items_per_page - 1) // items_per_page
    
    st.markdown("### 📄 페이지")
    
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col1:
        if current_page > 1:
            if st.button("◀️ 이전", key="prev_page"):
                st.session_state.db_page = current_page - 1
                st.rerun()
    
    with col2:
        # 페이지 번호 버튼들
        cols = st.columns(min(7, total_pages))
        
        start_page = max(1, current_page - 3)
        end_page = min(total_pages, start_page + 6)
        
        for i, page in enumerate(range(start_page, end_page + 1)):
            with cols[i]:
                if page == current_page:
                    st.markdown(f"**{page}**")
                else:
                    if st.button(str(page), key=f"page_{page}"):
                        st.session_state.db_page = page
                        st.rerun()
    
    with col3:
        if current_page < total_pages:
            if st.button("다음 ▶️", key="next_page"):
                st.session_state.db_page = current_page + 1
                st.rerun()
    
    st.caption(f"페이지 {current_page} / {total_pages}")


def handle_delete_confirmation():
    """삭제 확인 처리"""
    if 'confirm_delete' in st.session_state and st.session_state.confirm_delete:
        video_id = st.session_state.confirm_delete
        
        with st.container():
            st.warning(f"⚠️ 영상 {video_id}를 정말 삭제하시겠습니까?")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🗑️ 삭제 확인", key=f"confirm_delete_yes_{video_id}", type="secondary"):
                    success = delete_video_with_confirmation(video_id)
                    
                    if success:
                        st.success("✅ 삭제되었습니다!")
                        if video_id in st.session_state.selected_videos:
                            st.session_state.selected_videos.remove(video_id)
                    else:
                        st.error("❌ 삭제 중 오류가 발생했습니다.")
                    
                    st.session_state.confirm_delete = None
                    st.rerun()
            
            with col2:
                if st.button("❌ 취소", key=f"confirm_delete_no_{video_id}"):
                    st.session_state.confirm_delete = None
                    st.rerun()


def handle_video_details_display():
    """비디오 상세 정보 표시"""
    if 'show_video_details' in st.session_state and st.session_state.show_video_details:
        video_id = st.session_state.show_video_details
        
        db = VideoAnalysisDB()
        video = db.get_video_info(video_id)
        
        if video:
            analysis = db.get_latest_analysis(video_id)
            if analysis:
                video['analysis_result'] = analysis
            
            from ui.components.analysis_display import show_video_details
            show_video_details(video)
        
        db.close()
        
        if st.button("닫기", key="close_video_details"):
            st.session_state.show_video_details = None
            st.rerun()


def show_bulk_delete_confirmation():
    """일괄 삭제 확인"""
    count = len(st.session_state.selected_videos)
    st.warning(f"⚠️ 선택된 {count}개 영상을 정말 삭제하시겠습니까?")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ 일괄 삭제", key="confirm_bulk_delete", type="secondary"):
            success_count, fail_count = bulk_delete_videos(st.session_state.selected_videos)
            
            st.session_state.selected_videos = []
            
            if fail_count > 0:
                st.warning(f"✅ {success_count}개 삭제 성공, ❌ {fail_count}개 실패")
            else:
                st.success(f"✅ {count}개 영상이 모두 삭제되었습니다!")
            
            st.rerun()
    
    with col2:
        if st.button("❌ 취소", key="cancel_bulk_delete"):
            st.rerun()


def show_bulk_reanalyze_dialog():
    """일괄 재분석 다이얼로그"""
    count = len(st.session_state.selected_videos)
    st.warning(f"⚠️ 선택된 {count}개 영상을 재분석하시겠습니까? 시간이 오래 걸릴 수 있습니다.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 일괄 재분석", key="confirm_bulk_reanalyze", type="primary"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            video_service = st.session_state.video_service
            
            for i, video_id in enumerate(st.session_state.selected_videos):
                status_text.text(f"재분석 중... ({i+1}/{count}) - {video_id}")
                progress_bar.progress((i + 1) / count)
            
            success_count, fail_count = bulk_reanalyze_videos(
                st.session_state.selected_videos, 
                video_service
            )
            
            st.session_state.selected_videos = []
            
            if fail_count > 0:
                st.warning(f"✅ {success_count}개 성공, ❌ {fail_count}개 실패")
            else:
                st.success(f"✅ {count}개 영상 재분석이 완료되었습니다!")
            st.rerun()
    
    with col2:
        if st.button("❌ 취소", key="cancel_bulk_reanalyze"):
            st.rerun()


def show_bulk_notion_upload():
    """Notion 일괄 업로드 다이얼로그"""
    count = len(st.session_state.selected_videos)
    
    # Notion 연결 체크
    try:
        notion = NotionService()
        if not notion.test_connection():
            st.error("❌ Notion 연결 실패! 환경변수를 확인해주세요.")
            st.info("필요한 환경변수: NOTION_API_KEY, NOTION_PARENT_PAGE_ID")
            return
    except ValueError as e:
        st.error(f"❌ {str(e)}")
        return
    except Exception as e:
        st.error(f"❌ Notion 서비스 초기화 실패: {str(e)}")
        return
    
    st.info(f"📝 선택된 {count}개 영상을 Notion 페이지에 추가합니다.")
    st.warning("⚠️ AI 분석이 완료된 영상만 업로드됩니다.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📤 Notion 업로드 시작", key="confirm_notion_upload", type="primary"):
            # 데이터 준비
            db = VideoAnalysisDB()
            videos_to_upload = []
            
            for video_id in st.session_state.selected_videos:
                video_data = db.get_video_info(video_id)
                if video_data:
                    analysis_data = db.get_latest_analysis(video_id)
                    if analysis_data:
                        videos_to_upload.append((video_data, analysis_data))
            
            db.close()
            
            if not videos_to_upload:
                st.warning("분석이 완료된 영상이 없습니다.")
                return
            
            # 업로드 진행
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            def update_progress(current, total, message):
                progress_bar.progress(current / total)
                status_text.text(message)
            
            # 일괄 업로드 (페이지에 추가)
            success_count, fail_count, errors = notion.bulk_add_to_database(
            videos_to_upload,
            progress_callback=update_progress
            )
            
            st.session_state.selected_videos = []
            
            # 결과 표시
            if fail_count > 0:
                st.warning(f"✅ {success_count}개 성공, ❌ {fail_count}개 실패")
                if errors:
                    with st.expander("오류 상세"):
                        for error in errors:
                            st.error(error)
            else:
                st.success(f"✅ {success_count}개 영상이 Notion에 업로드되었습니다!")
            
            st.rerun()
    
    with col2:
        if st.button("❌ 취소", key="cancel_notion_upload"):
            st.rerun()


def render_edit_modal(db: VideoAnalysisDB):
    """영상 편집 모달"""
    video_id = st.session_state.edit_video_id
    video_data = db.get_video_info(video_id)
    analysis_data = db.get_latest_analysis(video_id)
    
    if not video_data:
        st.error("영상 정보를 찾을 수 없습니다.")
        st.session_state.edit_video_id = None
        return
    
    st.markdown("### ✏️ 영상 정보 편집")
    
    with st.form(f"edit_form_{video_id}"):
        # 기본 정보 편집
        title = st.text_input("제목", value=video_data.get('title', ''))
        uploader = st.text_input("업로더", value=video_data.get('uploader', ''))
        description = st.text_input("설명", value=video_data.get('description', ''))
        
        # AI 분석 결과 편집 (있는 경우)
        if analysis_data:
            st.markdown("#### 🤖 AI 분석 결과 편집")
            
            genre = st.selectbox(
                "장르", 
                GENRES,
                index=GENRES.index(analysis_data['genre']) if analysis_data.get('genre') in GENRES else 0
            )
            
            reasoning = st.text_area("판단 이유", value=analysis_data.get('reasoning', ''), height=100)
            features = st.text_area("특징 및 특이사항", value=analysis_data.get('features', ''), height=100)
            
            tags_str = ', '.join(analysis_data.get('tags', []))
            tags = st.text_input("태그 (쉼표로 구분)", value=tags_str)
            
            mood_tone = st.text_input("분위기", value=analysis_data.get('mood_tone', ''))
            target_audience = st.text_input("타겟 고객층", value=analysis_data.get('target_audience', ''))
        
        # 버튼
        col1, col2, col3 = st.columns(3)
        with col1:
            submitted = st.form_submit_button("💾 저장", type="primary")
        with col2:
            if st.form_submit_button("❌ 취소"):
                st.session_state.edit_video_id = None
                st.rerun()
        with col3:
            if analysis_data and st.form_submit_button("🗑️ 분석결과 삭제"):
                if delete_analysis_results(video_id):
                    st.success("분석 결과가 삭제되었습니다.")
                st.session_state.edit_video_id = None
                st.rerun()
        
        if submitted:
            # 기본 정보 업데이트
            if update_video_info(video_id, title, uploader, description):
                # 분석 결과 업데이트 (있는 경우)
                if analysis_data:
                    updated_analysis = {
                        **analysis_data,
                        'genre': genre,
                        'reasoning': reasoning,
                        'features': features,
                        'tags': [tag.strip() for tag in tags.split(',') if tag.strip()],
                        'mood_tone': mood_tone,
                        'target_audience': target_audience
                    }
                    update_analysis_result(video_id, updated_analysis)
                
                st.success("✅ 저장되었습니다!")
            else:
                st.error("저장 중 오류가 발생했습니다.")
            
            st.session_state.edit_video_id = None
            st.rerun()