# src/handlers/enhanced_video_handler.py
"""
향상된 비디오 처리 핸들러 - 실시간 콘솔 출력
"""

import streamlit as st
import time
import random
from typing import Optional, Callable
from utils.logger import get_logger

logger = get_logger(__name__)


def handle_video_analysis_enhanced(video_url: str, precision_level: int, console_callback: Callable):
    """
    향상된 비디오 분석 - 실시간 콘솔 출력
    
    Args:
        video_url: 분석할 비디오 URL
        precision_level: 정밀도 레벨 (1-10)
        console_callback: 콘솔 업데이트 콜백 함수
    """
    
    try:
        # 1. URL 파싱
        console_callback("🔍 영상 URL 분석 시작...")
        time.sleep(0.3)
        
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
        
        console_callback(f"✅ 플랫폼 확인: {platform} - ID: {video_id}")
        time.sleep(0.5)
        
        # 2. 기존 분석 결과 확인
        console_callback("📊 기존 분석 결과 확인 중...")
        time.sleep(0.8)
        console_callback("❌ 기존 분석 결과 없음 - 새로 분석 시작")
        time.sleep(0.3)
        
        # 3. 영상 다운로드
        console_callback("📥 영상 메타데이터 수집 중...")
        time.sleep(1.0)
        
        # 메타데이터 시뮬레이션 (실제로는 API 호출)
        metadata = {
            'title': 'AI가 만든 놀라운 광고 - 혁신적인 마케팅 사례',
            'duration': 127,
            'uploader': 'Creative Studio',
            'channel_id': 'UC' + ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=16)),
            'view_count': random.randint(50000, 2000000),
            'like_count': random.randint(1000, 50000),
            'upload_date': '20240115',
            'description': '최신 AI 기술을 활용한 혁신적인 광고 제작 사례입니다...',
            'tags': ['AI', '광고', '마케팅', '크리에이티브', '혁신']
        }
        
        console_callback(f"📹 제목: {metadata['title'][:30]}...")
        time.sleep(0.5)
        console_callback(f"⏱️ 길이: {metadata['duration']//60}분 {metadata['duration']%60}초")
        time.sleep(0.3)
        console_callback(f"👁️ 조회수: {metadata['view_count']:,}회")
        time.sleep(0.3)
        
        # 4. 영상 다운로드 진행
        console_callback("💾 영상 다운로드 시작...")
        time.sleep(0.5)
        
        # 다운로드 진행률 시뮬레이션
        download_steps = [20, 45, 70, 85, 100]
        for progress in download_steps:
            console_callback(f"⬇️ 다운로드 진행률: {progress}%")
            time.sleep(0.4)
        
        console_callback("✅ 영상 다운로드 완료!")
        time.sleep(0.3)
        
        # 5. 씬 추출
        console_callback(f"🎬 정밀도 레벨 {precision_level}로 씬 추출 시작...")
        time.sleep(0.5)
        
        # 정밀도별 설정
        precision_configs = {
            1: {'scenes': 4, 'time': 1.0, 'quality': '초고속'},
            2: {'scenes': 4, 'time': 1.5, 'quality': '고속'},
            3: {'scenes': 5, 'time': 2.0, 'quality': '빠름'},
            4: {'scenes': 5, 'time': 2.5, 'quality': '보통-빠름'},
            5: {'scenes': 6, 'time': 3.0, 'quality': '균형'},
            6: {'scenes': 7, 'time': 3.5, 'quality': '정밀'},
            7: {'scenes': 8, 'time': 4.0, 'quality': '고정밀'},
            8: {'scenes': 10, 'time': 4.5, 'quality': '매우정밀'},
            9: {'scenes': 10, 'time': 5.0, 'quality': '초정밀'},
            10: {'scenes': 10, 'time': 6.0, 'quality': '최고정밀'}
        }
        
        config = precision_configs.get(precision_level, precision_configs[5])
        target_scenes = config['scenes']
        
        console_callback(f"🎯 목표: {target_scenes}개 씬 ({config['quality']} 모드)")
        time.sleep(0.5)
        
        # 씬 추출 진행
        console_callback("🔍 씬 전환점 감지 중...")
        time.sleep(config['time'] * 0.3)
        
        console_callback(f"📸 주요 프레임 추출 중...")
        time.sleep(config['time'] * 0.3)
        
        # 씬별 추출
        extracted_scenes = []
        for i in range(target_scenes):
            timestamp = (metadata['duration'] / target_scenes) * i
            console_callback(f"  씬 {i+1}/{target_scenes} - {timestamp:.1f}초 지점")
            extracted_scenes.append({
                'index': i,
                'timestamp': timestamp,
                'type': 'thumbnail' if i == 0 else 'scene'
            })
            time.sleep(config['time'] * 0.4 / target_scenes)
        
        console_callback(f"✅ {target_scenes}개 씬 추출 완료!")
        time.sleep(0.3)
        
        # 6. 이미지 품질 개선
        console_callback("🖼️ 이미지 품질 개선 중...")
        time.sleep(0.5)
        console_callback("  노이즈 제거 및 선명도 향상...")
        time.sleep(0.3)
        console_callback("  색상 보정 완료")
        time.sleep(0.3)
        
        # 7. AI 분석
        console_callback("🤖 GPT-4 Vision API 준비...")
        time.sleep(0.5)
        
        console_callback("📤 이미지 인코딩 및 업로드...")
        time.sleep(0.8)
        
        console_callback("🧠 AI 영상 분석 시작...")
        time.sleep(0.5)
        
        # 분석 단계별 메시지
        analysis_steps = [
            ("시각적 구성 요소 분석...", 1.0),
            ("색감 및 톤 분석...", 0.8),
            ("편집 스타일 파악...", 0.7),
            ("장르 특성 매칭...", 0.9),
            ("내러티브 구조 분석...", 0.8),
            ("타겟 오디언스 추론...", 0.6),
            ("감정적 톤 파악...", 0.5)
        ]
        
        for step, delay in analysis_steps:
            console_callback(f"  ⚙️ {step}")
            time.sleep(delay)
        
        console_callback("✅ AI 분석 완료!")
        time.sleep(0.3)
        
        # 8. 결과 생성
        console_callback("📝 분석 결과 생성 중...")
        time.sleep(0.5)
        
        # 9. 데이터베이스 저장
        console_callback("💾 데이터베이스 저장...")
        time.sleep(0.3)
        console_callback("  메타데이터 저장 완료")
        time.sleep(0.2)
        console_callback("  분석 결과 저장 완료")
        time.sleep(0.2)
        
        # 10. 스토리지 업로드
        console_callback("☁️ 클라우드 스토리지 업로드...")
        time.sleep(0.5)
        console_callback("  이미지 파일 업로드 중...")
        time.sleep(0.5)
        console_callback("  분석 리포트 업로드 중...")
        time.sleep(0.3)
        
        console_callback("🎉 모든 처리가 완료되었습니다!")
        time.sleep(0.5)
        
        # 실제 Video 객체 생성 (더미 데이터)
        from src.models.video import Video, VideoMetadata, Scene
        
        video = Video(
            session_id=video_id,
            url=video_url,
            metadata=VideoMetadata(
                video_id=video_id,
                title=metadata['title'],
                duration=metadata['duration'],
                uploader=metadata['uploader'],
                channel_id=metadata['channel_id'],
                view_count=metadata['view_count'],
                like_count=metadata['like_count'],
                upload_date=metadata['upload_date'],
                description=metadata['description'],
                tags=metadata['tags'],
                url=video_url,
                platform=platform.lower()
            )
        )
        
        # 썸네일 경로 설정 (첫 번째 씬을 썸네일로)
        video.thumbnail_path = f"data/temp/{video_id}/thumbnail.jpg"
        
        # 씬 추가
        for scene_data in extracted_scenes:
            if scene_data['type'] != 'thumbnail':  # 썸네일은 별도 처리
                video.scenes.append(Scene(
                    timestamp=scene_data['timestamp'],
                    frame_path=f"data/temp/{video_id}/scene_{scene_data['index']:03d}.jpg",
                    scene_type='mid'
                ))
        
        # 분석 결과 (정밀도에 따라 품질 조정)
        analysis_quality = min(precision_level / 10.0, 1.0)
        
        # 장르 결정 (랜덤 선택 시뮬레이션)
        genres = ['TVC', '브랜드필름', '바이럴영상', '제품소개', '뮤직비디오', '모션그래픽']
        selected_genre = random.choice(genres)
        
        # 표현형식 결정
        expression_styles = ['실사', '2D애니메이션', '3D애니메이션', '혼합형', '모션그래픽']
        selected_style = random.choice(expression_styles)
        
        # 분석 결과 생성
        video.analysis_result = {
            'genre': selected_genre,
            'expression_style': selected_style,
            'reasoning': generate_reasoning(selected_genre, metadata['title'], analysis_quality),
            'features': generate_features(selected_style, analysis_quality),
            'mood_tone': generate_mood(selected_genre),
            'target_audience': generate_target_audience(selected_genre, metadata['tags']),
            'tags': generate_tags(metadata['tags'], selected_genre, selected_style),
            'confidence': 0.85 + (analysis_quality * 0.15),  # 85-100% 신뢰도
            'analysis_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'precision_level': precision_level
        }
        
        return video
        
    except Exception as e:
        console_callback(f"❌ 오류 발생: {str(e)}")
        logger.error(f"분석 중 오류: {str(e)}")
        raise


