# src/storage/storage_manager.py
"""통합 스토리지 관리자 - 여러 업로드 방식 지원"""

from enum import Enum
from typing import Optional
import os
from utils.logger import get_logger

class StorageType(Enum):
    LOCAL = "local"
    WEBDAV = "webdav"
    SYNOLOGY_API = "synology_api"
    SFTP = "sftp"

class StorageManager:
    """다양한 스토리지 백엔드를 관리하는 통합 인터페이스"""
    
    def __init__(self, storage_type: StorageType = StorageType.LOCAL):
        self.logger = get_logger(__name__)
        self.storage_type = storage_type
        self.storage = self._init_storage()
    
    def _init_storage(self):
        """선택된 스토리지 타입에 따라 적절한 클라이언트 초기화"""
        try:
            if self.storage_type == StorageType.LOCAL:
                from src.storage.local_storage import LocalStorage
                return LocalStorage()
                
            elif self.storage_type == StorageType.WEBDAV:
                from src.storage.webdav_client import WebDAVStorage
                return WebDAVStorage()
                
            elif self.storage_type == StorageType.SYNOLOGY_API:
                from src.storage.synology_api_client import SynologyFileStation
                return SynologyFileStation()
                
            elif self.storage_type == StorageType.SFTP:
                from src.storage.sftp_client import SFTPStorage
                return SFTPStorage()
                
        except Exception as e:
            self.logger.error(f"스토리지 초기화 실패 ({self.storage_type}): {e}")
            self.logger.info("로컬 스토리지로 대체")
            from src.storage.local_storage import LocalStorage
            return LocalStorage()
    
    def upload_file(self, local_path: str, remote_folder: str = None) -> str:
        """파일 업로드 (스토리지 타입에 관계없이 동일한 인터페이스)"""
        try:
            return self.storage.upload_file(local_path, remote_folder)
        except Exception as e:
            self.logger.error(f"업로드 실패: {e}")
            # 실패 시 로컬 저장으로 폴백
            self.logger.info("로컬 저장으로 대체 시도")
            from src.storage.local_storage import LocalStorage
            local_storage = LocalStorage()
            return local_storage.upload_file(local_path, remote_folder)
    
    def test_connection(self) -> bool:
        """연결 테스트"""
        try:
            if hasattr(self.storage, 'test_connection'):
                return self.storage.test_connection()
            elif hasattr(self.storage, 'login'):
                return self.storage.login()
            return True
        except Exception as e:
            self.logger.error(f"연결 테스트 실패: {e}")
            return False