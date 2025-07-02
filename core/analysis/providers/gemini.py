# core/analysis/providers/gemini.py
"""
Google Gemini AI Provider 구현 - FactChat 프록시 사용
"""

import os
import requests
from typing import List, Optional, Any, Tuple, Dict
from utils.logger import get_logger

from .base import AIProvider, ProviderConfig, ImagePayload


class GeminiConfig(ProviderConfig):
    """Gemini 전용 설정"""
    base_url: str = "https://factchat-cloud.mindlogic.ai/v1/api"
    api_type: str = "factchat"  # 'factchat' or 'google'
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 model: str = "gemini-pro-vision",
                 api_type: str = "factchat",
                 **kwargs):
        # FactChat API 키 사용
        api_key = api_key or os.getenv("FACTCHAT_API_KEY", "NPpDGrF4ShhrecUsBJm1dIIW7DZab4qC")
        self.api_type = api_type
        super().__init__(api_key=api_key, model=model, **kwargs)


class GeminiProvider(AIProvider):
    """Google Gemini API Provider - FactChat 프록시 사용"""
    
    def __init__(self, config: Optional[GeminiConfig] = None, **kwargs):
        # kwargs로 받은 설정을 config에 전달
        if config is None:
            config = GeminiConfig(**kwargs)
        super().__init__(config)
        self.logger = get_logger(__name__)
        
        # 초기홖
        self._initialize()
    
    def get_name(self) -> str:
        return "gemini"
    
    def _initialize(self):
        """Provider 초기화"""
        is_valid, error_msg = self.validate_config()
        if not is_valid:
            self.logger.error(f"❌ Gemini 설정 오류: {error_msg}")
            return
        
        self.logger.info("✅ Gemini Provider (via FactChat) 초기화 성공")
        self._log_config()
    
    def _log_config(self):
        """현재 설정 로그"""
        self.logger.info(f"🔑 API 키: {self.config.api_key[:8]}...{self.config.api_key[-4:]}")
        self.logger.info(f"🔗 Base URL: {self.config.base_url}")
        self.logger.info(f"🤖 모델: {self.config.model}")
    
    def validate_config(self) -> Tuple[bool, Optional[str]]:
        """설정 유효성 검사"""
        if not self.config.api_key:
            return False, "API key is required"
        
        if not self.config.model:
            return False, "Model is required"
        
        return True, None
    
    def initialize_client(self) -> Optional[Any]:
        """클라이언트 초기화 (requests 사용)"""
        return True  # requests를 사용하므로 별도 클라이언트 불필요
    
    def call_api(self,
                 images: List[ImagePayload],
                 prompt: str,
                 system_prompt: str) -> Optional[str]:
        """FactChat을 통한 Gemini API 호출"""
        try:
            # 정확한 Gemini API 엔드포인트
            url = f"{self.config.base_url}/google/models/generate-content"
            
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
            
            # Gemini 형식으로 parts 구성
            parts = [{"text": f"{system_prompt}\n\n{prompt}"}]
            
            # 이미지 변환 (ImagePayload → Gemini 형식)
            for img in images:
                parts.append({
                    "inlineData": {
                        "mimeType": "image/jpeg",
                        "data": img.data  # base64 데이터
                    }
                })
            
            # 정확한 Gemini 요청 형식
            data = {
                "model": self.config.model,
                "contents": [
                    {
                        "role": "user",
                        "parts": parts
                    }
                ]
            }
            
            self.logger.info(f"🔗 Gemini API 호출: {url}")
            self.logger.info(f"📋 모델: {self.config.model}")
            self.logger.info(f"📸 이미지 수: {len([p for p in parts if 'inlineData' in p])}")
            
            response = requests.post(url, headers=headers, json=data, timeout=120)
            
            self.logger.info(f"📤 Gemini 응답 상태: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                # Gemini 응답 구조 로깅 (디버깅용)
                self.logger.debug(f"Gemini 응답 구조: {list(result.keys())}")
                
                # 응답에서 텍스트 추출
                if "candidates" in result and len(result["candidates"]) > 0:
                    candidate = result["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        parts = candidate["content"]["parts"]
                        if len(parts) > 0 and "text" in parts[0]:
                            content = parts[0]["text"]
                            self.logger.info(f"✅ Gemini API 성공: {len(content)}자")
                            return content
                
                self.logger.error(f"❌ Gemini 응답 구조 오류: {result}")
                return None
            else:
                self.logger.error(f"❌ Gemini API 오류: {response.status_code}")
                self.logger.error(f"❌ 응답 내용: {response.text}")
                return None
                
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"❌ HTTP 오류: {e}")
            if e.response:
                self.logger.error(f"❌ 응답 내용: {e.response.text}")
            return None
        except Exception as e:
            self.logger.error(f"❌ Gemini API 실패: {e}")
            return None
