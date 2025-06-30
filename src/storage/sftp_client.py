# src/storage/sftp_client.py
"""SFTP를 통한 시놀로지 NAS 파일 업로드"""
import paramiko
import os
import time
from typing import Optional
from config.settings import Settings
from utils.logger import get_logger

class SFTPStorage:
    """SFTP 스토리지 클라이언트"""
    
    def __init__(self):
        self.settings = Settings()
        self.logger = get_logger(__name__)
        
        # .env에서 SFTP 설정 로드
        self.host = os.getenv("SFTP_HOST")
        self.port = int(os.getenv("SFTP_PORT", "22"))
        self.username = os.getenv("SFTP_USER")
        self.password = os.getenv("SFTP_PASS")
        
        # WebDAV와 동일한 기본 경로 사용
        self.base_path = os.getenv("SFTP_ROOT", "/dav/videoRef").rstrip('/')
        
        # 설정 검증
        self._validate_config()
        
    def _validate_config(self):
        """SFTP 설정 검증"""
        missing_configs = []
        
        if not self.host:
            missing_configs.append("SFTP_HOST")
        if not self.username:
            missing_configs.append("SFTP_USER")
        if not self.password:
            missing_configs.append("SFTP_PASS")
            
        if missing_configs:
            error_msg = f"필수 SFTP 설정이 누락되었습니다: {', '.join(missing_configs)}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
            
        # 설정 로그 (비밀번호는 마스킹)
        self.logger.info(f"📋 SFTP 설정:")
        self.logger.info(f"  - Host: {self.host}")
        self.logger.info(f"  - Port: {self.port}")
        self.logger.info(f"  - User: {self.username}")
        self.logger.info(f"  - Base Path: {self.base_path}")
        
    def upload_file(self, local_path: str, remote_path: str) -> str:
        """SFTP로 파일 업로드 - 개선된 버전"""
        transport = None
        sftp = None
        
        # 재시도 설정
        max_retries = int(os.getenv("SFTP_MAX_RETRIES", "3"))
        retry_delay = int(os.getenv("SFTP_RETRY_DELAY", "2"))
        
        for attempt in range(max_retries):
            try:
                # SSH 연결
                self.logger.info(f"🔌 SFTP 연결 중: {self.host}:{self.port} (시도 {attempt + 1}/{max_retries})")
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
                
                # 경로 정규화 (중요!)
                full_remote_path = full_remote_path.replace('\\', '/')
                full_remote_path = full_remote_path.replace('//', '/')
                
                # 디렉토리와 파일명 분리
                remote_dir = os.path.dirname(full_remote_path)
                filename = os.path.basename(full_remote_path)
                
                # 파일명이 없는 경우 오류
                if not filename or '.' not in filename:
                    raise ValueError(f"잘못된 파일 경로: {full_remote_path}")
                
                # 디렉토리 생성 (재귀적)
                self._mkdir_p(sftp, remote_dir)
                
                # 파일이 이미 존재하는지 확인
                try:
                    sftp.stat(full_remote_path)
                    self.logger.info(f"파일이 이미 존재함: {full_remote_path}")
                    return full_remote_path
                except IOError:
                    # 파일이 없으면 계속 진행
                    pass
                
                # 임시 파일명으로 먼저 업로드
                temp_remote_path = f"{full_remote_path}.tmp"
                
                # 파일 업로드
                self.logger.info(f"📤 업로드 시작: {local_path} -> {full_remote_path}")
                sftp.put(local_path, temp_remote_path)
                
                # 업로드 검증
                local_size = os.path.getsize(local_path)
                remote_size = sftp.stat(temp_remote_path).st_size
                
                if local_size != remote_size:
                    raise Exception(f"파일 크기 불일치: 로컬 {local_size} != 원격 {remote_size}")
                
                # 임시 파일을 최종 파일로 이동
                try:
                    # 기존 파일이 있다면 삭제
                    sftp.remove(full_remote_path)
                except:
                    pass
                
                sftp.rename(temp_remote_path, full_remote_path)
                
                self.logger.info(f"✅ SFTP 업로드 완료: {full_remote_path}")
                return full_remote_path
                
            except Exception as e:
                self.logger.error(f"❌ SFTP 업로드 실패 (시도 {attempt + 1}): {e}")
                
                # 임시 파일 정리
                if sftp:
                    try:
                        temp_path = f"{full_remote_path}.tmp"
                        sftp.remove(temp_path)
                    except:
                        pass
                
                # 마지막 시도가 아니면 재시도
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    # 연결 정리
                    if sftp:
                        sftp.close()
                    if transport:
                        transport.close()
                    continue
                else:
                    raise
                    
            finally:
                # 성공한 경우에만 연결 종료
                if attempt == max_retries - 1 or 'full_remote_path' in locals():
                    if sftp:
                        sftp.close()
                    if transport:
                        transport.close()
        
        # 모든 재시도 실패
        raise Exception(f"업로드 실패: {max_retries}번 시도 후 포기")
    
    def _mkdir_p(self, sftp, remote_directory):
        """원격 디렉토리 재귀적 생성 - 개선된 버전"""
        if remote_directory == '/' or remote_directory == '':
            return
        
        # 경로 정규화
        remote_directory = remote_directory.replace('\\', '/')
        remote_directory = remote_directory.rstrip('/')
        
        # 이미 존재하는지 확인
        try:
            attr = sftp.stat(remote_directory)
            # 파일이 아닌 디렉토리인지 확인
            if not paramiko.stat.S_ISDIR(attr.st_mode):
                raise Exception(f"경로가 파일입니다: {remote_directory}")
            return
        except IOError:
            # 디렉토리가 없으면 생성 필요
            pass
        
        # 상위 디렉토리 먼저 생성
        parent_dir = os.path.dirname(remote_directory)
        if parent_dir and parent_dir != '/':
            self._mkdir_p(sftp, parent_dir)
        
        # 현재 디렉토리 생성
        try:
            sftp.mkdir(remote_directory)
            self.logger.info(f"📁 디렉토리 생성: {remote_directory}")
        except IOError as e:
            # 이미 존재하는 경우 무시
            if "File exists" not in str(e):
                raise
    
    def test_connection(self) -> bool:
        """SFTP 연결 테스트"""
        transport = None
        sftp = None
        
        try:
            self.logger.info(f"🔌 SFTP 연결 테스트: {self.host}:{self.port}")
            transport = paramiko.Transport((self.host, self.port))
            transport.connect(username=self.username, password=self.password)
            
            sftp = paramiko.SFTPClient.from_transport(transport)
            
            # base_path 존재 확인
            try:
                sftp.stat(self.base_path)
                self.logger.info(f"✅ 기본 경로 확인: {self.base_path}")
            except IOError:
                self.logger.warning(f"⚠️ 기본 경로가 존재하지 않습니다: {self.base_path}")
                # 기본 경로 생성 시도
                self._mkdir_p(sftp, self.base_path)
            
            self.logger.info("✅ SFTP 연결 테스트 성공")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ SFTP 연결 테스트 실패: {e}")
            return False
            
        finally:
            if sftp:
                sftp.close()
            if transport:
                transport.close()
    
    def list_files(self, remote_path: str = "") -> list:
        """원격 디렉토리의 파일 목록 조회"""
        transport = None
        sftp = None
        
        try:
            transport = paramiko.Transport((self.host, self.port))
            transport.connect(username=self.username, password=self.password)
            sftp = paramiko.SFTPClient.from_transport(transport)
            
            full_path = f"{self.base_path}/{remote_path}" if remote_path else self.base_path
            files = sftp.listdir(full_path)
            
            return files
            
        except Exception as e:
            self.logger.error(f"파일 목록 조회 실패: {e}")
            return []
            
        finally:
            if sftp:
                sftp.close()
            if transport:
                transport.close()