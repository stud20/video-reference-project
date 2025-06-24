# src/analyzer/ai_analyzer.py
"""AI 기반 영상 장르 및 콘텐츠 분석 - 메타데이터 강화 버전"""

import os
import base64
import json
import re
from typing import List, Dict, Optional, Any
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
                
            except Exception as e:
                self.logger.error(f"❌ OpenAI 클라이언트 초기화 실패: {str(e)}")
                self.logger.error(f"❌ 오류 타입: {type(e).__name__}")
                import traceback
                self.logger.error(f"❌ 스택 트레이스:\n{traceback.format_exc()}")
                self.client = None
            
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
            
            # 썸네일 이미지 추가
            thumbnail_payload = self._prepare_thumbnail(video)
            if thumbnail_payload:
                # 썸네일을 첫 번째 이미지로 추가
                image_payloads.insert(0, thumbnail_payload)
                self.logger.info("📸 썸네일 이미지 추가됨")
            
            if not image_payloads:
                self.logger.error("준비된 이미지가 없습니다")
                return None
            
            # 컨텍스트 정보 준비 (확장된 메타데이터 포함)
            context = self._prepare_extended_context(video)
            
            # 프롬프트 생성
            prompt = self._create_enhanced_prompt(context, len(image_payloads))
            
            # 프롬프트 저장 (디버깅용)
            prompt_file = os.path.join(debug_dir, "api_prompt.txt")
            with open(prompt_file, 'w', encoding='utf-8') as f:
                f.write(f"=== API 요청 정보 ===\n")
                f.write(f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"이미지 수: {len(image_payloads)}\n")
                f.write(f"컨텍스트: {json.dumps(context, ensure_ascii=False, indent=2)}\n\n")
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
            
            # YouTube 태그와 병합
            if video.metadata and video.metadata.tags:
                youtube_tags = [tag for tag in video.metadata.tags if tag and len(tag) > 1]
                # 중복 제거하면서 병합
                merged_tags = list(set(result.tags + youtube_tags))
                result.tags = merged_tags[:20]  # 최대 20개로 제한
                self.logger.info(f"🏷️ YouTube 태그 {len(youtube_tags)}개 병합됨")
            
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
    
    def _prepare_thumbnail(self, video: Video) -> Optional[Dict]:
        """썸네일 이미지 준비"""
        if not video.metadata or not video.metadata.thumbnail:
            return None
        
        # 썸네일이 로컬 파일인지 확인
        thumbnail_path = None
        if os.path.exists(video.metadata.thumbnail):
            thumbnail_path = video.metadata.thumbnail
        else:
            # session_dir에서 썸네일 찾기
            possible_extensions = ['.jpg', '.jpeg', '.png', '.webp']
            for ext in possible_extensions:
                test_path = os.path.join(video.session_dir, f"thumbnail{ext}")
                if os.path.exists(test_path):
                    thumbnail_path = test_path
                    break
        
        if not thumbnail_path:
            self.logger.debug("썸네일 파일을 찾을 수 없음")
            return None
        
        try:
            with open(thumbnail_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            payload = {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{image_data}",
                    "detail": "low"  # 썸네일은 low 품질로
                }
            }
            
            self.logger.info(f"✅ 썸네일 이미지 준비 완료: {thumbnail_path}")
            return payload
            
        except Exception as e:
            self.logger.error(f"썸네일 로드 실패: {thumbnail_path} - {e}")
            return None
    
    def _prepare_extended_context(self, video: Video) -> Dict[str, Any]:
        """확장된 컨텍스트 정보 준비"""
        context = {
            "title": "",
            "uploader": "",
            "duration": "",
            "description": "",
            "tags": [],
            "view_count": 0
        }
        
        if video.metadata:
            context["title"] = video.metadata.title or ""
            context["uploader"] = video.metadata.uploader or ""
            
            # 영상 길이 포맷팅
            if video.metadata.duration:
                minutes = int(video.metadata.duration // 60)
                seconds = int(video.metadata.duration % 60)
                context["duration"] = f"{minutes}분 {seconds}초"
            
            context["description"] = video.metadata.description[:500] if video.metadata.description else ""  # 설명은 500자로 제한
            context["tags"] = video.metadata.tags[:10] if video.metadata.tags else []  # 상위 10개 태그만
            context["view_count"] = video.metadata.view_count or 0
        
        return context
    
    def _create_enhanced_prompt(self, context: Dict[str, Any], image_count: int) -> str:
        """강화된 API 프롬프트 생성"""
        # 메타데이터 정보 구성
        metadata_info = []
        
        if context["title"]:
            metadata_info.append(f"제목: {context['title']}")
        
        if context["uploader"]:
            metadata_info.append(f"업로더/채널: {context['uploader']}")
        
        if context["duration"]:
            metadata_info.append(f"영상 길이: {context['duration']}")
        
        if context["view_count"] > 0:
            metadata_info.append(f"조회수: {context['view_count']:,}회")
        
        if context["tags"]:
            metadata_info.append(f"YouTube 태그: {', '.join(context['tags'])}")
        
        metadata_text = "\n".join(metadata_info)
        
        # 설명 텍스트 추가
        description_text = ""
        if context["description"]:
            description_text = f"\n\n영상 설명:\n{context['description']}"
        
        prompt = f"""영상 메타데이터:
{metadata_text}{description_text}

위 영상에서 추출한 {image_count}개의 이미지를 분석해주세요. 
첫 번째 이미지는 썸네일이며, 나머지는 영상의 대표 장면들입니다.

제공된 메타데이터(제목, 설명, 태그 등)를 참고하여 더 정확한 분석을 수행하되,
실제 이미지 내용이 메타데이터와 다를 경우 이미지 내용을 우선시해주세요.

다음 7개 항목을 모두 작성해주세요. 각 항목의 답변에는 "장르 판단 이유:", "영상의 특징:" 같은 레이블을 포함하지 말고 내용만 작성하세요.

분석 항목:
A1. 영상 장르 (다음 중 하나만 선택): {', '.join(self.GENRES)}
A2. 장르 판단 이유 (시각적 특징, 연출 스타일, 정보 전달 방식, 메타데이터 등을 종합하여 200자 이상 상세히 설명)
A3. 영상의 특징 및 특이사항 (색감, 편집, 카메라워크, 분위기, 메시지 등을 200자 이상 상세히 설명)
A4. 관련 태그 10개 이상 (쉼표로 구분, # 기호 없이, YouTube 태그와 중복되지 않는 새로운 태그 위주로)
A5. 표현형식 (다음 중 하나만 선택): {', '.join(self.FORMAT_TYPES)}
A6. 전반적인 분위기와 톤
A7. 예상 타겟 고객층

중요: 각 답변은 레이블 없이 내용만 작성하세요."""
        
        return prompt
    
    def _call_gpt4_vision(self, image_payloads: List[Dict], prompt: str) -> Optional[str]:
        """GPT-4 Vision API 호출"""
        try:
            messages = [
                {
                    "role": "system",
                    "content": "당신은 광고 영상 전문 분석가입니다. 주어진 이미지들과 메타데이터를 종합적으로 분석하여 영상의 장르, 특징, 타겟 등을 상세히 분석해주세요. 메타데이터는 참고용이며, 실제 이미지 내용을 우선시하여 분석해주세요."
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
        """GPT-4 응답 파싱 - 개선된 버전"""
        if not response or len(response) < 100:
            self.logger.error(f"응답이 너무 짧거나 비어있음: {len(response) if response else 0}자")
            return None
        
        self.logger.info("📝 응답 파싱 시작...")
        
        # 응답을 줄 단위로 분리
        lines = response.strip().split('\n')
        
        # 빈 줄 제거
        lines = [line.strip() for line in lines if line.strip()]
        
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
        
        # 텍스트를 섹션으로 분리 (두 줄 이상의 빈 줄로 구분)
        sections = response.strip().split('\n\n')
        
        # 섹션이 7개가 아니면 다른 방식으로 파싱 시도
        if len(sections) < 7:
            # 각 줄을 하나씩 확인하면서 파싱
            self.logger.info(f"섹션 수: {len(sections)}, 대체 파싱 방식 사용")
            
            # 첫 번째 줄은 장르
            if lines:
                parsed['genre'] = lines[0].strip()
                self.logger.debug(f"장르: {parsed['genre']}")
            
            # 나머지 내용을 하나의 텍스트로 합쳐서 파싱
            remaining_text = '\n'.join(lines[1:])
            
            # 각 섹션을 구분할 수 있는 키워드나 패턴 찾기
            # 긴 텍스트는 reason과 features일 가능성이 높음
            paragraphs = [p.strip() for p in remaining_text.split('\n\n') if p.strip()]
            
            if len(paragraphs) >= 6:
                parsed['reason'] = paragraphs[0]
                parsed['features'] = paragraphs[1]
                
                # 태그 찾기 (쉼표로 구분된 리스트)
                for p in paragraphs[2:]:
                    if ',' in p and len(p.split(',')) > 5:
                        parsed['tags'] = [tag.strip() for tag in p.split(',')]
                        break
                
                # 표현형식 찾기 (FORMAT_TYPES 중 하나)
                for p in paragraphs:
                    for fmt in self.FORMAT_TYPES:
                        if fmt in p and len(p) < 20:  # 짧은 텍스트
                            parsed['format_type'] = fmt
                            break
                
                # 나머지 짧은 문장들은 mood와 target_audience
                short_paragraphs = [p for p in paragraphs if len(p) < 200 and p not in [parsed['reason'], parsed['features']]]
                if len(short_paragraphs) >= 2:
                    parsed['mood'] = short_paragraphs[-2]
                    parsed['target_audience'] = short_paragraphs[-1]
        
        else:
            # 섹션이 7개 이상이면 순서대로 할당
            parsed['genre'] = sections[0].strip()
            parsed['reason'] = sections[1].strip()
            parsed['features'] = sections[2].strip()
            
            # 태그 처리
            tags_text = sections[3].strip()
            parsed['tags'] = [tag.strip() for tag in tags_text.split(',')]
            
            parsed['format_type'] = sections[4].strip()
            parsed['mood'] = sections[5].strip()
            parsed['target_audience'] = sections[6].strip()
        
        # 파싱 결과 검증 및 정리
        if not parsed['genre']:
            self.logger.error("장르가 파싱되지 않음")
            return None
        
        # 장르가 유효한지 확인
        if parsed['genre'] not in self.GENRES:
            self.logger.warning(f"파싱된 장르가 목록에 없음: {parsed['genre']}")
            # 가장 유사한 장르 찾기 (옵션)
        
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
        # Video 객체에 결과 저장 (DB 스키마에 맞게 키 이름 변경)
        video.analysis_result = {
            'genre': result.genre,
            'reasoning': result.reason,  # reason -> reasoning
            'features': result.features,
            'tags': result.tags,
            'expression_style': result.format_type,  # format_type -> expression_style
            'mood_tone': result.mood,  # mood -> mood_tone
            'target_audience': result.target_audience,
            'model_used': os.getenv("OPENAI_MODEL", "gpt-4o"),
            'analysis_date': datetime.now().isoformat()
        }
        
        # JSON 파일로 저장
        result_path = os.path.join(video.session_dir, "analysis_result.json")
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(video.analysis_result, f, ensure_ascii=False, indent=2)
        
        # 텍스트 파일로도 저장 (사람이 읽기 쉬운 형식)
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