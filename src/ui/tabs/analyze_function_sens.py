# src/ui/tabs/analyze_function_sens.py
"""
정밀도 설정 기능 모듈
"""

import streamlit as st
import os
from typing import Dict, Any
from ui.styles import get_enhanced_styles
from storage.db_manager import VideoAnalysisDB
from utils.logger import get_logger

logger = get_logger(__name__)

# 정밀도 프리셋 정의
SENSITIVITY_PRESETS = {
    "빠른 분석": {
        "name": "빠른 분석",
        "icon": "⚡",
        "description": "핵심 장면만 추출하여 빠르게 분석합니다",
        "scene_detection_threshold": 0.5,
        "max_scenes": 10,
        "min_scene_duration": 3.0,
        "analysis_depth": "basic",
        "color": "#4CAF50"
    },
    "표준 분석": {
        "name": "표준 분석",
        "icon": "⚖️",
        "description": "균형잡힌 정밀도로 대부분의 영상에 적합합니다",
        "scene_detection_threshold": 0.3,
        "max_scenes": 20,
        "min_scene_duration": 2.0,
        "analysis_depth": "standard",
        "color": "#2196F3"
    },
    "정밀 분석": {
        "name": "정밀 분석",
        "icon": "🔍",
        "description": "세밀한 장면 변화까지 감지하여 상세히 분석합니다",
        "scene_detection_threshold": 0.15,
        "max_scenes": 30,
        "min_scene_duration": 1.0,
        "analysis_depth": "detailed",
        "color": "#FF9800"
    },
    "최고 정밀도": {
        "name": "최고 정밀도",
        "icon": "🔬",
        "description": "모든 장면 변화를 감지하여 최대한 상세하게 분석합니다",
        "scene_detection_threshold": 0.08,
        "max_scenes": 50,
        "min_scene_duration": 0.5,
        "analysis_depth": "comprehensive",
        "color": "#F44336"
    }
}

