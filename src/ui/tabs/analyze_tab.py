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


# src/ui/tabs/analyze_tab.py의 render_input_section 함수 수정

def render_input_section():
    """URL 입력 섹션 - 깔끔한 버전"""
    # 컨테이너 ID 설정 (애니메이션용)
  #  container_id = "input-container"
    
    #st.markdown(f"""
   # <div id="{container_id}" class="analyze-input-container">
   #     <div class="analyze-input-wrapper">
    #""", unsafe_allow_html=True)
    
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
    """처리 중 섹션 - 실시간 콘솔 출력 (Streamlit native 방식)"""
    video_url = st.session_state.get('current_video_url')
    if not video_url:
        st.error("비디오 URL이 존재하지 않습니다.")
        return

    # 비디오 임베드
    render_video_embed(video_url)

    # 콘솔창 컨테이너 생성
    st.markdown("### 💻 처리 상황")
    console_container = st.container()
    
    # 콘솔 스타일 적용
    with console_container:
        console_placeholder = st.empty()
        
    # 로그 라인 저장용 (세션 상태에 저장)
    if 'console_logs' not in st.session_state:
        st.session_state.console_logs = []
    
    def update_console(message: str):
        """콘솔 라인 업데이트 함수 - 최대 3줄 유지"""
        st.session_state.console_logs.append(f"> {message}")
        if len(st.session_state.console_logs) > 3:
            st.session_state.console_logs.pop(0)
        
        # 콘솔 스타일로 표시
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
                height: 100px;
                overflow-y: auto;
                white-space: pre-wrap;
            ">
{console_text}
            </div>
            """,
            unsafe_allow_html=True
        )

    try:
        # 콘솔 초기화
        st.session_state.console_logs = []
        
        # 정밀도 레벨
        precision_level = st.session_state.get('precision_level', 5)

        # 실제 분석 실행
        video = handle_video_analysis_enhanced(
            video_url=video_url,
            precision_level=precision_level,
            console_callback=update_console
        )

        # 분석 완료 후 상태 전환
        st.session_state.analysis_result = video
        st.session_state.console_logs = []  # 콘솔 로그 초기화
        set_analysis_state('completed')
        st.rerun()

    except Exception as e:
        st.error(f"분석 중 오류 발생: {str(e)}")
        st.session_state.console_logs = []  # 오류 시에도 초기화
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
    
    # 썸네일 포함 여부 확인 - 수정된 부분
    has_thumbnail = False
    thumbnail_path = None
    
    # 썸네일 경로 찾기
    if video.metadata and video.metadata.thumbnail:
        # 로컬 파일인지 확인
        if os.path.exists(video.metadata.thumbnail):
            has_thumbnail = True
            thumbnail_path = video.metadata.thumbnail
        else:
            # session_dir에서 썸네일 찾기
            if hasattr(video, 'session_dir') and video.session_dir:
                possible_extensions = ['.jpg', '.jpeg', '.png', '.webp']
                for ext in possible_extensions:
                    test_path = os.path.join(video.session_dir, f"thumbnail{ext}")
                    if os.path.exists(test_path):
                        has_thumbnail = True
                        thumbnail_path = test_path
                        break
    
    total_images = num_scenes + (1 if has_thumbnail else 0)
    
    st.markdown(f'<p style="color: var(--text-secondary); font-size: 0.9rem;">총 {total_images}개 이미지 (정밀도 레벨: {st.session_state.get("precision_level", 5)})</p>', unsafe_allow_html=True)
    
    # 이미지가 많을 때는 스크롤 가능한 필름 스트립
    if total_images > 6:
        st.markdown('<div class="film-strip">', unsafe_allow_html=True)
        
        html_content = ""
        
        # 썸네일 먼저 표시
        if has_thumbnail and thumbnail_path:
            html_content += render_film_frame(thumbnail_path, "썸네일", 0)
        
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
        if has_thumbnail and thumbnail_path:
            with cols[col_idx % len(cols)]:
                st.image(thumbnail_path, caption="📌 썸네일", use_container_width=True)
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
    """분석 결과 표시 - 2컬럼 레이아웃 (개선된 버전)"""
    if not video.analysis_result:
        return
    
    st.markdown("### 📊 분석 결과")
    
    # 스타일 정의
    st.markdown("""
    <style>
        .analysis-wrapper {
            display: grid;
            grid-template-columns: 35% 65%;
            gap: 2px;
            margin-top: 20px;
        }
        
        .column-left {
            background-color: #2a2a2a;
            padding: 20px;
            border-radius: 8px;
        }
        
        .column-right {
            background-color: #1e2936;
            padding: 20px;
            border-radius: 8px;
        }
        
        .result-row {
            padding: 15px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .result-row:last-child {
            border-bottom: none;
        }
        
        .result-label {
            font-weight: bold;
            color: #ffffff;
            margin-bottom: 8px;
            font-size: 0.95rem;
        }
        
        .result-content {
            color: #e0e0e0;
            line-height: 1.6;
            font-size: 0.9rem;
        }
        
        .tag-chip {
            display: inline-block;
            background-color: rgba(255, 255, 255, 0.15);
            color: #ffffff;
            padding: 4px 12px;
            margin: 2px;
            border-radius: 16px;
            font-size: 0.85rem;
        }
        
        .info-list {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        
        .info-list li {
            margin: 5px 0;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # 데이터 준비
    result = video.analysis_result
    metadata = video.metadata if video.metadata else None
    
    # Streamlit columns 사용
    col1, col2 = st.columns([35, 65])
    
    # 왼쪽 컬럼 - 메타데이터
    with col1:
        st.markdown('<div class="column-left">', unsafe_allow_html=True)
        
        # 제목
        st.markdown(f'''
        <div class="result-row">
            <div class="result-label">📹 제목</div>
            <div class="result-content">{metadata.title if metadata else 'Unknown'}</div>
        </div>
        ''', unsafe_allow_html=True)
        
        # 업로드 채널
        st.markdown(f'''
        <div class="result-row">
            <div class="result-label">👤 업로드 채널</div>
            <div class="result-content">{metadata.uploader if metadata else 'Unknown'}</div>
        </div>
        ''', unsafe_allow_html=True)
        
        # 설명
        description = metadata.description[:200] + '...' if metadata and metadata.description and len(metadata.description) > 200 else (metadata.description if metadata else '')
        st.markdown(f'''
        <div class="result-row">
            <div class="result-label">📝 설명</div>
            <div class="result-content">{description}</div>
        </div>
        ''', unsafe_allow_html=True)
        
        # 기타 정보
        meta_info_html = '<ul class="info-list">'
        if metadata:
            if metadata.view_count:
                meta_info_html += f'<li>👁️ 조회수: {metadata.view_count:,}회</li>'
            if metadata.duration:
                meta_info_html += f'<li>⏱️ 길이: {int(metadata.duration//60)}분 {int(metadata.duration%60)}초</li>'
            if metadata.upload_date:
                meta_info_html += f'<li>📅 업로드: {metadata.upload_date[:10] if len(metadata.upload_date) >= 10 else metadata.upload_date}</li>'
            if metadata.like_count:
                meta_info_html += f'<li>👍 좋아요: {metadata.like_count:,}</li>'
            if metadata.comment_count:
                meta_info_html += f'<li>💬 댓글: {metadata.comment_count:,}</li>'
        meta_info_html += '</ul>'
        
        st.markdown(f'''
        <div class="result-row">
            <div class="result-label">📊 기타 정보</div>
            <div class="result-content">{meta_info_html}</div>
        </div>
        ''', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 오른쪽 컬럼 - AI 분석 결과
    with col2:
        st.markdown('<div class="column-right">', unsafe_allow_html=True)
        
        # 장르 & 표현형식
        st.markdown(f'''
        <div class="result-row">
            <div class="result-label">🎭 장르 & 🎨 표현형식</div>
            <div class="result-content">{result.get('genre', 'Unknown')} • {result.get('expression_style', 'Unknown')}</div>
        </div>
        ''', unsafe_allow_html=True)
        
        # 판단이유
        st.markdown(f'''
        <div class="result-row">
            <div class="result-label">💡 판단이유</div>
            <div class="result-content">{result.get('reasoning', 'Unknown')}</div>
        </div>
        ''', unsafe_allow_html=True)
        
        # 특징
        st.markdown(f'''
        <div class="result-row">
            <div class="result-label">✨ 특징</div>
            <div class="result-content">{result.get('features', 'Unknown')}</div>
        </div>
        ''', unsafe_allow_html=True)
        
        # 분위기, 타겟, 태그를 하나의 row로
        tags_html = ""
        tags = result.get('tags', [])
        if tags:
            for tag in tags[:20]:
                tags_html += f'<span class="tag-chip">#{tag}</span>'
        
        st.markdown(f'''
        <div class="result-row">
            <div style="margin-bottom: 15px;">
                <div class="result-label">🌈 분위기</div>
                <div class="result-content">{result.get('mood_tone', 'Unknown')}</div>
            </div>
            <div style="margin-bottom: 15px;">
                <div class="result-label">👥 타겟 고객층</div>
                <div class="result-content">{result.get('target_audience', 'Unknown')}</div>
            </div>
            <div>
                <div class="result-label">🏷️ 태그</div>
                <div class="result-content">{tags_html}</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
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


# src/ui/tabs/analyze_tab.py에서 render_moodboard_modal 함수 수정

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
                # 체크박스와 이미지 - 레이블 추가하고 숨김
                is_selected = i in selected_images
                if st.checkbox(
                    f"이미지 {i+1} 선택",  # 레이블 추가
                    value=is_selected, 
                    key=f"mood_img_{i}",
                    label_visibility="collapsed"  # 레이블 숨김
                ):
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