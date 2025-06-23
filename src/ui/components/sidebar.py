# src/ui/components/sidebar.py
"""
사이드바 UI 컴포넌트
"""

import streamlit as st
import os
from storage.db_manager import VideoAnalysisDB
from utils.constants import PRECISION_DESCRIPTIONS, TIME_ESTIMATES, GENRES, VIDEO_QUALITY_OPTIONS
from handlers.db_handler import search_videos_by_genre, search_videos_by_tags, get_recent_analyses
from storage.storage_manager import StorageType


def render_sidebar(current_precision: int = 5) -> dict:
    """
    사이드바 렌더링
    
    Returns:
        dict: 사이드바 설정값들
    """
    # 프로젝트 정보
    st.sidebar.header("📋 프로젝트 정보")
    st.sidebar.info(
        "**AI 기반 광고 영상 콘텐츠 추론 연구**\n\n"
        "영상 광고의 레퍼런스를 분석하여 내용, 배경, "
        "장르 및 표현 방식을 AI로 추론합니다.\n\n"
        "개발자: 김윤섭 (C65028)"
    )
    
    st.sidebar.markdown("---")
    
    # 정밀도 설정
    precision_level = add_precision_settings_sidebar()
    
    st.sidebar.markdown("---")
    
    # DB 기능
    add_db_sidebar()
    
    st.sidebar.markdown("---")
    
    # 설정
    settings = add_settings_sidebar()
    
    return {
        'precision_level': precision_level,
        **settings
    }


def add_precision_settings_sidebar() -> int:
    """정밀도 레벨 설정을 사이드바에 추가"""
    st.sidebar.header("🎯 분석 정밀도 설정")
    
    # 정밀도 레벨 슬라이더
    precision_level = st.sidebar.slider(
        "정밀도 레벨",
        min_value=1,
        max_value=10,
        value=int(os.getenv("SCENE_PRECISION_LEVEL", "5")),
        help="레벨이 높을수록 정확하지만 시간이 오래 걸립니다"
    )
    
    # 정밀도 레벨별 설명
    st.sidebar.markdown(f"""
    <div class="precision-info">
        <strong>현재 레벨 {precision_level}:</strong><br>
        {PRECISION_DESCRIPTIONS[precision_level]}
    </div>
    """, unsafe_allow_html=True)
    
    # 예상 처리 시간 표시
    if precision_level <= 3:
        st.sidebar.markdown(f"""
        <div class="precision-success">
            ⏱️ 예상 처리 시간: <strong>{TIME_ESTIMATES[precision_level]}</strong><br>
            💡 빠른 처리로 테스트에 적합합니다
        </div>
        """, unsafe_allow_html=True)
    elif precision_level >= 8:
        st.sidebar.markdown(f"""
        <div class="precision-warning">
            ⏱️ 예상 처리 시간: <strong>{TIME_ESTIMATES[precision_level]}</strong><br>
            ⚠️ 처리 시간이 오래 걸릴 수 있습니다
        </div>
        """, unsafe_allow_html=True)
    else:
        st.sidebar.info(f"⏱️ 예상 처리 시간: **{TIME_ESTIMATES[precision_level]}**")
    
    # 고급 설정
    with st.sidebar.expander("🔧 고급 씬 추출 설정"):
        custom_threshold = st.slider(
            "씬 유사도 임계값",
            min_value=0.80,
            max_value=0.99,
            value=float(os.getenv("SCENE_SIMILARITY_THRESHOLD", "0.92")),
            step=0.01,
            help="높을수록 더 유사한 씬들만 그룹화됩니다"
        )
        
        max_analysis_images = st.number_input(
            "최대 분석 이미지 수",
            min_value=5,
            max_value=20,
            value=int(os.getenv("MAX_ANALYSIS_IMAGES", "10")),
            help="AI 분석에 사용할 최대 이미지 수"
        )
        
        min_scene_duration = st.number_input(
            "최소 씬 지속시간 (초)",
            min_value=0.1,
            max_value=5.0,
            value=float(os.getenv("MIN_SCENE_DURATION", "0.5")),
            step=0.1,
            help="이보다 짧은 씬은 무시됩니다"
        )
        
        scene_threshold = st.slider(
            "씬 전환 감지 임계값",
            min_value=0.1,
            max_value=0.8,
            value=float(os.getenv("SCENE_THRESHOLD", "0.3")),
            step=0.05,
            help="낮을수록 더 많은 씬 전환을 감지합니다"
        )
    
    # 환경변수 업데이트
    os.environ["SCENE_PRECISION_LEVEL"] = str(precision_level)
    os.environ["SCENE_SIMILARITY_THRESHOLD"] = str(custom_threshold)
    os.environ["MAX_ANALYSIS_IMAGES"] = str(max_analysis_images)
    os.environ["MIN_SCENE_DURATION"] = str(min_scene_duration)
    os.environ["SCENE_THRESHOLD"] = str(scene_threshold)
    
    return precision_level


