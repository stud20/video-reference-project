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


def handle_chrome_extension_integration():
    """크롬 확장프로그램 연동 처리"""
    # URL 파라미터에서 비디오 URL 추출
    query_params = st.query_params
    video_url = query_params.get('video')
    
    if video_url:
        # 확장프로그램을 통한 접근임을 표시
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
        
        # 자동으로 URL 입력 필드에 값 설정
        st.session_state.analyze_url_input = video_url
        
        # 자동 분석 시작
        if 'chrome_extension_auto_start' not in st.session_state:
            st.session_state.chrome_extension_auto_start = True
            # 기본 모델로 자동 분석 시작
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
    
    # 크롬 확장프로그램 연동 처리
    handle_chrome_extension_integration()
    
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

        # 중앙 정렬을 위해 radio를 감싸는 div 추가
        st.markdown(
            """
            <div style="display: flex; justify-content: center; align-items: center; margin-bottom: 16px;">
            """,
            unsafe_allow_html=True
        )
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
        st.markdown("</div>", unsafe_allow_html=True)

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

    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 버전 히스토리 추가
    render_version_history()
    
    # 분석 시작 처리
    if analyze_button and video_url:
        set_analysis_state('processing')
        st.session_state.current_video_url = video_url
        st.session_state.selected_model = model_selection[0]  # 모델 ID 저장
        st.rerun()
    elif analyze_button:
        st.error("URL을 입력해주세요!")

