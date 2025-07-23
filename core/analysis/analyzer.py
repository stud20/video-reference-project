# core/analysis/analyzer.py
"""리팩토링된 AI 기반 영상 분석기"""

import os
import base64
from typing import List, Dict, Optional, Any
from pathlib import Path
from datetime import datetime

from utils.logger import get_logger
from core.video.models import Video, Scene

from .providers import AIProvider, OpenAIProvider, ImagePayload
from .prompts import PromptBuilder
from .parser import ResponseParser, ParsedAnalysis


class VideoAnalyzer:
    """영상 분석 AI 엔진"""
    
    def __init__(self, provider: Optional[AIProvider] = None):
        """
        Args:
            provider: AI Provider 인스턴스. None이면 기본 FactChat 사용
        """
        self.logger = get_logger(__name__)
        
        # Provider 설정
        self.provider = provider or OpenAIProvider()
        self.logger.info(f"🤖 AI Analyzer 초기화 - Provider: {self.provider.get_name()}")
        
        # 컴포넌트 초기화
        self.prompt_builder = PromptBuilder()
        self.response_parser = ResponseParser()
        
        # 분석 설정
        self.max_images = int(os.getenv("MAX_ANALYSIS_IMAGES", "10"))
        self.image_quality = os.getenv("ANALYSIS_IMAGE_QUALITY", "low")
        
        self.logger.info(f"📸 최대 이미지 수: {self.max_images}")
        self.logger.info(f"🎨 이미지 품질: {self.image_quality}")
    
    def analyze_video(self, video: Video) -> Optional[Dict[str, Any]]:
        """비디오 분석 수행
        
        Args:
            video: 분석할 Video 객체
            
        Returns:
            분석 결과 딕셔너리 또는 None
        """
        if not video.scenes:
            self.logger.warning("분석할 씬 이미지가 없습니다")
            return None
        
        try:
            # 디버깅 디렉토리 준비
            debug_dir = self._prepare_debug_directory(video)
            
            # 1. 이미지 준비
            image_payloads = self._prepare_image_payloads(video)
            if not image_payloads:
                self.logger.error("준비된 이미지가 없습니다")
                return None
            
            # 2. 컨텍스트 준비
            context = self._prepare_context(video)
            
            # 3. 프롬프트 생성
            prompt = self.prompt_builder.build_analysis_prompt(
                context=context,
                image_count=len(image_payloads)
            )
            
            # custom_prompt가 있으면 추가
            if hasattr(self, 'custom_prompt') and self.custom_prompt:
                prompt += f"\n\n추가 분석 요청사항:\n{self.custom_prompt}"
            
            # 전체 프롬프트 저장 (시스템 프롬프트 + 사용자 프롬프트)
            self.last_full_prompt = f"시스템 프롬프트:\n{self.prompt_builder.system_prompt}\n\n사용자 프롬프트:\n{prompt}"
            
            # 디버깅: 프롬프트 저장
            self._save_debug_info(debug_dir, "prompt.txt", prompt, {
                "provider": self.provider.get_name(),
                "image_count": len(image_payloads),
                "context": context
            })
            
            # 4. API 호출
            self.logger.info(f"🚀 {self.provider.get_name()} API 호출 시작...")
            response = self.provider.call_api(
                images=image_payloads,
                prompt=prompt,
                system_prompt=self.prompt_builder.system_prompt
            )
            
            if not response:
                # Azure OpenAI 콘텐츠 필터 문제일 가능성 확인
                if "OpenAI" in self.provider.get_name():
                    self.logger.error("❌ Azure OpenAI 콘텐츠 필터로 인해 분석이 차단되었을 가능성이 있습니다")
                    self.logger.error("💡 해결 방안: Claude Sonnet 4 또는 Gemini 모델을 선택해보세요")
                self.logger.error("API 응답이 없습니다")
                return None
            
            # 디버깅: 응답 저장
            self._save_debug_info(debug_dir, "response.txt", response)
            
            # 5. 응답 파싱
            parsed = self.response_parser.parse(response)
            if not parsed:
                self.logger.error("응답 파싱 실패")
                return None
            
            # 6. 결과 후처리
            result = self._postprocess_result(parsed, video)
            
            # 7. 결과 저장
            self._save_analysis_result(video, result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"영상 분석 중 오류 발생: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
    
    def _prepare_image_payloads(self, video: Video) -> List[ImagePayload]:
        """이미지 페이로드 준비"""
        payloads = []
        
        # 썸네일 추가
        thumbnail_payload = self._prepare_thumbnail_payload(video)
        if thumbnail_payload:
            payloads.append(thumbnail_payload)
            self.logger.info("📸 썸네일 이미지 추가됨")
        
        # 씬 이미지 추가
        scene_payloads = self._prepare_scene_payloads(video.scenes)
        payloads.extend(scene_payloads)
        
        self.logger.info(f"📸 총 {len(payloads)}개 이미지 준비 완료")
        return payloads
    
    def _prepare_thumbnail_payload(self, video: Video) -> Optional[ImagePayload]:
        """썸네일 이미지 페이로드 준비"""
        if not video.metadata or not video.metadata.thumbnail:
            return None
        
        # 썸네일 파일 찾기
        thumbnail_path = self._find_thumbnail_file(video)
        if not thumbnail_path:
            return None
        
        try:
            with open(thumbnail_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            return ImagePayload(data=image_data, detail="low")
            
        except Exception as e:
            self.logger.error(f"썸네일 로드 실패: {thumbnail_path} - {e}")
            return None
    
    def _find_thumbnail_file(self, video: Video) -> Optional[str]:
        """썸네일 파일 경로 찾기"""
        # 메타데이터의 썸네일이 로컬 파일인지 확인
        if video.metadata.thumbnail and os.path.exists(video.metadata.thumbnail):
            return video.metadata.thumbnail
        
        # session_dir에서 썸네일 찾기
        if hasattr(video, 'session_dir'):
            for ext in ['.jpg', '.jpeg', '.png', '.webp']:
                test_path = os.path.join(video.session_dir, f"thumbnail{ext}")
                if os.path.exists(test_path):
                    return test_path
        
        return None
    
    def _prepare_scene_payloads(self, scenes: List[Scene]) -> List[ImagePayload]:
        """씬 이미지 페이로드 준비"""
        payloads = []
        
        # 최대 이미지 수만큼 선택
        selected_scenes = scenes[:self.max_images] if len(scenes) > self.max_images else scenes
        
        for i, scene in enumerate(selected_scenes):
            # 이미지 경로 찾기
            image_path = self._get_scene_image_path(scene)
            if not image_path:
                continue
            
            try:
                with open(image_path, "rb") as f:
                    image_data = base64.b64encode(f.read()).decode('utf-8')
                
                detail = self.image_quality if self.image_quality in ["low", "high"] else "auto"
                payloads.append(ImagePayload(data=image_data, detail=detail))
                
                self.logger.debug(f"✅ 씬 이미지 {i+1} 준비 완료")
                
            except Exception as e:
                self.logger.error(f"씬 이미지 로드 실패: {image_path} - {e}")
        
        return payloads
    
    def _get_scene_image_path(self, scene: Scene) -> Optional[str]:
        """씬 이미지 경로 찾기"""
        # 그룹화된 경로 우선
        if hasattr(scene, 'grouped_path') and scene.grouped_path and os.path.exists(scene.grouped_path):
            return scene.grouped_path
        
        # 기본 경로
        if os.path.exists(scene.frame_path):
            return scene.frame_path
        
        self.logger.warning(f"씬 이미지 파일 없음: {scene.frame_path}")
        return None
    
    def _prepare_context(self, video: Video) -> Dict[str, Any]:
        """분석 컨텍스트 준비"""
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
            
            # 설명은 500자로 제한
            if video.metadata.description:
                context["description"] = video.metadata.description[:500]
            
            context["tags"] = video.metadata.tags[:10] if video.metadata.tags else []
            context["view_count"] = video.metadata.view_count or 0
        
        return context
    
    def _postprocess_result(self, parsed: ParsedAnalysis, video: Video) -> Dict[str, Any]:
        """분석 결과 후처리"""
        result = parsed.to_dict()
        
        # YouTube 태그와 병합
        if video.metadata and video.metadata.tags:
            youtube_tags = [tag for tag in video.metadata.tags if tag and len(tag) > 1]
            merged_tags = list(set(result['tags'] + youtube_tags))
            result['tags'] = merged_tags[:20]  # 최대 20개
            self.logger.info(f"🏷️ YouTube 태그 {len(youtube_tags)}개 병합됨")
        
        # 메타데이터 추가
        result['model_used'] = f"{self.provider.get_name()}:{self.provider.config.model}"
        result['analysis_date'] = datetime.now().isoformat()
        
        return result
    
    def _prepare_debug_directory(self, video: Video) -> str:
        """디버깅 디렉토리 준비"""
        debug_dir = os.path.join(video.session_dir, "debug")
        os.makedirs(debug_dir, exist_ok=True)
        return debug_dir
    
    def _save_debug_info(self, debug_dir: str, filename: str, content: str, 
                        metadata: Optional[Dict[str, Any]] = None):
        """디버깅 정보 저장"""
        try:
            filepath = os.path.join(debug_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                # 메타데이터가 있으면 헤더로 추가
                if metadata:
                    import json
                    f.write(f"=== METADATA ===\n")
                    f.write(f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    for key, value in metadata.items():
                        if isinstance(value, (dict, list)):
                            f.write(f"{key}: {json.dumps(value, ensure_ascii=False)}\n")
                        else:
                            f.write(f"{key}: {value}\n")
                    f.write(f"\n=== CONTENT ===\n")
                
                f.write(content)
            
            self.logger.debug(f"💾 디버그 정보 저장: {filepath}")
            
        except Exception as e:
            self.logger.error(f"디버그 정보 저장 실패: {str(e)}")
    
    def _save_analysis_result(self, video: Video, result: Dict[str, Any]):
        """분석 결과 저장"""
        # Video 객체에 결과 저장
        video.analysis_result = result
        
        # JSON 파일로도 저장
        try:
            result_path = os.path.join(video.session_dir, "analysis_result.json")
            
            import json
            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"💾 분석 결과 저장: {result_path}")
            
        except Exception as e:
            self.logger.error(f"분석 결과 저장 실패: {str(e)}")
    
    # 기존 AI Analyzer와의 호환성을 위한 메서드들
    def analyze_video_legacy(self, video: Video) -> Optional[Any]:
        """기존 형식의 분석 결과 반환 (호환성)"""
        result_dict = self.analyze_video(video)
        if not result_dict:
            return None
        
        # ParsedAnalysis 형식으로 변환
        from .parser import ParsedAnalysis
        return ParsedAnalysis(
            genre=result_dict.get('genre', 'Unknown'),
            reason=result_dict.get('reasoning', ''),
            features=result_dict.get('features', ''),
            tags=result_dict.get('tags', []),
            format_type=result_dict.get('expression_style', '실사'),
            mood=result_dict.get('mood_tone', ''),
            target_audience=result_dict.get('target_audience', '')
        )
