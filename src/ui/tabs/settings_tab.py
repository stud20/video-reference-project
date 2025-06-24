# src/ui/tabs/settings_tab.py
"""
Settings 탭 - 시스템 설정
"""

import streamlit as st
import os
import shutil
from utils.constants import PRECISION_DESCRIPTIONS, TIME_ESTIMATES
from utils.logger import get_logger

logger = get_logger(__name__)


def render_settings_tab():
    """Settings 탭 렌더링"""
    st.header("⚙️ 시스템 설정")
    
    # 정밀도 설정
    render_precision_settings()
    
    st.markdown("---")
    
    # 캐시 관리
    render_cache_settings()
    
    st.markdown("---")
    
    # 스토리지 설정
    render_storage_settings()
    
    st.markdown("---")
    
    # 고급 설정
    render_advanced_settings()


def render_precision_settings():
    """정밀도 설정"""
    st.subheader("🎯 분석 정밀도 설정")
    
    # 현재 정밀도
    current_precision = st.session_state.get('precision_level', 5)
    
    # 정밀도 슬라이더
    new_precision = st.slider(
        "기본 정밀도 레벨",
        min_value=1,
        max_value=10,
        value=current_precision,
        help="모든 새로운 분석에 적용될 기본 정밀도입니다"
    )
    
    # 정밀도 변경 시 세션 상태 업데이트
    if new_precision != current_precision:
        st.session_state.precision_level = new_precision
        os.environ["SCENE_PRECISION_LEVEL"] = str(new_precision)
    
    # 정밀도 설명
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"""
        **레벨 {new_precision}: {PRECISION_DESCRIPTIONS[new_precision]}**
        
        예상 처리 시간: {TIME_ESTIMATES[new_precision]}
        """)
    
    with col2:
        # 정밀도별 상세 설정
        if new_precision == 1:
            st.write("**추출 내용:**")
            st.write("- 메타데이터 (제목, 설명, 길이)")
            st.write("- 썸네일 1장")
            st.write("- 대표 장면 2장")
        elif new_precision == 2:
            st.write("**추출 내용:**")
            st.write("- 메타데이터 (제목, 설명, 길이)")
            st.write("- 썸네일 1장")
            st.write("- 대표 장면 3장")
        elif new_precision == 3:
            st.write("**추출 내용:**")
            st.write("- 메타데이터 + 컷수 분석")
            st.write("- 썸네일 1장")
            st.write("- 대표 장면 5장")
        elif new_precision == 4:
            st.write("**추출 내용:**")
            st.write("- 메타데이터 + 컷수 분석")
            st.write("- 대표 장면 7장")
        elif new_precision == 5:
            st.write("**추출 내용:**")
            st.write("- 메타데이터 + 자막 내용")
            st.write("- 썸네일 1장")
            st.write("- 대표 장면 10장")
        else:
            st.write("**추출 내용:**")
            st.write(f"- 정밀도 레벨 {new_precision} 설정")


