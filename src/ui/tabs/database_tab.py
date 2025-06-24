# src/ui/tabs/database_tab.py
"""
Database 탭 - 영상 데이터베이스 관리
"""

import streamlit as st
from typing import List, Dict, Any
from datetime import datetime
import time
from storage.db_manager import VideoAnalysisDB
from utils.logger import get_logger

logger = get_logger(__name__)


def render_database_tab():
    """Database 탭 렌더링"""
    # 검색 및 필터 섹션
    render_search_section()
    
    # 비디오 카드 목록
    render_video_cards()
    
    # 무드보드 모달
    if st.session_state.get('show_moodboard_modal'):
        render_moodboard_modal()


def render_search_section():
    """검색 및 필터 섹션"""
    st.markdown("### 🔍 검색 및 필터")
    
    col1, col2, col3 = st.columns([3, 1, 1])
    
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
        if st.button("🗑️ 선택 삭제", type="secondary", use_container_width=True):
            if st.session_state.get('selected_videos'):
                st.session_state.show_delete_confirm = True
            else:
                st.warning("선택된 항목이 없습니다")
    
    with col3:
        if st.button("🔄 새로고침", use_container_width=True):
            st.rerun()
    
    # 태그 필터
    render_tag_filter()
    
    # 삭제 확인 다이얼로그
    if st.session_state.get('show_delete_confirm'):
        render_delete_confirmation()


def render_tag_filter():
    """태그 필터"""
    db = VideoAnalysisDB()
    
    # 모든 태그 수집
    all_tags = set()
    all_videos = db.videos_table.all()
    
    for video in all_videos:
        # YouTube 태그
        if video.get('tags'):
            all_tags.update(video['tags'])
        
        # AI 분석 태그
        analysis = db.get_latest_analysis(video.get('video_id'))
        if analysis and analysis.get('tags'):
            all_tags.update(analysis['tags'])
    
    db.close()
    
    if all_tags:
        with st.expander("🏷️ 태그 필터", expanded=False):
            # 태그를 알파벳 순으로 정렬
            sorted_tags = sorted(list(all_tags))
            
            # 선택된 태그 관리
            if 'selected_tags' not in st.session_state:
                st.session_state.selected_tags = []
            
            # 태그 체크박스 (3열로 표시)
            cols = st.columns(3)
            for i, tag in enumerate(sorted_tags[:30]):  # 최대 30개만 표시
                with cols[i % 3]:
                    if st.checkbox(tag, key=f"tag_{tag}"):
                        if tag not in st.session_state.selected_tags:
                            st.session_state.selected_tags.append(tag)
                    else:
                        if tag in st.session_state.selected_tags:
                            st.session_state.selected_tags.remove(tag)


