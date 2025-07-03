# core/handlers/video_handler.py
"""향상된 비디오 처리 핸들러 - Pipeline 기반"""

import streamlit as st
from typing import Optional, Callable
from utils.logger import get_logger

logger = get_logger(__name__)


def handle_video_analysis_enhanced(video_url: str, precision_level: int, console_callback: Callable, model_name: str = "gpt-4o"):
    """향상된 비디오 분석 - Pipeline 기반 실시간 콘솔 출력
    
    Args:
        video_url: 분석할 비디오 URL
        precision_level: 정밀도 레벨
        console_callback: 콘솔 출력 콜백 함수
        model_name: 사용할 AI 모델명 (기본값: gpt-4o)
    """
    
    try:
        # VideoService 가져오기 - 오류 처리 강화
        if 'video_service' not in st.session_state or st.session_state.video_service is None:
            console_callback("⚠️ VideoService가 초기화되지 않았습니다. 재초기화 시도...")
            
            # 세션 상태 재초기화 시도
            from web.state import init_session_state
            init_session_state()
            
            if 'video_service' not in st.session_state or st.session_state.video_service is None:
                raise RuntimeError("VideoService 초기화에 실패했습니다. 페이지를 새로고침하세요.")
        
        video_service = st.session_state.video_service
        
        # 정밀도 레벨 환경변수 설정
        import os
        os.environ["SCENE_PRECISION_LEVEL"] = str(precision_level)
        
        # 콘솔 업데이트를 위한 래퍼 함수
        def progress_callback(stage: str, progress: int, message: str):
            # 콘솔에 메시지 출력
            console_callback(message)
            
            # 특별한 단계에서 추가 정보 출력
            if stage == "download" and progress == 35:
                console_callback(f"  🎯 정밀도 레벨 {precision_level} 사용")
            
            elif stage == "ai_analysis" and progress == 70:
                # AI 분석 중 상세 단계 표시
                import time
                analysis_steps = [
                    "시각적 구성 요소 분석...",
                    "색감 및 톤 분석...",
                    "편집 스타일 파악...",
                    "장르 특성 매칭...",
                    "내러티브 구조 분석...",
                    "타겟 오디언스 추론...",
                    "감정적 톤 파악..."
                ]
                
                for analysis_step in analysis_steps:
                    time.sleep(0.3)
                    console_callback(f"  ⚙️ {analysis_step}")
        
        # 시작 메시지
        console_callback("🎬 영상 분석 프로세스 시작")
        console_callback(f"🎯 정밀도 레벨: {precision_level}")
        
        # 모델명을 환경변수로 설정
        os.environ["AI_MODEL_NAME"] = model_name
        
        # Pipeline 기반 VideoProcessor 호출
        video = video_service.process(
            url=video_url,
            force_reanalyze=False,
            progress_callback=progress_callback
        )
        
        # 분석 완료 후 결과 요약
        if video:
            console_callback("━" * 50)
            console_callback("📊 분석 결과 요약:")
            
            if video.metadata:
                if video.metadata.title:
                    title = video.metadata.title[:50] + "..." if len(video.metadata.title) > 50 else video.metadata.title
                    console_callback(f"  📹 제목: {title}")
                
                if video.metadata.duration is not None and video.metadata.duration > 0:
                    minutes = int(video.metadata.duration // 60)
                    seconds = int(video.metadata.duration % 60)
                    console_callback(f"  ⏱️ 길이: {minutes}분 {seconds}초")
                
                if video.metadata.view_count is not None:
                    console_callback(f"  👁️ 조회수: {video.metadata.view_count:,}회")
            
            if video.analysis_result:
                genre = video.analysis_result.get('genre', 'Unknown')
                console_callback(f"  🎭 장르: {genre}")
                
                expression = video.analysis_result.get('expression_style', 'Unknown')
                console_callback(f"  🎨 표현형식: {expression}")
                
                tags = video.analysis_result.get('tags', [])
                if tags:
                    tag_list = tags[:5]  # 상위 5개만
                    console_callback(f"  🏷️ 주요 태그: {', '.join(tag_list)}")
            
            console_callback("━" * 50)
            console_callback("🎉 모든 처리가 완료되었습니다!")
        
        return video
        
    except Exception as e:
        error_msg = f"❌ 오류 발생: {str(e)}"
        console_callback(error_msg)
        logger.error(f"분석 중 오류: {str(e)}")
        raise
