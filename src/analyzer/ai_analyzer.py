# src/analyzer/ai_analyzer.py
"""AI 기반 영상 장르 및 콘텐츠 분석 - FactChat 전용 버전"""

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
    """영상 분석을 위한 AI 엔진 - FactChat 전용"""
    
    # 기본 장르 목록
    DEFAULT_GENRES = [
        "2D애니메이션", "3D애니메이션", "모션그래픽", "인터뷰", 
        "스팟광고", "VLOG", "유튜브콘텐츠", "다큐멘터리", 
        "브랜드필름", "TVC", "뮤직비디오", "교육콘텐츠",
        "제품소개", "이벤트영상", "웹드라마", "바이럴영상"
    ]
    
    # 기본 표현 형식
    DEFAULT_FORMAT_TYPES = ["2D", "3D", "실사", "혼합형", "스톱모션", "타이포그래피"]
        
    def __init__(self, api_key: Optional[str] = None):
        self.logger = get_logger(__name__)
        
        # FactChat 설정만 사용
        self.provider = "factchat"
        self.api_key = api_key or "NPpDGrF4ShhrecUsBJm1dIIW7DZab4qC"  # 직접 하드코딩
        self.base_url = "https://factchat-cloud.mindlogic.ai/v1/api/openai"
        self.model_default = "gpt-4o"
        
        # 토큰 절약을 위한 설정
        self.max_images = int(os.getenv("MAX_ANALYSIS_IMAGES", "10"))
        self.image_quality = os.getenv("ANALYSIS_IMAGE_QUALITY", "low")
        
        # 프롬프트 설정 로드
        self._load_prompt_settings()
        
        # FactChat 클라이언트 초기화
        self.client = None
        
        self.logger.info("🎯 FactChat 전용 모드")
        self.logger.info(f"🔑 API 키: {self.api_key[:8]}...{self.api_key[-4:]}")
        self.logger.info(f"🔗 Base URL: {self.base_url}")
        self.logger.info(f"🤖 모델: {self.model_default}")
        
        try:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            self.logger.info("✅ FactChat 클라이언트 초기화 성공")
            
        except Exception as e:
            self.logger.error(f"❌ FactChat 클라이언트 초기화 실패: {str(e)}")
            import traceback
            self.logger.error(f"❌ 스택 트레이스:\n{traceback.format_exc()}")
            self.client = None

    def _load_prompt_settings(self):
        """프롬프트 설정 로드"""
        settings_file = "config/prompt_settings.json"
        
        # 기본값 설정
        self.system_prompt = "당신은 광고 영상 전문 분석가입니다. 주어진 이미지들과 메타데이터를 종합적으로 분석하여 영상의 장르, 특징, 타겟 등을 상세히 분석해주세요. 메타데이터는 참고용이며, 실제 이미지 내용을 우선시하여 분석해주세요."
        self.analysis_instruction = """제공된 메타데이터(제목, 설명, 태그 등)를 참고하여 더 정확한 분석을 수행하되,
실제 이미지 내용이 메타데이터와 다를 경우 이미지 내용을 우선시해주세요."""
        
        self.GENRES = self.DEFAULT_GENRES.copy()
        self.FORMAT_TYPES = self.DEFAULT_FORMAT_TYPES.copy()
        self.analysis_items = None
        self.require_labels = True
        self.strict_format = True
        
        # 설정 파일이 있으면 로드
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                # 설정 적용
                self.system_prompt = settings.get('system_prompt', self.system_prompt)
                self.analysis_instruction = settings.get('analysis_instruction', self.analysis_instruction)
                self.GENRES = settings.get('genres', self.DEFAULT_GENRES)
                self.FORMAT_TYPES = settings.get('format_types', self.DEFAULT_FORMAT_TYPES)
                self.analysis_items = settings.get('analysis_items', None)
                self.require_labels = settings.get('require_labels', True)
                self.strict_format = settings.get('strict_format', True)
                
                self.logger.info("✅ 프롬프트 설정 로드 완료")
                
            except Exception as e:
                self.logger.error(f"프롬프트 설정 로드 실패: {str(e)}")
                self.logger.info("기본 설정을 사용합니다")
    
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
        
        # 분석 항목이 설정되어 있으면 사용, 아니면 기본값
        if self.analysis_items:
            # 설정된 분석 항목 사용
            analysis_items_text = []
            for item in self.analysis_items:
                item_text = f"{item['label']}. {item['title']}"
                
                # A1 (장르)와 A5 (표현형식)는 선택 목록 추가
                if item['label'] == 'A1':
                    item_text += f" (다음 중 하나만 선택): {', '.join(self.GENRES)}"
                elif item['label'] == 'A5':
                    item_text += f" (다음 중 하나만 선택): {', '.join(self.FORMAT_TYPES)}"
                
                # 설명/지침 추가
                if item['instruction']:
                    item_text += f" ({item['instruction']})"
                
                analysis_items_text.append(item_text)
            
            num_items = len(analysis_items_text)
            items_text = '\n'.join(analysis_items_text)
        else:
            # 기본 분석 항목
            num_items = 7
            items_text = f"""A1. 영상 장르 (다음 중 하나만 선택): {', '.join(self.GENRES)}
A2. 장르 판단 이유 (시각적 특징, 연출 스타일, 정보 전달 방식, 메타데이터 등을 종합하여 200자 이상 상세히 설명)
A3. 영상의 특징 및 특이사항 (색감, 편집, 카메라워크, 분위기, 메시지 등을 200자 이상 상세히 설명)
A4. 관련 태그 10개 이상 (쉼표로 구분, # 기호 없이, YouTube 태그와 중복되지 않는 새로운 태그 위주로)
A5. 표현형식 (다음 중 하나만 선택): {', '.join(self.FORMAT_TYPES)}
A6. 전반적인 분위기와 톤
A7. 예상 타겟 고객층"""
        
        # 추가 지침 구성
        additional_instructions = []
        if self.require_labels:
            additional_instructions.append('각 항목의 답변에는 "장르 판단 이유:", "영상의 특징:" 같은 레이블을 포함하지 말고 내용만 작성하세요.')
        if self.strict_format:
            additional_instructions.append("각 항목은 빈 줄로 구분하여 명확히 구분해주세요.")
        
        instructions_text = ' ' + ' '.join(additional_instructions) if additional_instructions else ''
        
        # 전체 프롬프트 조합
        prompt = f"""영상 메타데이터:
{metadata_text}{description_text}

위 영상에서 추출한 {image_count}개의 이미지를 분석해주세요. 
첫 번째 이미지는 썸네일이며, 나머지는 영상의 대표 장면들입니다.

{self.analysis_instruction}

다음 {num_items}개 항목을 모두 작성해주세요.{instructions_text}

분석 항목:
{items_text}"""
        
        return prompt
    
    def _call_gpt4_vision(self, image_payloads: List[Dict], prompt: str) -> Optional[str]:
        """GPT-4 Vision API 호출 (호환성 메서드)"""
        return self._call_factchat_api(image_payloads, prompt)
        
    def _call_ai_vision(self, image_payloads: List[Dict], prompt: str) -> Optional[str]:
        """AI Vision API 호출 - FactChat 전용"""
        return self._call_factchat_api(image_payloads, prompt)

    def _call_factchat_api(self, image_payloads: List[Dict], prompt: str) -> Optional[str]:
        """FactChat API 호출"""
        try:
            messages = [
                {
                    "role": "system",
                    "content": self.system_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        *image_payloads
                    ]
                }
            ]
            
            self.logger.info("🤖 FactChat API 호출 중...")
            self.logger.info(f"📋 사용 모델: {self.model_default}")
            self.logger.info(f"🔗 API URL: {self.base_url}/chat/completions")
            self.logger.info(f"🔑 API 키: {self.api_key[:8]}...{self.api_key[-4:]}")
            self.logger.info(f"📸 이미지 개수: {len(image_payloads)}")
            
            response = self.client.chat.completions.create(
                model=self.model_default,
                messages=messages,
                max_tokens=2000,
                temperature=0.7
            )
            
            # 토큰 사용량 로깅
            if hasattr(response, 'usage'):
                self.logger.info(f"📊 토큰 사용량 - 입력: {response.usage.prompt_tokens}, 출력: {response.usage.completion_tokens}")
            
            content = response.choices[0].message.content
            self.logger.info(f"📝 API 응답 성공! 길이: {len(content)}자")
            
            return content
            
        except Exception as e:
            self.logger.error(f"❌ FactChat API 호출 실패: {e}")
            
            # 구체적인 오류 분석
            error_str = str(e)
            if "401" in error_str or "Invalid API Key" in error_str:
                self.logger.error("🔑 API 키 문제:")
                self.logger.error(f"   - 현재 키: {self.api_key}")
                self.logger.error("   - FactChat 대시보드에서 키 확인 필요")
            elif "404" in error_str:
                self.logger.error("🔗 URL 문제:")
                self.logger.error(f"   - 사용된 URL: {self.base_url}")
            elif "model" in error_str.lower():
                self.logger.error("🤖 모델 문제:")
                self.logger.error(f"   - 요청한 모델: {self.model_default}")
            
            return None

    def analyze_video(self, video: Video) -> Optional[AnalysisResult]:
        """비디오 분석 수행"""
        if not self.client:
            self.logger.error("FactChat 클라이언트가 초기화되지 않았습니다")
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
                image_payloads.insert(0, thumbnail_payload)
                self.logger.info("📸 썸네일 이미지 추가됨")
            
            if not image_payloads:
                self.logger.error("준비된 이미지가 없습니다")
                return None
            
            # 컨텍스트 정보 준비
            context = self._prepare_extended_context(video)
            
            # 프롬프트 생성
            prompt = self._create_enhanced_prompt(context, len(image_payloads))
            
            # 프롬프트 저장 (디버깅용)
            prompt_file = os.path.join(debug_dir, "factchat_prompt.txt")
            with open(prompt_file, 'w', encoding='utf-8') as f:
                f.write(f"=== FactChat API 요청 정보 ===\n")
                f.write(f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"이미지 수: {len(image_payloads)}\n")
                f.write(f"API 키: {self.api_key}\n")
                f.write(f"Base URL: {self.base_url}\n")
                f.write(f"모델: {self.model_default}\n")
                f.write(f"컨텍스트: {json.dumps(context, ensure_ascii=False, indent=2)}\n\n")
                f.write(f"=== 프롬프트 ===\n")
                f.write(prompt)
            
            self.logger.info(f"💾 프롬프트 저장: {prompt_file}")
            
            # FactChat API 호출
            response = self._call_factchat_api(image_payloads, prompt)
            
            if not response:
                self.logger.error("API 응답이 없습니다")
                return None
            
            # API 응답 저장 (디버깅용)
            response_file = os.path.join(debug_dir, "factchat_response.txt")
            with open(response_file, 'w', encoding='utf-8') as f:
                f.write(f"=== FactChat API 응답 ===\n")
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
                merged_tags = list(set(result.tags + youtube_tags))
                result.tags = merged_tags[:20]
                self.logger.info(f"🏷️ YouTube 태그 {len(youtube_tags)}개 병합됨")
            
            # 결과 저장
            self._save_analysis_result(video, result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"영상 분석 중 오류 발생: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None

    # 나머지 메서드들 (_prepare_images, _prepare_thumbnail, _prepare_extended_context, _parse_response, _save_analysis_result)은 
    # 기존 코드와 동일하므로 생략...
    
    def _prepare_images(self, scenes: List[Scene]) -> List[Dict]:
        """분석을 위한 이미지 준비"""
        image_payloads = []
        
        # 최대 이미지 수만큼 선택
        selected_scenes = scenes[:self.max_images] if len(scenes) > self.max_images else scenes
        
        self.logger.info(f"🖼️ 이미지 준비 시작: {len(selected_scenes)}개")
        
        for i, scene in enumerate(selected_scenes):
            # 그룹화된 경로가 있으면 우선 사용
            image_path = None
            if hasattr(scene, 'grouped_path') and scene.grouped_path and os.path.exists(scene.grouped_path):
                image_path = scene.grouped_path
            elif os.path.exists(scene.frame_path):
                image_path = scene.frame_path
            else:
                self.logger.warning(f"이미지 파일 없음: {scene.frame_path}")
                continue
            
            try:
                # 이미지 읽기
                with open(image_path, "rb") as f:
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
                self.logger.error(f"이미지 로드 실패: {image_path} - {e}")
        
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
            
            context["description"] = video.metadata.description[:500] if video.metadata.description else ""
            context["tags"] = video.metadata.tags[:10] if video.metadata.tags else []
            context["view_count"] = video.metadata.view_count or 0
        
        return context

    def _parse_response(self, response: str) -> Optional[AnalysisResult]:
        """응답 파싱 - 간단화된 버전"""
        if not response or len(response) < 100:
            self.logger.error(f"응답이 너무 짧거나 비어있음: {len(response) if response else 0}자")
            return None
        
        self.logger.info("📝 응답 파싱 시작...")
        
        # 기본값으로 초기화
        parsed_data = {
            'genre': 'Unknown',
            'reason': '분석 내용 없음',
            'features': '분석 내용 없음',
            'tags': [],
            'format_type': '실사',
            'mood': '',
            'target_audience': ''
        }
        
        # 간단한 파싱 로직 (섹션별로 분리)
        sections = []
        current_section = []
        
        for line in response.strip().split('\n'):
            if line.strip():
                current_section.append(line)
            else:
                if current_section:
                    sections.append('\n'.join(current_section))
                    current_section = []
        
        if current_section:
            sections.append('\n'.join(current_section))
        
        self.logger.info(f"파싱된 섹션 수: {len(sections)}")
        
        # 각 섹션을 순서대로 매핑
        if len(sections) >= 1:
            parsed_data['genre'] = self._clean_text(sections[0])
        if len(sections) >= 2:
            parsed_data['reason'] = self._clean_text(sections[1])
        if len(sections) >= 3:
            parsed_data['features'] = self._clean_text(sections[2])
        if len(sections) >= 4:
            tags_text = self._clean_text(sections[3])
            parsed_data['tags'] = [tag.strip() for tag in tags_text.replace('#', '').split(',') if tag.strip()]
        if len(sections) >= 5:
            parsed_data['format_type'] = self._clean_text(sections[4])
        if len(sections) >= 6:
            parsed_data['mood'] = self._clean_text(sections[5])
        if len(sections) >= 7:
            parsed_data['target_audience'] = self._clean_text(sections[6])
        
        result = AnalysisResult(
            genre=parsed_data['genre'],
            reason=parsed_data['reason'],
            features=parsed_data['features'],
            tags=parsed_data['tags'],
            format_type=parsed_data['format_type'],
            mood=parsed_data['mood'],
            target_audience=parsed_data['target_audience']
        )
        
        self.logger.info(f"✅ 파싱 완료 - 장르: {result.genre}, 태그 수: {len(result.tags)}")
        return result
    
    def _clean_text(self, text: str) -> str:
        """텍스트 정리"""
        # A1., A2. 등 레이블 제거
        text = re.sub(r'^A\d+\.\s*', '', text.strip())
        # 첫 줄만 사용 (장르의 경우)
        first_line = text.split('\n')[0].strip()
        return first_line if len(first_line) < 50 else text.strip()

    def _save_analysis_result(self, video: Video, result: AnalysisResult):
        """분석 결과 저장"""
        # Video 객체에 결과 저장
        video.analysis_result = {
            'genre': result.genre,
            'reasoning': result.reason,
            'features': result.features,
            'tags': result.tags,
            'expression_style': result.format_type,
            'mood_tone': result.mood or '',
            'target_audience': result.target_audience or '',
            'model_used': f"factchat:{self.model_default}",
            'analysis_date': datetime.now().isoformat()
        }
        
        # JSON 파일로 저장
        result_path = os.path.join(video.session_dir, "analysis_result.json")
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(video.analysis_result, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"💾 분석 결과 저장: {result_path}")