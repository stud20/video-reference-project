# src/analyzer/providers/base_provider.py
"""AI Provider 기본 추상 클래스"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import base64


@dataclass
class ImagePayload:
    """이미지 페이로드 데이터 클래스"""
    data: str  # base64 encoded image
    detail: str = "auto"  # low, high, auto
    
    def to_dict(self) -> Dict[str, Any]:
        """OpenAI API 형식으로 변환"""
        return {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{self.data}",
                "detail": self.detail
            }
        }


@dataclass
class ProviderConfig:
    """Provider 설정 기본 클래스"""
    api_key: str
    model: str
    max_tokens: int = 2000
    temperature: float = 0.7


class AIProvider(ABC):
    """AI Provider 추상 기본 클래스"""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self.logger = None  # 각 구현체에서 설정
    
    @abstractmethod
    def get_name(self) -> str:
        """Provider 이름 반환"""
        pass
    
    @abstractmethod
    def initialize_client(self) -> Any:
        """클라이언트 초기화"""
        pass
    
    @abstractmethod
    def call_api(self, 
                 images: List[ImagePayload], 
                 prompt: str,
                 system_prompt: str) -> Optional[str]:
        """API 호출 수행"""
        pass
    
    @abstractmethod
    def validate_config(self) -> Tuple[bool, Optional[str]]:
        """설정 유효성 검사
        
        Returns:
            (is_valid, error_message)
        """
        pass
    
    def prepare_messages(self, 
                        images: List[ImagePayload], 
                        prompt: str,
                        system_prompt: str) -> List[Dict[str, Any]]:
        """메시지 형식 준비 (기본 OpenAI 형식)"""
        content = [{"type": "text", "text": prompt}]
        content.extend([img.to_dict() for img in images])
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content}
        ]
    
    def get_token_usage(self, response: Any) -> Optional[Dict[str, int]]:
        """응답에서 토큰 사용량 추출"""
        if hasattr(response, 'usage'):
            return {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
        return None
