# src/analyzer/ai_analyzer.py
"""AI 기반 영상 장르 및 콘텐츠 분석"""

import os
import base64
import json
import re
from typing import List, Dict, Optional
from pathlib import Path
from openai import OpenAI
from dataclasses import dataclass
from datetime import datetime
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
        
        # 토큰 절약을 위한 설정
        self.max_images = int(os.getenv("MAX_ANALYSIS_IMAGES", "10"))
        self.image_quality = os.getenv("ANALYSIS_IMAGE_QUALITY", "low")
        
        # OpenAI 클라이언트 안전한 초기화
        self.client = None
        
        if not self.api_key:
            self.logger.warning("OpenAI API 키가 설정되지 않았습니다")
        else:
            try:
                self.client = OpenAI(api_key=self.api_key)
                self.logger.info("✅ OpenAI 클라이언트 초기화 성공")
                
                # 간단한 연결 테스트 (옵션)
                # self._test_connection()
                
            except Exception as e:
                self.logger.error(f"❌ OpenAI 클라이언트 초기화 실패: {str(e)}")
                self.logger.error(f"❌ 오류 타입: {type(e).__name__}")
                import traceback
                self.logger.error(f"❌ 스택 트레이스:\n{traceback.format_exc()}")
                self.client = None

    def _test_connection(self):
        """OpenAI API 연결 테스트 (옵션)"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            self.logger.info("✅ OpenAI API 연결 테스트 성공")
        except Exception as e:
            self.logger.warning(f"⚠️ OpenAI API 연결 테스트 실패: {e}")
            # 테스트 실패해도 클라이언트는 유지
            
    def analyze_video(self, video: Video) -> Optional[AnalysisResult]:
        """비디오 분석 수행"""
        if not self.client:
            self.logger.error("OpenAI 클라이언트가 초기화되지 않았습니다")
            return None
        
        if not video.scenes:
            self.logger.warning("분석할 씬 이미지가 없습니다")
            return None
        
        try:
            # 디버깅용 디렉토리 생성
            debug_dir = os.path.join(video.session_dir, "debug")
            os.makedirs(debug_dir, exist_ok=True)
            
            # 이미지 준비
            image_payloads = self._prepare_images(video.scenes)
            
            if not image_payloads:
                self.logger.error("준비된 이미지가 없습니다")
                return None
            
            # 컨텍스트 정보 준비
            context = self._prepare_context(video)
            
            # 프롬프트 생성
            prompt = self._create_prompt(context, len(image_payloads))
            
            # 프롬프트 저장 (디버깅용)
            prompt_file = os.path.join(debug_dir, "api_prompt.txt")
            with open(prompt_file, 'w', encoding='utf-8') as f:
                f.write(f"=== API 요청 정보 ===\n")
                f.write(f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"이미지 수: {len(image_payloads)}\n")
                f.write(f"컨텍스트: {context}\n\n")
                f.write(f"=== 프롬프트 ===\n")
                f.write(prompt)
                f.write(f"\n\n=== 이미지 정보 ===\n")
                for i, img in enumerate(image_payloads):
                    f.write(f"이미지 {i+1}: 품질={self.image_quality}\n")
            
            self.logger.info(f"💾 프롬프트 저장: {prompt_file}")
            
            # GPT-4 Vision API 호출
            response = self._call_gpt4_vision(image_payloads, prompt)
            
            if not response:
                self.logger.error("API 응답이 없습니다")
                return None
            
            # API 응답 저장 (디버깅용)
            response_file = os.path.join(debug_dir, "api_response.txt")
            with open(response_file, 'w', encoding='utf-8') as f:
                f.write(f"=== API 응답 ===\n")
                f.write(f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"응답 길이: {len(response)}자\n\n")
                f.write(f"=== 원본 응답 ===\n")
                f.write(response)
            
            self.logger.info(f"💾 API 응답 저장: {response_file}")
            
            # 응답 파싱
            result = self._parse_response(response)
            
            if not result:
                self.logger.error("파싱 실패")
                return None
            
            # 파싱 결과 저장 (디버깅용)
            parsing_file = os.path.join(debug_dir, "parsing_result.txt")
            with open(parsing_file, 'w', encoding='utf-8') as f:
                f.write(f"=== 파싱 결과 ===\n")
                f.write(f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"장르: {result.genre}\n")
                f.write(f"판단 이유 ({len(result.reason)}자): {result.reason}\n")
                f.write(f"특징 ({len(result.features)}자): {result.features}\n")
                f.write(f"태그 ({len(result.tags)}개): {', '.join(result.tags)}\n")
                f.write(f"표현형식: {result.format_type}\n")
                f.write(f"분위기: {result.mood}\n")
                f.write(f"타겟: {result.target_audience}\n")
            
            self.logger.info(f"💾 파싱 결과 저장: {parsing_file}")
            
            # 결과 저장
            self._save_analysis_result(video, result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"영상 분석 중 오류 발생: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
    
    def _prepare_images(self, scenes: List[Scene]) -> List[Dict]:
        """분석을 위한 이미지 준비"""
        image_payloads = []
        
        # 최대 이미지 수만큼 선택
        selected_scenes = scenes[:self.max_images] if len(scenes) > self.max_images else scenes
        
        self.logger.info(f"🖼️ 이미지 준비 시작: {len(selected_scenes)}개")
        
        for i, scene in enumerate(selected_scenes):
            if not os.path.exists(scene.frame_path):
                self.logger.warning(f"이미지 파일 없음: {scene.frame_path}")
                continue
            
            try:
                # 이미지 읽기
                with open(scene.frame_path, "rb") as f:
                    image_data = base64.b64encode(f.read()).decode('utf-8')
                
                # 페이로드 생성
                payload = {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_data}"
                    }
                }
                
                # detail 파라미터는 low/high만 가능
                if self.image_quality in ["low", "high"]:
                    payload["image_url"]["detail"] = self.image_quality
                
                image_payloads.append(payload)
                self.logger.debug(f"✅ 이미지 {i+1} 준비 완료")
                
            except Exception as e:
                self.logger.error(f"이미지 로드 실패: {scene.frame_path} - {e}")
        
        self.logger.info(f"📸 {len(image_payloads)}개 이미지 준비 완료")
        return image_payloads
    
    def _prepare_context(self, video: Video) -> str:
        """분석을 위한 컨텍스트 정보 준비"""
        context_parts = []
        
        if video.metadata:
            if video.metadata.title:
                context_parts.append(f"제목: {video.metadata.title}")
            
            if video.metadata.duration:
                minutes = video.metadata.duration // 60
                seconds = video.metadata.duration % 60
                context_parts.append(f"길이: {minutes}분 {seconds}초")
        
        return " / ".join(context_parts) if context_parts else "정보 없음"
    
    def _create_prompt(self, context: str, image_count: int) -> str:
        """API 프롬프트 생성"""
        prompt = f"""영상 정보: {context}

