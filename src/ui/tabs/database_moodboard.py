# src/ui/tabs/database_moodboard.py
"""
Database 탭의 무드보드 컴포넌트
"""

import streamlit as st
import os
from typing import Dict, Any, List, Set, Optional
from storage.db_manager import VideoAnalysisDB
from utils.logger import get_logger

logger = get_logger(__name__)

def render_inline_moodboard(video_id: str):
    """인라인 무드보드 렌더링 (비디오 카드 아래에 펼쳐지는 형태)"""
    
    # expander를 사용하여 접을 수 있는 무드보드
    with st.expander(f"🎨 무드보드", expanded=True):
        # 닫기 버튼을 우측 정렬하기 위한 columns
        col1, col2, col3 = st.columns([10, 1, 1])
        with col3:
            if st.button("✖️ 닫기", key=f"close_mood_{video_id}"):
                st.session_state.show_moodboard_modal = False
                st.session_state.moodboard_video_id = None
                st.rerun()
        
        # 씬 정보 가져오기
        video_data = get_video_with_scenes(video_id)
        if not video_data:
            st.error("비디오 정보를 찾을 수 없습니다.")
            return
        
        # 선택된 이미지 추적
        if f'selected_scenes_{video_id}' not in st.session_state:
            st.session_state[f'selected_scenes_{video_id}'] = set()
        
        # 이미지 표시
        render_scene_grid(video_id, video_data)


def get_video_with_scenes(video_id: str) -> Optional[Dict[str, Any]]:
    """비디오 정보와 씬 정보 가져오기"""
    db = VideoAnalysisDB()
    
    try:
        # 비디오 정보 가져오기
        video_info = db.get_video_info(video_id)
        if not video_info:
            return None
        
        # 분석 정보 가져오기
        analysis = db.get_latest_analysis(video_id)
        if analysis:
            video_info['analysis_result'] = analysis
        
        return video_info
        
    finally:
        db.close()


def render_scene_grid(video_id: str, video_data: Dict[str, Any]):
    """씬 이미지 그리드 렌더링"""
    # 웹 서버 URL 설정
    base_url = "https://ref.greatminds.kr"
    session_id = video_id  # video_id가 session_id와 동일
    
    all_items = []
    
    # 썸네일 추가
    thumbnail_url = f"{base_url}/{session_id}/{session_id}_Thumbnail.jpg"
    all_items.append({
        'url': thumbnail_url,
        'type': 'thumbnail',
        'label': '📌 썸네일',
        'scene_num': -1
    })
    
    # 씬 이미지들 추가
    # 로컬에서 씬 파일 목록 확인 (씬 번호 추출용)
    session_dir = f"data/temp/{video_id}"
    scenes_dir = os.path.join(session_dir, "scenes")
    
    scene_numbers = []
    if os.path.exists(scenes_dir):
        scene_files = sorted([f for f in os.listdir(scenes_dir) if f.endswith(('.jpg', '.jpeg', '.png'))])
        for scene_file in scene_files:
            try:
                # scene_0001.jpg 형식에서 번호 추출
                if 'scene_' in scene_file:
                    scene_num = int(scene_file.split('_')[1].split('.')[0])
                    scene_numbers.append(scene_num)
            except:
                pass
    
    # 분석에 사용된 씬 번호들 가져오기
    analyzed_scenes = set()
    if video_data.get('analysis_result', {}).get('analyzed_scenes'):
        for scene_name in video_data['analysis_result']['analyzed_scenes']:
            try:
                if 'scene_' in scene_name:
                    scene_num = int(scene_name.split('_')[1].split('.')[0])
                    analyzed_scenes.add(scene_num)
            except:
                pass
    
    # 씬 URL 생성
    for scene_num in scene_numbers:
        scene_url = f"{base_url}/{session_id}/scene_{scene_num:04d}.jpg"
        is_analyzed = scene_num in analyzed_scenes
        
        all_items.append({
            'url': scene_url,
            'type': 'analyzed' if is_analyzed else 'normal',
            'label': f"Scene #{scene_num:04d}",
            'scene_num': scene_num
        })
    
    # 이미지 그리드 표시 (4열)
    num_cols = 4
    
    # 그리드 렌더링
    for i in range(0, len(all_items), num_cols):
        cols = st.columns(num_cols)
        
        for j, col in enumerate(cols):
            if i + j < len(all_items):
                item = all_items[i + j]
                
                with col:
                    # 이미지와 체크박스를 함께 표시
                    scene_num = item['scene_num']
                    is_selected = scene_num in st.session_state[f'selected_scenes_{video_id}']
                    
                    # URL에서 이미지 표시
                    try:
                        st.image(item['url'], use_container_width=True)
                    except Exception as e:
                        st.error("이미지 로드 실패")
                        logger.error(f"이미지 로드 실패: {item['url']} - {str(e)}")