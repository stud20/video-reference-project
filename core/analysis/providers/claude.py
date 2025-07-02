# core/analysis/providers/claude.py
"""
Claude AI Provider 구현 - FactChat 프록시 사용
"""

import os
import requests
from typing import List, Optional, Any, Tuple, Dict
from utils.logger import get_logger

from .base import AIProvider, ProviderConfig, ImagePayload


class ClaudeConfig(ProviderConfig):
    """Claude 전용 설정"""
    base_url: str = "https://factchat-cloud.mindlogic.ai/v1/api"
    api_type: str = "factchat"  # 'factchat' or 'anthropic'
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 model: str = "claude-3-opus-20240229",
                 api_type: str = "factchat",
                 **kwargs):
        # FactChat API 키 사용
        api_key = api_key or os.getenv("FACTCHAT_API_KEY", "NPpDGrF4ShhrecUsBJm1dIIW7DZab4qC")
        self.api_type = api_type
        super().__init__(api_key=api_key, model=model, **kwargs)
        
        # Anthropic 특화 설정
        self.max_tokens = kwargs.get('max_tokens', 4096)


class ClaudeProvider(AIProvider):
    """Claude API Provider - FactChat 프록시 사용"""
    
    def __init__(self, config: Optional[ClaudeConfig] = None, **kwargs):
        # kwargs로 받은 설정을 config에 전달
        if config is None:
            config = ClaudeConfig(**kwargs)
        super().__init__(config)
        self.logger = get_logger(__name__)
        
        # 초기화
        self._initialize()
    
    def get_name(self) -> str:
        return "claude"
    
    def _initialize(self):
        """Provider 초기화"""
        is_valid, error_msg = self.validate_config()
        if not is_valid:
            self.logger.error(f"❌ Anthropic 설정 오류: {error_msg}")
            return
        
        self.logger.info("✅ Anthropic Provider (Claude via FactChat) 초기화 성공")
        self._log_config()
    
    def _log_config(self):
        """현재 설정 로그"""
        self.logger.info(f"🔑 API 키: {self.config.api_key[:8]}...{self.config.api_key[-4:]}")
        self.logger.info(f"🔗 Base URL: {self.config.base_url}")
        self.logger.info(f"🤖 모델: {self.config.model}")
        self.logger.info(f"📝 최대 토큰: {self.config.max_tokens}")
    
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
        """FactChat을 통한 Claude API 호출"""
        try:
            url = f"{self.config.base_url}/anthropic/messages"
            
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            }
            
            # Claude 형식으로 content 구성
            content_parts = [{"type": "text", "text": prompt}]
            
            # 이미지 변환 (ImagePayload → Claude 형식)
            for img in images:
                content_parts.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": img.data  # base64 데이터
                    }
                })
            
            data = {
                "model": self.config.model,
                "max_tokens": self.config.max_tokens,
                "system": system_prompt,
                "messages": [
                    {
                        "role": "user",
                        "content": content_parts
                    }
                ]
            }
            
            self.logger.info(f"🔗 Claude API 호출: {self.config.model}")
            self.logger.info(f"📸 이미지 수: {len([p for p in content_parts if p['type'] == 'image'])}")
            
            response = requests.post(url, headers=headers, json=data, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            content = result["content"][0]["text"]
            
            self.logger.info(f"✅ Claude API 성공: {len(content)}자")
            return content
            
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"❌ HTTP 오류: {e}")
            if e.response:
                self.logger.error(f"❌ 응답 내용: {e.response.text}")
            return None
        except Exception as e:
            self.logger.error(f"❌ Claude API 실패: {e}")
            return None
