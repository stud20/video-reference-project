# src/storage/sftp_client.py
"""SFTP를 통한 시놀로지 NAS 파일 업로드"""

import paramiko
import os
from config.settings import Settings
from utils.logger import get_logger

class SFTPStorage:
    """SFTP 스토리지 클라이언트"""
    
    def __init__(self):
        self.settings = Settings()
        self.logger = get_logger(__name__)
        
        # SFTP 설정
        self.host = os.getenv("SYNOLOGY_HOST", "nas.greatminds.kr")
        self.port = int(os.getenv("SFTP_PORT", "22"))
        self.username = os.getenv("SYNOLOGY_USER", "dav")
        self.password = os.getenv("SYNOLOGY_PASS", "dav123")
        self.base_path = "/dav/videoRef"  # 시놀로지 실제 경로
        
    def upload_file(self, local_path: str, remote_folder: str = "2025-session") -> str:
        """SFTP로 파일 업로드"""
        transport = None
        sftp = None
        
        try:
            # SSH 연결
            self.logger.info(f"🔌 SFTP 연결 중: {self.host}:{self.port}")
            transport = paramiko.Transport((self.host, self.port))
            transport.connect(username=self.username, password=self.password)
            
            # SFTP 클라이언트 생성
            sftp = paramiko.SFTPClient.from_transport(transport)
            
            # 원격 경로 생성
            remote_base = f"{self.base_path}/{remote_folder}"
            
            # 디렉토리 생성 (재귀적)
            self._mkdir_p(sftp, remote_base)
            
            # 파일 업로드
            filename = os.path.basename(local_path)
            remote_path = f"{remote_base}/{filename}"
            
            self.logger.info(f"📤 업로드 시작: {local_path} -> {remote_path}")
            sftp.put(local_path, remote_path)
            
            self.logger.info(f"✅ SFTP 업로드 완료: {remote_path}")
            return remote_path
            
        except Exception as e:
            self.logger.error(f"❌ SFTP 업로드 실패: {e}")
            raise
        finally:
            if sftp:
                sftp.close()
            if transport:
                transport.close()
    
    def _mkdir_p(self, sftp, remote_directory):
        """원격 디렉토리 재귀적 생성"""
        if remote_directory == '/':
            return
        if remote_directory == '':
            return
            
        try:
            sftp.stat(remote_directory)
        except IOError:
            # 상위 디렉토리 먼저 생성
            dirname, basename = os.path.split(remote_directory.rstrip('/'))
            self._mkdir_p(sftp, dirname)
            sftp.mkdir(remote_directory)
            self.logger.info(f"📁 디렉토리 생성: {remote_directory}")