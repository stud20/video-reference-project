# app.py
import streamlit as st
from src.services.video_service import VideoService
from utils.logger import get_logger
import traceback

# 로거 설정
logger = get_logger(__name__)

# 페이지 설정
st.set_page_config(
    page_title="AI 영상 레퍼런스 분석기",
    page_icon="🎥",
    layout="wide"
)

# 세션 상태 초기화
if 'video_service' not in st.session_state:
    st.session_state.video_service = VideoService()

def main():
    """메인 앱 함수"""
    st.title("🎥 AI 기반 광고 영상 콘텐츠 추론 시스템")
    st.markdown("---")
    
    # 사이드바
    with st.sidebar:
        st.header("📋 프로젝트 정보")
        st.info(
            "**AI 기반 광고 영상 콘텐츠 추론 연구**\n\n"
            "영상 광고의 레퍼런스를 분석하여 내용, 배경, "
            "장르 및 표현 방식을 AI로 추론합니다."
        )
        
        st.header("🔧 설정")
        debug_mode = st.checkbox("디버그 모드", value=False)
    
    # 메인 컨텐츠
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("🔗 영상 URL 입력")
        video_url = st.text_input(
            "분석할 YouTube 또는 Vimeo 영상 링크를 입력하세요:",
            placeholder="https://www.youtube.com/watch?v=..."
        )
        
        # 분석 버튼
        if st.button("🚀 분석 시작", type="primary", use_container_width=True):
            if not video_url:
                st.error("❌ 영상 URL을 입력해주세요!")
                return
            
            try:
                # 진행 상황 표시
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # 1. 영상 다운로드
                status_text.text("1️⃣ 영상 다운로드 중...")
                progress_bar.progress(25)
                
                video = st.session_state.video_service.process_video(video_url)
                
                # 2. 메타데이터 표시
                status_text.text("2️⃣ 메타데이터 분석 중...")
                progress_bar.progress(50)
                
                # 3. NAS 업로드
                status_text.text("3️⃣ NAS 업로드 중...")
                progress_bar.progress(75)
                
                # 4. 완료
                progress_bar.progress(100)
                status_text.text("✅ 분석 완료!")
                
                # 결과 표시
                st.success("✅ 영상 분석이 완료되었습니다!")
                
                # 메타데이터 표시
                with st.expander("📄 영상 메타데이터", expanded=True):
                    if video.metadata:
                        metadata_dict = video.metadata.to_dict()
                        for key, value in metadata_dict.items():
                            st.write(f"**{key}:** {value}")
                
                # 세션 정보 표시
                st.info(f"📁 세션 ID: {video.session_id}")
                
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
        st.header("📊 분석 상태")
        
        # 지원 플랫폼 표시
        st.subheader("🌐 지원 플랫폼")
        col_yt, col_vm = st.columns(2)
        with col