def render_processing_section():
    """처리 중 섹션 - 향상된 콘솔 및 프로그레스 바"""
    video_url = st.session_state.get('current_video_url')
    if not video_url:
        st.error("비디오 URL이 존재하지 않습니다.")
        return

    # 비디오 임베드
    from web.components.analyze.results import render_video_embed
    render_video_embed(video_url)

    # 처리 상태 초기화
    if 'processing_state' not in st.session_state:
        st.session_state.processing_state = {
            'current_stage': 'init',
            'progress': 0,
            'total_stages': 7,
            'console_logs': [],
            'stage_progress': {},
            'start_time': time.time()
        }
    
    # 전체 진행률 표시
    st.markdown("### 🎬 영상 분석 진행 상황")
    
    # 메인 프로그레스 바만 표시
    progress_col1, progress_col2 = st.columns([3, 1])
    
    with progress_col1:
        main_progress = st.progress(0)
        stage_info = st.empty()
    
    with progress_col2:
        elapsed_time = st.empty()
        estimated_time = st.empty()
    
    # 단계 정의 (프로그레스 바는 제거)
    stages = [
        ("url_parser", "🔍 URL 분석"),
        ("download", "📥 영상 다운로드"),
        ("scene_extraction", "🎞️ 장면 추출"),
        ("ai_analysis", "🤖 AI 분석"),
        ("metadata_save", "💾 메타데이터 저장"),
        ("storage_upload", "☁️ 스토리지 업로드"),
        ("cleanup", "🧹 정리")
    ]
    
    # 실시간 콘솔 로그
    st.markdown("#### 💻 실시간 로그")
    console_placeholder = st.empty()
    
    # 로그 모니터링을 위한 상태 초기화
    if 'real_time_logs' not in st.session_state:
        st.session_state.real_time_logs = []
        st.session_state.last_log_check = time.time()
    
    # 실시간 로그 업데이트 함수
    def check_and_update_logs():
        """1초마다 로그 파일 확인 및 업데이트"""
        current_time = time.time()
        if current_time - st.session_state.last_log_check >= 1.0:  # 1초마다
            try:
                import datetime
                today = datetime.datetime.now().strftime('%Y%m%d')
                log_file_path = f"logs/{today}.log"
                
                if os.path.exists(log_file_path):
                    with open(log_file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        # 마지막 10줄에서 관련 로그만 추출
                        recent_lines = lines[-20:] if len(lines) > 20 else lines
                        
                        new_logs = []
                        for line in recent_lines:
                            if any(keyword in line for keyword in 
                                   ['영상', '다운로드', '분석', '장면', 'AI', '완료', '시작']):
                                formatted_line = line.strip()
                                if formatted_line and formatted_line not in st.session_state.real_time_logs:
                                    new_logs.append(formatted_line)
                        
                        # 새로운 로그 추가
                        st.session_state.real_time_logs.extend(new_logs)
                        
                        # 로그 개수 제한
                        if len(st.session_state.real_time_logs) > 10:
                            st.session_state.real_time_logs = st.session_state.real_time_logs[-10:]
                        
                        # 콘솔 업데이트
                        if st.session_state.real_time_logs:
                            console_text = "\n".join(st.session_state.real_time_logs)
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
                
                st.session_state.last_log_check = current_time
                
            except Exception as e:
                # 로그 모니터링 에러는 조용히 처리
                pass
    
    # 자동 새로고침 제거 - 분석 중단 문제 해결
    # if st.session_state.get('auto_refresh_active', False):
    #     time.sleep(1.0)
    #     st.rerun()
    
    # 대신 매누얼 새로고침 버튼 추가
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔄 로그 새로고침", key="manual_refresh"):
            check_and_update_logs()
            st.rerun()
    
    # 실시간 로그 읽기 기능 추가
    def read_real_time_logs():
        """실제 로그 파일에서 최신 로그를 읽어오기"""
        try:
            # 로그 파일 경로 (예: logs/app.log)
            log_file_path = "logs/app.log"
            if os.path.exists(log_file_path):
                with open(log_file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # 마지막 10줄만 가져오기
                    recent_lines = lines[-10:] if len(lines) > 10 else lines
                    return [line.strip() for line in recent_lines if line.strip()]
        except Exception as e:
            logger.error(f"로그 읽기 오류: {e}")
        return []
    
    # 자동 새로고침 설정 (처리 중일 때만)
    if st.session_state.processing_state.get('auto_refresh', True):
        # 마지막 업데이트 시간 확인
        current_time = time.time()
        last_update = st.session_state.processing_state.get('last_update_time', current_time)
        
        # 1초마다 자동 새로고침
        if current_time - last_update >= 1.0:
            st.session_state.processing_state['last_update_time'] = current_time
            time.sleep(0.1)  # 짧은 대기
            st.rerun()
    
    def update_progress_and_console(stage: str, progress: int, message: str, detailed_message: str = None):
        """프로그레스 바와 콘솔 업데이트"""
        current_time = time.time()
        
        # 처리 상태 업데이트
        st.session_state.processing_state['current_stage'] = stage
        st.session_state.processing_state['stage_progress'][stage] = progress
        
        # 전체 진행률 계산 (단순화)
        stage_weights = {
            'url_parser': 5,     # URL 분석
            'download': 30,      # 다운로드
            'scene_extraction': 40,  # 장면 추출
            'ai_analysis': 20,   # AI 분석
            'metadata_save': 3,  # 메타데이터 저장
            'storage_upload': 1, # 스토리지 업로드
            'cleanup': 1         # 정리
        }
        
        # 현재 단계의 진행률만 사용하여 전체 진행률 계산
        total_progress = 0
        current_stage_weight = stage_weights.get(stage, 0)
        
        # 이전 단계들의 가중치 합계
        stage_order = ['url_parser', 'download', 'scene_extraction', 'ai_analysis', 'metadata_save', 'storage_upload', 'cleanup']
        current_stage_index = stage_order.index(stage) if stage in stage_order else 0
        
        # 이전 단계들은 100% 완료로 처리
        for i in range(current_stage_index):
            total_progress += stage_weights.get(stage_order[i], 0)
        
        # 현재 단계의 진행률 추가
        total_progress += (progress / 100) * current_stage_weight
        
        # UI 업데이트
        main_progress.progress(total_progress / 100)
        
        # 현재 단계 정보
        stage_names = dict(stages)
        current_stage_name = stage_names.get(stage, stage)
        stage_info.markdown(f"**{current_stage_name}** - {message}")
        
        # 시간 정보
        elapsed = current_time - st.session_state.processing_state['start_time']
        elapsed_time.markdown(f"**경과 시간**: {elapsed:.1f}초")
        
        if total_progress > 0:
            estimated_total = elapsed * (100 / total_progress)
            remaining = estimated_total - elapsed
            estimated_time.markdown(f"**예상 완료**: {remaining:.1f}초")
        
        # 개별 단계 프로그레스 바 업데이트 제거
        # (메인 프로그레스 바만 사용)
        
        # 콘솔 로그 업데이트 (중요한 메시지만 표시)
        timestamp = time.strftime('%H:%M:%S')
        formatted_message = f"[{timestamp}] {message}"
        
        st.session_state.processing_state['console_logs'].append(formatted_message)
        # 로그 개수를 8개로 제한하여 깔끔하게 유지
        if len(st.session_state.processing_state['console_logs']) > 8:
            st.session_state.processing_state['console_logs'].pop(0)
        
        # 실시간 로그 파일에서 추가 로그 읽기
        try:
            real_time_logs = read_real_time_logs()
            # 세션 로그와 실시간 로그 병합
            all_logs = st.session_state.processing_state['console_logs'].copy()
            
            # 실시간 로그에서 관련 로그만 추가 (중복 제거)
            for log_line in real_time_logs[-3:]:  # 마지막 3줄만
                if any(keyword in log_line.lower() for keyword in ['download', '다운로드', 'scene', '장면', 'ai', 'analysis', '분석']):
                    # 이미 있는 메시지와 중복되지 않는 경우만 추가
                    if not any(log_line.split(']')[-1].strip() in existing_log for existing_log in all_logs):
                        all_logs.append(f"[{timestamp}] {log_line.split(']')[-1].strip() if ']' in log_line else log_line}")
            
            # 로그 개수 제한
            if len(all_logs) > 8:
                all_logs = all_logs[-8:]
                
            console_text = "\n".join(all_logs)
        except Exception as e:
            console_text = "\n".join(st.session_state.processing_state['console_logs'])
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
        
        # 상세 로그 (선택적)
        if show_detailed_logs and detailed_message:
            if 'detailed_logs' not in st.session_state:
                st.session_state.detailed_logs = []
            
            st.session_state.detailed_logs.append(f"[{timestamp}] {detailed_message}")
            if len(st.session_state.detailed_logs) > 20:
                st.session_state.detailed_logs.pop(0)
            
            detailed_text = "\n".join(st.session_state.detailed_logs)
            detailed_logs_container.markdown(
                f"""
                <div style="
                    background: #1a1a1a;
                    color: #888;
                    padding: 15px;
                    border-radius: 5px;
                    font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
                    font-size: 11px;
                    line-height: 1.4;
                    height: 200px;
                    overflow-y: auto;
                    white-space: pre-wrap;
                    border: 1px solid #333;
                    margin-top: 10px;
                ">
{detailed_text}
                </div>
                """,
                unsafe_allow_html=True
            )
        
        # 실시간 로그 모니터링도 함께 수행
        update_console_from_logs()

    try:
        # 처리 상태 초기화 및 자동 새로고침 시작
        st.session_state.processing_state = {
            'current_stage': 'init',
            'progress': 0,
            'total_stages': 7,
            'console_logs': [],
            'stage_progress': {},
            'start_time': time.time(),
            'auto_refresh': True,  # 새로고침 활성화
            'last_update_time': time.time()
        }
        
        precision_level = st.session_state.get('precision_level', 5)
        selected_model = st.session_state.get('selected_model', 'gpt-4o')
        
        # 모델 이름 표시
        model_display_names = {
            "gemini-2.0-flash": "Google Gemini",
            "gpt-4o": "GPT-4o",
            "claude-sonnet-4-20250514": "Claude Sonnet 4"
        }
        
        update_progress_and_console(
            "init", 0, 
            f"🤖 AI 모델 선택: {model_display_names.get(selected_model, selected_model)}",
            f"Starting analysis with model: {selected_model}, precision: {precision_level}"
        )

        video = handle_video_analysis_enhanced(
            video_url=video_url,
            precision_level=precision_level,
            console_callback=lambda msg: update_progress_and_console(
                st.session_state.processing_state.get('current_stage', 'processing'),
                st.session_state.processing_state.get('progress', 0),
                msg,
                msg
            ),
            model_name=selected_model,
            progress_callback=update_progress_and_console
        )

        # video 객체 검증
        if video and hasattr(video, 'url') and hasattr(video, 'session_id'):
            update_progress_and_console("completed", 100, "✅ 분석 완료!", "Analysis completed successfully")
            st.session_state.analysis_result = video
            
            # 처리 상태 정리 및 자동 새로고침 비활성화
            if 'processing_state' in st.session_state:
                st.session_state.processing_state['auto_refresh'] = False  # 새로고침 중단
                del st.session_state.processing_state
            if 'detailed_logs' in st.session_state:
                del st.session_state.detailed_logs
            
            set_analysis_state('completed')
            logger.info(f"Analysis completed successfully for video: {video.session_id}")
            
            # 완료 후 잠시 대기
            time.sleep(2)
        else:
            raise ValueError("Invalid video object returned from analysis")
        
        st.rerun()

    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        update_progress_and_console("error", 0, f"❌ 오류 발생: {str(e)}", f"Error details: {str(e)}")
        st.error(f"분석 중 오류 발생: {str(e)}")
        
        # 처리 상태 정리 및 자동 새로고침 비활성화
        if 'processing_state' in st.session_state:
            st.session_state.processing_state['auto_refresh'] = False  # 새로고침 중단
            del st.session_state.processing_state
        if 'detailed_logs' in st.session_state:
            del st.session_state.detailed_logs
        
        set_analysis_state('idle')
        time.sleep(3)
        st.rerun()
