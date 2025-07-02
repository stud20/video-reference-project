# web/components/analyze/actions.py
"""
하단 액션 버튼들과 모달 기능
"""

import streamlit as st
import os
import re
import urllib.parse
import requests
from streamlit_extras.grid import grid
from streamlit_javascript import st_javascript
from web.state import set_analysis_state, get_analysis_state
from web.styles.theme import get_enhanced_styles
from web.utils.analysis_state import reset_analysis_state
from utils.logger import get_logger

logger = get_logger(__name__)


def render_action_buttons(video):
    """액션 버튼들"""
    # 통합 스타일 적용
    st.markdown(get_enhanced_styles(), unsafe_allow_html=True)
    
    # video 객체 확인 - 더 유연하게 처리
    if not video:
        st.error("분석 결과가 없습니다.")
        return
        
    # Video 객체의 필수 속성 확인
    has_session_id = hasattr(video, 'session_id')
    has_metadata = hasattr(video, 'metadata')
    has_url = hasattr(video, 'url')
    
    if not (has_session_id and has_url):
        st.error("비디오 정보가 올바르지 않습니다.")
        logger.error(f"Invalid video object - Type: {type(video)}, Attributes: {dir(video)}")
        return
    
    base_url = "https://ref.greatminds.kr"
    video_id = video.session_id
    
    # 파일명 정리
    def sanitize_filename(title: str, max_length: int = 100) -> str:
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
        safe_title = re.sub(r'_+', '_', safe_title)
        safe_title = safe_title.strip('_ ')
        return safe_title[:max_length]
    
    # 메타데이터가 있으면 제목 사용, 없으면 기본값
    if has_metadata and video.metadata and hasattr(video.metadata, 'title'):
        video_title = video.metadata.title
    else:
        video_title = "video"
        
    sanitized_title = sanitize_filename(video_title)
    video_filename = f"{video_id}_{sanitized_title}.mp4"
    
    encoded_filename = urllib.parse.quote(video_filename)
    video_url = f"{base_url}/{video_id}/{encoded_filename}"
    download_filename = f"{sanitized_title}_{video_id}.mp4"
    
    col1, col2, col3 = st.columns(3)
    

    with col1:
        # 다운로드 상태 관리
        if 'download_state' not in st.session_state:
            st.session_state.download_state = 'idle'  # idle, loading, ready
        if 'video_content' not in st.session_state:
            st.session_state.video_content = None
        
        # 버튼 텍스트 결정
        if st.session_state.download_state == 'idle':
            button_text = "💾 다운로드"
        elif st.session_state.download_state == 'loading':
            button_text = "⏳ 다운로드 준비 중..."
        else:  # ready
            button_text = "📥 클릭하여 다운로드"
        
        
        # 단일 버튼으로 처리
        if st.session_state.download_state == 'ready' and st.session_state.video_content:
            # 다운로드 준비 완료 상태 - download_button 표시
            st.download_button(
                label=button_text,
                data=st.session_state.video_content,
                file_name=download_filename,
                mime="video/mp4",
                key="download_video_final",
                use_container_width=True,
                on_click=lambda: setattr(st.session_state, 'download_state', 'idle')
            )
        else:
            # 일반 버튼
            if st.button(button_text, 
                        use_container_width=True, 
                        key="download_video",
                        disabled=(st.session_state.download_state == 'loading')):
                if st.session_state.download_state == 'idle':
                    # 다운로드 시작
                    st.session_state.download_state = 'loading'
                    st.rerun()
        
        # 로딩 중일 때 처리
        if st.session_state.download_state == 'loading':
            try:
                with st.spinner("비디오 다운로드 준비 중..."):
                    response = requests.get(video_url, stream=True)
                    response.raise_for_status()
                    st.session_state.video_content = response.content
                    st.session_state.download_state = 'ready'
                    st.rerun()
            except Exception as e:
                st.error(f"다운로드 준비 실패: {str(e)}")
                st.session_state.download_state = 'idle'
                st.session_state.video_content = None

    with col2:
        # 무드보드 토글 버튼
        if st.button(
            "🎨 무드보드 " + ("접기" if st.session_state.get('show_moodboard', False) else "펼치기"), 
            use_container_width=True, 
            key="toggle_moodboard"
        ):
            st.session_state.show_moodboard = not st.session_state.get('show_moodboard', False)
            st.rerun()
    
    with col3:
        if st.button("🔄 재추론하기", use_container_width=True, key="reanalyze"):
            st.session_state.show_reanalysis = not st.session_state.get('show_reanalysis', False)
            # 무드보드가 열려있으면 닫기
            if st.session_state.get('show_moodboard', False):
                st.session_state.show_moodboard = False
            st.rerun()
    
    # 무드보드 영역 (버튼 아래에 표시)
    if st.session_state.get('show_moodboard', False):
        st.markdown("---")
        render_moodboard_section(video)
    
    # 재추론 영역 (버튼 아래에 표시)
    if st.session_state.get('show_reanalysis', False):
        from .reanalysis import render_reanalysis_section
        render_reanalysis_section(video)

    # 새로운 분석 입력 섹션
    st.markdown("---")
    st.markdown("### 🆕 새로운 영상 분석")
    
    # 입력창과 모델 선택
    col1, col2 = st.columns([3, 1])
    
    with col1:
        new_video_url = st.text_input(
            "URL",
            placeholder="유튜브, 비메오 동영상 링크를 넣어주세요",
            label_visibility="collapsed",
            key="new_analyze_url_input"
        )
    
    with col2:
        new_analyze_button = st.button(
            "분석하기",
            type="primary",
            key="new_analyze_start_button",
            use_container_width=True
        )
    
    # 모델 선택
    new_model_selection = st.radio(
        "AI 모델",
        options=[
            ("gemini-2.0-flash", "⚡ 빠른 분석 (Google Gemini)"),
            ("gpt-4o", "🤖 균형 분석 (GPT-4o)"),
            ("claude-sonnet-4-20250514", "🧠 상세 분석 (Claude Sonnet 4)")
        ],
        format_func=lambda x: x[1],
        index=1,  # 기본값: GPT-4o
        key="new_model_selection",
        label_visibility="collapsed",
        horizontal=True
    )
    
    # 분석 시작 처리
    if new_analyze_button and new_video_url:
        # 현재 상태 초기화
        reset_analysis_state()
        # 새로운 분석 시작
        set_analysis_state('processing')
        st.session_state.current_video_url = new_video_url
        st.session_state.selected_model = new_model_selection[0]
        st.rerun()
    elif new_analyze_button:
        st.error("URL을 입력해주세요!")