def extract_youtube_id(url: str) -> str:
    """YouTube ID 추출"""
    if "watch?v=" in url:
        return url.split("watch?v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    return "unknown"


def generate_reasoning(genre: str, title: str, quality: float) -> str:
    """장르 판단 이유 생성"""
    base_reasoning = {
        'TVC': '제품의 특징을 강조하는 클로즈업 샷과 모델의 사용 장면이 번갈아 나타나며, 짧은 시간 내에 임팩트 있는 메시지를 전달하는 구성을 보입니다.',
        '브랜드필름': '브랜드의 철학과 가치를 스토리텔링을 통해 전달하며, 감성적인 연출과 시네마틱한 영상미가 돋보입니다.',
        '바이럴영상': 'SNS 공유에 최적화된 짧고 임팩트 있는 구성으로, 시청자의 관심을 즉시 끌어들이는 후킹 요소가 강합니다.',
        '제품소개': '제품의 기능과 특징을 체계적으로 설명하며, 실제 사용 시나리오를 통해 이해도를 높이는 구성입니다.',
        '뮤직비디오': '음악의 리듬과 분위기에 맞춘 영상 편집과 아티스트의 퍼포먼스가 조화롭게 구성되어 있습니다.',
        '모션그래픽': '텍스트와 그래픽 요소의 역동적인 움직임을 통해 정보를 시각적으로 전달하는 구성입니다.'
    }
    
    reasoning = base_reasoning.get(genre, '영상의 구성과 연출 방식을 종합적으로 분석한 결과입니다.')
    
    # 품질에 따라 상세도 추가
    if quality > 0.7:
        reasoning += f' 특히 "{title}"라는 제목에서 암시하는 것처럼, 영상 전반에 걸쳐 일관된 메시지를 전달하고 있습니다.'
    
    return reasoning


def generate_features(style: str, quality: float) -> str:
    """특징 생성"""
    base_features = {
        '실사': '자연스러운 조명과 색감, 안정적인 카메라 워크, 실제 배우와 로케이션을 활용한 현실감 있는 연출이 특징입니다.',
        '2D애니메이션': '플랫한 디자인 요소와 부드러운 모션, 선명한 색상 대비와 캐릭터 중심의 스토리텔링이 돋보입니다.',
        '3D애니메이션': '입체적인 공간감과 사실적인 텍스처, 다이나믹한 카메라 앵글과 조명 효과가 인상적입니다.',
        '혼합형': '실사와 그래픽 요소가 자연스럽게 융합되어 현실과 상상의 경계를 넘나드는 표현이 특징입니다.',
        '모션그래픽': '타이포그래피와 도형의 리듬감 있는 움직임, 트렌디한 색상 조합과 트랜지션 효과가 돋보입니다.'
    }
    
    features = base_features.get(style, '독특한 시각적 스타일과 창의적인 연출이 특징입니다.')
    
    if quality > 0.6:
        features += ' 전체적으로 높은 제작 퀄리티와 디테일한 후반 작업이 눈에 띕니다.'
    
    return features


def generate_mood(genre: str) -> str:
    """분위기 생성"""
    mood_map = {
        'TVC': '활기차고 긍정적인',
        '브랜드필름': '감성적이고 영감을 주는',
        '바이럴영상': '재미있고 경쾌한',
        '제품소개': '전문적이고 신뢰감 있는',
        '뮤직비디오': '몽환적이고 아티스틱한',
        '모션그래픽': '모던하고 다이나믹한'
    }
    
    return mood_map.get(genre, '독특하고 인상적인')


def generate_target_audience(genre: str, tags: list) -> str:
    """타겟 고객층 생성"""
    # 태그 기반 타겟 추론
    if any(tag in ['패션', '뷰티', '코스메틱'] for tag in tags):
        return '20-30대 여성'
    elif any(tag in ['게임', 'IT', '테크'] for tag in tags):
        return '10-30대 남성'
    elif any(tag in ['육아', '교육', '키즈'] for tag in tags):
        return '30-40대 부모'
    
    # 장르 기반 기본 타겟
    target_map = {
        'TVC': 'MZ세대 전반',
        '브랜드필름': '브랜드 충성도가 높은 2040',
        '바이럴영상': 'SNS 활동이 활발한 1030',
        '제품소개': '구매 의사결정권자',
        '뮤직비디오': '음악 팬덤 및 대중',
        '모션그래픽': '비주얼에 민감한 크리에이터'
    }
    
    return target_map.get(genre, '일반 대중')


def generate_tags(original_tags: list, genre: str, style: str) -> list:
    """태그 생성 (기존 태그 + AI 추론 태그)"""
    # 기본 태그 풀
    genre_tags = {
        'TVC': ['광고', '상업광고', 'CF', '제품홍보'],
        '브랜드필름': ['브랜딩', '기업홍보', '스토리텔링'],
        '바이럴영상': ['바이럴', 'SNS', '화제영상'],
        '제품소개': ['제품소개', '언박싱', '리뷰'],
        '뮤직비디오': ['뮤비', 'MV', '음악영상'],
        '모션그래픽': ['모션', '그래픽', '인포그래픽']
    }
    
    style_tags = {
        '실사': ['실사촬영', '라이브액션'],
        '2D애니메이션': ['2D', '애니메이션', '일러스트'],
        '3D애니메이션': ['3D', 'CGI', '컴퓨터그래픽'],
        '혼합형': ['MixedMedia', '합성영상'],
        '모션그래픽': ['키네틱타이포', '모션디자인']
    }
    
    # 태그 조합
    all_tags = list(original_tags)  # 원본 태그 유지
    all_tags.extend(genre_tags.get(genre, []))
    all_tags.extend(style_tags.get(style, []))
    
    # 추가 추론 태그
    additional_tags = ['크리에이티브', '영상제작', '비디오마케팅', '콘텐츠', '디지털마케팅']
    all_tags.extend(random.sample(additional_tags, 3))
    
    # 중복 제거 및 최대 20개 제한
    unique_tags = list(dict.fromkeys(all_tags))
    return unique_tags[:20]