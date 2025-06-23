# src/storage/webdav_client.py
from webdav3.client import Client
import os
from typing import List
from config.settings import Settings
from utils.logger import get_logger

class WebDAVStorage:
    """WebDAV 스토리지 클라이언트"""
    
    def __init__(self):
        self.settings = Settings()
        self.logger = get_logger(__name__)
        self.client = self._create_client()
    
    def _create_client(self) -> Client:
        """WebDAV 클라이언트 생성"""
        options = {
            'webdav_hostname': self.settings.webdav.hostname,
            'webdav_login': self.settings.webdav.login,
            'webdav_password': self.settings.webdav.password,
            'webdav_root': self.settings.webdav.root
        }
        return Client(options)
    
    def _ensure_remote_directory(self, remote_dir: str):
        """원격 디렉토리가 존재하는지 확인하고 없으면 생성"""
        # 경로를 '/'로 분리하고 순차적으로 생성
        parts = remote_dir.strip('/').split('/')
        current_path = ""
        
        for part in parts:
            current_path = os.path.join(current_path, part)
            try:
                # 디렉토리 존재 여부 확인
                if not self.client.check(current_path):
                    self.logger.info(f"📁 디렉토리 생성: {current_path}")
                    self.client.mkdir(current_path)
            except Exception as e:
                # 이미 존재하는 경우 무시
                self.logger.debug(f"디렉토리 확인/생성 중 오류 (무시 가능): {e}")
    
    def upload_file(self, local_path: str, remote_folder: str = None) -> str:
        """파일을 WebDAV 서버에 업로드"""
        if remote_folder is None:
            remote_folder = self.settings.webdav.remote_folder
            
        # 경로 정리
        clean_folder = remote_folder.strip("/")
        filename = os.path.basename(local_path)
        remote_path = os.path.join(clean_folder, filename)
        
        try:
            # 원격 디렉토리 생성
            remote_dir = os.path.dirname(remote_path)
            if remote_dir:
                self._ensure_remote_directory(remote_dir)
            
            self.logger.info(f"📤 업로드 시작: {local_path} -> {remote_path}")
            
            # 파일 업로드
            self.client.upload_sync(remote_path=remote_path, local_path=local_path)
            
            self.logger.info(f"✅ 업로드 완료: {remote_path}")
            return remote_path
            
        except Exception as e:
            self.logger.error(f"❌ 업로드 실패: {e}")
            raise
    
    def upload_directory(self, local_dir: str, remote_folder: str = None) -> List[str]:
        """디렉토리 전체를 업로드"""
        uploaded_files = []
        
        for root, dirs, files in os.walk(local_dir):
            for file in files:
                local_path = os.path.join(root, file)
                # 상대 경로 계산
                rel_path = os.path.relpath(local_path, local_dir)
                remote_path = os.path.join(remote_folder or self.settings.webdav.remote_folder, rel_path)
                
                try:
                    self.upload_file(local_path, os.path.dirname(remote_path))
                    uploaded_files.append(remote_path)
                except Exception as e:
                    self.logger.error(f"파일 업로드 실패: {local_path}, 오류: {e}")
        
        return uploaded_files
    
    def list_files(self, remote_folder: str = None) -> List[str]:
        """원격 폴더의 파일 목록 조회"""
        folder = remote_folder or self.settings.webdav.remote_folder
        try:
            # 폴더가 존재하는지 먼저 확인
            if not self.client.check(folder):
                self.logger.warning(f"폴더가 존재하지 않습니다: {folder}")
                return []
            return self.client.list(folder)
        except Exception as e:
            self.logger.error(f"폴더 목록 조회 실패: {e}")
            return []
    
    def test_connection(self) -> bool:
        """WebDAV 연결 테스트"""
        try:
            # 루트 디렉토리 목록 조회로 연결 테스트
            self.client.list("/")
            self.logger.info("✅ WebDAV 연결 성공")
            return True
        except Exception as e:
            self.logger.error(f"❌ WebDAV 연결 실패: {e}")
            return False