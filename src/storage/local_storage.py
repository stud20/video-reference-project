# src/storage/local_storage.py
"""로컬 파일 시스템 스토리지"""

import os
import shutil
from typing import List
from config.settings import Settings
from utils.logger import get_logger

class LocalStorage:
    """로컬 파일 시스템 스토리지"""
    
    def __init__(self):
        self.settings = Settings()
        self.logger = get_logger(__name__)
        self.base_path = "results/videos"
        os.makedirs(self.base_path, exist_ok=True)
    
    def upload_file(self, local_path: str, remote_folder: str = None) -> str:
        """파일을 로컬 저장소에 복사"""
        if remote_folder is None:
            remote_folder = "2025-session"
            
        # 대상 경로 생성
        dest_dir = os.path.join(self.base_path, remote_folder.strip("/"))
        os.makedirs(dest_dir, exist_ok=True)
        
        filename = os.path.basename(local_path)
        dest_path = os.path.join(dest_dir, filename)
        
        try:
            self.logger.info(f"📁 로컬 복사: {local_path} -> {dest_path}")
            shutil.copy2(local_path, dest_path)
            self.logger.info(f"✅ 복사 완료: {dest_path}")
            return dest_path
        except Exception as e:
            self.logger.error(f"❌ 복사 실패: {e}")
            raise
    
    def list_files(self, folder: str = None) -> List[str]:
        """폴더의 파일 목록 조회"""
        target_dir = os.path.join(self.base_path, folder.strip("/") if folder else "")
        if os.path.exists(target_dir):
            return os.listdir(target_dir)
        return []
    
    def test_connection(self) -> bool:
        """연결 테스트 (로컬은 항상 True)"""
        return True