# app.py
from dotenv import load_dotenv
load_dotenv()  # .env 파일 로드

import streamlit as st
import os
import traceback
from datetime import datetime
from src.services.video_service import VideoService
from src.storage.storage_manager import StorageManager, StorageType
from src.storage.db_manager import VideoAnalysisDB
from utils.logger import get_logger

# 로거 설정
logger = get_logger(__name__)

# 페이지 설정
st.set_page_config(
    page_title="AI 영상 레퍼런스 분석기",
    page_icon="🎥",
    layout="wide"
)

# CSS 스타일 추가
st.markdown("""
<style>
    .precision-info {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f4e79;
        margin: 1rem 0;
    }
    .precision-warning {
        background-color: #fff3cd;
        padding: 0.8rem;
        border-radius: 6px;
        border-left: 4px solid #ffc107;
        margin: 0.5rem 0;
        font-size: 14px;
    }
    .precision-success {
        background-color: #d4edda;
        padding: 0.8rem;
        border-radius: 6px;
        border-left: 4px solid #28a745;
        margin: 0.5rem 0;
        font-size: 14px;
    }
    .stProgress > div > div > div > div {
        background-color: #1f4e79;
    }
</style>
""", unsafe_allow_html=True)

def init_session_state():
    """세션 상태 초기화"""
    if 'video_service' not in st.session_state:
        # 환경변수에서 스토리지 타입 읽기
        storage_type_str = os.getenv("STORAGE_TYPE", "sftp")  # 기본값 sftp
        try:
            storage_type = StorageType[storage_type_str.upper()]
        except KeyError:
            storage_type = StorageType.SFTP
            logger.warning(f"알 수 없는 스토리지 타입: {storage_type_str}, SFTP 사용")
        
        # VideoService 초기화 (스토리지 타입 전달)
        st.session_state.video_service = VideoService(storage_type=storage_type)
        st.session_state.storage_type = storage_type
    
    if 'processing_history' not in st.session_state:
        st.session_state.processing_history = []

def get_precision_descriptions():
    """정밀도 레벨별 설명 반환"""
    return {
        1: "⚡ 초고속 - 색상 히스토그램만",
        2: "🏃 고속 - 색상 + 기본 엣지",
        3: "🚶 빠름 - 색상 + 엣지 + 밝기",
        4: "🚶‍♂️ 보통-빠름 - 기본 특징들",
        5: "⚖️ 균형 (권장) - 모든 기본 특징",
        6: "🔍 정밀 - 기본 + 텍스처",
        7: "🔬 고정밀 - 기본 + 텍스처 + 공간색상",
        8: "🎯 매우정밀 - 대부분 특징 활성화",
        9: "🏆 초정밀 - 거의 모든 특징",
        10: "💎 최고정밀 - 모든 특징 + 고해상도"
    }

def add_precision_settings_sidebar():
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
    precision_descriptions = get_precision_descriptions()
    
    st.sidebar.markdown(f"""
    <div class="precision-info">
        <strong>현재 레벨 {precision_level}:</strong><br>
        {precision_descriptions[precision_level]}
    </div>
    """, unsafe_allow_html=True)
    
    # 예상 처리 시간 표시
    time_estimates = {
        1: "30초-1분", 2: "1-2분", 3: "2-3분", 4: "3-4분", 5: "4-6분",
        6: "6-8분", 7: "8-12분", 8: "12-15분", 9: "15-20분", 10: "20-30분"
    }
    
    if precision_level <= 3:
        st.sidebar.markdown(f"""
        <div class="precision-success">
            ⏱️ 예상 처리 시간: <strong>{time_estimates[precision_level]}</strong><br>
            💡 빠른 처리로 테스트에 적합합니다
        </div>
        """, unsafe_allow_html=True)
    elif precision_level >= 8:
        st.sidebar.markdown(f"""
        <div class="precision-warning">
            ⏱️ 예상 처리 시간: <strong>{time_estimates[precision_level]}</strong><br>
            ⚠️ 처리 시간이 오래 걸릴 수 있습니다
        </div>
        """, unsafe_allow_html=True)
    else:
        st.sidebar.info(f"⏱️ 예상 처리 시간: **{time_estimates[precision_level]}**")
    
    # 고급 설정 (접을 수 있는 섹션)
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


