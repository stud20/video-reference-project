# src/storage/local_storage.py
"""로컬 파일 시스템 스토리지"""
import os
import shutil
from pathlib import Path
from utils.logger import get_logger

class LocalStorage:
    """로컬 파일 시스템 스토리지 클라이언트"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.base_path = "results/videos"
        
        # 기본 디렉토리 생성
        os.makedirs(self.base_path, exist_ok=True)
        
    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """로컬 스토리지에 파일 복사"""
        try:
            # 대상 경로 생성 (파일명 제외한 디렉토리만)
            if remote_path.startswith('video_analysis/'):
                # video_analysis/896832106/scene_0000.jpg 형태
                dest_dir = os.path.join(self.base_path, os.path.dirname(remote_path))
                dest_file = os.path.join(self.base_path, remote_path)
            else:
                dest_dir = os.path.dirname(remote_path)
                dest_file = remote_path
            
            # 디렉토리만 생성 (파일명은 제외)
            os.makedirs(dest_dir, exist_ok=True)
            
            # 파일 복사
            self.logger.info(f"📁 로컬 복사: {local_path} -> {dest_file}")
            shutil.copy2(local_path, dest_file)
            
            self.logger.info(f"✅ 복사 완료: {dest_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"로컬 스토리지 업로드 실패: {str(e)}")
            return False
    
    def test_connection(self) -> bool:
        """로컬 스토리지 연결 테스트 (항상 성공)"""
        return True