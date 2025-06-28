# utils/env_manager.py
"""
환경변수 관리 유틸리티 - 메모리와 .env 파일 동시 업데이트
"""

import os
from typing import Any, Optional
from dotenv import set_key, find_dotenv
from utils.logger import get_logger

logger = get_logger(__name__)


class EnvManager:
    """환경변수 관리 클래스"""
    
    @staticmethod
    def update(key: str, value: Any, description: str = "") -> bool:
        """
        환경변수를 메모리와 .env 파일 모두에 업데이트
        
        Args:
            key: 환경변수 키
            value: 설정할 값
            description: 로그용 설명
            
        Returns:
            성공 여부
        """
        try:
            # 값을 문자열로 변환
            str_value = str(value)
            
            # 1. 메모리상의 환경변수 업데이트
            os.environ[key] = str_value
            
            # 2. .env 파일 찾기
            dotenv_path = find_dotenv()
            if not dotenv_path:
                logger.warning(".env 파일을 찾을 수 없습니다")
                return False
            
            # 3. .env 파일 업데이트
            success, key_to_set, value_to_set = set_key(dotenv_path, key, str_value)
            
            if success:
                logger.info(f"✅ 환경변수 업데이트 성공: {key}={str_value} {description}")
                return True
            else:
                logger.error(f"❌ .env 파일 업데이트 실패: {key}")
                return False
                
        except Exception as e:
            logger.error(f"환경변수 업데이트 중 오류: {str(e)}")
            return False
    
    @staticmethod
    def get(key: str, default: Any = None) -> str:
        """환경변수 값 가져오기"""
        return os.getenv(key, str(default) if default is not None else "")
    
    @staticmethod
    def get_int(key: str, default: int = 0) -> int:
        """정수형 환경변수 값 가져오기"""
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            return default
    
    @staticmethod
    def get_float(key: str, default: float = 0.0) -> float:
        """실수형 환경변수 값 가져오기"""
        try:
            return float(os.getenv(key, str(default)))
        except ValueError:
            return default
    
    @staticmethod
    def get_bool(key: str, default: bool = False) -> bool:
        """불린형 환경변수 값 가져오기"""
        value = os.getenv(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')