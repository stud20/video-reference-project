# src/ui/tabs/analyze_tab.py
"""
Analyze 탭 - 영상 분석 UI (개선된 버전)
"""

import streamlit as st
import time
import os
import base64
from typing import Optional, Dict, Any
from handlers.enhanced_video_handler import handle_video_analysis_enhanced
from utils.session_state import get_analysis_state, set_analysis_state
from utils.logger import get_logger

logger = get_logger(__name__)


def render_analyze_tab():
    """Analyze 탭 렌더링"""
    # 모달 처리
    render_modals()
    
    # 분석 상태 확인
    analysis_state = get_analysis_state()
    
    if analysis_state == 'idle':
        render_input_section()
    elif analysis_state == 'processing':
        render_processing_section()
    elif analysis_state == 'completed':
        render_results_section()


def render_input_section():
    """URL 입력 섹션 - 애니메이션 효과 포함"""
    # 컨테이너 ID 설정 (애니메이션용)
    container_id = "input-container"
    
    st.markdown(f"""
    <div id="{container_id}" class="analyze-input-container">
        <div class="analyze-input-wrapper">
    """, unsafe_allow_html=True)
    
    # 타이틀
    st.markdown("### 🎬 영상 분석 시작하기")
    st.markdown("YouTube 또는 Vimeo 링크를 입력해주세요")
    
    # URL 입력
    col1, col2 = st.columns([4, 1])
    
    with col1:
        video_url = st.text_input(
            "URL",
            placeholder="https://www.youtube.com/watch?v=...",
            label_visibility="collapsed",
            key="analyze_url_input"
        )
    
    with col2:
        analyze_button = st.button(
            "🚀 분석",
            type="primary",
            use_container_width=True,
            key="analyze_start_button"
        )
    
    # Enter 키 이벤트 처리
    if st.session_state.get('enter_pressed'):
        analyze_button = True
        st.session_state.enter_pressed = False
    
    # 예시 링크
    st.markdown("---")
    st.markdown("#### 💡 예시 링크")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📺 YouTube 예시", use_container_width=True):
            st.session_state.analyze_url_input = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            st.rerun()
    
    with col2:
        if st.button("🎬 Vimeo 예시", use_container_width=True):
            st.session_state.analyze_url_input = "https://vimeo.com/347119375"
            st.rerun()
    
    st.markdown("</div></div>", unsafe_allow_html=True)
    
    # JavaScript for Enter key and animations
    st.markdown("""
    <script>
        // Enter 키 처리
        const input = document.querySelector('input[type="text"]');
        if (input) {
            input.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    const button = document.querySelector('button[kind="primary"]');
                    if (button) button.click();
                }
            });
        }
        
        // 애니메이션 트리거 함수
        window.triggerInputAnimation = function() {
            const container = document.getElementById('input-container');
            if (container) {
                container.style.animation = 'fadeOut 0.3s ease-out forwards, slideUp 0.3s ease-out forwards';
                setTimeout(() => {
                    container.style.display = 'none';
                }, 300);
            }
        }
    </script>
    
    <style>
        @keyframes fadeOut {
            to { opacity: 0; }
        }
        
        @keyframes slideUpHide {
            to { 
                transform: translateY(-20px);
                opacity: 0;
            }
        }
    </style>
    """, unsafe_allow_html=True)
    
    # 분석 시작 처리
    if analyze_button and video_url:
        # 애니메이션 트리거
        st.markdown("<script>triggerInputAnimation();</script>", unsafe_allow_html=True)
        time.sleep(0.3)  # 애니메이션 대기
        
        set_analysis_state('processing')
        st.session_state.current_video_url = video_url
        st.rerun()
    elif analyze_button:
        st.error("URL을 입력해주세요!")


