# app.py
import streamlit as st
import os
import traceback
from src.services.video_service import VideoService
from src.storage.storage_manager import StorageManager, StorageType
from utils.logger import get_logger

# 로거 설정
logger = get_logger(__name__)

# 페이지 설정
st.set_page_config(
    page_title="AI 영상 레퍼런스 분석기",
    page_icon="🎥",
    layout="wide"
)

def init_session_state():
    """세션 상태 초기화"""
    if 'video_service' not in st.session_state:
        # 환경변수에서 스토리지 타입 읽기
        storage_type_str = os.getenv("STORAGE_TYPE", "sftp")
        try:
            storage_type = StorageType[storage_type_str.upper()]
        except KeyError:
            storage_type = StorageType.LOCAL
            logger.warning(f"알 수 없는 스토리지 타입: {storage_type_str}, 로컬 저장소 사용")
        
        # VideoService 초기화 (스토리지 타입 전달)
        st.session_state.video_service = VideoService(storage_type=storage_type)
        st.session_state.storage_type = storage_type
    
    if 'processing_history' not in st.session_state:
        st.session_state.processing_history = []

def main():
    """메인 앱 함수"""
    # 세션 상태 초기화
    init_session_state()
    
    # 헤더
    st.title("🎥 AI 기반 광고 영상 콘텐츠 추론 시스템")
    st.markdown("---")
    
    # 사이드바
    with st.sidebar:
        st.header("📋 프로젝트 정보")
        st.info(
            "**AI 기반 광고 영상 콘텐츠 추론 연구**\n\n"
            "영상 광고의 레퍼런스를 분석하여 내용, 배경, "
            "장르 및 표현 방식을 AI로 추론합니다.\n\n"
            "개발자: 김윤섭 (C65028)"
        )
        
        st.header("🔧 설정")
        
        # 스토리지 상태 표시
        st.subheader("💾 스토리지")
        storage_status = st.empty()
        with storage_status.container():
            if st.session_state.storage_type == StorageType.LOCAL:
                st.warning("📁 로컬 저장소 사용 중")
            elif st.session_state.storage_type == StorageType.SYNOLOGY_API:
                st.success("☁️ Synology NAS 연결")
            elif st.session_state.storage_type == StorageType.SFTP:
                st.success("🔐 SFTP 연결")
            elif st.session_state.storage_type == StorageType.WEBDAV:
                st.info("🌐 WebDAV 연결")
        
        # 스토리지 연결 테스트
        if st.button("🔌 연결 테스트"):
            with st.spinner("연결 테스트 중..."):
                if st.session_state.video_service.test_storage_connection():
                    st.success("✅ 스토리지 연결 성공!")
                else:
                    st.error("❌ 스토리지 연결 실패")
        
        # 디버그 모드
        debug_mode = st.checkbox("🐛 디버그 모드", value=False)
        
        # 비디오 품질 선택
        st.subheader("🎥 다운로드 품질")
        quality = st.radio(
            "품질 선택",
            options=["best", "balanced", "fast"],
            format_func=lambda x: {
                "best": "🏆 최고 품질 (1080p, 느림)",
                "balanced": "⚖️ 균형 (720p, 보통)",
                "fast": "🚀 빠른 다운로드 (MP4만)"
            }[x],
            index=0,
            help="높은 품질일수록 다운로드 시간이 오래 걸립니다"
        )
        # 환경변수로 설정
        os.environ["VIDEO_QUALITY"] = quality
        
        # 처리 이력
        st.header("📝 최근 처리")
        if st.session_state.processing_history:
            for item in st.session_state.processing_history[-5:]:  # 최근 5개
                st.text(f"• {item['time']} - {item['title'][:20]}...")
        else:
            st.info("처리된 영상이 없습니다.")
    
    # 메인 컨텐츠
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("🔗 영상 URL 입력")
        
        # URL 입력
        video_url = st.text_input(
            "분석할 YouTube 또는 Vimeo 영상 링크를 입력하세요:",
            placeholder="https://www.youtube.com/watch?v=... 또는 https://vimeo.com/...",
            help="YouTube와 Vimeo 영상을 지원합니다."
        )
        
        # 예시 URL 버튼들
        st.caption("예시:")
        example_col1, example_col2 = st.columns(2)
        with example_col1:
            if st.button("📺 YouTube 예시", use_container_width=True):
                video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
                st.rerun()
        with example_col2:
            if st.button("🎬 Vimeo 예시", use_container_width=True):
                video_url = "https://vimeo.com/347119375"
                st.rerun()
        
        # 분석 버튼
        if st.button("🚀 분석 시작", type="primary", use_container_width=True):
            if not video_url:
                st.error("❌ 영상 URL을 입력해주세요!")
            else:
                try:
                    # 진행 상황 컨테이너
                    progress_container = st.container()
                    with progress_container:
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        # 1단계: 영상 정보 확인
                        status_text.text("🔍 영상 정보 확인 중...")
                        progress_bar.progress(10)
                        
                        # 2단계: 영상 다운로드
                        status_text.text("📥 영상 다운로드 중...")
                        progress_bar.progress(30)
                        
                        # VideoService를 통해 처리
                        video = st.session_state.video_service.process_video(video_url)
                        
                        # 3단계: 메타데이터 분석
                        status_text.text("📊 메타데이터 분석 중...")
                        progress_bar.progress(60)
                        
                        # 4단계: 스토리지 업로드
                        status_text.text("💾 스토리지에 저장 중...")
                        progress_bar.progress(80)
                        
                        # 5단계: 완료
                        progress_bar.progress(100)
                        status_text.text("✅ 분석 완료!")
                    
                    # 성공 메시지
                    st.success("✅ 영상 분석이 완료되었습니다!")
                    
                    # 처리 이력에 추가
                    from datetime import datetime
                    st.session_state.processing_history.append({
                        'time': datetime.now().strftime("%H:%M"),
                        'title': video.metadata.title if video.metadata else "제목 없음",
                        'url': video_url
                    })
                    
                    # 결과 표시
                    st.header("📋 분석 결과")
                    
                    # 메타데이터 표시
                    with st.expander("📄 영상 메타데이터", expanded=True):
                        if video.metadata:
                            metadata_dict = video.metadata.to_dict()
                            
                            # 주요 정보를 보기 좋게 표시
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.metric("제목", metadata_dict.get('title', 'N/A'))
                                st.metric("업로더", metadata_dict.get('uploader', 'N/A'))
                                st.metric("길이", f"{metadata_dict.get('duration', 0) // 60}분 {metadata_dict.get('duration', 0) % 60}초")
                            with col_b:
                                st.metric("업로드 날짜", metadata_dict.get('upload_date', 'N/A'))
                                st.metric("비디오 ID", metadata_dict.get('video_id', 'N/A'))
                                st.metric("형식", metadata_dict.get('ext', 'N/A'))
                            
                            # 설명
                            if metadata_dict.get('description'):
                                st.text_area("설명", metadata_dict['description'], height=100, disabled=True)
                    
                    # 세션 정보
                    with st.expander("🔧 기술 정보"):
                        st.info(f"📁 세션 ID: {video.session_id}")
                        st.info(f"💾 저장 위치: {st.session_state.storage_type.value}")
                        if video.local_path:
                            st.text(f"📄 로컬 경로: {video.local_path}")
                    
                except ValueError as e:
                    st.error(f"❌ 오류: {str(e)}")
                    logger.error(f"ValueError: {e}")
                    
                except Exception as e:
                    st.error(f"❌ 예기치 않은 오류가 발생했습니다: {str(e)}")
                    logger.error(f"Exception: {e}")
                    if debug_mode:
                        st.text("🐛 디버그 정보:")
                        st.code(traceback.format_exc())
    
    with col2:
        st.header("📊 시스템 상태")
        
        # 지원 플랫폼
        st.subheader("🌐 지원 플랫폼")
        platform_col1, platform_col2 = st.columns(2)
        with platform_col1:
            st.metric("YouTube", "✅ 지원", delta="활성")
        with platform_col2:
            st.metric("Vimeo", "✅ 지원", delta="활성")
        
        # 시스템 리소스 (더미 데이터, 실제로는 시스템 모니터링 추가 가능)
        st.subheader("💻 시스템 리소스")
        resource_col1, resource_col2 = st.columns(2)
        with resource_col1:
            st.metric("CPU 사용률", "15%", delta="-2%")
        with resource_col2:
            st.metric("메모리", "2.1 GB", delta="0.1 GB")
        
        # 작업 통계
        st.subheader("📈 작업 통계")
        total_processed = len(st.session_state.processing_history)
        st.metric("총 처리 영상", f"{total_processed}개")
        
        # 빠른 작업
        st.subheader("⚡ 빠른 작업")
        if st.button("🗑️ 임시 파일 정리", use_container_width=True):
            with st.spinner("정리 중..."):
                # 임시 파일 정리 로직
                import shutil
                temp_dir = "data/temp"
                if os.path.exists(temp_dir):
                    for item in os.listdir(temp_dir):
                        item_path = os.path.join(temp_dir, item)
                        if os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                st.success("✅ 임시 파일 정리 완료!")

if __name__ == "__main__":
    main()