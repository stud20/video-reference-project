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
        
    def upload_file(self, local_path: str, remote_path: str) -> str:
        """SFTP로 파일 업로드 - 수정된 버전"""
        transport = None
        sftp = None
        
        try:
            # SSH 연결
            self.logger.info(f"🔌 SFTP 연결 중: {self.host}:{self.port}")
            transport = paramiko.Transport((self.host, self.port))
            transport.connect(username=self.username, password=self.password)
            
            # SFTP 클라이언트 생성
            sftp = paramiko.SFTPClient.from_transport(transport)
            
            # remote_path가 전체 경로인 경우 처리
            if remote_path.startswith('video_analysis/'):
                # base_path와 결합
                full_remote_path = f"{self.base_path}/{remote_path}"
            else:
                full_remote_path = remote_path
            
            # 디렉토리와 파일명 분리
            remote_dir = os.path.dirname(full_remote_path)
            filename = os.path.basename(full_remote_path)
            
            # 디렉토리 생성 (재귀적)
            self._mkdir_p(sftp, remote_dir)
            
            # 파일 업로드 (디렉토리가 아닌 파일 경로로)
            self.logger.info(f"📤 업로드 시작: {local_path} -> {full_remote_path}")
            sftp.put(local_path, full_remote_path)
            
            self.logger.info(f"✅ SFTP 업로드 완료: {full_remote_path}")
            return full_remote_path
            
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