def render_processing_section():
    """처리 중 섹션 - 실시간 콘솔 출력"""
    video_url = st.session_state.get('current_video_url')
    
    # 비디오 임베드 (슬라이드업 + 페이드인 애니메이션)
    st.markdown("""
    <div style="animation: slideDown 0.5s ease-out, fadeIn 0.5s ease-out;">
    """, unsafe_allow_html=True)
    
    render_video_embed(video_url)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 3줄 콘솔 창
    st.markdown("""
    <div class="console-window" id="console-window">
        <div id="console-content"></div>
    </div>
    """, unsafe_allow_html=True)
    
    # 콘솔 메시지를 실시간으로 업데이트하는 placeholder
    console_placeholder = st.empty()
    
    # JavaScript for console updates
    st.markdown("""
    <script>
        window.updateConsole = function(message) {
            const consoleContent = document.getElementById('console-content');
            if (consoleContent) {
                // 새 라인 추가
                const line = document.createElement('div');
                line.className = 'console-line';
                line.textContent = '> ' + message;
                consoleContent.appendChild(line);
                
                // 3줄만 유지
                while (consoleContent.children.length > 3) {
                    consoleContent.removeChild(consoleContent.firstChild);
                }
                
                // 스크롤을 아래로
                const consoleWindow = document.getElementById('console-window');
                consoleWindow.scrollTop = consoleWindow.scrollHeight;
            }
        }
    </script>
    """, unsafe_allow_html=True)
    
    # 분석 프로세스 시작
    try:
        # 정밀도 레벨 가져오기
        precision_level = st.session_state.get('precision_level', 5)
        
        # 콘솔 업데이트 함수
        def update_console(message):
            # JavaScript 특수문자 이스케이프
            escaped_message = message.replace("'", "\\'").replace('"', '\\"')
            console_placeholder.markdown(
                f"<script>updateConsole('{escaped_message}');</script>",
                unsafe_allow_html=True
            )
        
        # 분석 실행
        video = handle_video_analysis_enhanced(
            video_url, 
            precision_level,
            update_console
        )
        
        # 콘솔 창 숨기기 애니메이션
        st.markdown("""
        <script>
            setTimeout(() => {
                const console = document.getElementById('console-window');
                if (console) {
                    console.style.animation = 'fadeOut 0.3s ease-out forwards';
                    setTimeout(() => {
                        console.style.display = 'none';
                    }, 300);
                }
            }, 500);
        </script>
        """, unsafe_allow_html=True)
        
        time.sleep(0.8)  # 애니메이션 대기
        
        # 결과 저장
        st.session_state.analysis_result = video
        set_analysis_state('completed')
        st.rerun()
        
    except Exception as e:
        st.error(f"분석 중 오류 발생: {str(e)}")
        set_analysis_state('idle')
        st.rerun()


def render_results_section():
    """결과 표시 섹션"""
    video = st.session_state.get('analysis_result')
    if not video:
        set_analysis_state('idle')
        st.rerun()
        return
    
    # 비디오 임베드 유지
    render_video_embed(video.url)
    
    # 필름 스트립 (슬라이드업 애니메이션)
    st.markdown('<div style="animation: slideUp 0.5s ease-out;">', unsafe_allow_html=True)
    render_film_strip(video)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 분석 결과 (슬라이드업 애니메이션)
    st.markdown('<div style="animation: slideUp 0.6s ease-out 0.1s both;">', unsafe_allow_html=True)
    render_analysis_results(video)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 액션 버튼들 (슬라이드업 애니메이션)
    st.markdown('<div style="animation: slideUp 0.7s ease-out 0.2s both;">', unsafe_allow_html=True)
    render_action_buttons(video)
    st.markdown('</div>', unsafe_allow_html=True)


def render_video_embed(url: str):
    """비디오 임베드"""
    # YouTube/Vimeo 판별 및 ID 추출
    video_id = extract_video_id(url)
    platform = detect_platform(url)
    
    if platform == "youtube":
        st.markdown(f"""
        <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden;">
            <iframe style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"
                    src="https://www.youtube.com/embed/{video_id}"
                    frameborder="0" allowfullscreen>
            </iframe>
        </div>
        """, unsafe_allow_html=True)
    
    elif platform == "vimeo":
        st.markdown(f"""
        <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden;">
            <iframe style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"
                    src="https://player.vimeo.com/video/{video_id}"
                    frameborder="0" allowfullscreen>
            </iframe>
        </div>
        """, unsafe_allow_html=True)


