# core/analysis/providers/openai_gpt4.py
"""
OpenAI GPT-4 Provider 구현 - FactChat 프록시 사용
"""

import os
import json
import requests
from typing import List, Optional, Any, Tuple, Dict
from utils.logger import get_logger

from .base import AIProvider, ProviderConfig, ImagePayload


class OpenAIConfig(ProviderConfig):
    """OpenAI 전용 설정"""
    base_url: str = "https://factchat-cloud.mindlogic.ai/v1/api"
    api_type: str = "factchat"  # 'factchat' or 'openai'
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 model: str = "gpt-4o",
                 api_type: str = "factchat",
                 **kwargs):
        # 환경변수 또는 기본값 사용
        api_key = api_key or os.getenv("FACTCHAT_API_KEY", "NPpDGrF4ShhrecUsBJm1dIIW7DZab4qC")
        self.api_type = api_type
        super().__init__(api_key=api_key, model=model, **kwargs)


class OpenAIProvider(AIProvider):
    """OpenAI GPT-4 API Provider - FactChat 프록시 사용"""
    
    def __init__(self, config: Optional[OpenAIConfig] = None, **kwargs):
        # kwargs로 받은 설정을 config에 전달
        if config is None:
            config = OpenAIConfig(**kwargs)
        super().__init__(config)
        self.logger = get_logger(__name__)
        
        # 초기화
        self._initialize()
    
    def get_name(self) -> str:
        return "openai-gpt4"
    
    def _initialize(self):
        """Provider 초기화"""
        is_valid, error_msg = self.validate_config()
        if not is_valid:
            self.logger.error(f"❌ FactChat 설정 오류: {error_msg}")
            return
        
        self.logger.info("✅ FactChat Provider (OpenAI GPT-4o) 초기화 성공")
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
        
        if not self.config.base_url:
            return False, "Base URL is required"
        
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
        """FactChat을 통한 OpenAI API 호출"""
        try:
            # FactChat OpenAI API 엔드포인트
            url = f"{self.config.base_url}/openai/chat/completions"
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config.api_key}"
            }
            
            # OpenAI 형식 메시지 준비
            image_payloads = [img.to_dict() for img in images]
            
            messages = [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        *image_payloads
                    ]
                }
            ]
            
            data = {
                "model": self.config.model,
                "messages": messages,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature
            }
            
            self.logger.info(f"🔗 OpenAI API 호출: {self.config.model}")
            self.logger.info(f"📸 이미지 수: {len(images)}")
            self.logger.info(f"🔑 API URL: {url}")
            self.logger.info(f"🔑 API Key: {self.config.api_key[:8]}...{self.config.api_key[-4:]}")
            
            # 요청 데이터 크기 확인 (이미지 데이터 제외)
            request_size = len(json.dumps({**data, "messages": [{"role": m["role"], "content": "[TRUNCATED]"} for m in data["messages"]]}))
            self.logger.info(f"📦 요청 데이터 크기 (이미지 제외): {request_size} bytes")
            
            response = requests.post(url, headers=headers, json=data, timeout=120)
            
            # 응답 상태 코드 로깅
            self.logger.info(f"📤 OpenAI 응답 상태: {response.status_code}")
            
            # 응답 내용 디버깅
            if response.status_code != 200:
                self.logger.error(f"❌ API 오류: {response.status_code}")
                self.logger.error(f"❌ 응답 내용: {response.text}")
                return None
            
            # 응답 파싱
            try:
                result = response.json()
            except json.JSONDecodeError as e:
                self.logger.error(f"❌ JSON 파싱 오류: {e}")
                self.logger.error(f"❌ 응답 텍스트: {response.text[:500]}")
                return None
            
            # 응답 구조 로깅
            self.logger.info(f"OpenAI 응답 키: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            
            # 오류 메시지가 있는지 확인 - Azure OpenAI 오류 포함
            if isinstance(result, dict):
                if "error" in result:
                    self.logger.error(f"❌ API 오류 메시지: {result.get('error')}")
                    return None
                elif "detail" in result:
                    # Azure OpenAI 오류 처리
                    detail = result.get('detail', '')
                    if 'ResponsibleAIPolicyViolation' in str(detail):
                        self.logger.error("❌ Azure OpenAI 콘텐츠 필터에 의해 차단됨")
                        self.logger.error("💡 해결 방안: Claude 또는 Gemini 모델을 사용해보세요")
                    else:
                        self.logger.error(f"❌ FactChat API 오류: {detail}")
                    return None
            
            # 응답에서 content 추출 - 다양한 형식 지원
            content = None
            
            # 표준 OpenAI 형식
            if "choices" in result and len(result["choices"]) > 0:
                choice = result["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    content = choice["message"]["content"]
                elif "text" in choice:
                    content = choice["text"]
            
            # FactChat 특별 형식 (만약 다른 형식이라면)
            elif "response" in result:
                content = result["response"]
            elif "content" in result:
                content = result["content"]
            elif "message" in result:
                content = result["message"]
            
            if not content:
                # 전체 응답 내용을 제한된 크기로 로깅
                result_str = json.dumps(result, ensure_ascii=False, indent=2)
                if len(result_str) > 1000:
                    result_str = result_str[:1000] + "..."
                self.logger.error(f"❌ 예상치 못한 응답 형식. 전체 응답:\n{result_str}")
                return None
            
            # 토큰 사용량 로깅
            if "usage" in result:
                usage = result["usage"]
                self.logger.info(
                    f"📊 토큰 사용량 - "
                    f"입력: {usage.get('prompt_tokens', 0)}, "
                    f"출력: {usage.get('completion_tokens', 0)}, "
                    f"총합: {usage.get('total_tokens', 0)}"
                )
            
            self.logger.info(f"✅ OpenAI API 성공: {len(content)}자")
            return content
            
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"❌ HTTP 오류: {e}")
            if e.response:
                self.logger.error(f"❌ 응답 내용: {e.response.text}")
            return None
        except Exception as e:
            self.logger.error(f"❌ OpenAI API 실패: {e}")
            import traceback
            self.logger.error(f"❌ 스택 트레이스:\n{traceback.format_exc()}")
            return None
