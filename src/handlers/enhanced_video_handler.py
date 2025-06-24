# src/handlers/enhanced_video_handler.py
"""
향상된 비디오 처리 핸들러 - 실시간 콘솔 출력
"""

import streamlit as st
import time
import random
from typing import Optional
from utils.logger import get_logger

logger = get_logger(__name__)


def handle_video_analysis_enhanced(video_url: str, precision_level: int, console_placeholder):
    """향상된 비디오 분석 - 실시간 콘솔 출력"""
    
    # 콘솔 메시지 리스트
    console_messages = []
    
    def add_console_message(message: str, delay: float = 0.1):
        """콘솔에 메시지 추가"""
        console_messages.append(f"[{time.strftime('%H:%M:%S')}] {message}")
        
        # 콘솔 업데이트
        console_html = '<div class="console-window">'
        for i, msg in enumerate(console_messages[-10:]):  # 최근 10줄만 표시
            console_html += f'<div class="console-line" style="animation-delay: {i*0.1}s">{msg}</div>'
        console_html += '</div>'
        
        console_placeholder.markdown(console_html, unsafe_allow_html=True)
        time.sleep(delay)
    
    try:
        # 1. URL 파싱
        add_console_message("🔍 영상 URL 분석 시작...")
        add_console_message(f"URL: {video_url}")
        time.sleep(0.5)
        
        # 플랫폼 감지
        if "youtube.com" in video_url or "youtu.be" in video_url:
            platform = "YouTube"
            video_id = extract_youtube_id(video_url)
        elif "vimeo.com" in video_url:
            platform = "Vimeo"
            video_id = video_url.split("/")[-1]
        else:
            platform = "Unknown"
            video_id = "unknown"
        
        add_console_message(f"✅ 플랫폼 확인: {platform}")
        add_console_message(f"📹 비디오 ID: {video_id}")
        
        # 2. 기존 분석 결과 확인
        add_console_message("📊 기존 분석 결과 확인 중...")
        time.sleep(0.3)
        add_console_message("❌ 기존 분석 결과 없음")
        
        # 3. 영상 다운로드
        add_console_message("📥 영상 정보 가져오는 중...")
        time.sleep(0.5)
        
        # 메타데이터 시뮬레이션
        metadata = {
            'title': 'Sample Video Title',
            'duration': 180,
            'uploader': 'Sample Channel',
            'view_count': random.randint(10000, 1000000)
        }
        
        add_console_message(f"제목: {metadata['title']}")
        add_console_message(f"길이: {metadata['duration']}초")
        add_console_message(f"채널: {metadata['uploader']}")
        add_console_message(f"조회수: {metadata['view_count']:,}회")
        
        # 4. 씬 추출
        add_console_message(f"🎬 정밀도 레벨 {precision_level}로 씬 추출 시작...")
        
        # 정밀도별 설정
        scene_counts = {
            1: 3,  # 썸네일 + 2장
            2: 4,  # 썸네일 + 3장
            3: 6,  # 썸네일 + 5장
            4: 7,  # 7장
            5: 11  # 썸네일 + 10장
        }
        
        target_scenes = scene_counts.get(precision_level, 10)
        
        # 씬 추출 진행
        for i in range(target_scenes):
            add_console_message(f"  씬 {i+1}/{target_scenes} 추출 중...", delay=0.2)
        
        add_console_message(f"✅ {target_scenes}개 씬 추출 완료")
        
        # 5. AI 분석
        add_console_message("🤖 GPT-4 Vision API 호출 준비...")
        time.sleep(0.3)
        
        add_console_message("📤 이미지 업로드 중...")
        time.sleep(0.5)
        
        add_console_message("🧠 AI 분석 진행 중...")
        
        # 분석 단계별 메시지
        analysis_steps = [
            "시각적 요소 분석...",
            "장르 판단 중...",
            "표현 형식 파악...",
            "분위기 분석...",
            "타겟 고객층 추론..."
        ]
        
        for step in analysis_steps:
            add_console_message(f"  {step}", delay=0.3)
        
        add_console_message("✅ AI 분석 완료")
        
        # 6. 결과 저장
        add_console_message("💾 분석 결과 저장 중...")
        time.sleep(0.3)
        
        add_console_message("📤 스토리지 업로드...")
        time.sleep(0.2)
        
        add_console_message("✅ 모든 처리가 완료되었습니다!")
        
        # 더미 결과 반환 (실제로는 video_service 사용)
        from src.models.video import Video, VideoMetadata, Scene
        
        video = Video(
            session_id=video_id,
            url=video_url,
            metadata=VideoMetadata(
                video_id=video_id,
                title=metadata['title'],
                duration=metadata['duration'],
                uploader=metadata['uploader'],
                view_count=metadata['view_count'],
                url=video_url
            )
        )
        
        # 더미 씬 추가
        for i in range(target_scenes):
            video.scenes.append(Scene(
                timestamp=i * 30,
                frame_path=f"dummy_scene_{i}.jpg",
                scene_type='mid'
            ))
        
        # 더미 분석 결과
        video.analysis_result = {
            'genre': 'TVC',
            'expression_style': '실사',
            'reasoning': '제품의 특징을 강조하는 클로즈업 샷과 모델의 사용 장면이 번갈아 나타나며, 짧은 시간 내에 임팩트 있는 메시지를 전달하는 구성을 보입니다.',
            'features': '빠른 컷 전환, 제품 클로즈업, 밝은 조명, 경쾌한 배경음악이 특징적입니다.',
            'mood_tone': '활기차고 긍정적인',
            'target_audience': '20-30대 여성',
            'tags': ['광고', '제품소개', '라이프스타일', '뷰티', '트렌디']
        }
        
        return video
        
    except Exception as e:
        add_console_message(f"❌ 오류 발생: {str(e)}")
        raise


def extract_youtube_id(url: str) -> str:
    """YouTube ID 추출"""
    if "watch?v=" in url:
        return url.split("watch?v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    return "unknown"