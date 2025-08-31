# app.py
"""
동시 사용자 5명 지원 최적화된 AI 기반 광고 영상 콘텐츠 추론 시스템
"""

from dotenv import load_dotenv
load_dotenv(override=True)

import streamlit as st
import sys
import os
import threading
import time
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 최적화된 모듈 임포트
from utils.session_manager import get_session_manager, get_current_session
from core.database.concurrent_db import get_database
from core.queue.task_queue import get_task_queue, submit_video_analysis_task, TaskStatus
from utils.cache_manager import get_cache_manager
from utils.logger import get_logger

# 기존 컴포넌트 임포트
from web.styles.theme import get_enhanced_styles
from web.pages.analyze import render_analyze_tab
from web.pages.database import render_database_tab
from web.pages.settings import render_settings_tab
from web.pages.dashboard import render_dashboard_tab, get_dashboard_styles
from utils.git_utils import is_beta_branch

logger = get_logger(__name__)


def setup_page():
    """페이지 설정 및 스타일 적용"""
    st.set_page_config(
        page_title="AI 영상 레퍼런스 분석기",
        page_icon="🎥",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # 향상된 CSS 스타일 적용
    st.markdown(get_enhanced_styles(), unsafe_allow_html=True)
    st.markdown(get_dashboard_styles(), unsafe_allow_html=True)
    
    # 세션 상태 초기화 먼저 수행
    from web.state import init_session_state
    init_session_state()
    
    # 시스템 초기화
    init_system()


def init_system():
    """시스템 초기화"""
    try:
        # 세션 관리자 초기화
        session_manager = get_session_manager()
        current_session = get_current_session()
        
        # 데이터베이스 초기화
        db = get_database()
        
        # 작업 큐 초기화
        task_queue = get_task_queue()
        
        # 캐시 관리자 초기화
        cache_manager = get_cache_manager()
        
        # Streamlit 세션 상태에 저장
        if 'system_initialized' not in st.session_state:
            st.session_state.system_initialized = True
            st.session_state.current_session = current_session
            st.session_state.db = db
            st.session_state.task_queue = task_queue
            st.session_state.cache_manager = cache_manager
            
            logger.info(f"시스템 초기화 완료 - 세션: {current_session.session_id[:8]}...")
        
    except Exception as e:
        logger.error(f"시스템 초기화 실패: {e}")
        st.error(f"시스템 초기화 중 오류가 발생했습니다: {e}")
        st.stop()


def render_system_status():
    """시스템 상태 표시 (사이드바)"""
    with st.sidebar:
        st.markdown("### 📊 시스템 상태")
        
        # 세션 정보
        session_manager = get_session_manager()
        session_stats = session_manager.get_session_stats()
        
        st.markdown(f"""
        **🔗 연결 상태**
        - 전체 사용자: {session_stats['total_sessions']}명
        - 활성 사용자: {session_stats['active_sessions']}명
        - 처리 중: {session_stats['processing_sessions']}명
        - 활성 작업: {session_stats['total_active_tasks']}개
        - 최대 사용자: {session_stats['max_concurrent_users']}명
        """)
        
        # 작업 큐 상태
        task_queue = get_task_queue()
        queue_stats = task_queue.get_queue_status()
        
        st.markdown(f"""
        **⚙️ 작업 큐**
        - 대기 중: {queue_stats['queue_size']}개
        - 실행 중: {queue_stats['running_tasks']}개
        - 완료: {queue_stats['stats']['total_completed']}개
        """)
        
        # 시스템 리소스
        system_resources = session_stats.get('system_resources', {})
        if system_resources and 'error' not in system_resources:
            cpu_percent = system_resources.get('cpu_percent', 0)
            memory_percent = system_resources.get('memory_percent', 0)
            
            st.markdown(f"""
            **💻 시스템 리소스**
            - CPU: {cpu_percent:.1f}%
            - 메모리: {memory_percent:.1f}%
            """)
            
            # 리소스 경고
            if cpu_percent > 80 or memory_percent > 85:
                st.warning("⚠️ 시스템 리소스 부족")
        
        # 캐시 상태
        cache_manager = get_cache_manager()
        cache_stats = cache_manager.get_stats()
        
        memory_cache_stats = cache_stats.get('memory_cache', {})
        hit_rate = memory_cache_stats.get('hit_rate', 0) * 100
        
        st.markdown(f"""
        **💾 캐시 상태**
        - 적중률: {hit_rate:.1f}%
        - Redis: {'✅' if cache_stats.get('redis_available') else '❌'}
        """)
        
        # 세션 정리 버튼
        if st.button("🧡 비활성 세션 정리", key="cleanup_sessions"):
            session_manager._cleanup_inactive_sessions()
            st.success("비활성 세션 정리 완료")
            st.rerun()
        
        # 새로고침 버튼
        if st.button("🔄 새로고침", key="refresh_status"):
            st.rerun()


def render_optimized_analyze_tab():
    """최적화된 분석 탭"""
    # 기본 렌더링
    render_analyze_tab()
    
    # 추가 기능: 실시간 작업 상태
    if 'current_task_id' in st.session_state:
        task_id = st.session_state.current_task_id
        task_queue = get_task_queue()
        
        status = task_queue.get_task_status(task_id)
        
        if status == TaskStatus.RUNNING:
            st.info("🔄 분석이 진행 중입니다...")
            
            # 진행률 표시
            progress_placeholder = st.empty()
            
            # 5초마다 상태 확인
            time.sleep(5)
            st.rerun()
            
        elif status == TaskStatus.COMPLETED:
            result = task_queue.get_task_result(task_id)
            if result and result.result:
                st.session_state.analysis_result = result.result
                st.session_state.analysis_state = 'completed'
                del st.session_state.current_task_id
                st.rerun()
                
        elif status == TaskStatus.FAILED:
            result = task_queue.get_task_result(task_id)
            error_msg = result.error if result else "알 수 없는 오류"
            st.error(f"❌ 분석 실패: {error_msg}")
            st.session_state.analysis_state = 'idle'
            del st.session_state.current_task_id


def handle_optimized_video_analysis(video_url: str, model_name: str = "gpt-4o"):
    """최적화된 비디오 분석 처리"""
    try:
        session_manager = get_session_manager()
        current_session = get_current_session()
        
        # 동시 작업 제한 확인
        if not session_manager.start_task(current_session.session_id, f"analysis_{video_url}"):
            st.warning("⏳ 시스템이 바쁩니다. 잠시 후 다시 시도해주세요.")
            return
        
        # 캐시 확인
        cache_manager = get_cache_manager()
        cached_result = cache_manager.get_video_analysis(video_url)
        
        if cached_result:
            st.success("✅ 캐시된 분석 결과를 사용합니다.")
            st.session_state.analysis_result = cached_result
            st.session_state.analysis_state = 'completed'
            session_manager.end_task(current_session.session_id, f"analysis_{video_url}")
            return
        
        # 비동기 작업 제출
        def progress_callback(message: str):
            # 실시간 진행 상황은 별도 처리
            logger.info(f"Progress: {message}")
        
        task_id = submit_video_analysis_task(
            url=video_url,
            session_id=current_session.session_id,
            model_name=model_name,
            progress_callback=progress_callback
        )
        
        st.session_state.current_task_id = task_id
        st.session_state.analysis_state = 'processing'
        
        st.info("🚀 분석 작업이 큐에 추가되었습니다.")
        
    except Exception as e:
        logger.error(f"비디오 분석 오류: {e}")
        st.error(f"분석 중 오류가 발생했습니다: {e}")
        
        # 작업 종료 처리
        session_manager = get_session_manager()
        current_session = get_current_session()
        session_manager.end_task(current_session.session_id, f"analysis_{video_url}")
        
        # 추가: 분석 완료 후 세션 상태 업데이트
        session_manager.mark_pipeline_completed(current_session.session_id)


def render_health_check():
    """시스템 상태 확인 페이지"""
    st.markdown("### 🏥 시스템 헬스 체크")
    
    # 컴포넌트 상태 확인
    checks = []
    
    try:
        # 세션 관리자
        session_manager = get_session_manager()
        stats = session_manager.get_session_stats()
        checks.append(("세션 관리자", "✅", f"{stats['total_sessions']}개 세션"))
    except Exception as e:
        checks.append(("세션 관리자", "❌", str(e)))
    
    try:
        # 데이터베이스
        db = get_database()
        db_stats = db.get_statistics()
        checks.append(("데이터베이스", "✅", f"{db_stats['total_videos']}개 비디오"))
    except Exception as e:
        checks.append(("데이터베이스", "❌", str(e)))
    
    try:
        # 작업 큐
        task_queue = get_task_queue()
        queue_stats = task_queue.get_queue_status()
        checks.append(("작업 큐", "✅", f"{queue_stats['running_tasks']}개 실행 중"))
    except Exception as e:
        checks.append(("작업 큐", "❌", str(e)))
    
    try:
        # 캐시
        cache_manager = get_cache_manager()
        cache_stats = cache_manager.get_stats()
        memory_stats = cache_stats.get('memory_cache', {})
        hit_rate = memory_stats.get('hit_rate', 0) * 100
        checks.append(("캐시 시스템", "✅", f"적중률 {hit_rate:.1f}%"))
    except Exception as e:
        checks.append(("캐시 시스템", "❌", str(e)))
    
    # 결과 표시
    for component, status, details in checks:
        col1, col2, col3 = st.columns([2, 1, 3])
        with col1:
            st.write(component)
        with col2:
            st.write(status)
        with col3:
            st.write(details)


def main():
    """메인 앱 함수"""
    # 페이지 설정
    setup_page()
    
    # 시스템 상태 사이드바
    render_system_status()
    
    # 메인 헤더
    if is_beta_branch():
        st.markdown("""
            <div class="main-header">
                <h1 class="main-title">Sense of Frame <span style="font-size: 0.5em; color: #ff6b6b; vertical-align: super;">[BETA]</span></h1>
                <p class="powered-by">Powered by greatminds.</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div class="main-header">
                <h1 class="main-title">Sense of Frame</h1>
                <p class="powered-by">Powered by greatminds.</p>
            </div>
        """, unsafe_allow_html=True)
    
    # 탭 생성
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "ANALYZE", 
        "DASHBOARD",
        "DATABASE", 
        "SETTINGS",
        "SYSTEM"
    ])
    
    with tab1:
        render_optimized_analyze_tab()
    
    with tab2:
        render_dashboard_tab()
    
    with tab3:
        render_database_tab()
    
    with tab4:
        render_settings_tab()
    
    with tab5:
        render_health_check()
    
    # Footer
    if is_beta_branch():
        # 베타 버전 표시가 포함된 footer
        st.markdown("""
            <div class="footer">
                <div style="background-color: #ff6b6b; color: white; padding: 10px; text-align: center; margin-bottom: 20px; border-radius: 5px;">
                    <strong>⚠️ BETA VERSION ⚠️</strong><br>
                    <small>This is a beta version for testing. Features may be unstable.</small>
                </div>
                <p>서강대학교 미디어커뮤니케이션 대학원</p>
                <p>인공지능버추얼콘텐츠 전공 C65028 김윤섭</p>
                <p><small>Optimized for concurrent users with session management, caching, and task queuing</small></p>
                <hr style="margin: 20px 0 10px 0; border: 0; border-top: 1px solid #333;">
                <details style="margin-top: 10px;">
                    <summary style="cursor: pointer; font-weight: bold;">📋 Version History</summary>
                    <div style="padding: 10px 0; font-size: 0.85em; line-height: 1.6;">
                        <p><strong>v2.10.4</strong> (2025-01-29) - Vimeo URL 라우팅 문제 수정</p>
                        <p><strong>v2.10.3</strong> (2025-01-29) - Vimeo 401 Unauthorized 오류 해결 (브라우저 쿠키 인증)</p>
                        <p><strong>v2.10.2</strong> (2025-01-29) - Vimeo OAuth 오류 완전 해결 (Player URL 대안 사용)</p>
                        <p><strong>v2.10.1</strong> (2025-01-29) - Vimeo OAuth 오류 수정 (Android API 비활성화)</p>
                        <p><strong>v2.10.0</strong> (2025-01-29) - Docker 환경변수 경로 설정 기능 추가</p>
                        <p><strong>v2.9.1</strong> (2025-01-29) - Footer HTML 렌더링 문제 수정</p>
                        <p><strong>v2.9.0</strong> (2025-01-29) - 브랜치별 베타 버전 자동 표시 기능 추가</p>
                        <p><strong>v2.8.1</strong> (2025-01-23) - Shorts 감지 로직 개선 (URL 패턴 기반)</p>
                        <p><strong>v2.8.0</strong> (2025-01-23) - YouTube Shorts/Reels 지원 추가</p>
                        <p><strong>v2.7.0</strong> (2025-01-23) - 고화질 비디오 다운로드 설정 개선</p>
                        <p><strong>v2.6.5</strong> (2025-01-23) - 분석 실행 로직 수정 및 UI 플래그 분리</p>
                        <p><strong>v2.6.4</strong> (2025-01-23) - 상세 분석 UI 레이아웃 개선 및 세로 배치로 변경</p>
                        <p><strong>v2.6.3</strong> (2025-01-23) - 분석하기 버튼 클릭 시 상세 분석 UI 완전 숨김 처리</p>
                        <p><strong>v2.6.2</strong> (2025-01-23) - 구버전 히스토리 정리 및 UI 개선</p>
                        <p><strong>v2.6.1</strong> (2025-01-23) - 자동 배포 워크플로우 & 버전 관리 시스템 추가</p>
                        <p><strong>v2.6.0</strong> (2025-01-23) - Phase 2 완료: 실시간 대시보드 및 동적 애니메이션 구현</p>
                        <p><strong>v2.5.0</strong> (2025-01-23) - Phase 1 UI 통합: 맞춤형 프롬프트 시스템 구현</p>
                        <p><strong>v2.4.1</strong> (2025-01-22) - 비디오 다운로드 안정성 개선</p>
                        <p><strong>v2.4.0</strong> (2025-01-21) - Chrome agent 지원 추가</p>
                        <p><strong>v2.3.2</strong> (2025-01-20) - Parser 및 AI Analyzer 버그 수정</p>
                        <p><strong>v2.3.0</strong> (2025-01-19) - 동시 사용자 5명 지원 최적화 완료</p>
                    </div>
                </details>
            </div>
        """, unsafe_allow_html=True)
    else:
        # 일반 버전 footer
        st.markdown("""
            <div class="footer">
                <p>서강대학교 미디어커뮤니케이션 대학원</p>
                <p>인공지능버추얼콘텐츠 전공 C65028 김윤섭</p>
                <p><small>Optimized for concurrent users with session management, caching, and task queuing</small></p>
                <hr style="margin: 20px 0 10px 0; border: 0; border-top: 1px solid #333;">
                <details style="margin-top: 10px;">
                    <summary style="cursor: pointer; font-weight: bold;">📋 Version History</summary>
                    <div style="padding: 10px 0; font-size: 0.85em; line-height: 1.6;">
                        <p><strong>v2.10.4</strong> (2025-01-29) - Vimeo URL 라우팅 문제 수정</p>
                        <p><strong>v2.10.3</strong> (2025-01-29) - Vimeo 401 Unauthorized 오류 해결 (브라우저 쿠키 인증)</p>
                        <p><strong>v2.10.2</strong> (2025-01-29) - Vimeo OAuth 오류 완전 해결 (Player URL 대안 사용)</p>
                        <p><strong>v2.10.1</strong> (2025-01-29) - Vimeo OAuth 오류 수정 (Android API 비활성화)</p>
                        <p><strong>v2.10.0</strong> (2025-01-29) - Docker 환경변수 경로 설정 기능 추가</p>
                        <p><strong>v2.9.1</strong> (2025-01-29) - Footer HTML 렌더링 문제 수정</p>
                        <p><strong>v2.9.0</strong> (2025-01-29) - 브랜치별 베타 버전 자동 표시 기능 추가</p>
                        <p><strong>v2.8.1</strong> (2025-01-23) - Shorts 감지 로직 개선 (URL 패턴 기반)</p>
                        <p><strong>v2.8.0</strong> (2025-01-23) - YouTube Shorts/Reels 지원 추가</p>
                        <p><strong>v2.7.0</strong> (2025-01-23) - 고화질 비디오 다운로드 설정 개선</p>
                        <p><strong>v2.6.5</strong> (2025-01-23) - 분석 실행 로직 수정 및 UI 플래그 분리</p>
                        <p><strong>v2.6.4</strong> (2025-01-23) - 상세 분석 UI 레이아웃 개선 및 세로 배치로 변경</p>
                        <p><strong>v2.6.3</strong> (2025-01-23) - 분석하기 버튼 클릭 시 상세 분석 UI 완전 숨김 처리</p>
                        <p><strong>v2.6.2</strong> (2025-01-23) - 구버전 히스토리 정리 및 UI 개선</p>
                        <p><strong>v2.6.1</strong> (2025-01-23) - 자동 배포 워크플로우 & 버전 관리 시스템 추가</p>
                        <p><strong>v2.6.0</strong> (2025-01-23) - Phase 2 완료: 실시간 대시보드 및 동적 애니메이션 구현</p>
                        <p><strong>v2.5.0</strong> (2025-01-23) - Phase 1 UI 통합: 맞춤형 프롬프트 시스템 구현</p>
                        <p><strong>v2.4.1</strong> (2025-01-22) - 비디오 다운로드 안정성 개선</p>
                        <p><strong>v2.4.0</strong> (2025-01-21) - Chrome agent 지원 추가</p>
                        <p><strong>v2.3.2</strong> (2025-01-20) - Parser 및 AI Analyzer 버그 수정</p>
                        <p><strong>v2.3.0</strong> (2025-01-19) - 동시 사용자 5명 지원 최적화 완료</p>
                    </div>
                </details>
            </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"애플리케이션 치명적 오류: {e}")
        st.error("시스템에 치명적인 오류가 발생했습니다. 관리자에게 문의하세요.")
        st.stop()
