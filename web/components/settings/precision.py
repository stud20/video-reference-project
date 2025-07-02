# web/components/settings/precision.py
"""
분석 정밀도 설정 모듈 - .env 파일 자동 업데이트 지원
"""

import streamlit as st
import os
from utils.constants import PRECISION_DESCRIPTIONS, TIME_ESTIMATES
from utils.env_manager import EnvManager
from utils.logger import get_logger

logger = get_logger(__name__)


def render_precision_settings():
    """분석 정밀도 설정 렌더링"""
    st.subheader("🎯 분석 정밀도 설정")
    
    # 현재 정밀도 레벨
    current_precision = EnvManager.get_int("SCENE_PRECISION_LEVEL", 5)
    
    # 메인 정밀도 설정
    col1, col2 = st.columns([3, 1])
    
    with col1:
        new_precision = st.slider(
            "정밀도 레벨",
            min_value=1,
            max_value=10,
            value=current_precision,
            help="씬 그룹화의 정밀도를 설정합니다"
        )
    
    with col2:
        st.metric("현재 레벨", f"{current_precision}")
        if new_precision != current_precision:
            st.caption(f"→ {new_precision}")
    
    # 레벨 변경 시 즉시 환경변수 업데이트
    if new_precision != current_precision:
        # 환경변수 즉시 업데이트
        os.environ["SCENE_PRECISION_LEVEL"] = str(new_precision)
        
        # .env 파일에도 저장
        if EnvManager.update("SCENE_PRECISION_LEVEL", new_precision):
            st.success(f"✅ 정밀도 레벨이 {current_precision}에서 {new_precision}로 변경되었습니다")
            
            # 세션 상태에도 저장 (옵션)
            st.session_state['scene_precision_level'] = new_precision
    
    # 정밀도 레벨 상세 정보
    st.markdown("---")
    render_precision_details(new_precision)
    
    # 고급 설정
    st.markdown("---")
    render_advanced_settings()
    
    # 정밀도 레벨별 비교표
    st.markdown("---")
    render_precision_comparison()


def render_advanced_settings():
    """고급 씬 추출 설정"""
    with st.expander("⚙️ 고급 씬 추출 설정"):
        st.markdown("### 씬 감지 설정")
        
        col1, col2 = st.columns(2)
        
        with col1:
            current_threshold = EnvManager.get_float("SCENE_THRESHOLD", 0.3)
            scene_threshold = st.slider(
                "씬 전환 감지 임계값",
                min_value=0.1,
                max_value=0.8,
                value=current_threshold,
                step=0.05,
                help="낮을수록 더 많은 씬 전환을 감지합니다"
            )
            if scene_threshold != current_threshold:
                EnvManager.update("SCENE_THRESHOLD", scene_threshold)
            
            current_duration = EnvManager.get_float("MIN_SCENE_DURATION", 0.5)
            min_scene_duration = st.number_input(
                "최소 씬 지속시간 (초)",
                min_value=0.1,
                max_value=5.0,
                value=current_duration,
                step=0.1,
                help="이보다 짧은 씬은 무시됩니다"
            )
            if min_scene_duration != current_duration:
                EnvManager.update("MIN_SCENE_DURATION", min_scene_duration)
        
        with col2:
            current_similarity = EnvManager.get_float("SCENE_SIMILARITY_THRESHOLD", 0.92)
            similarity_threshold = st.slider(
                "씬 유사도 임계값",
                min_value=0.80,
                max_value=0.99,
                value=current_similarity,
                step=0.01,
                help="높을수록 더 유사한 씬들만 그룹화됩니다"
            )
            if similarity_threshold != current_similarity:
                EnvManager.update("SCENE_SIMILARITY_THRESHOLD", similarity_threshold)
            
            current_max_images = EnvManager.get_int("MAX_ANALYSIS_IMAGES", 10)
            max_analysis_images = st.number_input(
                "최대 분석 이미지 수",
                min_value=5,
                max_value=20,
                value=current_max_images,
                help="AI 분석에 사용할 최대 이미지 수"
            )
            if max_analysis_images != current_max_images:
                EnvManager.update("MAX_ANALYSIS_IMAGES", max_analysis_images)
        
        st.markdown("### 그룹화 설정")
        
        col3, col4 = st.columns(2)
        
        with col3:
            current_min_scenes = EnvManager.get_int("MIN_SCENES_FOR_GROUPING", 10)
            min_scenes_for_grouping = st.number_input(
                "그룹화 최소 씬 개수",
                min_value=5,
                max_value=30,
                value=current_min_scenes,
                help="이보다 적은 씬은 그룹화하지 않습니다"
            )
            if min_scenes_for_grouping != current_min_scenes:
                EnvManager.update("MIN_SCENES_FOR_GROUPING", min_scenes_for_grouping)
        
        with col4:
            current_hash = EnvManager.get_int("SCENE_HASH_THRESHOLD", 5)
            hash_threshold = st.number_input(
                "해시 차이 임계값",
                min_value=1,
                max_value=20,
                value=current_hash,
                help="지각적 해시의 차이 허용치"
            )
            if hash_threshold != current_hash:
                EnvManager.update("SCENE_HASH_THRESHOLD", hash_threshold)
        
        # 변경사항 저장 알림
        if st.button("💾 모든 변경사항이 자동으로 저장됩니다", disabled=True):
            pass


