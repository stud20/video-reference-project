# src/handlers/enhanced_video_handler.py
"""
향상된 비디오 처리 핸들러 - 실시간 콘솔 출력 with 실제 VideoService 연동
"""

import streamlit as st
import time
from typing import Optional, Callable
from utils.logger import get_logger

logger = get_logger(__name__)


def handle_video_analysis_enhanced(video_url: str, precision_level: int, console_callback: Callable):
    """
    향상된 비디오 분석 - 실시간 콘솔 출력 with 실제 VideoService
    
    Args:
        video_url: 분석할 비디오 URL
        precision_level: 정밀도 레벨 (1-10)
        console_callback: 콘솔 업데이트 콜백 함수
    """
    
    try:
        # VideoService 가져오기
        video_service = st.session_state.video_service
        
        # 정밀도 레벨 환경변수 설정
        import os
        os.environ["SCENE_PRECISION_LEVEL"] = str(precision_level)
        
        # 진행 상황 메시지 매핑
        step_messages = {
            'parsing': {
                5: "🔍 영상 URL 분석 시작...",
                10: "✅ 플랫폼 확인: {platform} - {video_id}"
            },
            'checking': {
                12: "📊 기존 분석 결과 확인 중...",
                15: "✅ 기존 분석 결과 발견"
            },
            'download': {
                20: "📥 영상 정보 가져오는 중...",
                25: "📥 영상 다운로드 시작...",
                35: "✅ 다운로드 완료: {title}"
            },
            'metadata': {
                40: "📋 메타데이터 처리 중..."
            },
            'database': {
                45: "💾 데이터베이스에 정보 저장 중..."
            },
            'extract': {
                50: "🎬 주요 씬 추출 시작...",
                60: "✅ {count}개 씬 추출 완료"
            },
            'analyze': {
                65: "🤖 AI 영상 분석 시작...",
                70: "🤖 이미지 준비 중...",
                75: "✅ AI 분석 성공: {genre}",
                78: "💾 분석 결과 저장 중...",
                80: "✅ AI 분석 완료"
            },
            'upload': {
                85: "📤 스토리지 업로드 시작...",
                95: "✅ 스토리지 업로드 완료"
            },
            'notion': {
                96: "📝 Notion 데이터베이스에 업로드 중...",
                98: "✅ Notion 업로드 성공!"
            },
            'cleanup': {
                99: "🗑️ 임시 파일 정리 중..."
            },
            'complete': {
                100: "✅ 영상 처리 완료: {video_id}"
            }
        }
        
        # 진행 상황 추적을 위한 변수들
        current_step = ""
        step_start_time = time.time()
        
        # 콘솔 업데이트를 위한 래퍼 함수
        def progress_callback(step: str, progress: int, message: str):
            nonlocal current_step, step_start_time
            
            # 새로운 단계 시작 시
            if step != current_step:
                current_step = step
                step_start_time = time.time()
            
            # 콘솔에 메시지 출력
            console_callback(message)
            
            # 단계별 추가 정보 출력
            if step == "download" and progress == 35:
                # 다운로드 완료 시 추가 정보
                elapsed = time.time() - step_start_time
                console_callback(f"  ⏱️ 다운로드 시간: {elapsed:.1f}초")
            
            elif step == "extract" and progress == 60:
                # 씬 추출 완료 시 추가 정보
                console_callback(f"  🎯 정밀도 레벨 {precision_level} 사용")
            
            elif step == "analyze" and progress == 70:
                # AI 분석 중 상세 단계 표시
                analysis_steps = [
                    "시각적 구성 요소 분석...",
                    "색감 및 톤 분석...",
                    "편집 스타일 파악...",
                    "장르 특성 매칭...",
                    "내러티브 구조 분석...",
                    "타겟 오디언스 추론...",
                    "감정적 톤 파악..."
                ]
                
                for i, analysis_step in enumerate(analysis_steps):
                    time.sleep(0.3)  # 각 단계별 약간의 지연
                    console_callback(f"  ⚙️ {analysis_step}")
            
            # 진행률이 특정 값일 때 추가 메시지
            if progress in [25, 50, 75]:
                total_elapsed = time.time() - step_start_time
                if total_elapsed > 2:
                    console_callback(f"  ⏳ 처리 중... (경과 시간: {total_elapsed:.1f}초)")
        
        # 실제 VideoService 호출
        console_callback("🎬 영상 분석 프로세스 시작")
        console_callback(f"🎯 정밀도 레벨: {precision_level}")
        
        video = video_service.process_video(
            url=video_url,
            force_reanalyze=False,
            progress_callback=progress_callback
        )
        
        # 분석 완료 후 추가 정보 출력
        if video:
            console_callback("━" * 50)
            console_callback("📊 분석 결과 요약:")
            
            if video.metadata:
                console_callback(f"  📹 제목: {video.metadata.title[:50]}...")
                console_callback(f"  ⏱️ 길이: {video.metadata.duration//60}분 {video.metadata.duration%60}초")
                console_callback(f"  👁️ 조회수: {video.metadata.view_count:,}회")
            
            if video.analysis_result:
                console_callback(f"  🎭 장르: {video.analysis_result.get('genre', 'Unknown')}")
                console_callback(f"  🎨 표현형식: {video.analysis_result.get('expression_style', 'Unknown')}")
                tags = video.analysis_result.get('tags', [])[:5]
                if tags:
                    console_callback(f"  🏷️ 주요 태그: {', '.join(tags)}")
            
            console_callback("━" * 50)
            console_callback("🎉 모든 처리가 완료되었습니다!")
        
        return video
        
    except Exception as e:
        error_msg = f"❌ 오류 발생: {str(e)}"
        console_callback(error_msg)
        logger.error(f"분석 중 오류: {str(e)}")
        raise


def extract_youtube_id(url: str) -> str:
    """YouTube ID 추출"""
    if "watch?v=" in url:
        return url.split("watch?v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    return "unknown"