def render_moodboard_section(video):
    """무드보드 섹션 렌더링"""
    if not video:
        st.error("분석 결과가 없습니다.")
        return
    
    # 재추론된 경우 원본 씬 정보 사용
    if getattr(video, 'is_reanalyzed', False) and hasattr(video, 'original_scenes'):
        st.info("🎨 원본 영상의 모든 씬을 표시합니다 (재추론에 사용된 씬은 ✅ 표시)")
    
    # 무드보드 컨테이너
    with st.container():
        # 씬 정보 준비
        base_url = "https://ref.greatminds.kr"
        session_id = video.session_id
        
        # 재추론된 경우와 일반 분석 구분
        if getattr(video, 'is_reanalyzed', False):
            # 재추론된 씬 번호들
            reanalyzed_scene_nums = get_analyzed_scene_numbers(video)
            # 전체 씬 번호들 (원본)
            all_scene_numbers = get_all_scene_numbers(video)
        else:
            analyzed_scene_nums = get_analyzed_scene_numbers(video)
            all_scene_numbers = get_all_scene_numbers(video)
        
        # 이미지 그리드
        # 썸네일 + 씬들을 5열로 표시
        num_cols = 5
        all_items = []
        
        # 썸네일
        thumbnail_url = f"{base_url}/{session_id}/{session_id}_Thumbnail.jpg"
        all_items.append({
            'url': thumbnail_url,
            'type': 'thumbnail',
            'label': '썸네일',
            'scene_num': -1,
            'is_reanalyzed': 'thumbnail' in getattr(video, 'reanalyzed_images', [])
        })
        
        # 씬들
        for scene_num in sorted(all_scene_numbers):
            scene_url = f"{base_url}/{session_id}/scene_{scene_num:04d}.jpg"
            
            if getattr(video, 'is_reanalyzed', False):
                # 재추론된 경우
                is_used = scene_num in reanalyzed_scene_nums
                item_type = 'reanalyzed' if is_used else 'normal'
            else:
                # 일반 분석의 경우
                is_used = scene_num in analyzed_scene_nums
                item_type = 'analyzed' if is_used else 'normal'
                
            all_items.append({
                'url': scene_url,
                'type': item_type,
                'label': f'Scene #{scene_num:04d}',
                'is_analyzed': is_used,
                'scene_num': scene_num
            })
        
        # 행별로 이미지 표시
        for i in range(0, len(all_items), num_cols):
            cols = st.columns(num_cols)
            for j, col in enumerate(cols):
                if i + j < len(all_items):
                    item = all_items[i + j]
                    
                    with col:
                        # 이미지 표시
                        try:
                            st.image(item['url'], use_container_width=True)
                            
                            # 캡션 표시
                            if item['type'] == 'reanalyzed':
                                st.caption(f"{item['label']} ✅")
                            elif item['type'] == 'analyzed' and not getattr(video, 'is_reanalyzed', False):
                                st.caption(f"{item['label']} 📍")
                            else:
                                st.caption(item['label'])
                                
                        except Exception as e:
                            st.error(f"이미지 로드 실패: {item['label']}")


