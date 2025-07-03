# core/handlers/video_handler.py
"""향상된 비디오 처리 핸들러 - Pipeline 기반"""

import streamlit as st
from typing import Optional, Callable
from utils.logger import get_logger

logger = get_logger(__name__)


def handle_video_analysis_enhanced(video_url: str, precision_level: int, console_callback: Callable, model_name: str = "gpt-4o", progress_callback: Callable = None):
    """향상된 비디오 분석 - Pipeline 기반 실시간 콘솔 출력
    
    Args:
        video_url: 분석할 비디오 URL
        precision_level: 정밀도 레벨
        console_callback: 콘솔 출력 콜백 함수
        model_name: 사용할 AI 모델명 (기본값: gpt-4o)
        progress_callback: 진행률 콜백 함수 (stage, progress, message, detailed_message)
    """
    
    try:
        # VideoService 가져오기 - 오류 처리 강화
        if 'video_service' not in st.session_state or st.session_state.video_service is None:
            console_callback("⚠️ VideoService가 초기화되지 않았습니다. 재초기화 시도...")
            if progress_callback:
                progress_callback("init", 0, "⚠️ VideoService 재초기화 중...", "VideoService not initialized, attempting restart")
            
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
        def progress_callback_wrapper(stage: str, progress: int, message: str):
            # 콘솔에 메시지 출력
            console_callback(message)
            
            # 진행률 콜백 호출
            if progress_callback:
                progress_callback(stage, progress, message, f"Stage: {stage}, Progress: {progress}%, Message: {message}")
            
            # 특별한 단계에서 추가 정보 출력
            if stage == "url_parser" and progress == 100:
                console_callback(f"  🎯 정밀도 레벨 {precision_level} 사용")
                if progress_callback:
                    progress_callback("url_parser", 100, "URL 분석 완료", f"Using precision level: {precision_level}")
            
            elif stage == "download":
                if progress == 10:
                    console_callback("  📡 서버 연결 중...")
                elif progress == 30:
                    console_callback("  📥 영상 다운로드 시작...")
                elif progress == 60:
                    console_callback("  🎬 영상 메타데이터 수집 중...")
                elif progress == 90:
                    console_callback("  ✅ 영상 다운로드 완료")
                    
                if progress_callback:
                    download_details = {
                        10: "Connecting to server...",
                        30: "Starting video download...",
                        60: "Collecting video metadata...",
                        90: "Video download completed"
                    }
                    detail = download_details.get(progress, f"Download progress: {progress}%")
                    progress_callback("download", progress, message, detail)
            
            elif stage == "scene_extraction":
                if progress == 20:
                    console_callback("  🎞️ 장면 전환 감지 중...")
                elif progress == 50:
                    console_callback("  📸 키프레임 추출 중...")
                elif progress == 80:
                    console_callback("  🎨 장면 그룹화 중...")
                elif progress == 100:
                    console_callback("  ✅ 장면 추출 완료")
                    
                if progress_callback:
                    scene_details = {
                        20: "Detecting scene transitions...",
                        50: "Extracting key frames...",
                        80: "Grouping scenes...",
                        100: "Scene extraction completed"
                    }
                    detail = scene_details.get(progress, f"Scene extraction: {progress}%")
                    progress_callback("scene_extraction", progress, message, detail)
            
            elif stage == "ai_analysis":
                if progress == 10:
                    console_callback("  🤖 AI 모델 로딩 중...")
                elif progress == 30:
                    console_callback("  👁️ 시각적 구성 요소 분석...")
                elif progress == 50:
                    console_callback("  🎨 색감 및 톤 분석...")
                elif progress == 70:
                    console_callback("  ✂️ 편집 스타일 파악...")
                elif progress == 85:
                    console_callback("  🎭 장르 특성 매칭...")
                elif progress == 95:
                    console_callback("  📊 최종 분석 결과 생성...")
                elif progress == 100:
                    console_callback("  ✅ AI 분석 완료")
                    
                if progress_callback:
                    ai_details = {
                        10: "Loading AI model...",
                        30: "Analyzing visual composition...",
                        50: "Analyzing color and tone...",
                        70: "Identifying editing style...",
                        85: "Matching genre characteristics...",
                        95: "Generating final analysis...",
                        100: "AI analysis completed"
                    }
                    detail = ai_details.get(progress, f"AI analysis: {progress}%")
                    progress_callback("ai_analysis", progress, message, detail)
            
            elif stage == "metadata_save":
                if progress == 50:
                    console_callback("  💾 데이터베이스 저장 중...")
                elif progress == 100:
                    console_callback("  ✅ 메타데이터 저장 완료")
                    
                if progress_callback:
                    save_details = {
                        50: "Saving to database...",
                        100: "Metadata saved successfully"
                    }
                    detail = save_details.get(progress, f"Metadata save: {progress}%")
                    progress_callback("metadata_save", progress, message, detail)
            
            elif stage == "storage_upload":
                if progress == 100:
                    console_callback("  ☁️ 스토리지 업로드 완료")
                    
                if progress_callback:
                    progress_callback("storage_upload", progress, message, "Storage upload completed")
            
            elif stage == "cleanup":
                if progress == 100:
                    console_callback("  🧹 임시 파일 정리 완료")
                    
                if progress_callback:
                    progress_callback("cleanup", progress, message, "Temporary files cleaned up")
        
        # 시작 메시지
        console_callback("🎬 영상 분석 프로세스 시작")
        console_callback(f"🎯 정밀도 레벨: {precision_level}")
        
        if progress_callback:
            progress_callback("init", 0, "🎬 영상 분석 시작", f"Starting analysis with precision level: {precision_level}")
        
        # 모델명을 환경변수로 설정
        os.environ["AI_MODEL_NAME"] = model_name
        
        # Pipeline 기반 VideoProcessor 호출
        video = video_service.process(
            url=video_url,
            force_reanalyze=False,
            progress_callback=progress_callback_wrapper
        )
        
        # 분석 완료 후 결과 요약
        if video:
            console_callback("━" * 50)
            console_callback("📊 분석 결과 요약:")
            
            if progress_callback:
                progress_callback("completed", 100, "📊 분석 결과 요약 생성", "Generating analysis summary")
            
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
        
        # 파이프라인 완료 후 세션 상태 업데이트
        try:
            from utils.session_manager import get_session_manager, get_current_session
            session_manager = get_session_manager()
            current_session = get_current_session()
            session_manager.mark_pipeline_completed(current_session.session_id)
            console_callback("💾 분석 완료 - 세션 상태 업데이트됨 (5분 후 정리 예정)")
        except Exception as session_error:
            logger.warning(f"세션 상태 업데이트 실패: {session_error}")
        
        return video
        
    except Exception as e:
        error_msg = f"❌ 오류 발생: {str(e)}"
        console_callback(error_msg)
        
        if progress_callback:
            progress_callback("error", 0, error_msg, f"Error details: {str(e)}")
        
        logger.error(f"분석 중 오류: {str(e)}")
        raise