def add_database_modal():
    """데이터베이스 모달 관리자"""
    
    # CSS 스타일 (기존 CSS에 추가)
    st.markdown("""
    <style>
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.5);
            z-index: 1000;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .modal-content {
            background-color: white;
            border-radius: 10px;
            max-width: 90vw;
            max-height: 90vh;
            overflow-y: auto;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        }
        .db-header {
            background: linear-gradient(90deg, #1f4e79, #2e8b57);
            color: white;
            padding: 1rem 2rem;
            border-radius: 10px 10px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .db-content {
            padding: 2rem;
        }
        .video-card {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
            background: #f9f9f9;
        }
        .video-card:hover {
            background: #f0f0f0;
            border-color: #1f4e79;
        }
        .video-card.selected {
            background: #e3f2fd;
            border-color: #1976d2;
        }
        .tag-container {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin: 0.5rem 0;
        }
        .tag {
            background-color: #007ACC;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
            display: inline-block;
        }
        .action-buttons {
            display: flex;
            gap: 0.5rem;
            margin-top: 1rem;
        }
        .btn-danger {
            background-color: #dc3545;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            cursor: pointer;
        }
        .btn-warning {
            background-color: #ffc107;
            color: black;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            cursor: pointer;
        }
        .btn-info {
            background-color: #17a2b8;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            cursor: pointer;
        }
        .pagination {
            display: flex;
            justify-content: center;
            gap: 0.5rem;
            margin: 1rem 0;
        }
        .page-btn {
            padding: 0.5rem 1rem;
            border: 1px solid #ddd;
            background: white;
            cursor: pointer;
            border-radius: 3px;
        }
        .page-btn.active {
            background: #1f4e79;
            color: white;
        }
    </style>
    """, unsafe_allow_html=True)

def show_database_manager():
    """데이터베이스 관리 모달 표시"""
    
    # 세션 상태 초기화
    if 'show_db_modal' not in st.session_state:
        st.session_state.show_db_modal = False
    if 'selected_videos' not in st.session_state:
        st.session_state.selected_videos = []
    if 'db_page' not in st.session_state:
        st.session_state.db_page = 1
    if 'db_filter' not in st.session_state:
        st.session_state.db_filter = 'all'
    if 'db_search' not in st.session_state:
        st.session_state.db_search = ''
    if 'edit_video_id' not in st.session_state:
        st.session_state.edit_video_id = None