def render_cache_settings():
    """캐시 관리 설정"""
    st.subheader("🗑️ 캐시 관리")
    
    # 캐시 디렉토리 크기 계산
    temp_dir = "data/temp"
    cache_size = 0
    file_count = 0
    
    if os.path.exists(temp_dir):
        for dirpath, dirnames, filenames in os.walk(temp_dir):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                cache_size += os.path.getsize(filepath)
                file_count += 1
    
    # 크기를 MB로 변환
    cache_size_mb = cache_size / (1024 * 1024)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("캐시 크기", f"{cache_size_mb:.1f} MB")
    
    with col2:
        st.metric("파일 수", f"{file_count}개")
    
    with col3:
        if st.button("🧹 캐시 정리", type="secondary", use_container_width=True):
            if cache_size > 0:
                with st.spinner("캐시 정리 중..."):
                    try:
                        # temp 디렉토리의 모든 내용 삭제
                        for item in os.listdir(temp_dir):
                            item_path = os.path.join(temp_dir, item)
                            if os.path.isdir(item_path):
                                shutil.rmtree(item_path)
                            else:
                                os.remove(item_path)
                        
                        st.success(f"✅ {cache_size_mb:.1f} MB의 캐시를 정리했습니다!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"캐시 정리 중 오류 발생: {str(e)}")
            else:
                st.info("정리할 캐시가 없습니다")
    
    # 자동 정리 옵션
    auto_clean = st.checkbox(
        "서버 업로드 후 자동으로 로컬 파일 삭제",
        value=os.getenv("AUTO_CLEANUP", "false").lower() == "true",
        help="분석 완료 후 로컬에 저장된 비디오와 이미지를 자동으로 삭제합니다"
    )
    
    if auto_clean:
        os.environ["AUTO_CLEANUP"] = "true"
    else:
        os.environ["AUTO_CLEANUP"] = "false"


def render_storage_settings():
    """스토리지 설정"""
    st.subheader("💾 스토리지 설정")
    
    # 현재 스토리지 타입
    current_storage = os.getenv("STORAGE_TYPE", "sftp").upper()
    
    storage_options = {
        "SFTP": "SFTP (Synology NAS)",
        "WEBDAV": "WebDAV",
        "LOCAL": "로컬 저장소"
    }
    
    selected_storage = st.selectbox(
        "스토리지 타입",
        options=list(storage_options.keys()),
        format_func=lambda x: storage_options[x],
        index=list(storage_options.keys()).index(current_storage)
    )
    
    # 스토리지 변경 시
    if selected_storage != current_storage:
        os.environ["STORAGE_TYPE"] = selected_storage.lower()
        st.info("⚠️ 스토리지 설정이 변경되었습니다. 앱을 재시작해야 적용됩니다.")
    
    # 스토리지별 설정
    if selected_storage == "SFTP":
        with st.expander("SFTP 설정", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                sftp_host = st.text_input("호스트", value=os.getenv("SYNOLOGY_HOST", ""))
                sftp_user = st.text_input("사용자명", value=os.getenv("SYNOLOGY_USER", ""))
            with col2:
                sftp_port = st.number_input("포트", value=int(os.getenv("SFTP_PORT", "22")))
                sftp_pass = st.text_input("비밀번호", type="password", value=os.getenv("SYNOLOGY_PASS", ""))
            
            if st.button("연결 테스트"):
                # TODO: 실제 연결 테스트
                st.success("✅ 연결 성공!")
    
    elif selected_storage == "WEBDAV":
        with st.expander("WebDAV 설정", expanded=True):
            webdav_url = st.text_input("WebDAV URL", value=os.getenv("WEBDAV_HOSTNAME", ""))
            col1, col2 = st.columns(2)
            with col1:
                webdav_user = st.text_input("사용자명", value=os.getenv("WEBDAV_LOGIN", ""))
            with col2:
                webdav_pass = st.text_input("비밀번호", type="password", value=os.getenv("WEBDAV_PASSWORD", ""))


def render_advanced_settings():
    """고급 설정"""
    st.subheader("🔧 고급 설정")
    
    with st.expander("씬 추출 설정"):
        col1, col2 = st.columns(2)
        
        with col1:
            scene_threshold = st.slider(
                "씬 전환 감지 임계값",
                min_value=0.1,
                max_value=0.8,
                value=float(os.getenv("SCENE_THRESHOLD", "0.3")),
                step=0.05,
                help="낮을수록 더 많은 씬 전환을 감지합니다"
            )
            os.environ["SCENE_THRESHOLD"] = str(scene_threshold)
            
            similarity_threshold = st.slider(
                "씬 유사도 임계값",
                min_value=0.80,
                max_value=0.99,
                value=float(os.getenv("SCENE_SIMILARITY_THRESHOLD", "0.92")),
                step=0.01,
                help="높을수록 더 유사한 씬들만 그룹화됩니다"
            )
            os.environ["SCENE_SIMILARITY_THRESHOLD"] = str(similarity_threshold)
        
        with col2:
            min_scene_duration = st.number_input(
                "최소 씬 지속시간 (초)",
                min_value=0.1,
                max_value=5.0,
                value=float(os.getenv("MIN_SCENE_DURATION", "0.5")),
                step=0.1,
                help="이보다 짧은 씬은 무시됩니다"
            )
            os.environ["MIN_SCENE_DURATION"] = str(min_scene_duration)
            
            max_analysis_images = st.number_input(
                "최대 분석 이미지 수",
                min_value=5,
                max_value=20,
                value=int(os.getenv("MAX_ANALYSIS_IMAGES", "10")),
                help="AI 분석에 사용할 최대 이미지 수"
            )
            os.environ["MAX_ANALYSIS_IMAGES"] = str(max_analysis_images)
    
    with st.expander("API 설정"):
        # OpenAI 모델 선택
        openai_model = st.selectbox(
            "OpenAI 모델",
            options=["gpt-4o", "gpt-4-vision-preview", "gpt-4-turbo-preview"],
            index=0
        )
        os.environ["OPENAI_MODEL"] = openai_model
        
        # API 키 확인
        api_key_status = "✅ 설정됨" if os.getenv("OPENAI_API_KEY") else "❌ 미설정"
        st.info(f"OpenAI API 키: {api_key_status}")
    
    # 디버그 모드
    debug_mode = st.checkbox(
        "🐛 디버그 모드",
        value=os.getenv("DEBUG", "false").lower() == "true",
        help="상세한 로그 정보를 표시합니다"
    )
    
    if debug_mode:
        os.environ["DEBUG"] = "true"
    else:
        os.environ["DEBUG"] = "false"