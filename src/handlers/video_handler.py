# src/handlers/video_handler.py
"""
비디오 처리 관련 핸들러 - stqdm을 사용한 실시간 진행 표시
"""

import streamlit as st
import os
import traceback
import time
import asyncio
from typing import Dict, Any
from stqdm import stqdm
from utils.session_state import add_to_processing_history
from ui.components.analysis_display import display_analysis_results
from utils.logger import get_logger, clear_log_buffer, get_recent_logs

logger = get_logger(__name__)


def handle_video_analysis(video_url: str, current_precision: int):
    """비디오 분석 처리 - stqdm 실시간 진행 표시"""
    try:
        # 진행 상황 컨테이너
        progress_container = st.container()
        with progress_container:
            st.markdown("### 📊 분석 진행 상황")
            
            # 전체 진행률 표시
            total_steps = 9  # 전체 단계 수
            main_progress = stqdm(
                total=total_steps,
                desc="🚀 전체 진행률",
                gui=True,
                leave=True,
                colour="green",
                unit="단계"
            )
            
            # 현재 단계 표시
            status_container = st.empty()
            
            # 상세 로그 영역
            with st.expander("📝 상세 처리 내역", expanded=True):
                log_container = st.empty()
                log_messages = []
            
            def add_log(message: str, emoji: str = "ℹ️"):
                """로그 메시지 추가"""
                timestamp = time.strftime("%H:%M:%S")
                log_messages.append(f"[{timestamp}] {emoji} {message}")
                # 최근 10개만 표시
                display_logs = log_messages[-10:]
                log_container.text("\n".join(display_logs))
            
            # 진행 상황 업데이트 콜백
            def progress_callback(step: str, progress: int, message: str):
                """진행 상황 업데이트"""
                # progress 값 검증
                progress = max(0, min(100, progress))
                
                # 상태 메시지 업데이트
                status_container.info(f"🔄 {message}")
                
                # 로그 추가
                if "완료" in message:
                    add_log(message, "✅")
                elif "시작" in message:
                    add_log(message, "🚀")
                elif "오류" in message:
                    add_log(message, "❌")
                else:
                    add_log(message, "⚙️")
                
                # 메인 프로그레스 업데이트 (10% 단위로)
                if progress % 10 == 0 and progress > 0:
                    steps_completed = min(progress // 10, total_steps)  # 최대값 제한
                    current_step = main_progress.n
                    if steps_completed > current_step:
                        main_progress.update(steps_completed - current_step)
            
            # 개별 단계별 처리
            st.markdown("### 🔄 처리 단계별 상세 진행")
            
            # 단계별 컨테이너
            step_containers = {
                'download': st.container(),
                'extract': st.container(),
                'analyze': st.container(),
                'upload': st.container()
            }
            
            # VideoService 호출 (콜백 함수 전달)
            add_log("영상 분석 프로세스 시작", "🎬")
            
            try:
                video = st.session_state.video_service.process_video(
                    video_url,
                    force_reanalyze=False,
                    progress_callback=progress_callback
                )
                
                # 완료
                main_progress.update(total_steps - main_progress.n)
                status_container.success("✅ 모든 처리가 완료되었습니다!")
                add_log("영상 분석 완료", "🎉")
                
            except Exception as e:
                main_progress.close()
                status_container.error(f"❌ 오류 발생: {str(e)}")
                add_log(f"오류 발생: {str(e)}", "❌")
                raise
        
        # 성공 메시지
        st.success(f"✅ 영상 분석이 완료되었습니다! (정밀도 레벨: {current_precision})")
        
        # 처리 이력에 추가
        title = video.metadata.title if video.metadata else "제목 없음"
        add_to_processing_history(video_url, title, current_precision)
        
        # 결과 표시
        display_analysis_results(video)
        
    except ValueError as e:
        st.error(f"❌ 오류: {str(e)}")
        logger.error(f"ValueError: {e}")
        
    except Exception as e:
        st.error(f"❌ 예기치 않은 오류가 발생했습니다: {str(e)}")
        logger.error(f"Exception: {e}")
        if st.session_state.get('debug_mode', False):
            st.text("🐛 디버그 정보:")
            st.code(traceback.format_exc())


def handle_video_analysis_with_substeps(video_url: str, current_precision: int):
    """비디오 분석 처리 - 단계별 서브 프로그레스 표시"""
    try:
        st.markdown("### 📊 영상 분석 진행 상황")
        
        # 전체 진행률
        main_progress = stqdm(
            total=100,
            desc="🎯 전체 진행률",
            gui=True,
            leave=True,
            colour="blue",
            unit="%"
        )
        
        # 현재 상태 표시
        status_text = st.empty()
        
        # 로그 메시지 컨테이너
        log_container = st.container()
        
        # 각 단계별 진행률과 가중치
        steps = {
            'parsing': {'weight': 5, 'desc': '🔍 URL 분석'},
            'checking': {'weight': 5, 'desc': '📊 기존 결과 확인'},
            'download': {'weight': 20, 'desc': '📥 영상 다운로드'},
            'metadata': {'weight': 5, 'desc': '📋 메타데이터 처리'},
            'extract': {'weight': 20, 'desc': '🎬 씬 추출'},
            'analyze': {'weight': 30, 'desc': '🤖 AI 분석'},
            'upload': {'weight': 10, 'desc': '📤 스토리지 업로드'},
            'cleanup': {'weight': 5, 'desc': '🗑️ 정리'}
        }
        
        # 누적 진행률
        cumulative_progress = 0
        
        # 진행 상황 업데이트 함수
        def update_progress(step: str, progress: int, message: str):
            nonlocal cumulative_progress
            
            # 현재 단계의 진행률 계산
            if step in steps:
                step_info = steps[step]
                step_progress = (progress / 100) * step_info['weight']
                
                # 이전 단계들의 가중치 합계
                prev_weight = 0
                for s, info in steps.items():
                    if s == step:
                        break
                    prev_weight += info['weight']
                
                # 전체 진행률 업데이트
                total_progress = min(prev_weight + step_progress, 100)  # 100을 초과하지 않도록 제한
                main_progress.n = int(total_progress)
                main_progress.refresh()
                
                # 상태 텍스트 업데이트
                status_text.markdown(f"**{step_info['desc']}** - {message}")
                
                # 단계별 진행 표시
                with log_container:
                    if progress == 0:
                        st.info(f"{step_info['desc']} 시작...")
                    elif progress == 100:
                        st.success(f"{step_info['desc']} 완료! ✅")
                    else:
                        # 서브 프로그레스 바
                        sub_progress = st.progress(progress / 100)
        
        # VideoService 호출
        video = st.session_state.video_service.process_video(
            video_url,
            force_reanalyze=False,
            progress_callback=update_progress
        )
        
        # 완료
        main_progress.n = 100
        main_progress.refresh()
        status_text.markdown("### ✅ 분석 완료!")
        
        # 결과 요약
        with st.container():
            st.markdown("### 📋 처리 결과 요약")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("영상 제목", video.metadata.title if video.metadata else "Unknown")
            with col2:
                st.metric("추출된 씬", f"{len(video.scenes) if video.scenes else 0}개")
            with col3:
                if video.analysis_result:
                    st.metric("분석 장르", video.analysis_result.get('genre', 'Unknown'))
                else:
                    st.metric("분석 장르", "미분석")
        
        # 성공 메시지
        st.success(f"✅ 영상 분석이 완료되었습니다! (정밀도 레벨: {current_precision})")
        
        # 처리 이력에 추가
        title = video.metadata.title if video.metadata else "제목 없음"
        add_to_processing_history(video_url, title, current_precision)
        
        # 결과 표시
        display_analysis_results(video)
        
    except Exception as e:
        st.error(f"❌ 오류가 발생했습니다: {str(e)}")
        logger.error(f"Exception: {e}")
        if st.session_state.get('debug_mode', False):
            st.text("🐛 디버그 정보:")
            st.code(traceback.format_exc())


def render_video_input_section(current_precision: int):
    """비디오 URL 입력 섹션 렌더링"""
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
    
    # 진행 표시 모드 선택
    progress_mode = st.radio(
        "진행 표시 모드",
        ["기본", "상세"],
        horizontal=True,
        help="상세 모드는 각 단계별 진행률을 자세히 보여줍니다."
    )
    
    # 분석 버튼
    if st.button("🚀 분석 시작", type="primary", use_container_width=True, key="analyze_btn"):
        if not video_url:
            st.error("❌ 영상 URL을 입력해주세요!")
        else:
            if progress_mode == "상세":
                handle_video_analysis_with_substeps(video_url, current_precision)
            else:
                handle_video_analysis(video_url, current_precision)


def render_system_status(current_precision: int):
    """시스템 상태 표시"""
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
    
    db = VideoAnalysisDB()
    stats = db.get_statistics()
    db.close()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("총 분석 영상", f"{stats['total_videos']}개")
    with col2:
        st.metric("오늘 처리", f"{len(st.session_state.processing_history)}개")
    
    # 처리 이력 (stqdm으로 표시)
    st.subheader("📝 최근 처리")
    if st.session_state.processing_history:
        # 최근 처리 항목을 프로그레스 바로 표시
        recent_items = list(reversed(st.session_state.processing_history[-5:]))
        
        for i, item in enumerate(stqdm(recent_items, desc="최근 처리 항목")):
            precision_badge = f"L{item.get('precision_level', '?')}"
            st.caption(f"{item['time']} - {item['title'][:30]}... ({precision_badge})")
            time.sleep(0.1)  # 애니메이션 효과
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
                # 정리 진행률 표시
                progress_bar = stqdm(
                    items,
                    desc="폴더 정리 중",
                    gui=True,
                    leave=False,
                    colour="red"
                )
                
                cleaned = 0
                for item in progress_bar:
                    item_path = os.path.join(temp_dir, item)
                    if os.path.isdir(item_path):
                        try:
                            shutil.rmtree(item_path)
                            cleaned += 1
                            progress_bar.set_postfix({"정리됨": cleaned})
                        except Exception as e:
                            logger.error(f"폴더 삭제 실패: {e}")
                
                st.success(f"✅ {cleaned}개 폴더 정리 완료!")
            else:
                st.info("정리할 임시 파일이 없습니다.")
        else:
            st.info("임시 폴더가 존재하지 않습니다.")