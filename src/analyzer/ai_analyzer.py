# src/analyzer/ai_analyzer.py
"""AI 기반 영상 장르 및 콘텐츠 분석"""

import os
import base64
import json
from typing import List, Dict, Optional
from pathlib import Path
from openai import OpenAI
from dataclasses import dataclass
from utils.logger import get_logger
from src.models.video import Video, Scene

@dataclass
class AnalysisResult:
    """분석 결과 데이터 클래스"""
    genre: str  # 영상 장르
    reason: str  # 판단 이유
    features: str  # 특이사항
    tags: List[str]  # 태그 목록
    format_type: str  # 표현 형식 (2D, 3D, 실사 등)
    mood: Optional[str] = None  # 전반적인 분위기
    target_audience: Optional[str] = None  # 타겟 고객층
    confidence: Optional[float] = None  # 분석 신뢰도

class AIAnalyzer:
    """영상 분석을 위한 AI 엔진"""
    
    # 가능한 장르 목록
    GENRES = [
        "2D애니메이션", "3D애니메이션", "모션그래픽", "인터뷰", 
        "스팟광고", "VLOG", "유튜브콘텐츠", "다큐멘터리", 
        "브랜드필름", "TVC", "뮤직비디오", "교육콘텐츠",
        "제품소개", "이벤트영상", "웹드라마", "바이럴영상"
    ]
    
    # 표현 형식
    FORMAT_TYPES = ["2D", "3D", "실사", "혼합형", "스톱모션", "타이포그래피"]
    
    def __init__(self, api_key: Optional[str] = None):
        self.logger = get_logger(__name__)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            self.logger.warning("OpenAI API 키가 설정되지 않았습니다")
            self.client = None
        else:
            self.client = OpenAI(api_key=self.api_key)
    
    def analyze_video(self, video: Video) -> Optional[AnalysisResult]:
        """비디오 분석 수행"""
        if not self.client:
            self.logger.error("OpenAI 클라이언트가 초기화되지 않았습니다")
            return None
        
        if not video.scenes:
            self.logger.warning("분석할 씬 이미지가 없습니다")
            return None
        
        try:
            # 이미지 준비
            image_payloads = self._prepare_images(video.scenes)
            
            # 컨텍스트 정보 준비
            context = self._prepare_context(video)
            
            # GPT-4 Vision API 호출
            response = self._call_gpt4_vision(image_payloads, context)
            
            # 응답 파싱
            result = self._parse_response(response)
            
            # 결과 저장
            self._save_analysis_result(video, result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"영상 분석 중 오류 발생: {e}")
            return None
    
    def _prepare_images(self, scenes: List[Scene], max_images: int = 10) -> List[Dict]:
        """분석을 위한 이미지 준비"""
        image_payloads = []
        
        # 최대 10개의 대표 씬 선택
        selected_scenes = scenes[:max_images] if len(scenes) > max_images else scenes
        
        for scene in selected_scenes:
            if os.path.exists(scene.frame_path):
                try:
                    with open(scene.frame_path, "rb") as f:
                        b64_image = base64.b64encode(f.read()).decode("utf-8")
                        image_payloads.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}
                        })
                except Exception as e:
                    self.logger.warning(f"이미지 로드 실패: {scene.frame_path} - {e}")
        
        self.logger.info(f"📸 {len(image_payloads)}개 이미지 준비 완료")
        return image_payloads
    
    def _prepare_context(self, video: Video) -> str:
        """분석을 위한 컨텍스트 정보 준비"""
        context_parts = []
        
        if video.metadata:
            # 제목
            if video.metadata.title:
                context_parts.append(f"제목: {video.metadata.title}")
            
            # 길이
            if video.metadata.duration:
                minutes = video.metadata.duration // 60
                seconds = video.metadata.duration % 60
                context_parts.append(f"영상 길이: {minutes}분 {seconds}초")
            
            # 업로더
            if video.metadata.uploader:
                context_parts.append(f"업로더: {video.metadata.uploader}")
            
            # 설명 (처음 200자만)
            if video.metadata.description:
                desc = video.metadata.description[:200]
                if len(video.metadata.description) > 200:
                    desc += "..."
                context_parts.append(f"설명: {desc}")
        
        return "\n".join(context_parts)
    
    def _call_gpt4_vision(self, image_payloads: List[Dict], context: str) -> str:
        """GPT-4 Vision API 호출"""
        prompt = f"""
{context}

다음은 하나의 영상에서 추출한 대표 장면 이미지입니다.
이 영상에 대해 아래 항목을 명확하게 판단해주세요. 이미지와 제공된 정보를 종합적으로 분석해주세요.
어떻게든 최대한 정보를 이용해서 100자 이상으로 작성해줘

[분석 요청 항목]
1. 영상의 장르를 판단해주세요. (표현 방식과 러닝타임을 기준으로 판단, 한 가지만 작성)
   가능한 장르: {', '.join(self.GENRES)}
   
2. 장르로 판단한 이유 (연출 방식, 정보 전달 구조, 시청자에게 주는 인상 등을 구체적으로)

3. 영상의 주요 특징 및 특이사항
   - 시각적 스타일
   - 편집 리듬
   - 색감과 톤
   - 카메라 워크
   
4. 이 영상에 어울리는 태그를 10개 추출 (쉼표로 구분, 띄어쓰기 없이)
   예: 감성적,미니멀,브랜드스토리,젊은층타겟

5. 영상의 표현 형식: {', '.join(self.FORMAT_TYPES)} 중 선택

6. 전반적인 분위기와 톤 (예: 밝고경쾌한, 진중하고무거운, 감성적이고따뜻한 등)

7. 예상 타겟 고객층 (연령대, 성별, 관심사 등)

답변 형식:
A1. [장르]
A2. [판단 이유]
A3. [특징 및 특이사항]
A4. [태그1,태그2,태그3,...]
A5. [표현형식]
A6. [분위기와 톤]
A7. [타겟 고객층]
"""
        
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    *image_payloads
                ]
            }
        ]
        
        self.logger.info("🤖 GPT-4 Vision API 호출 중...")
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=1500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    
    def _parse_response(self, response: str) -> AnalysisResult:
        """GPT-4 응답 파싱"""
        lines = response.strip().split('\n')
        parsed = {}
        
        for line in lines:
            if line.startswith('A1.'):
                parsed['genre'] = line.replace('A1.', '').strip()
            elif line.startswith('A2.'):
                parsed['reason'] = line.replace('A2.', '').strip()
            elif line.startswith('A3.'):
                parsed['features'] = line.replace('A3.', '').strip()
            elif line.startswith('A4.'):
                tags_str = line.replace('A4.', '').strip()
                parsed['tags'] = [tag.strip() for tag in tags_str.split(',')]
            elif line.startswith('A5.'):
                parsed['format_type'] = line.replace('A5.', '').strip()
            elif line.startswith('A6.'):
                parsed['mood'] = line.replace('A6.', '').strip()
            elif line.startswith('A7.'):
                parsed['target_audience'] = line.replace('A7.', '').strip()
        
        # 기본값 설정
        result = AnalysisResult(
            genre=parsed.get('genre', '미분류'),
            reason=parsed.get('reason', ''),
            features=parsed.get('features', ''),
            tags=parsed.get('tags', []),
            format_type=parsed.get('format_type', '실사'),
            mood=parsed.get('mood'),
            target_audience=parsed.get('target_audience')
        )
        
        self.logger.info(f"📊 분석 결과: {result.genre} ({result.format_type})")
        return result
    
    def _save_analysis_result(self, video: Video, result: AnalysisResult):
        """분석 결과 저장"""
        # Video 객체에 결과 저장
        video.analysis_result = {
            'genre': result.genre,
            'reason': result.reason,
            'features': result.features,
            'tags': result.tags,
            'format_type': result.format_type,
            'mood': result.mood,
            'target_audience': result.target_audience
        }
        
        # JSON 파일로도 저장
        result_path = os.path.join(video.session_dir, "analysis_result.json")
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(video.analysis_result, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"💾 분석 결과 저장: {result_path}")