def render_video_cards():
    """비디오 카드 목록"""
    # 데이터 가져오기
    videos = get_filtered_videos()
    
    if not videos:
        st.info("검색 결과가 없습니다")
        return
    
    # 페이지네이션 설정
    if 'db_page' not in st.session_state:
        st.session_state.db_page = 1
    
    items_per_page = 10
    total_pages = (len(videos) + items_per_page - 1) // items_per_page
    current_page = st.session_state.db_page
    
    # 현재 페이지의 비디오들
    start_idx = (current_page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    page_videos = videos[start_idx:end_idx]
    
    # 통계 표시
    st.markdown(f"### 📹 영상 목록 (총 {len(videos)}개)")
    
    # 전체 선택 체크박스
    col1, col2 = st.columns([1, 10])
    with col1:
        select_all = st.checkbox("전체", key="select_all_db")
        if select_all:
            for video in page_videos:
                if video['video_id'] not in st.session_state.get('selected_videos', []):
                    if 'selected_videos' not in st.session_state:
                        st.session_state.selected_videos = []
                    st.session_state.selected_videos.append(video['video_id'])
    
    # 비디오 카드 렌더링
    for video in page_videos:
        render_single_video_card(video)
    
    # 무한 스크롤 시뮬레이션 (더 보기 버튼)
    if end_idx < len(videos):
        if st.button("🔽 더 보기", use_container_width=True):
            st.session_state.db_page += 1
            st.rerun()


def render_single_video_card(video: Dict[str, Any]):
    """단일 비디오 카드"""
    video_id = video.get('video_id', 'unknown')
    
    # 선택 상태 확인
    if 'selected_videos' not in st.session_state:
        st.session_state.selected_videos = []
    
    is_selected = video_id in st.session_state.selected_videos
    
    # 카드 컨테이너
    card_class = "video-card selected" if is_selected else "video-card"
    
    with st.container():
        st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
        
        col1, col2, col3, col4, col5 = st.columns([0.5, 1.5, 3, 2, 1.5])
        
        # 체크박스
        with col1:
            if st.checkbox("", value=is_selected, key=f"select_{video_id}"):
                if video_id not in st.session_state.selected_videos:
                    st.session_state.selected_videos.append(video_id)
            else:
                if video_id in st.session_state.selected_videos:
                    st.session_state.selected_videos.remove(video_id)
        
        # 썸네일 (임시)
        with col2:
            st.markdown("""
            <div style="width: 120px; height: 80px; background: #444; 
                        border-radius: 8px; display: flex; align-items: center; 
                        justify-content: center; color: #888;">
                📹
            </div>
            """, unsafe_allow_html=True)
        
        # 정보
        with col3:
            title = video.get('title', 'Unknown')[:50]
            if len(video.get('title', '')) > 50:
                title += "..."
            
            st.markdown(f"**{title}**")
            
            # 메타 정보
            uploader = video.get('uploader', 'Unknown')
            duration = video.get('duration', 0)
            duration_str = f"{duration//60}:{duration%60:02d}"
            
            st.caption(f"👤 {uploader} • ⏱️ {duration_str}")
            
            # 분석 정보
            analysis = video.get('analysis_result')
            if analysis:
                genre = analysis.get('genre', 'Unknown')
                mood = analysis.get('mood_tone', 'Unknown')
                st.write(f"🎬 {genre} • 🎭 {mood}")
        
        # 태그
        with col4:
            if analysis and analysis.get('tags'):
                tags_html = '<div class="tag-container">'
                for tag in analysis['tags'][:5]:
                    tags_html += f'<span class="tag">#{tag}</span>'
                if len(analysis['tags']) > 5:
                    tags_html += f'<span class="tag">+{len(analysis["tags"])-5}</span>'
                tags_html += '</div>'
                st.markdown(tags_html, unsafe_allow_html=True)
        
        # 액션 버튼
        with col5:
            render_card_actions(video_id, video)
        
        st.markdown('</div>', unsafe_allow_html=True)


def render_card_actions(video_id: str, video: Dict[str, Any]):
    """카드 액션 버튼들"""
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("💾", key=f"download_{video_id}", help="다운로드"):
            st.info("다운로드 기능 준비 중...")
    
    with col2:
        if st.button("🎨", key=f"mood_{video_id}", help="무드보드"):
            st.session_state.show_moodboard_modal = True
            st.session_state.moodboard_video_id = video_id
            st.rerun()
    
    with col3:
        if st.button("🔄", key=f"reanalyze_{video_id}", help="재추론"):
            st.info("재추론 기능 준비 중...")
    
    with col4:
        if st.button("✏️", key=f"edit_{video_id}", help="수정"):
            st.session_state.edit_mode = video_id
            st.rerun()
    
    with col5:
        if st.button("🗑️", key=f"delete_{video_id}", help="삭제"):
            st.session_state.delete_target = video_id
            st.session_state.show_delete_single = True
            st.rerun()


def get_filtered_videos() -> List[Dict[str, Any]]:
    """필터링된 비디오 목록 가져오기"""
    db = VideoAnalysisDB()
    
    try:
        # 모든 비디오 가져오기
        all_videos = db.videos_table.all()
        
        # 분석 결과 추가
        for video in all_videos:
            analysis = db.get_latest_analysis(video.get('video_id'))
            if analysis:
                video['analysis_result'] = analysis
        
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
        
    finally:
        db.close()


def render_delete_confirmation():
    """삭제 확인 다이얼로그"""
    if st.session_state.get('show_delete_confirm'):
        st.warning(f"⚠️ 선택된 {len(st.session_state.selected_videos)}개 항목을 삭제하시겠습니까?")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ 삭제", type="primary"):
                # TODO: 실제 삭제 구현
                st.success("삭제되었습니다")
                st.session_state.selected_videos = []
                st.session_state.show_delete_confirm = False
                st.rerun()
        
        with col2:
            if st.button("❌ 취소"):
                st.session_state.show_delete_confirm = False
                st.rerun()


def render_moodboard_modal():
    """무드보드 모달"""
    video_id = st.session_state.get('moodboard_video_id')
    
    # 모달 스타일 적용
    st.markdown("""
    <div class="modal-overlay">
        <div class="modal-content">
    """, unsafe_allow_html=True)
    
    # 헤더
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"### 🎨 무드보드 - {video_id}")
    with col2:
        if st.button("✖️ 닫기"):
            st.session_state.show_moodboard_modal = False
            st.session_state.moodboard_video_id = None
            st.rerun()
    
    # 이미지 그리드 (임시)
    st.markdown('<div class="image-grid">', unsafe_allow_html=True)
    
    # 더미 이미지들
    cols = st.columns(4)
    for i in range(12):
        with cols[i % 4]:
            st.markdown(f"""
            <div class="grid-image">
                <div style="width: 100%; height: 100%; background: #555; 
                            display: flex; align-items: center; justify-content: center;">
                    Scene {i+1}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 액션 버튼
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 선택 이미지로 재추론", disabled=True):
            st.info("재추론 기능 준비 중...")
    
    with col2:
        if st.button("💾 선택 이미지 다운로드", disabled=True):
            st.info("다운로드 기능 준비 중...")
    
    st.markdown("</div></div>", unsafe_allow_html=True)