def render_database_modal():
    """데이터베이스 모달 렌더링"""
    if not st.session_state.get('show_db_modal', False):
        return
    
    db = VideoAnalysisDB()
    
    # 모달 헤더
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
                st.rerun()
    
    # 필터 및 검색 영역
    with st.container():
        st.markdown("### 🔍 필터 및 검색")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            filter_options = ['all', 'analyzed', 'not_analyzed', 'recent']
            filter_labels = {
                'all': '전체',
                'analyzed': 'AI 분석 완료',
                'not_analyzed': '분석 미완료',
                'recent': '최근 7일'
            }
            db_filter = st.selectbox(
                "필터",
                filter_options,
                format_func=lambda x: filter_labels[x],
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
    
    # 데이터 가져오기 및 필터링
    videos = get_filtered_videos(db, db_filter, db_search)
    
    # 통계 정보
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
    
    # 일괄 작업 버튼
    if st.session_state.selected_videos:
        st.markdown("### ⚡ 일괄 작업")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🗑️ 선택 항목 삭제", key="bulk_delete", type="secondary"):
                show_bulk_delete_confirmation()
        
        with col2:
            if st.button("📤 선택 항목 내보내기", key="bulk_export"):
                export_selected_videos(st.session_state.selected_videos)
        
        with col3:
            if st.button("🔄 선택 항목 재분석", key="bulk_reanalyze"):
                show_bulk_reanalyze_dialog()
        
        with col4:
            if st.button("❌ 선택 해제", key="clear_selection"):
                st.session_state.selected_videos = []
                st.rerun()
    
    # 페이지네이션 계산
    total_pages = (len(videos) + items_per_page - 1) // items_per_page
    current_page = st.session_state.get('db_page', 1)
    
    if current_page > total_pages and total_pages > 0:
        st.session_state.db_page = total_pages
        current_page = total_pages
    
    start_idx = (current_page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    page_videos = videos[start_idx:end_idx]
    
    # 영상 목록 표시
    st.markdown("### 📹 영상 목록")
    
    if not page_videos:
        st.info("검색 조건에 맞는 영상이 없습니다.")
    else:
        # 전체 선택/해제 체크박스
        col1, col2 = st.columns([1, 10])
        with col1:
            select_all = st.checkbox("전체 선택", key="select_all_videos")
            if select_all:
                st.session_state.selected_videos = [v['video_id'] for v in page_videos]
            elif not select_all and st.session_state.get('was_select_all', False):
                st.session_state.selected_videos = []
            st.session_state.was_select_all = select_all
        
        # 영상 카드들
        for video in page_videos:
            render_video_card(video)
    
    # 페이지네이션
    if total_pages > 1:
        render_pagination(current_page, total_pages)
    
    # 편집 모달
    if st.session_state.get('edit_video_id'):
        render_edit_modal(db)
    
    db.close()

def get_filtered_videos(db, filter_type, search_query):
    """필터 및 검색 조건에 따른 영상 목록 반환"""
    videos = db.get_all_videos()
    
    # 필터 적용
    if filter_type == 'analyzed':
        videos = [v for v in videos if v.get('analysis_result')]
    elif filter_type == 'not_analyzed':
        videos = [v for v in videos if not v.get('analysis_result')]
    elif filter_type == 'recent':
        from datetime import datetime, timedelta
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        videos = [v for v in videos if v.get('download_date', '') > week_ago]
    
    # 검색 적용
    if search_query:
        search_lower = search_query.lower()
        filtered_videos = []
        for video in videos:
            # 제목, 장르, 태그에서 검색
            title_match = search_lower in video.get('title', '').lower()
            genre_match = False
            tag_match = False
            
            if video.get('analysis_result'):
                genre_match = search_lower in video['analysis_result'].get('genre', '').lower()
                tags = video['analysis_result'].get('tags', [])
                tag_match = any(search_lower in tag.lower() for tag in tags)
            
            if title_match or genre_match or tag_match:
                filtered_videos.append(video)
        
        videos = filtered_videos
    
    # 최신순 정렬
    videos.sort(key=lambda x: x.get('download_date', ''), reverse=True)
    
    return videos

def render_video_card(video):
    """개별 영상 카드 렌더링"""
    video_id = video['video_id']
    is_selected = video_id in st.session_state.selected_videos
    
    # 카드 컨테이너
    with st.container():
        # 체크박스와 기본 정보
        col1, col2, col3, col4 = st.columns([0.5, 3, 2, 1])
        
        with col1:
            selected = st.checkbox("", value=is_selected, key=f"select_{video_id}")
            if selected and video_id not in st.session_state.selected_videos:
                st.session_state.selected_videos.append(video_id)
            elif not selected and video_id in st.session_state.selected_videos:
                st.session_state.selected_videos.remove(video_id)
        
        with col2:
            st.markdown(f"**📹 {video.get('title', 'Unknown')}**")
            st.caption(f"ID: {video_id}")
            st.caption(f"업로더: {video.get('uploader', 'Unknown')}")
            duration = video.get('duration', 0)
            st.caption(f"길이: {duration//60}분 {duration%60}초")
        
        with col3:
            # 분석 결과 정보
            if video.get('analysis_result'):
                analysis = video['analysis_result']
                st.success("✅ AI 분석 완료")
                st.write(f"**장르**: {analysis.get('genre', 'Unknown')}")
                st.write(f"**분위기**: {analysis.get('mood_tone', 'Unknown')}")
                
                # 태그 표시
                tags = analysis.get('tags', [])
                if tags:
                    tag_html = '<div class="tag-container">'
                    for tag in tags[:5]:  # 최대 5개 표시
                        tag_html += f'<span class="tag">#{tag}</span>'
                    if len(tags) > 5:
                        tag_html += f'<span class="tag">+{len(tags)-5}</span>'
                    tag_html += '</div>'
                    st.markdown(tag_html, unsafe_allow_html=True)
            else:
                st.warning("⚠️ 분석 미완료")
        
        with col4:
            # 액션 버튼
            st.markdown("<div class='action-buttons'>", unsafe_allow_html=True)
            
            if st.button("✏️", key=f"edit_{video_id}", help="편집"):
                st.session_state.edit_video_id = video_id
                st.rerun()
            
            if st.button("👁️", key=f"view_{video_id}", help="상세보기"):
                show_video_details(video)
            
            if st.button("🗑️", key=f"delete_{video_id}", help="삭제"):
                show_delete_confirmation(video_id)
            
            if not video.get('analysis_result'):
                if st.button("🔄", key=f"reanalyze_{video_id}", help="재분석"):
                    trigger_reanalysis(video_id)
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("---")

def render_pagination(current_page, total_pages):
    """페이지네이션 렌더링"""
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

def render_edit_modal(db):
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
        description = st.text_area("설명", value=video_data.get('description', ''), height=100)
        
        # AI 분석 결과 편집 (있는 경우)
        if analysis_data:
            st.markdown("#### 🤖 AI 분석 결과 편집")
            genre = st.selectbox("장르", 
                               ["2D애니메이션", "3D애니메이션", "모션그래픽", "인터뷰", 
                                "스팟광고", "VLOG", "유튜브콘텐츠", "다큐멘터리", 
                                "브랜드필름", "TVC", "뮤직비디오", "교육콘텐츠",
                                "제품소개", "이벤트영상", "웹드라마", "바이럴영상"],
                               index=0 if not analysis_data.get('genre') else 
                               ["2D애니메이션", "3D애니메이션", "모션그래픽", "인터뷰", 
                                "스팟광고", "VLOG", "유튜브콘텐츠", "다큐멘터리", 
                                "브랜드필름", "TVC", "뮤직비디오", "교육콘텐츠",
                                "제품소개", "이벤트영상", "웹드라마", "바이럴영상"].index(analysis_data['genre']) 
                               if analysis_data['genre'] in ["2D애니메이션", "3D애니메이션", "모션그래픽", "인터뷰", 
                                                            "스팟광고", "VLOG", "유튜브콘텐츠", "다큐멘터리", 
                                                            "브랜드필름", "TVC", "뮤직비디오", "교육콘텐츠",
                                                            "제품소개", "이벤트영상", "웹드라마", "바이럴영상"] else 0)
            
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
                db.delete_analysis(video_id)
                st.success("분석 결과가 삭제되었습니다.")
                st.session_state.edit_video_id = None
                st.rerun()
        
        if submitted:
            # 기본 정보 업데이트
            updated_video = {
                **video_data,
                'title': title,
                'uploader': uploader,
                'description': description
            }
            db.update_video_info(video_id, updated_video)
            
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
                db.update_analysis_result(video_id, updated_analysis)
            
            st.success("✅ 저장되었습니다!")
            st.session_state.edit_video_id = None
            st.rerun()

def show_video_details(video):
    """영상 상세 정보 표시"""
    st.markdown("### 👁️ 영상 상세 정보")
    
    with st.expander("📄 기본 정보", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**제목**: {video.get('title', 'Unknown')}")
            st.write(f"**업로더**: {video.get('uploader', 'Unknown')}")
            st.write(f"**플랫폼**: {video.get('platform', 'Unknown')}")
        with col2:
            duration = video.get('duration', 0)
            st.write(f"**길이**: {duration//60}분 {duration%60}초")
            st.write(f"**조회수**: {video.get('view_count', 'Unknown'):,}회" if video.get('view_count') else "**조회수**: Unknown")
            st.write(f"**다운로드**: {video.get('download_date', 'Unknown')[:10]}")
        
        if video.get('description'):
            st.write("**설명**:")
            st.write(video['description'][:500] + "..." if len(video.get('description', '')) > 500 else video.get('description', ''))
    
    # AI 분석 결과
    if video.get('analysis_result'):
        analysis = video['analysis_result']
        with st.expander("🤖 AI 분석 결과", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**장르**: {analysis.get('genre', 'Unknown')}")
                st.write(f"**표현형식**: {analysis.get('expression_style', 'Unknown')}")
                st.write(f"**분위기**: {analysis.get('mood_tone', 'Unknown')}")
            with col2:
                st.write(f"**타겟 고객층**: {analysis.get('target_audience', 'Unknown')}")
                st.write(f"**분석 날짜**: {analysis.get('analysis_date', 'Unknown')[:10]}")
                st.write(f"**사용 모델**: {analysis.get('model_used', 'Unknown')}")
            
            if analysis.get('reasoning'):
                st.write("**판단 이유**:")
                st.info(analysis['reasoning'])
            
            if analysis.get('features'):
                st.write("**특징 및 특이사항**:")
                st.info(analysis['features'])
            
            if analysis.get('tags'):
                st.write("**태그**:")
                tag_html = '<div class="tag-container">'
                for tag in analysis['tags']:
                    tag_html += f'<span class="tag">#{tag}</span>'
                tag_html += '</div>'
                st.markdown(tag_html, unsafe_allow_html=True)

def show_delete_confirmation(video_id):
    """삭제 확인 다이얼로그"""
    st.warning(f"⚠️ 영상 {video_id}를 정말 삭제하시겠습니까?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ 삭제", key=f"confirm_delete_{video_id}", type="secondary"):
            db = VideoAnalysisDB()
            db.delete_video(video_id)
            db.close()
            st.success("✅ 삭제되었습니다!")
            st.rerun()
    with col2:
        if st.button("❌ 취소", key=f"cancel_delete_{video_id}"):
            st.rerun()

def show_bulk_delete_confirmation():
    """일괄 삭제 확인"""
    count = len(st.session_state.selected_videos)
    st.warning(f"⚠️ 선택된 {count}개 영상을 정말 삭제하시겠습니까?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ 일괄 삭제", key="confirm_bulk_delete", type="secondary"):
            db = VideoAnalysisDB()
            for video_id in st.session_state.selected_videos:
                db.delete_video(video_id)
            db.close()
            st.session_state.selected_videos = []
            st.success(f"✅ {count}개 영상이 삭제되었습니다!")
            st.rerun()
    with col2:
        if st.button("❌ 취소", key="cancel_bulk_delete"):
            st.rerun()

def export_selected_videos(video_ids):
    """선택된 영상들 내보내기"""
    db = VideoAnalysisDB()
    exported_data = []
    
    for video_id in video_ids:
        video_info = db.get_video_info(video_id)
        analysis_info = db.get_latest_analysis(video_id)
        
        exported_data.append({
            'video_info': video_info,
            'analysis_result': analysis_info
        })
    
    import json
    from datetime import datetime
    
    export_filename = f"video_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    export_path = f"data/export/{export_filename}"
    
    os.makedirs("data/export", exist_ok=True)
    
    with open(export_path, 'w', encoding='utf-8') as f:
        json.dump(exported_data, f, ensure_ascii=False, indent=2)
    
    db.close()
    st.success(f"✅ {len(video_ids)}개 영상이 내보내기되었습니다!")
    st.info(f"📁 파일 위치: {export_path}")

def add_db_sidebar():
    """데이터베이스 조회 기능을 사이드바에 추가"""
    st.sidebar.header("📊 분석 데이터베이스")
    
    # 데이터베이스 관리자 버튼
    if st.sidebar.button("🗂️ 데이터베이스 관리자", use_container_width=True, type="primary"):
        st.session_state.show_db_modal = True
        st.rerun()
    
    # 기존 사이드바 DB 기능들...
    db = VideoAnalysisDB()
    
    # 통계 표시
    stats = db.get_statistics()
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric("총 영상", stats['total_videos'])
    with col2:
        st.metric("총 분석", stats['total_analyses'])
    
    # 나머지 기존 코드들...
    db.close()

def display_search_results():
    """검색 결과 표시"""
    if 'search_result' in st.session_state:
        result = st.session_state['search_result']
        
        st.markdown("### 🔍 검색 결과")
        
        # 검색 결과 카드 형태로 표시
        with st.container():
            st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                <h4>📹 {result['video_id']}</h4>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("장르", result['genre'])
                st.caption(f"표현형식: {result['expression_style']}")
            with col2:
                st.metric("분위기", result['mood_tone'])
                st.caption(f"타겟: {result['target_audience']}")
            with col3:
                st.metric("분석 날짜", result['analysis_date'][:10])
                st.caption(f"모델: {result['model_used']}")
            
            # 상세 정보
            with st.expander("📝 상세 정보 보기"):
                st.markdown("**판단 이유**")
                st.info(result['reasoning'])
                
                st.markdown("**특징 및 특이사항**")
                st.info(result['features'])
                
                st.markdown("**태그**")
                tag_html = '<div>'
                for tag in result['tags']:
                    tag_html += f'<span style="background-color: #007ACC; color: white; padding: 5px 10px; margin: 3px; border-radius: 15px; display: inline-block; font-size: 12px;">#{tag}</span>'
                tag_html += '</div>'
                st.markdown(tag_html, unsafe_allow_html=True)
                
                if result.get('token_usage'):
                    st.caption(f"토큰 사용량: {result['token_usage'].get('total', 'N/A')}")
        
        del st.session_state['search_result']
    
    if 'search_results' in st.session_state:
        results = st.session_state['search_results']
        st.markdown(f"### 🔍 검색 결과 ({len(results)}개)")
        
        for result in results:
            with st.expander(f"📹 {result['video_id']} - {result['genre']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**분석 날짜**: {result['analysis_date'][:10]}")
                    st.write(f"**분위기**: {result['mood_tone']}")
                    st.write(f"**타겟**: {result['target_audience']}")
                with col2:
                    st.write(f"**표현형식**: {result['expression_style']}")
                    st.write(f"**태그**: {', '.join(result['tags'][:5])}...")
        
        del st.session_state['search_results']

def main():
    """메인 앱 함수"""
    # 세션 상태 초기화
    init_session_state()
    
    # 헤더
    st.title("🎥 AI 기반 광고 영상 콘텐츠 추론 시스템")
    st.markdown("---")
    
    # 사이드바
    with st.sidebar:
        st.header("📋 프로젝트 정보")
        st.info(
            "**AI 기반 광고 영상 콘텐츠 추론 연구**\n\n"
            "영상 광고의 레퍼런스를 분석하여 내용, 배경, "
            "장르 및 표현 방식을 AI로 추론합니다.\n\n"
            "개발자: 김윤섭 (C65028)"
        )
        
        st.markdown("---")
        
        # 정밀도 설정 추가
        current_precision = add_precision_settings_sidebar()
        
        st.markdown("---")
        
        # DB 기능 추가
        add_db_sidebar()
        
        st.markdown("---")
        
        st.header("🔧 설정")
        
        # 스토리지 상태 표시
        st.subheader("💾 스토리지")
        storage_status = st.empty()
        with storage_status.container():
            if st.session_state.storage_type == StorageType.LOCAL:
                st.warning("📁 로컬 저장소 사용 중")
            elif st.session_state.storage_type == StorageType.SFTP:
                st.success("🔐 SFTP 연결 (시놀로지 NAS)")
            elif st.session_state.storage_type == StorageType.SYNOLOGY_API:
                st.success("☁️ Synology API 연결")
            elif st.session_state.storage_type == StorageType.WEBDAV:
                st.info("🌐 WebDAV 연결")
        
        # 스토리지 연결 테스트
        if st.button("🔌 연결 테스트", key="storage_test_btn"):
            with st.spinner("연결 테스트 중..."):
                if st.session_state.video_service.test_storage_connection():
                    st.success("✅ 스토리지 연결 성공!")
                else:
                    st.error("❌ 스토리지 연결 실패")
        
        # 디버그 모드
        debug_mode = st.checkbox("🐛 디버그 모드", value=False)
        
        # 비디오 품질 선택
        st.subheader("🎥 다운로드 품질")
        quality = st.radio(
            "품질 선택",
            options=["best", "balanced", "fast"],
            format_func=lambda x: {
                "best": "🏆 최고 품질 (1080p, 느림)",
                "balanced": "⚖️ 균형 (720p, 보통)",
                "fast": "🚀 빠른 다운로드 (MP4만)"
            }[x],
            index=0,
            help="높은 품질일수록 다운로드 시간이 오래 걸립니다"
        )
        # 환경변수로 설정
        os.environ["VIDEO_QUALITY"] = quality
    
    # 검색 결과 표시 (메인 영역 상단)
    display_search_results()
    
    # 메인 컨텐츠
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("🔗 영상 URL 입력")
        
        # 현재 정밀도 레벨 표시
        precision_descriptions = get_precision_descriptions()
        st.markdown(f"""
        <div class="precision-info">
            <strong>🎯 현재 정밀도 레벨: {current_precision}</strong><br>
            {precision_descriptions[current_precision]}
        </div>
        """, unsafe_allow_html=True)
        
        # URL 입력
        video_url = st.text_input(
            "분석할 YouTube 또는 Vimeo 영상 링크를 입력하세요:",
            placeholder="https://www.youtube.com/watch?v=... 또는 https://vimeo.com/...",
            help="YouTube와 Vimeo 영상을 지원합니다.",
            key="video_url_input"
        )
        
        # 예시 URL 버튼들
        st.caption("예시:")
        example_col1, example_col2 = st.columns(2)
        with example_col1:
            if st.button("📺 YouTube 예시", use_container_width=True, key="youtube_example_btn"):
                st.session_state['video_url_input'] = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
                st.rerun()
        with example_col2:
            if st.button("🎬 Vimeo 예시", use_container_width=True, key="vimeo_example_btn"):
                st.session_state['video_url_input'] = "https://vimeo.com/347119375"
                st.rerun()
        
        # 분석 버튼
        if st.button("🚀 분석 시작", type="primary", use_container_width=True, key="analyze_btn"):
            if not video_url:
                st.error("❌ 영상 URL을 입력해주세요!")
            else:
                try:
                    # 진행 상황 컨테이너
                    progress_container = st.container()
                    with progress_container:
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        # 1단계: 영상 정보 확인
                        status_text.text("🔍 영상 정보 확인 중...")
                        progress_bar.progress(10)
                        
                        # 2단계: 영상 다운로드
                        status_text.text("📥 영상 다운로드 중...")
                        progress_bar.progress(20)
                        
                        # 3단계: 씬 추출 (정밀도 레벨 표시)
                        status_text.text(f"🎬 주요 씬 추출 중... (정밀도 레벨: {current_precision})")
                        progress_bar.progress(40)
                        
                        # VideoService를 통해 처리 - 실제 처리 시작
                        video = st.session_state.video_service.process_video(video_url)
                        progress_bar.progress(60)
                        
                        # 4단계: AI 분석 여부 확인 및 표시
                        if hasattr(video, 'analysis_result') and video.analysis_result:
                            status_text.text("🤖 AI 영상 분석 완료!")
                            progress_bar.progress(80)
                        elif os.getenv("OPENAI_API_KEY"):
                            status_text.text("⚠️ AI 분석이 실행되었으나 결과가 없습니다")
                            progress_bar.progress(80)
                        else:
                            status_text.text("ℹ️ AI 분석 건너뜀 (API 키 없음)")
                            progress_bar.progress(80)
                        
                        # 5단계: 스토리지 업로드
                        status_text.text("💾 스토리지 저장 완료")
                        progress_bar.progress(90)
                        
                        # 완료
                        progress_bar.progress(100)
                        status_text.text(f"✅ 분석 완료! (정밀도 레벨 {current_precision})")
                    
                    # 성공 메시지
                    st.success(f"✅ 영상 분석이 완료되었습니다! (정밀도 레벨: {current_precision})")
                    
                    # 처리 이력에 추가
                    st.session_state.processing_history.append({
                        'time': datetime.now().strftime("%H:%M"),
                        'title': video.metadata.title if video.metadata else "제목 없음",
                        'url': video_url,
                        'precision_level': current_precision
                    })
                    
                    # 결과 표시
                    st.header("📋 분석 결과")
                    
                    # 메타데이터 표시
                    with st.expander("📄 영상 메타데이터", expanded=True):
                        if video.metadata:
                            metadata_dict = video.metadata.to_dict()
                            
                            # 주요 정보를 보기 좋게 표시
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.metric("제목", metadata_dict.get('title', 'N/A'))
                                st.metric("업로더", metadata_dict.get('uploader', 'N/A'))
                                st.metric("길이", f"{metadata_dict.get('duration', 0) // 60}분 {metadata_dict.get('duration', 0) % 60}초")
                            with col_b:
                                st.metric("업로드 날짜", metadata_dict.get('upload_date', 'N/A'))
                                st.metric("비디오 ID", metadata_dict.get('video_id', 'N/A'))
                                st.metric("형식", metadata_dict.get('ext', 'N/A'))
                            
                            # 분석 정보 추가
                            precision_descriptions = get_precision_descriptions()
                            st.info(f"🎯 **사용된 정밀도 레벨**: {current_precision} - {precision_descriptions[current_precision]}")
                            
                            # 설명
                            if metadata_dict.get('description'):
                                st.text_area("설명", metadata_dict['description'], height=100, disabled=True)
                    
                    # 씬 이미지 표시
                    if video.scenes:
                        with st.expander("🎬 추출된 씬 이미지", expanded=True):
                            st.write(f"총 {len(video.scenes)}개의 주요 씬이 추출되었습니다. (정밀도 레벨: {current_precision})")
                            
                            # 이미지 그리드로 표시
                            cols = st.columns(3)  # 3열로 표시
                            for i, scene in enumerate(video.scenes):
                                with cols[i % 3]:
                                    if os.path.exists(scene.frame_path):
                                        st.image(scene.frame_path, 
                                               caption=f"씬 {i+1} ({scene.timestamp:.1f}초)",
                                               use_container_width=True)
                                    else:
                                        st.warning(f"씬 {i+1} 이미지를 찾을 수 없습니다")
                    
                    # AI 분석 결과 표시 (있는 경우)
                    if video.analysis_result:
                        with st.expander("🤖 AI 분석 결과", expanded=True):
                            # 상단 주요 정보
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.subheader("📌 주요 정보")
                                st.info(f"**장르**: {video.analysis_result.get('genre', 'N/A')}")
                                st.info(f"**표현 형식**: {video.analysis_result.get('expression_style', 'N/A')}")
                            
                            with col2:
                                st.subheader("🎭 분위기 및 타겟")
                                if video.analysis_result.get('mood_tone'):
                                    st.info(f"**분위기**: {video.analysis_result['mood_tone']}")
                                if video.analysis_result.get('target_audience'):
                                    st.info(f"**타겟 고객층**: {video.analysis_result['target_audience']}")
                            
                            # 구분선
                            st.markdown("---")
                            
                            # 판단 이유 - 전체 너비로 표시
                            if video.analysis_result.get('reasoning'):
                                st.subheader("📝 장르 판단 이유")
                                reason_text = video.analysis_result['reasoning']
                                st.markdown(f"""
                                <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                                    <p style="font-size: 16px; line-height: 1.6; white-space: pre-wrap;">{reason_text}</p>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            # 특징 및 특이사항 - 전체 너비로 표시
                            if video.analysis_result.get('features'):
                                st.subheader("🎯 특징 및 특이사항")
                                features_text = video.analysis_result['features']
                                st.markdown(f"""
                                <div style="background-color: #e8f4fd; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                                    <p style="font-size: 16px; line-height: 1.6; white-space: pre-wrap;">{features_text}</p>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            # 태그 표시
                            tags = video.analysis_result.get('tags', [])
                            if tags:
                                st.subheader("🏷️ 태그")
                                tag_html = '<div style="margin-top: 10px;">'
                                for tag in tags:
                                    tag_html += f'''
                                    <span style="
                                        background-color: #007ACC;
                                        color: white;
                                        padding: 5px 15px;
                                        margin: 5px;
                                        border-radius: 20px;
                                        font-size: 14px;
                                        display: inline-block;
                                        font-weight: 500;
                                    ">#{tag}</span>
                                    '''
                                tag_html += '</div>'
                                st.markdown(tag_html, unsafe_allow_html=True)
                            
                            # 분석 품질 정보 표시
                            st.markdown("---")
                            quality_col1, quality_col2, quality_col3 = st.columns(3)
                            with quality_col1:
                                reason_length = len(video.analysis_result.get('reasoning', ''))
                                if reason_length >= 200:
                                    st.success(f"✅ 판단 이유: {reason_length}자")
                                else:
                                    st.warning(f"⚠️ 판단 이유: {reason_length}자 (200자 미만)")
                            
                            with quality_col2:
                                features_length = len(video.analysis_result.get('features', ''))
                                if features_length >= 200:
                                    st.success(f"✅ 특징 설명: {features_length}자")
                                else:
                                    st.warning(f"⚠️ 특징 설명: {features_length}자 (200자 미만)")
                            
                            with quality_col3:
                                tag_count = len(tags)
                                if tag_count >= 10:
                                    st.success(f"✅ 태그 수: {tag_count}개")
                                else:
                                    st.warning(f"⚠️ 태그 수: {tag_count}개 (10개 미만)")
                            
                            # 원본 데이터 보기 옵션
                            with st.expander("🔍 원본 분석 데이터 보기", expanded=False):
                                st.json(video.analysis_result)
                    
                    # 세션 정보
                    with st.expander("🔧 기술 정보"):
                        st.info(f"📁 세션 ID (Video ID): {video.session_id}")
                        st.info(f"🎯 사용된 정밀도 레벨: {current_precision}")
                        st.info(f"💾 저장 위치: {st.session_state.storage_type.value}")
                        if video.local_path:
                            st.text(f"📄 비디오 경로: {video.local_path}")
                        if video.scenes:
                            st.text(f"🎬 추출된 씬 수: {len(video.scenes)}개")
                    
                except ValueError as e:
                    st.error(f"❌ 오류: {str(e)}")
                    logger.error(f"ValueError: {e}")
                    
                except Exception as e:
                    st.error(f"❌ 예기치 않은 오류가 발생했습니다: {str(e)}")
                    logger.error(f"Exception: {e}")
                    if debug_mode:
                        st.text("🐛 디버그 정보:")
                        st.code(traceback.format_exc())
    
    with col2:
        st.header("📊 시스템 상태")
        
        # 현재 정밀도 레벨 표시
        st.subheader("🎯 현재 설정")
        st.metric("정밀도 레벨", f"{current_precision}/10")
        
        # 지원 플랫폼
        st.subheader("🌐 지원 플랫폼")
        st.metric("YouTube", "✅ 지원")
        st.metric("Vimeo", "✅ 지원")
        
        # 작업 통계
        st.subheader("📈 작업 통계")
        
        # DB에서 실제 통계 가져오기
        db = VideoAnalysisDB()
        stats = db.get_statistics()
        db.close()
        
        st.metric("총 분석 영상", f"{stats['total_videos']}개")
        st.metric("오늘 처리", f"{len(st.session_state.processing_history)}개")
        
        # 처리 이력
        st.subheader("📝 최근 처리")
        if st.session_state.processing_history:
            for item in reversed(st.session_state.processing_history[-3:]):  # 최근 3개
                with st.container():
                    precision_badge = f"L{item.get('precision_level', '?')}"
                    st.caption(f"{item['time']} - {item['title'][:20]}... ({precision_badge})")
        else:
            st.info("처리된 영상이 없습니다.")
        
        # 빠른 작업
        st.subheader("⚡ 빠른 작업")
        if st.button("🗑️ 임시 파일 정리", use_container_width=True, key="clean_temp_btn"):
            with st.spinner("정리 중..."):
                # 임시 파일 정리 로직
                import shutil
                temp_dir = "data/temp"
                cleaned = 0
                if os.path.exists(temp_dir):
                    for item in os.listdir(temp_dir):
                        item_path = os.path.join(temp_dir, item)
                        if os.path.isdir(item_path):
                            try:
                                shutil.rmtree(item_path)
                                cleaned += 1
                            except Exception as e:
                                logger.error(f"폴더 삭제 실패: {e}")
                st.success(f"✅ {cleaned}개 폴더 정리 완료!")

if __name__ == "__main__":
    main()