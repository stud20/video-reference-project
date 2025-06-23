# src/handlers/video_handler.py
"""
비디오 처리 관련 핸들러 - 새로운 UI 호환 버전
"""

import streamlit as st
import os
import traceback
import time
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from utils.session_state import add_to_processing_history
from ui.components.analysis_display import display_analysis_results
from utils.logger import get_logger

logger = get_logger(__name__)


def handle_video_analysis(video_url: str, current_precision: int, progress_callback: Optional[Callable] = None):
    """
    비디오 분석 처리 - 새로운 UI와 호환
    
    Args:
        video_url: 분석할 영상 URL
        current_precision: 정밀도 레벨
        progress_callback: 진행 상황 업데이트 콜백 함수
                          callback(step: str, progress: int, message: str)
    """
    try:
        # VideoService 가져오기
        video_service = st.session_state.video_service
        
        # 진행 상황 업데이트 함수
        def update_progress(step: str, progress: int, message: str):
            if progress_callback:
                progress_callback(step, progress, message)
            logger.info(message)
        
        # 실제 비디오 처리
        video = video_service.process_video(
            url=video_url,
            force_reanalyze=False,
            progress_callback=update_progress
        )
        
        # 결과 저장
        st.session_state.current_video = video
        
        # 처리 이력에 추가
        title = video.metadata.title if video.metadata else "제목 없음"
        add_to_processing_history(video_url, title, current_precision)
        
        # 마지막 분석 시간 업데이트
        st.session_state.last_analysis_time = datetime.now().strftime("%H:%M")
        
        logger.info(f"✅ 영상 분석 완료: {title}")
        
        return video
        
    except ValueError as e:
        error_msg = f"❌ 오류: {str(e)}"
        logger.error(f"ValueError: {e}")
        if progress_callback:
            progress_callback("error", 0, error_msg)
        raise
        
    except Exception as e:
        error_msg = f"❌ 예기치 않은 오류가 발생했습니다: {str(e)}"
        logger.error(f"Exception: {e}")
        if st.session_state.get('debug_mode', False):
            logger.error(traceback.format_exc())
        if progress_callback:
            progress_callback("error", 0, error_msg)
        raise


def render_video_input_section(current_precision: int):
    """비디오 URL 입력 섹션 렌더링 - 레거시 호환성"""
    from utils.constants import PRECISION_DESCRIPTIONS
    
    st.header("🔗 영상 URL 입력")
    
    # 현재 정밀도 레벨 표시
    st.markdown(f"""
    <div class="precision-info">
        <strong>🎯 현재 정밀도 레벨: {current_precision}</strong><br>
        {PRECISION_DESCRIPTIONS[current_precision]}
    </div>
    """, unsafe_allow_html=True)
    
    # URL 입력
    video_url = st.text_input(
        "분석할 YouTube 또는 Vimeo 영상 링크를 입력하세요:",
        placeholder="https://www.youtube.com/watch?v=... 또는 https://vimeo.com/...",
        help="YouTube와 Vimeo 영상을 지원합니다.",
        key="video_url_input_legacy"
    )
    
    # 분석 버튼
    if st.button("🚀 분석 시작", type="primary", use_container_width=True, key="analyze_btn_legacy"):
        if not video_url:
            st.error("❌ 영상 URL을 입력해주세요!")
        else:
            with st.spinner("분석 중..."):
                try:
                    video = handle_video_analysis(video_url, current_precision)
                    st.success("✅ 분석 완료!")
                    display_analysis_results(video)
                except Exception as e:
                    st.error(str(e))


def render_system_status(current_precision: int):
    """시스템 상태 표시 - 레거시 호환성"""
    from storage.db_manager import VideoAnalysisDB
    
    st.header("📊 시스템 상태")
    
    # 현재 정밀도 레벨
    st.subheader("🎯 현재 설정")
    st.metric("정밀도 레벨", f"{current_precision}/10")
    
    # 지원 플랫폼
    st.subheader("🌐 지원 플랫폼")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("YouTube", "✅ 지원")
    with col2:
        st.metric("Vimeo", "✅ 지원")
    
    # 작업 통계
    st.subheader("📈 작업 통계")
    
    try:
        db = VideoAnalysisDB()
        stats = db.get_statistics()
        db.close()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("총 분석 영상", f"{stats['total_videos']}개")
        with col2:
            st.metric("오늘 처리", f"{len(st.session_state.processing_history)}개")
    except:
        st.info("통계를 불러올 수 없습니다.")
    
    # 처리 이력
    st.subheader("📝 최근 처리")
    if st.session_state.processing_history:
        recent_items = list(reversed(st.session_state.processing_history[-5:]))
        
        for item in recent_items:
            precision_badge = f"L{item.get('precision_level', '?')}"
            st.caption(f"{item['time']} - {item['title'][:30]}... ({precision_badge})")
    else:
        st.info("처리된 영상이 없습니다.")
    
    # 빠른 작업
    render_quick_actions()


def render_quick_actions():
    """빠른 작업 버튼들"""
    import shutil
    
    st.subheader("⚡ 빠른 작업")
    
    # 임시 파일 정리
    if st.button("🗑️ 임시 파일 정리", use_container_width=True, key="clean_temp_btn"):
        temp_dir = "data/temp"
        if os.path.exists(temp_dir):
            items = os.listdir(temp_dir)
            if items:
                cleaned = 0
                for item in items:
                    item_path = os.path.join(temp_dir, item)
                    if os.path.isdir(item_path):
                        try:
                            shutil.rmtree(item_path)
                            cleaned += 1
                        except Exception as e:
                            logger.error(f"폴더 삭제 실패: {e}")
                
                st.success(f"✅ {cleaned}개 폴더 정리 완료!")
            else:
                st.info("정리할 임시 파일이 없습니다.")
        else:
            st.info("임시 폴더가 존재하지 않습니다.")