def render_modals():
    """모달 창들 렌더링 (정밀도 선택만)"""
    if st.session_state.get('show_precision_modal'):
        show_precision_dialog()


def get_analyzed_scene_numbers(video) -> set:
    """AI 분석에 사용된 씬 번호들을 추출"""
    analyzed_nums = set()
    
    if not video.scenes:
        return analyzed_nums
    
    for scene in video.scenes:
        basename = os.path.basename(scene.frame_path)
        if 'scene_' in basename:
            try:
                scene_num = int(basename.replace('scene_', '').replace('.jpg', ''))
                analyzed_nums.add(scene_num)
            except:
                continue
    
    return analyzed_nums


def get_all_scene_numbers(video) -> set:
    """실제 존재하는 모든 씬 번호 추출"""
    all_nums = set()
    
    scenes_dir = os.path.join("data/temp", video.session_id, "scenes")
    
    if os.path.exists(scenes_dir):
        for filename in os.listdir(scenes_dir):
            if filename.startswith('scene_') and filename.endswith('.jpg'):
                try:
                    scene_num = int(filename.replace('scene_', '').replace('.jpg', ''))
                    all_nums.add(scene_num)
                except:
                    continue
    
    if not all_nums and video.scenes:
        analyzed_nums = get_analyzed_scene_numbers(video)
        if analyzed_nums:
            max_num = max(analyzed_nums)
            all_nums = set(range(0, max_num + 1))
    
    return all_nums


@st.dialog("🎚️ 정밀도 선택", width="medium")
def show_precision_dialog():
    """정밀도 선택 다이얼로그"""
    # 다이얼로그에도 스타일 적용
    st.markdown(get_enhanced_styles(), unsafe_allow_html=True)
    
    current_precision = st.session_state.get('precision_level', 5)
    
    st.info(f"현재 정밀도: **레벨 {current_precision}**")
    
    new_precision = st.slider(
        "새로운 정밀도 레벨",
        min_value=1,
        max_value=10,
        value=current_precision,
        help="높은 레벨일수록 더 많은 이미지를 추출하고 정밀한 분석을 수행합니다."
    )
    
    precision_info = {
        1: ("⚡ 초고속", "4개 이미지, 30초-1분", "precision-success"),
        2: ("🏃 고속", "4개 이미지, 1-2분", "precision-success"),
        3: ("🚶 빠름", "5개 이미지, 2-3분", "precision-info"),
        4: ("🚶‍♂️ 보통-빠름", "5개 이미지, 3-4분", "precision-info"),
        5: ("⚖️ 균형 (권장)", "6개 이미지, 4-6분", "precision-info"),
        6: ("🔍 정밀", "7개 이미지, 6-8분", "precision-warning"),
        7: ("🔬 고정밀", "8개 이미지, 8-12분", "precision-warning"),
        8: ("🎯 매우정밀", "10개 이미지, 12-15분", "precision-warning"),
        9: ("🏆 초정밀", "10개 이미지, 15-20분", "precision-warning"),
        10: ("💎 최고정밀", "10개 이미지, 20-30분", "precision-warning")
    }
    
    if new_precision in precision_info:
        title, desc, style_class = precision_info[new_precision]
        st.markdown(f'''
        <div class="{style_class}">
            <strong>{title}</strong><br>
            {desc}
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 이 정밀도로 재분석", type="primary", use_container_width=True):
            st.session_state.precision_level = new_precision
            st.session_state.show_precision_modal = False
            st.session_state.analysis_result = None
            set_analysis_state('processing')
            st.rerun()
    
    with col2:
        if st.button("취소", use_container_width=True):
            st.session_state.show_precision_modal = False
            st.rerun()