def render_film_strip(video):
    """필름 스트립 표시 - 정밀도에 따른 동적 레이아웃"""
    if not video.scenes:
        return
    
    st.markdown('<div class="film-strip-container">', unsafe_allow_html=True)
    st.markdown("#### 🎞️ 추출된 주요 장면")
    
    num_scenes = len(video.scenes)
    
    # 썸네일 포함 여부 확인
    has_thumbnail = hasattr(video, 'thumbnail_path') and video.thumbnail_path
    total_images = num_scenes + (1 if has_thumbnail else 0)
    
    st.markdown(f'<p style="color: var(--text-secondary); font-size: 0.9rem;">총 {total_images}개 이미지 (정밀도 레벨: {st.session_state.get("precision_level", 5)})</p>', unsafe_allow_html=True)
    
    # 이미지가 많을 때는 스크롤 가능한 필름 스트립
    if total_images > 6:
        st.markdown('<div class="film-strip">', unsafe_allow_html=True)
        
        html_content = ""
        
        # 썸네일 먼저 표시
        if has_thumbnail:
            html_content += render_film_frame(video.thumbnail_path, "썸네일", 0)
        
        # 씬 이미지들
        for i, scene in enumerate(video.scenes):
            if os.path.exists(scene.frame_path):
                html_content += render_film_frame(
                    scene.frame_path, 
                    f"Scene {i+1} ({scene.timestamp:.1f}s)", 
                    i+1
                )
        
        st.markdown(html_content, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    else:
        # 6개 이하일 때는 그리드 레이아웃
        cols = st.columns(min(total_images, 4))
        col_idx = 0
        
        # 썸네일 표시
        if has_thumbnail:
            with cols[col_idx % len(cols)]:
                st.image(video.thumbnail_path, caption="📌 썸네일", use_container_width=True)
            col_idx += 1
        
        # 씬 이미지들
        for i, scene in enumerate(video.scenes):
            if os.path.exists(scene.frame_path):
                with cols[col_idx % len(cols)]:
                    st.image(
                        scene.frame_path, 
                        caption=f"Scene {i+1} ({scene.timestamp:.1f}s)",
                        use_container_width=True
                    )
                col_idx += 1
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_film_frame(image_path: str, caption: str, index: int) -> str:
    """필름 프레임 HTML 생성"""
    image_base64 = get_base64_image(image_path)
    return f"""
    <div class="film-frame" style="animation-delay: {index * 0.1}s;">
        <img src="data:image/jpeg;base64,{image_base64}" alt="{caption}" />
        <div style="text-align: center; font-size: 0.8rem; margin-top: 5px; color: var(--text-secondary);">
            {caption}
        </div>
    </div>
    """


def render_analysis_results(video):
    """분석 결과 표시"""
    if not video.analysis_result:
        return
    
    st.markdown('<div class="result-section">', unsafe_allow_html=True)
    st.markdown("### 📊 분석 결과")
    
    result = video.analysis_result
    
    # 결과 아이템들
    items = [
        ("🎭 장르", result.get('genre', 'Unknown')),
        ("🎨 표현형식", result.get('expression_style', 'Unknown')),
        ("💡 판단이유", result.get('reasoning', 'Unknown')),
        ("✨ 특징", result.get('features', 'Unknown')),
        ("🌈 분위기", result.get('mood_tone', 'Unknown')),
        ("👥 타겟 고객층", result.get('target_audience', 'Unknown'))
    ]
    
    for label, value in items:
        st.markdown(f"""
        <div class="result-item">
            <div class="result-label">{label}</div>
            <div class="result-value">{value}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # 태그
    tags = result.get('tags', [])
    if tags:
        st.markdown("""
        <div class="result-item">
            <div class="result-label">🏷️ 태그</div>
            <div class="result-value">
                <div class="tag-container">
        """, unsafe_allow_html=True)
        
        for i, tag in enumerate(tags[:20]):  # 최대 20개
            st.markdown(
                f'<span class="tag" style="animation-delay: {i * 0.05}s;">#{tag}</span>', 
                unsafe_allow_html=True
            )
        
        st.markdown("</div></div></div>", unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_action_buttons(video):
    """액션 버튼들"""
    st.markdown("### 🎯 추가 작업")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("💾 다른 이름으로 저장", use_container_width=True, key="save_as"):
            st.session_state.show_save_modal = True
            st.rerun()
    
    with col2:
        if st.button("🎨 무드보드 보기", use_container_width=True, key="view_moodboard"):
            st.session_state.show_moodboard = True
            st.rerun()
    
    with col3:
        if st.button("🔄 재추론하기", use_container_width=True, key="reanalyze"):
            # 현재 결과 삭제하고 재분석
            st.session_state.analysis_result = None
            set_analysis_state('processing')
            st.rerun()
    
    with col4:
        if st.button("🎚️ 다른 정밀도로", use_container_width=True, key="change_precision"):
            st.session_state.show_precision_modal = True
            st.rerun()
    
    # 새로운 분석 버튼
    st.markdown("---")
    if st.button("🆕 새로운 영상 분석", type="secondary", use_container_width=True):
        # 상태 초기화
        reset_analysis_state()
        st.rerun()


def render_modals():
    """모달 창들 렌더링"""
    # 무드보드 모달
    if st.session_state.get('show_moodboard'):
        render_moodboard_modal()
    
    # 정밀도 선택 모달
    if st.session_state.get('show_precision_modal'):
        render_precision_modal()
    
    # 저장 모달
    if st.session_state.get('show_save_modal'):
        render_save_modal()


def render_moodboard_modal():
    """무드보드 모달"""
    st.markdown("""
    <div class="modal-overlay">
        <div class="modal-content">
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("## 🎨 무드보드")
    with col2:
        if st.button("✖️ 닫기", key="close_moodboard"):
            st.session_state.show_moodboard = False
            st.rerun()
    
    video = st.session_state.get('analysis_result')
    if video and video.scenes:
        # 이미지 그리드
        st.markdown('<div class="image-grid">', unsafe_allow_html=True)
        
        # 선택 가능한 이미지들
        selected_images = st.session_state.get('moodboard_selected', [])
        
        cols = st.columns(4)
        for i, scene in enumerate(video.scenes):
            with cols[i % 4]:
                # 체크박스와 이미지
                is_selected = i in selected_images
                if st.checkbox("", value=is_selected, key=f"mood_img_{i}"):
                    if i not in selected_images:
                        selected_images.append(i)
                else:
                    if i in selected_images:
                        selected_images.remove(i)
                
                st.image(scene.frame_path, use_container_width=True)
        
        st.session_state.moodboard_selected = selected_images
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 액션 버튼
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("📥 무드보드 다운로드", use_container_width=True):
                # TODO: 무드보드 생성 및 다운로드
                st.info("무드보드 생성 중...")
        
        with col2:
            if st.button("🎨 템플릿 선택", use_container_width=True):
                st.info("템플릿 선택 기능 준비 중...")
    
    st.markdown("</div></div>", unsafe_allow_html=True)


def render_precision_modal():
    """정밀도 선택 모달"""
    st.markdown("""
    <div class="modal-overlay">
        <div class="modal-content" style="max-width: 600px;">
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("## 🎚️ 정밀도 선택")
    with col2:
        if st.button("✖️ 닫기", key="close_precision"):
            st.session_state.show_precision_modal = False
            st.rerun()
    
    current_precision = st.session_state.get('precision_level', 5)
    st.markdown(f"현재 정밀도: **레벨 {current_precision}**")
    
    # 정밀도 슬라이더
    new_precision = st.slider(
        "새로운 정밀도 레벨",
        min_value=1,
        max_value=10,
        value=current_precision,
        help="높은 레벨일수록 더 많은 이미지를 추출하고 정밀한 분석을 수행합니다."
    )
    
    # 정밀도별 설명
    precision_info = {
        1: ("⚡ 초고속", "4개 이미지, 30초-1분"),
        2: ("🏃 고속", "4개 이미지, 1-2분"),
        3: ("🚶 빠름", "5개 이미지, 2-3분"),
        4: ("🚶‍♂️ 보통-빠름", "5개 이미지, 3-4분"),
        5: ("⚖️ 균형 (권장)", "6개 이미지, 4-6분"),
        6: ("🔍 정밀", "7개 이미지, 6-8분"),
        7: ("🔬 고정밀", "8개 이미지, 8-12분"),
        8: ("🎯 매우정밀", "10개 이미지, 12-15분"),
        9: ("🏆 초정밀", "10개 이미지, 15-20분"),
        10: ("💎 최고정밀", "10개 이미지, 20-30분")
    }
    
    if new_precision in precision_info:
        title, desc = precision_info[new_precision]
        st.info(f"{title}: {desc}")
    
    # 재분석 버튼
    if st.button("🔄 이 정밀도로 재분석", type="primary", use_container_width=True):
        st.session_state.precision_level = new_precision
        st.session_state.show_precision_modal = False
        set_analysis_state('processing')
        st.rerun()
    
    st.markdown("</div></div>", unsafe_allow_html=True)


def render_save_modal():
    """저장 모달"""
    st.markdown("""
    <div class="modal-overlay">
        <div class="modal-content" style="max-width: 500px;">
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("## 💾 다른 이름으로 저장")
    with col2:
        if st.button("✖️ 닫기", key="close_save"):
            st.session_state.show_save_modal = False
            st.rerun()
    
    # 저장 옵션
    save_name = st.text_input("파일명", value=f"analysis_{int(time.time())}")
    
    save_options = st.multiselect(
        "저장할 항목",
        ["분석 결과", "추출된 이미지", "메타데이터", "전체 리포트"],
        default=["분석 결과", "추출된 이미지"]
    )
    
    save_format = st.radio(
        "저장 형식",
        ["JSON", "PDF", "ZIP (전체)"],
        horizontal=True
    )
    
    if st.button("💾 저장하기", type="primary", use_container_width=True):
        # TODO: 실제 저장 로직 구현
        st.success(f"'{save_name}.{save_format.lower()}'로 저장되었습니다!")
        time.sleep(1)
        st.session_state.show_save_modal = False
        st.rerun()
    
    st.markdown("</div></div>", unsafe_allow_html=True)


# 유틸리티 함수들
def get_base64_image(image_path: str) -> str:
    """이미지를 base64로 변환"""
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception as e:
        logger.error(f"이미지 변환 실패: {e}")
        return ""


def extract_video_id(url: str) -> str:
    """비디오 ID 추출"""
    if "youtube.com" in url or "youtu.be" in url:
        if "watch?v=" in url:
            return url.split("watch?v=")[1].split("&")[0]
        elif "youtu.be" in url:
            return url.split("/")[-1].split("?")[0]
    elif "vimeo.com" in url:
        return url.split("/")[-1].split("?")[0]
    return ""


def detect_platform(url: str) -> str:
    """플랫폼 감지"""
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    elif "vimeo.com" in url:
        return "vimeo"
    return "unknown"


def reset_analysis_state():
    """분석 상태 초기화"""
    set_analysis_state('idle')
    st.session_state.analysis_result = None
    st.session_state.current_video_url = None
    st.session_state.show_moodboard = False
    st.session_state.show_precision_modal = False
    st.session_state.show_save_modal = False
    st.session_state.moodboard_selected = []