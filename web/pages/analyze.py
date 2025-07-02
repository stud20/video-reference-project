# src/ui/tabs/analyze_tab.py
"""
Analyze 탭 - 메인 진입점 및 URL 입력/분석 처리
"""

import streamlit as st
import time
from core.handlers import handle_video_analysis_enhanced
from web.state import get_analysis_state, set_analysis_state
from utils.logger import get_logger
from web.styles.theme import get_enhanced_styles  # 스타일 import 추가
from web.components.analyze import render_results_section, render_modals
from web.utils.analysis_state import reset_analysis_state

logger = get_logger(__name__)


def render_analyze_tab():
    """Analyze 탭 렌더링"""
    # 스타일 적용
    # 모달 처리
    render_modals()
    
    # 세션 상태 검증 - AnalysisResult 객체가 잘못 저장된 경우 처리
    if 'analysis_result' in st.session_state:
        result = st.session_state.analysis_result
        # AnalysisResult 타입이면 제거하고 idle로 전환
        if result.__class__.__name__ == 'AnalysisResult':
            logger.warning("Found AnalysisResult instead of Video object, resetting state")
            del st.session_state.analysis_result
            set_analysis_state('idle')
    
    # 분석 상태 확인
    analysis_state = get_analysis_state()
    
    if analysis_state == 'idle':
        render_input_section()
    elif analysis_state == 'processing':
        render_processing_section()
    elif analysis_state == 'completed':
        render_results_section()
        # analyze_tab.py의 render_input_section() 수정

def render_input_section():
    """URL 입력 섹션 - Figma 디자인"""
    
    # 사용방법 안내
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
    
    # 화면 중앙 정렬을 위한 컨테이너
    st.markdown('<div class="input-section-wrapper">', unsafe_allow_html=True)
    
    # 중앙 정렬을 위한 컬럼 구조
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # 입력창과 버튼을 같은 줄에 배치
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
        
        # 모델 선택 섹션
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 🤖 추론 모델 선택")
        
        model_selection = st.radio(
            "AI 모델",
            options=[
                ("gemini-2.0-flash", "⚡ 빠른 분석 (Google Gemini)"),
                ("gpt-4o", "🤖 균형 분석 (GPT-4o)"),
                ("claude-sonnet-4-20250514", "🧠 상세 분석 (Claude Sonnet 4)")
            ],
            format_func=lambda x: x[1],
            index=1,  # 기본값: GPT-4o
            key="model_selection",
            label_visibility="collapsed",
            horizontal=True
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 분석 시작 처리
    if analyze_button and video_url:
        set_analysis_state('processing')
        st.session_state.current_video_url = video_url
        st.session_state.selected_model = model_selection[0]  # 모델 ID 저장
        st.rerun()
    elif analyze_button:
        st.error("URL을 입력해주세요!")

def render_processing_section():
    """처리 중 섹션"""
    video_url = st.session_state.get('current_video_url')
    if not video_url:
        st.error("비디오 URL이 존재하지 않습니다.")
        return

    # 비디오 임베드
    from web.components.analyze.results import render_video_embed
    render_video_embed(video_url)

    # 콘솔창
    st.markdown("### 💻 처리 상황")
    console_container = st.container()
    
    with console_container:
        console_placeholder = st.empty()
    
    # 로그 라인 저장용
    if 'console_logs' not in st.session_state:
        st.session_state.console_logs = []
    
    def update_console(message: str):
        """콘솔 업데이트"""
        st.session_state.console_logs.append(f"> {message}")
        if len(st.session_state.console_logs) > 3:
            st.session_state.console_logs.pop(0)
        
        console_text = "\n".join(st.session_state.console_logs)
        console_placeholder.markdown(
            f"""
            <div style="
                background-color: #1e1e1e;
                color: #00ff00;
                padding: 15px;
                border-radius: 5px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 14px;
                height: 150px;
                overflow-y: auto;
                white-space: pre-wrap;
            ">
{console_text}
            </div>
            """,
            unsafe_allow_html=True
        )

    try:
        st.session_state.console_logs = []
        precision_level = st.session_state.get('precision_level', 5)
        selected_model = st.session_state.get('selected_model', 'gpt-4o')  # 기본값: GPT-4o
        
        # 모델 이름 표시
        model_display_names = {
            "gemini-2.0-flash": "Google Gemini",
            "gpt-4o": "GPT-4o",
            "claude-sonnet-4-20250514": "Claude Sonnet 4"
        }
        update_console(f"🤖 선택된 AI 모델: {model_display_names.get(selected_model, selected_model)}")

        video = handle_video_analysis_enhanced(
            video_url=video_url,
            precision_level=precision_level,
            console_callback=update_console,
            model_name=selected_model  # 선택된 모델 전달
        )

        # video 객체 검증
        if video and hasattr(video, 'url') and hasattr(video, 'session_id'):
            st.session_state.analysis_result = video
            st.session_state.console_logs = []
            set_analysis_state('completed')
            logger.info(f"Analysis completed successfully for video: {video.session_id}")
        else:
            raise ValueError("Invalid video object returned from analysis")
        
        st.rerun()

    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        st.error(f"분석 중 오류 발생: {str(e)}")
        st.session_state.console_logs = []
        set_analysis_state('idle')
        st.rerun()