위 영상에서 추출한 {image_count}개의 대표 장면을 분석해주세요.

다음 7개 항목을 모두 작성해주세요. A2와 A3는 반드시 200자 이상 상세히 작성하세요.

분석 항목:
A1. 영상 장르 (다음 중 하나만 선택): {', '.join(self.GENRES)}
A2. 장르 판단 이유 (시각적 특징, 연출 스타일, 정보 전달 방식 등을 200자 이상 상세히 설명)
A3. 영상의 특징 및 특이사항 (색감, 편집, 카메라워크, 분위기 등을 200자 이상 상세히 설명)
A4. 관련 태그 10개 이상 (쉼표로 구분)
A5. 표현형식 (다음 중 하나만 선택): {', '.join(self.FORMAT_TYPES)}
A6. 전반적인 분위기와 톤
A7. 예상 타겟 고객층

위 형식을 정확히 지켜서 답변해주세요."""
        
        return prompt
    
    def _call_gpt4_vision(self, image_payloads: List[Dict], prompt: str) -> Optional[str]:
        """GPT-4 Vision API 호출"""
        try:
            messages = [
                {
                    "role": "system",
                    "content": "당신은 광고 영상 전문 분석가입니다. 주어진 이미지들을 보고 영상의 장르, 특징, 타겟 등을 상세히 분석해주세요."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        *image_payloads
                    ]
                }
            ]
            
            self.logger.info("🤖 GPT-4 Vision API 호출 중...")
            
            # 모델 선택
            model = os.getenv("OPENAI_MODEL", "gpt-4o")
            self.logger.info(f"사용 모델: {model}")
            
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=2000,
                temperature=0.7
            )
            
            # 토큰 사용량 로깅
            if hasattr(response, 'usage'):
                self.logger.info(f"📊 토큰 사용량 - 입력: {response.usage.prompt_tokens}, 출력: {response.usage.completion_tokens}")
            
            content = response.choices[0].message.content
            self.logger.info(f"📝 API 응답 길이: {len(content)}자")
            
            return content
            
        except Exception as e:
            self.logger.error(f"API 호출 실패: {e}")
            return None
    
    def _parse_response(self, response: str) -> Optional[AnalysisResult]:
        """GPT-4 응답 파싱"""
        if not response or len(response) < 100:
            self.logger.error(f"응답이 너무 짧거나 비어있음: {len(response) if response else 0}자")
            return None
        
        self.logger.info("📝 응답 파싱 시작...")
        
        # 파싱 결과 초기화
        parsed = {
            'genre': '',
            'reason': '',
            'features': '',
            'tags': [],
            'format_type': '',
            'mood': '',
            'target_audience': ''
        }
        
        # 정규표현식으로 파싱
        patterns = {
            'genre': r'A1[\.:\s]*([^\n]+)',
            'reason': r'A2[\.:\s]*([\s\S]+?)(?=A3[\.:\s]|$)',
            'features': r'A3[\.:\s]*([\s\S]+?)(?=A4[\.:\s]|$)',
            'tags': r'A4[\.:\s]*([\s\S]+?)(?=A5[\.:\s]|$)',
            'format_type': r'A5[\.:\s]*([^\n]+)',
            'mood': r'A6[\.:\s]*([\s\S]+?)(?=A7[\.:\s]|$)',
            'target_audience': r'A7[\.:\s]*([\s\S]+?)$'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, response, re.MULTILINE | re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                
                # 대괄호 제거
                value = value.strip('[]')
                
                if key == 'tags':
                    # 태그는 쉼표로 분리
                    parsed[key] = [tag.strip() for tag in value.split(',') if tag.strip()]
                else:
                    parsed[key] = value
                
                self.logger.debug(f"파싱 - {key}: {value[:50]}...")
        
        # 파싱 결과 검증
        if not parsed['genre']:
            self.logger.error("장르가 파싱되지 않음")
            return None
        
        # 결과 생성
        result = AnalysisResult(
            genre=parsed['genre'],
            reason=parsed['reason'] or '분석 내용 없음',
            features=parsed['features'] or '분석 내용 없음',
            tags=parsed['tags'] or [],
            format_type=parsed['format_type'] or '실사',
            mood=parsed['mood'],
            target_audience=parsed['target_audience']
        )
        
        self.logger.info(f"✅ 파싱 완료 - 장르: {result.genre}, 태그 수: {len(result.tags)}")
        
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
        
        # JSON 파일로 저장
        result_path = os.path.join(video.session_dir, "analysis_result.json")
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(video.analysis_result, f, ensure_ascii=False, indent=2)
        
        # 텍스트 파일로도 저장
        result_text_path = os.path.join(video.session_dir, "analysis_result.txt")
        with open(result_text_path, 'w', encoding='utf-8') as f:
            f.write(f"=== AI 영상 분석 결과 ===\n\n")
            f.write(f"[장르]: {result.genre}\n\n")
            f.write(f"[판단 이유]:\n{result.reason}\n\n")
            f.write(f"[특징 및 특이사항]:\n{result.features}\n\n")
            f.write(f"[태그]: {', '.join(result.tags)}\n\n")
            f.write(f"[표현형식]: {result.format_type}\n\n")
            f.write(f"[분위기와 톤]: {result.mood}\n\n")
            f.write(f"[타겟 고객층]: {result.target_audience}\n")
        
        self.logger.info(f"💾 분석 결과 저장: {result_path}")