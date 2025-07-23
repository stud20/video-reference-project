# src/ui/tabs/analyze_tab.py
"""
Analyze 탭 - 실시간 로그 모니터링 (새 버전)
"""

import streamlit as st
import time
import os
from core.handlers import handle_video_analysis_enhanced
from web.state import get_analysis_state, set_analysis_state
from utils.logger import get_logger
from web.components.analyze import render_results_section, render_modals
from web.components.analyze.custom_prompt import render_custom_analysis_prompt
from web.utils.analysis_state import reset_analysis_state

logger = get_logger(__name__)


def handle_chrome_extension_integration():
    """크롬 확장프로그램 연동 처리"""
    query_params = st.query_params
    video_url = query_params.get('video')
    
    if video_url:
        st.markdown("""
            <div style="
                background: linear-gradient(135deg, #4CAF50, #45a049);
                color: white;
                padding: 12px 20px;
                border-radius: 8px;
                margin-bottom: 20px;
                text-align: center;
                box-shadow: 0 4px 8px rgba(76, 175, 80, 0.3);
                font-weight: 500;
            ">
                🔗 크롬 확장프로그램을 통해 연결되었습니다
            </div>
        """, unsafe_allow_html=True)
        
        st.session_state.analyze_url_input = video_url
        
        if 'chrome_extension_auto_start' not in st.session_state:
            st.session_state.chrome_extension_auto_start = True
            st.session_state.selected_model = 'gpt-4o'
            st.session_state.current_video_url = video_url
            set_analysis_state('processing')
            st.rerun()