def add_db_sidebar():
    """데이터베이스 조회 기능을 사이드바에 추가"""
    st.sidebar.header("📊 분석 데이터베이스")
    
    # 데이터베이스 관리자 버튼
    if st.sidebar.button("🗂️ 데이터베이스 관리자", use_container_width=True, type="primary"):
        st.session_state.show_db_modal = True
        st.rerun()
    
    # DB 통계
    db = VideoAnalysisDB()
    stats = db.get_statistics()
    db.close()
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric("총 영상", stats['total_videos'])
    with col2:
        st.metric("총 분석", stats['total_analyses'])
    
    # 빠른 검색
    st.sidebar.subheader("🔍 빠른 검색")
    
    # 장르별 필터
    selected_genre = st.sidebar.selectbox(
        "장르별 조회", 
        ["전체"] + GENRES, 
        key="sidebar_genre_filter"
    )
    
    # 태그 검색
    tag_search = st.sidebar.text_input("태그 검색", key="sidebar_tag_search")
    
    if st.sidebar.button("🔍 검색", key="sidebar_search_btn"):
        if selected_genre != "전체":
            results = search_videos_by_genre(selected_genre)
        elif tag_search:
            results = search_videos_by_tags([tag_search])
        else:
            results = []
        
        if results:
            st.session_state['search_results'] = results
        else:
            st.sidebar.warning("검색 결과가 없습니다.")
    
    # 최근 분석 목록
    st.sidebar.subheader("📅 최근 분석")
    recent_analyses = get_recent_analyses(limit=5)
    
    if recent_analyses:
        for analysis in recent_analyses:
            with st.sidebar.expander(f"🎬 {analysis.get('video_id', 'Unknown')[:15]}..."):
                st.write(f"**장르**: {analysis.get('genre', 'Unknown')}")
                st.write(f"**날짜**: {analysis.get('analysis_date', 'Unknown')[:10]}")
                if st.button("📋 상세보기", key=f"sidebar_detail_{analysis.get('video_id', '')}_{analysis.doc_id}"):
                    st.session_state['search_result'] = analysis
    else:
        st.sidebar.info("최근 분석 내역이 없습니다.")


def add_settings_sidebar() -> dict:
    """설정 섹션 추가"""
    st.sidebar.header("🔧 설정")
    
    settings = {}
    
    # 스토리지 상태 표시
    st.sidebar.subheader("💾 스토리지")
    if st.session_state.storage_type == StorageType.LOCAL:
        st.sidebar.warning("📁 로컬 저장소 사용 중")
    elif st.session_state.storage_type == StorageType.SFTP:
        st.sidebar.success("🔐 SFTP 연결 (시놀로지 NAS)")
    elif st.session_state.storage_type == StorageType.SYNOLOGY_API:
        st.sidebar.success("☁️ Synology API 연결")
    elif st.session_state.storage_type == StorageType.WEBDAV:
        st.sidebar.info("🌐 WebDAV 연결")
    
    # 스토리지 연결 테스트
    if st.sidebar.button("🔌 연결 테스트", key="storage_test_btn"):
        with st.spinner("연결 테스트 중..."):
            if st.session_state.video_service.test_storage_connection():
                st.sidebar.success("✅ 스토리지 연결 성공!")
            else:
                st.sidebar.error("❌ 스토리지 연결 실패")
    
    # 디버그 모드
    settings['debug_mode'] = st.sidebar.checkbox("🐛 디버그 모드", value=False)
    
    # 비디오 품질 선택
    st.sidebar.subheader("🎥 다운로드 품질")
    quality = st.sidebar.radio(
        "품질 선택",
        options=list(VIDEO_QUALITY_OPTIONS.keys()),
        format_func=lambda x: VIDEO_QUALITY_OPTIONS[x],
        index=0,
        help="높은 품질일수록 다운로드 시간이 오래 걸립니다"
    )
    settings['video_quality'] = quality
    os.environ["VIDEO_QUALITY"] = quality
    
    return settings