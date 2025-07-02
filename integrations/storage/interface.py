# src/storage/storage_manager.py
"""스토리지 매니저 - 다양한 스토리지 백엔드 지원"""
import os
from enum import Enum
from typing import Optional, List, Dict, Any
from utils.logger import get_logger


class StorageType(Enum):
    """지원하는 스토리지 타입"""
    LOCAL = "local"
    WEBDAV = "webdav"
    SFTP = "sftp"


class StorageManager:
    """스토리지 추상화 레이어"""
    
    def __init__(self, storage_type: StorageType = StorageType.LOCAL):
        """
        스토리지 매니저 초기화
        
        Args:
            storage_type: 사용할 스토리지 타입
        """
        self.logger = get_logger(__name__)
        self.storage_type = storage_type
        
        self.logger.info(f"🗄️ StorageManager 초기화 - 타입: {storage_type.value}")
        
        # 스토리지 클라이언트 초기화
        self.sftp_client = None
        self.webdav_client = None
        self.local_storage = None
        
        # 스토리지 타입별 클라이언트 초기화
        if storage_type == StorageType.SFTP:
            self.logger.info("📡 SFTP 클라이언트 초기화 중...")
            try:
                from .sftp import SFTPStorage
                self.sftp_client = SFTPStorage()
                self.logger.info("✅ SFTP 클라이언트 초기화 성공")
            except Exception as e:
                self.logger.error(f"❌ SFTP 클라이언트 초기화 실패: {str(e)}")
                raise
                
        elif storage_type == StorageType.WEBDAV:
            self.logger.info("🌐 WebDAV 클라이언트 초기화 중...")
            try:
                from .webdav_client import WebDAVStorage
                self.webdav_client = WebDAVStorage()
                self.logger.info("✅ WebDAV 클라이언트 초기화 성공")
            except Exception as e:
                self.logger.error(f"❌ WebDAV 클라이언트 초기화 실패: {str(e)}")
                raise
                
        elif storage_type == StorageType.LOCAL:
            self.logger.info("💾 로컬 스토리지 클라이언트 초기화 중...")
            try:
                from .local import LocalStorage
                self.local_storage = LocalStorage()
                self.logger.info("✅ 로컬 스토리지 클라이언트 초기화 성공")
            except Exception as e:
                self.logger.error(f"❌ 로컬 스토리지 클라이언트 초기화 실패: {str(e)}")
                raise
        else:
            raise ValueError(f"지원하지 않는 스토리지 타입: {storage_type}")
    
    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """
        파일 업로드
        
        Args:
            local_path: 로컬 파일 경로
            remote_path: 원격 저장 경로
            
        Returns:
            업로드 성공 여부
        """
        try:
            # 파일 존재 확인
            if not os.path.exists(local_path):
                self.logger.error(f"로컬 파일이 존재하지 않음: {local_path}")
                return False
            
            # 스토리지 타입별 업로드
            if self.storage_type == StorageType.SFTP:
                if self.sftp_client:
                    return self.sftp_client.upload_file(local_path, remote_path)
                else:
                    self.logger.error("SFTP 클라이언트가 초기화되지 않음")
                    return False
                    
            elif self.storage_type == StorageType.WEBDAV:
                if self.webdav_client:
                    return self.webdav_client.upload_file(local_path, remote_path)
                else:
                    self.logger.error("WebDAV 클라이언트가 초기화되지 않음")
                    return False
                    
            elif self.storage_type == StorageType.LOCAL:
                if self.local_storage:
                    return self.local_storage.upload_file(local_path, remote_path)
                else:
                    self.logger.error("로컬 스토리지 클라이언트가 초기화되지 않음")
                    return False
            else:
                self.logger.error(f"지원하지 않는 스토리지 타입: {self.storage_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"파일 업로드 실패: {str(e)}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return False
    
    def test_connection(self) -> bool:
        """
        스토리지 연결 테스트
        
        Returns:
            연결 성공 여부
        """
        try:
            if self.storage_type == StorageType.SFTP:
                if self.sftp_client:
                    return self.sftp_client.test_connection()
                else:
                    self.logger.error("SFTP 클라이언트가 초기화되지 않음")
                    return False
                    
            elif self.storage_type == StorageType.WEBDAV:
                if self.webdav_client:
                    return self.webdav_client.test_connection()
                else:
                    self.logger.error("WebDAV 클라이언트가 초기화되지 않음")
                    return False
                    
            elif self.storage_type == StorageType.LOCAL:
                if self.local_storage:
                    return self.local_storage.test_connection()
                else:
                    self.logger.error("로컬 스토리지 클라이언트가 초기화되지 않음")
                    return False
            else:
                self.logger.error(f"지원하지 않는 스토리지 타입: {self.storage_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"연결 테스트 실패: {str(e)}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return False
    
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """
        파일 다운로드
        
        Args:
            remote_path: 원격 파일 경로
            local_path: 로컬 저장 경로
            
        Returns:
            다운로드 성공 여부
        """
        try:
            if self.storage_type == StorageType.SFTP:
                if self.sftp_client and hasattr(self.sftp_client, 'download_file'):
                    return self.sftp_client.download_file(remote_path, local_path)
                else:
                    self.logger.warning("SFTP 다운로드 미구현")
                    return False
                    
            elif self.storage_type == StorageType.WEBDAV:
                if self.webdav_client and hasattr(self.webdav_client, 'download_file'):
                    return self.webdav_client.download_file(remote_path, local_path)
                else:
                    self.logger.warning("WebDAV 다운로드 미구현")
                    return False
                    
            elif self.storage_type == StorageType.LOCAL:
                # 로컬의 경우 복사
                import shutil
                shutil.copy2(remote_path, local_path)
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"파일 다운로드 실패: {str(e)}")
            return False
    
    def list_files(self, remote_path: str = "") -> List[str]:
        """
        원격 디렉토리의 파일 목록 조회
        
        Args:
            remote_path: 원격 디렉토리 경로
            
        Returns:
            파일 목록
        """
        try:
            if self.storage_type == StorageType.SFTP:
                if self.sftp_client and hasattr(self.sftp_client, 'list_files'):
                    return self.sftp_client.list_files(remote_path)
                    
            elif self.storage_type == StorageType.WEBDAV:
                if self.webdav_client and hasattr(self.webdav_client, 'list_files'):
                    return self.webdav_client.list_files(remote_path)
                    
            elif self.storage_type == StorageType.LOCAL:
                # 로컬의 경우 os.listdir 사용
                full_path = os.path.join("results/videos", remote_path)
                if os.path.exists(full_path):
                    return os.listdir(full_path)
                    
            return []
            
        except Exception as e:
            self.logger.error(f"파일 목록 조회 실패: {str(e)}")
            return []
    
    def get_storage_info(self) -> Dict[str, Any]:
        """현재 스토리지 정보 반환"""
        return {
            "type": self.storage_type.value,
            "connected": self.test_connection(),
            "base_path": self._get_base_path()
        }
    
    def _get_base_path(self) -> str:
        """스토리지별 기본 경로 반환"""
        if self.storage_type == StorageType.SFTP and self.sftp_client:
            return getattr(self.sftp_client, 'base_path', 'N/A')
        elif self.storage_type == StorageType.WEBDAV and self.webdav_client:
            return getattr(self.webdav_client, 'base_path', 'N/A')
        elif self.storage_type == StorageType.LOCAL and self.local_storage:
            return getattr(self.local_storage, 'base_path', 'results/videos')
        return 'N/A'