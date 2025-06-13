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
    
    # 영상 URL 입력
    video_url = st.text_input(
        "분석할 YouTube 또는 Vimeo 영상 링크를 입력하세요:",
        placeholder="https://www.youtube.com/watch?v=..."
    )
    
    if st.button("🚀 분석 시작", type="primary"):
        if not video_url:
            st.error("❌ 영상 URL을 입력해주세요!")
        else:
            with st.spinner("처리 중..."):
                try:
                    video = st.session_state.video_service.process_video(video_url)
                    st.success("✅ 분석 완료!")
                    st.json(video.metadata.to_dict() if video.metadata else {})
                except Exception as e:
                    st.error(f"오류: {str(e)}")

if __name__ == "__main__":
    main()