def render_sensitivity_settings():
    """정밀도 설정 UI 렌더링"""
    if not st.session_state.get('show_sensitivity', False):
        return
    
    st.markdown("---")
    st.markdown("### 🎚️ 분석 정밀도 설정")
    st.info("영상 분석의 정밀도를 조정할 수 있습니다. 정밀도가 높을수록 더 많은 장면을 추출하고 분석 시간이 길어집니다.")
    
    # 현재 설정 가져오기
    current_preset = st.session_state.get('sensitivity_preset', '표준 분석')
    
    # CSS 스타일
    st.markdown("""
    <style>
    .preset-card {
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        cursor: pointer;
        transition: all 0.3s ease;
        background-color: white;
    }
    
    .preset-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    
    .preset-card.selected {
        border-color: #2196F3;
        background-color: #E3F2FD;
        box-shadow: 0 3px 10px rgba(33,150,243,0.3);
    }
    
    .preset-header {
        display: flex;
        align-items: center;
        margin-bottom: 10px;
    }
    
    .preset-icon {
        font-size: 24px;
        margin-right: 10px;
    }
    
    .preset-name {
        font-size: 18px;
        font-weight: bold;
        color: #333;
    }
    
    .preset-description {
        color: #666;
        margin-bottom: 15px;
    }
    
    .preset-details {
        background-color: #f5f5f5;
        border-radius: 5px;
        padding: 10px;
        font-size: 14px;
    }
    
    .detail-item {
        display: flex;
        justify-content: space-between;
        margin: 5px 0;
    }
    
    .detail-label {
        color: #888;
    }
    
    .detail-value {
        font-weight: bold;
        color: #333;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 프리셋 선택 UI
    cols = st.columns(2)
    selected_preset = None
    
    for idx, (preset_name, preset_data) in enumerate(SENSITIVITY_PRESETS.items()):
        col = cols[idx % 2]
        
        with col:
            # 카드 컨테이너
            is_selected = current_preset == preset_name
            card_class = "preset-card selected" if is_selected else "preset-card"
            
            # 프리셋 카드 HTML
            card_html = f"""
            <div class="{card_class}" style="border-color: {preset_data['color'] if is_selected else '#e0e0e0'};">
                <div class="preset-header">
                    <span class="preset-icon">{preset_data['icon']}</span>
                    <span class="preset-name" style="color: {preset_data['color']};">{preset_data['name']}</span>
                </div>
                <div class="preset-description">{preset_data['description']}</div>
                <div class="preset-details">
                    <div class="detail-item">
                        <span class="detail-label">장면 감지 민감도:</span>
                        <span class="detail-value">{preset_data['scene_detection_threshold']}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">최대 장면 수:</span>
                        <span class="detail-value">{preset_data['max_scenes']}개</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">최소 장면 길이:</span>
                        <span class="detail-value">{preset_data['min_scene_duration']}초</span>
                    </div>
                </div>
            </div>
            """
            
            st.markdown(card_html, unsafe_allow_html=True)
            
            # 선택 버튼
            button_type = "secondary" if is_selected else "primary"
            if st.button(
                "✓ 선택됨" if is_selected else "선택",
                key=f"select_preset_{preset_name}",
                use_container_width=True,
                type=button_type
            ):
                selected_preset = preset_name
    
    # 선택 처리
    if selected_preset and selected_preset != current_preset:
        st.session_state.sensitivity_preset = selected_preset
        st.success(f"✅ '{selected_preset}' 모드가 선택되었습니다!")
        
        # 선택된 프리셋의 설정을 세션 상태에 저장
        preset = SENSITIVITY_PRESETS[selected_preset]
        st.session_state.scene_detection_config = {
            'threshold': preset['scene_detection_threshold'],
            'max_scenes': preset['max_scenes'],
            'min_scene_duration': preset['min_scene_duration'],
            'analysis_depth': preset['analysis_depth']
        }
        
        logger.info(f"Sensitivity preset changed to: {selected_preset}")
        st.rerun()
    
    # 고급 설정 섹션
    with st.expander("🔧 고급 설정", expanded=False):
        st.markdown("### 세부 파라미터 조정")
        
        col1, col2 = st.columns(2)
        
        with col1:
            custom_threshold = st.slider(
                "장면 감지 임계값",
                min_value=0.05,
                max_value=1.0,
                value=st.session_state.get('scene_detection_config', {}).get('threshold', 0.3),
                step=0.05,
                help="낮을수록 더 많은 장면을 감지합니다"
            )
            
            custom_max_scenes = st.number_input(
                "최대 장면 수",
                min_value=5,
                max_value=100,
                value=st.session_state.get('scene_detection_config', {}).get('max_scenes', 20),
                step=5,
                help="추출할 최대 장면 수"
            )
        
        with col2:
            custom_min_duration = st.slider(
                "최소 장면 길이 (초)",
                min_value=0.5,
                max_value=5.0,
                value=st.session_state.get('scene_detection_config', {}).get('min_scene_duration', 2.0),
                step=0.5,
                help="이보다 짧은 장면은 무시됩니다"
            )
            
            custom_analysis_depth = st.selectbox(
                "분석 깊이",
                options=["basic", "standard", "detailed", "comprehensive"],
                index=["basic", "standard", "detailed", "comprehensive"].index(
                    st.session_state.get('scene_detection_config', {}).get('analysis_depth', 'standard')
                ),
                help="AI 분석의 상세도를 결정합니다"
            )
        
        # 사용자 정의 설정 적용 버튼
        if st.button("🔧 사용자 정의 설정 적용", type="primary", use_container_width=True):
            st.session_state.sensitivity_preset = "사용자 정의"
            st.session_state.scene_detection_config = {
                'threshold': custom_threshold,
                'max_scenes': custom_max_scenes,
                'min_scene_duration': custom_min_duration,
                'analysis_depth': custom_analysis_depth
            }
            st.success("✅ 사용자 정의 설정이 적용되었습니다!")
            logger.info("Custom sensitivity settings applied")
            st.rerun()
    
    # 현재 설정 요약
    st.markdown("---")
    st.markdown("### 📊 현재 설정")
    
    current_config = st.session_state.get('scene_detection_config', {})
    if current_config:
        config_cols = st.columns(4)
        
        with config_cols[0]:
            st.metric("모드", st.session_state.get('sensitivity_preset', '표준 분석'))
        
        with config_cols[1]:
            st.metric("장면 감지 임계값", f"{current_config.get('threshold', 0.3):.2f}")
        
        with config_cols[2]:
            st.metric("최대 장면 수", f"{current_config.get('max_scenes', 20)}개")
        
        with config_cols[3]:
            st.metric("분석 깊이", current_config.get('analysis_depth', 'standard'))
    
    # 설정 완료 버튼
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("✅ 설정 완료", type="primary", use_container_width=True):
            st.session_state.show_sensitivity = False
            st.success("정밀도 설정이 완료되었습니다!")
            st.rerun()

def get_current_sensitivity_config() -> Dict[str, Any]:
    """현재 정밀도 설정 반환"""
    # 기본값
    default_config = {
        'threshold': 0.3,
        'max_scenes': 20,
        'min_scene_duration': 2.0,
        'analysis_depth': 'standard'
    }
    
    # 세션 상태에서 설정 가져오기
    return st.session_state.get('scene_detection_config', default_config)

def apply_sensitivity_to_scene_detection(video_service):
    """비디오 서비스에 정밀도 설정 적용"""
    config = get_current_sensitivity_config()
    
    if hasattr(video_service, 'scene_detector') and video_service.scene_detector:
        # SceneDetector에 설정 적용
        video_service.scene_detector.threshold = config['threshold']
        video_service.scene_detector.min_scene_len = int(config['min_scene_duration'] * 30)  # fps를 30으로 가정
        
        logger.info(f"Applied sensitivity settings to scene detector: {config}")
    
    return config