def render_version_history():
    """버전 히스토리 렌더링"""
    st.markdown("""
        <div style="
            background: linear-gradient(135deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 8px;
            padding: 16px;
            margin: 20px auto;
            max-width: 600px;
            backdrop-filter: blur(10px);
            opacity: 0.6;
            transition: opacity 0.3s ease;
        ">
            <div style="
                font-size: 12px;
                color: rgba(255,255,255,0.5);
                line-height: 1.4;
                font-family: 'SF Pro Text', -apple-system, BlinkMacSystemFont, sans-serif;
            ">
                <div style="margin-bottom: 8px;"><strong style="color: rgba(255,255,255,0.7);">v2.1.0</strong> - 동시 사용자 5명 지원, Redis 캐시, SQLite 커넥션 풀링 추가</div>
                <div style="margin-bottom: 8px;"><strong style="color: rgba(255,255,255,0.7);">v2.0.0</strong> - 세션 관리 시스템, 비동기 작업 큐, 리소스 모니터링 도입</div>
                <div style="margin-bottom: 8px;"><strong style="color: rgba(255,255,255,0.7);">v1.2.0</strong> - 멀티 AI 모델 지원 (GPT-4o, Claude Sonnet 4, Gemini), UI/UX 개선</div>
                <div style="margin-bottom: 8px;"><strong style="color: rgba(255,255,255,0.7);">v1.1.0</strong> - Pipeline 기반 비디오 처리, Notion 연동, 데이터베이스 기능 추가</div>
                <div><strong style="color: rgba(255,255,255,0.7);">v1.0.0</strong> - 초기 버전, YouTube/Vimeo 영상 분석, 씨네 추출, AI 분석 기본 기능</div>
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_input_section():
    """URL 입력 섹션"""
    handle_chrome_extension_integration()
    
    st.markdown("""
        <div class="usage-guide">
            <h3 class="usage-title">광고 레퍼런스를 분석하세요</h3>
            <div class="usage-steps">
                <div class="usage-step">
                    <div class="step-number">1</div>
                    <div class="step-content">
                        <h4>URL 입력</h4>
                        <p>YouTube 또는 Vimeo 영상 링크를 입력하세요</p>
                    </div>
                </div>
                <div class="usage-step">
                    <div class="step-number">2</div>
                    <div class="step-content">
                        <h4>AI 분석</h4>
                        <p>선택한 AI 모델이 영상을 심층 분석합니다</p>
                    </div>
                </div>
                <div class="usage-step">
                    <div class="step-number">3</div>
                    <div class="step-content">
                        <h4>인사이트 확인</h4>
                        <p>장르, 무드보드, 메타데이터를 확인하세요</p>
                    </div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="input-section-wrapper">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
            <div style="display: flex; justify-content: center; align-items: center; margin-bottom: 16px;">
            """, unsafe_allow_html=True)
        
        model_selection = st.radio(
            "AI 모델",
            options=[
                ("gemini-2.0-flash", "⚡ 빠른 분석 (Google Gemini)"),
                ("gpt-4o", "🤖 균형 분석 (GPT-4o)"),
                ("claude-sonnet-4-20250514", "🧠 상세 분석 (Claude Sonnet 4)")
            ],
            format_func=lambda x: x[1],
            index=1,
            key="model_selection",
            label_visibility="collapsed",
            horizontal=True
        )
        st.markdown("</div>", unsafe_allow_html=True)

        input_col, btn_col = st.columns([3, 1])
        
        with input_col:
            video_url = st.text_input(
                "URL",
                placeholder="유튜브, 비메오 동영상 링크를 넣어주세요",
                label_visibility="collapsed",
                key="analyze_url_input"
            )
        
        with btn_col:
            analyze_button = st.button(
                "분석하기",
                type="primary",
                key="analyze_start_button",
                use_container_width=True
            )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Phase 1: 맞춤형 분석 프롬프트 - 체크박스와 아코디언
    # idle 상태에서만 표시
    if get_analysis_state() == 'idle':
        with col2:
            use_custom_prompt = st.checkbox(
                "🎯 상세 분석 요청사항 추가",
                key="use_custom_prompt",
                help="특정 목적에 맞는 맞춤형 분석을 원하시면 체크하세요"
            )
            
            if use_custom_prompt:
                with st.expander("상세 분석 설정", expanded=True):
                    custom_prompt = render_custom_analysis_prompt()
                    if custom_prompt:
                        st.session_state.custom_analysis_prompt = custom_prompt
            else:
                # 체크박스 해제 시 custom_prompt 초기화
                if 'custom_analysis_prompt' in st.session_state:
                    del st.session_state.custom_analysis_prompt
    
    # 메인 화면에서만 버전 히스토리 표시
    if get_analysis_state() == 'idle':
        render_version_history()
    
    if analyze_button and video_url:
        set_analysis_state('processing')
        st.session_state.current_video_url = video_url
        st.session_state.selected_model = model_selection[0]
        st.rerun()
    elif analyze_button:
        st.error("URL을 입력해주세요!")


def render_processing_section():
    """처리 중 섹션 - progress_callback 기반 실시간 업데이트"""
    video_url = st.session_state.get('current_video_url')
    if not video_url:
        st.error("비디오 URL이 존재하지 않습니다.")
        return

    # 비디오 임베드
    from web.components.analyze.results import render_video_embed
    render_video_embed(video_url)

    # 전체 진행률 표시
    st.markdown("### 🎬 영상 분석 진행 상황")
    
    # 프로그레스 바 및 상태 표시
    progress_col1, progress_col2 = st.columns([3, 1])
    
    with progress_col1:
        main_progress = st.progress(0)
        stage_info = st.empty()
    
    with progress_col2:
        elapsed_time = st.empty()
        estimated_time = st.empty()
    
    # 실시간 콘솔 로그
    st.markdown("#### 💻 실시간 로그")
    console_placeholder = st.empty()
    
    # 세션 상태 초기화
    if 'processing_data' not in st.session_state:
        st.session_state.processing_data = {
            'start_time': time.time(),
            'console_logs': [],
            'current_progress': 0,
            'current_stage': 'init'
        }
    
    # 콘솔 업데이트 함수
    def update_console_display(logs):
        """콘솔 화면 업데이트"""
        if logs:
            console_text = "\n".join(logs)
            console_placeholder.markdown(
                f"""
                <div style="
                    background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
                    color: #00ff41;
                    padding: 20px;
                    border-radius: 10px;
                    font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
                    font-size: 13px;
                    line-height: 1.6;
                    height: 200px;
                    overflow-y: auto;
                    white-space: pre-wrap;
                    border: 1px solid #333;
                    box-shadow: inset 0 2px 4px rgba(0,0,0,0.5);
                ">
{console_text}
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            console_placeholder.markdown(
                """
                <div style="
                    background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
                    color: #888;
                    padding: 20px;
                    border-radius: 10px;
                    font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
                    font-size: 13px;
                    line-height: 1.6;
                    height: 200px;
                    border: 1px solid #333;
                    text-align: center;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                ">
                    분석 시작 대기 중...
                </div>
                """,
                unsafe_allow_html=True
            )
    
    # progress_callback 함수 - 실시간 업데이트
    def update_progress_and_console(stage: str, progress: int, message: str, detailed_message: str = None):
        """실시간 프로그레스 및 콘솔 업데이트"""
        # 스테이지별 가중치
        stage_weights = {
            'url_parser': 5,
            'download': 30,
            'scene_extraction': 40,
            'ai_analysis': 20,
            'metadata_save': 3,
            'storage_upload': 1,
            'cleanup': 1
        }
        
        # 전체 진행률 계산
        stage_order = ['url_parser', 'download', 'scene_extraction', 'ai_analysis', 'metadata_save', 'storage_upload', 'cleanup']
        current_stage_index = stage_order.index(stage) if stage in stage_order else 0
        
        total_progress = 0
        # 이전 완료된 스테이지들
        for i in range(current_stage_index):
            total_progress += stage_weights.get(stage_order[i], 0)
        # 현재 스테이지 진행률
        total_progress += (progress / 100) * stage_weights.get(stage, 0)
        
        # UI 업데이트
        main_progress.progress(min(total_progress / 100, 1.0))
        stage_info.markdown(f"**{message}**")
        
        # 시간 정보 업데이트
        elapsed = time.time() - st.session_state.processing_data['start_time']
        elapsed_time.markdown(f"**경과 시간**: {elapsed:.1f}초")
        
        if total_progress > 0:
            estimated_total = elapsed * (100 / total_progress)
            remaining = max(estimated_total - elapsed, 0)
            estimated_time.markdown(f"**예상 완료**: {remaining:.1f}초")
        
        # 콘솔 로그 업데이트
        timestamp = time.strftime('%H:%M:%S')
        formatted_message = f"[{timestamp}] {message}"
        
        st.session_state.processing_data['console_logs'].append(formatted_message)
        # 최대 12개 로그 유지
        if len(st.session_state.processing_data['console_logs']) > 12:
            st.session_state.processing_data['console_logs'] = st.session_state.processing_data['console_logs'][-12:]
        
        # 콘솔 화면 즉시 업데이트
        update_console_display(st.session_state.processing_data['console_logs'])
        
        # 세션 상태 업데이트
        st.session_state.processing_data['current_progress'] = total_progress
        st.session_state.processing_data['current_stage'] = stage
    
    # 초기 콘솔 표시
    update_console_display(st.session_state.processing_data['console_logs'])
    
    # 분석 실행 (한 번만)
    if 'analysis_started' not in st.session_state:
        st.session_state.analysis_started = True
        
        try:
            precision_level = st.session_state.get('precision_level', 5)
            selected_model = st.session_state.get('selected_model', 'gpt-4o')
            custom_prompt = st.session_state.get('custom_analysis_prompt', None)
            
            model_display_names = {
                "gemini-2.0-flash": "Google Gemini",
                "gpt-4o": "GPT-4o",
                "claude-sonnet-4-20250514": "Claude Sonnet 4"
            }
            
            # 초기 메시지에 커스텀 프롬프트 사용 여부 표시
            init_message = f"🤖 AI 모델: {model_display_names.get(selected_model, selected_model)}"
            if custom_prompt:
                init_message += " (맞춤형 분석)"
            update_progress_and_console("init", 0, init_message)

            # 분석 실행
            video = handle_video_analysis_enhanced(
                video_url=video_url,
                precision_level=precision_level,
                console_callback=lambda msg: None,  # 콘솔 콜백 비활성화
                model_name=selected_model,
                progress_callback=update_progress_and_console,  # 실시간 업데이트
                custom_prompt=custom_prompt  # 커스텀 프롬프트 전달
            )

            # 결과 처리
            if video and hasattr(video, 'url') and hasattr(video, 'session_id'):
                update_progress_and_console("completed", 100, "✅ 분석 완료!")
                st.session_state.analysis_result = video
                
                # 상태 정리
                if 'processing_data' in st.session_state:
                    del st.session_state.processing_data
                if 'analysis_started' in st.session_state:
                    del st.session_state.analysis_started
                
                set_analysis_state('completed')
                logger.info(f"Analysis completed successfully for video: {video.session_id}")
                
                # 완료 후 결과 페이지로 이동
                time.sleep(2)
                st.rerun()
            else:
                raise ValueError("Invalid video object returned from analysis")

        except Exception as e:
            logger.error(f"Analysis error: {str(e)}")
            update_progress_and_console("error", 0, f"❌ 오류 발생: {str(e)}")
            st.error(f"분석 중 오류 발생: {str(e)}")
            
            # 상태 정리
            if 'processing_data' in st.session_state:
                del st.session_state.processing_data
            if 'analysis_started' in st.session_state:
                del st.session_state.analysis_started
            
            set_analysis_state('idle')
            time.sleep(3)
            st.rerun()


def render_analyze_tab():
    """Analyze 탭 메인 렌더링"""
    render_modals()
    
    # 세션 상태 검증
    if 'analysis_result' in st.session_state:
        result = st.session_state.analysis_result
        if result.__class__.__name__ == 'AnalysisResult':
            logger.warning("Found AnalysisResult instead of Video object, resetting state")
            del st.session_state.analysis_result
            set_analysis_state('idle')
    
    # 분석 상태에 따른 화면 렌더링
    analysis_state = get_analysis_state()
    
    if analysis_state == 'idle':
        render_input_section()
    elif analysis_state == 'processing':
        render_processing_section()
    elif analysis_state == 'completed':
        render_results_section()