def render_precision_details(level: int):
    """정밀도 레벨 상세 정보 표시"""
    st.markdown("### 📊 레벨 상세 정보")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info(f"""
        **{PRECISION_DESCRIPTIONS[level]}**
        
        예상 처리 시간: **{TIME_ESTIMATES[level]}**
        """)
    
    with col2:
        # 목표 씬 개수 계산
        target_scenes = get_target_scene_count(level)
        st.metric("목표 씬 개수", f"{target_scenes}개")
        
        # 활성화된 특징 수
        active_features = get_active_features_count(level)
        st.metric("활성 특징", f"{active_features}개")
    
    with col3:
        # 처리 속도와 정확도 게이지
        speed = 11 - level  # 1-10 반전
        accuracy = level
        
        st.markdown("**처리 속도**")
        st.progress(speed / 10)
        st.markdown("**분석 정확도**")
        st.progress(accuracy / 10)
    
    # 활성화된 특징 목록
    with st.expander("🔍 활성화된 특징 보기"):
        features = get_active_features_list(level)
        for feature in features:
            st.write(f"• {feature}")


def render_precision_comparison():
    """정밀도 레벨별 비교표"""
    st.markdown("### 📈 정밀도 레벨 비교")
    
    # 비교 데이터 준비
    comparison_data = []
    for level in range(1, 11):
        comparison_data.append({
            "레벨": level,
            "설명": PRECISION_DESCRIPTIONS[level].split(" - ")[1],
            "목표 씬": f"{get_target_scene_count(level)}개",
            "처리 시간": TIME_ESTIMATES[level],
            "추천": "⭐" if level in [5, 6] else ""
        })
    
    # 테이블로 표시
    st.dataframe(
        comparison_data,
        use_container_width=True,
        hide_index=True,
        column_config={
            "레벨": st.column_config.NumberColumn("레벨", width=60),
            "설명": st.column_config.TextColumn("특징", width=200),
            "목표 씬": st.column_config.TextColumn("씬 개수", width=80),
            "처리 시간": st.column_config.TextColumn("예상 시간", width=100),
            "추천": st.column_config.TextColumn("추천", width=50)
        }
    )
    
    st.info("""
    💡 **사용 권장사항**
    - **테스트/프로토타입**: 레벨 1-3 (빠른 처리)
    - **일반적인 분석**: 레벨 5-6 (균형잡힌 선택) ⭐
    - **중요한 프로젝트**: 레벨 7-8 (높은 정확도)
    - **최고 품질 필요시**: 레벨 9-10 (모든 특징 활용)
    """)


# 헬퍼 함수들
def get_target_scene_count(level: int) -> int:
    """정밀도 레벨별 목표 씬 개수"""
    if level <= 2:
        return 4
    elif level <= 4:
        return 5
    elif level == 5:
        return 6
    elif level == 6:
        return 7
    elif level == 7:
        return 8
    else:  # 8-10
        return 10


def get_active_features_count(level: int) -> int:
    """정밀도 레벨별 활성 특징 수"""
    features_count = {
        1: 1,   # color_hist
        2: 2,   # + edge_density
        3: 3,   # + brightness
        4: 4,   # + contrast
        5: 5,   # + color_diversity
        6: 6,   # + texture
        7: 7,   # + spatial_color
        8: 8,   # + perceptual_hash
        9: 8,   # 모든 특징
        10: 8   # 모든 특징 + 고해상도
    }
    return features_count.get(level, 8)


def get_active_features_list(level: int) -> list:
    """정밀도 레벨별 활성 특징 목록"""
    all_features = {
        'color_hist': '색상 히스토그램',
        'edge_density': '엣지 밀도',
        'brightness': '밝기 통계',
        'contrast': '대비',
        'color_diversity': '색상 다양성',
        'texture': '텍스처 특징 (LBP)',
        'spatial_color': '공간별 색상 분포',
        'perceptual_hash': '지각적 해시'
    }
    
    active = []
    if level >= 1:
        active.append(all_features['color_hist'])
    if level >= 2:
        active.append(all_features['edge_density'])
    if level >= 3:
        active.append(all_features['brightness'])
    if level >= 4:
        active.append(all_features['contrast'])
    if level >= 5:
        active.append(all_features['color_diversity'])
    if level >= 6:
        active.append(all_features['texture'])
    if level >= 7:
        active.append(all_features['spatial_color'])
    if level >= 8:
        active.append(all_features['perceptual_hash'])
    if level == 10:
        active.append("고해상도 처리 모드")
    
    return active
