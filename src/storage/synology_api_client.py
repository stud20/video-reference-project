# src/storage/synology_api_client.py
"""Synology File Station API를 사용한 파일 업로드"""

import requests
import os
from typing import Dict, Optional
from config.settings import Settings
from utils.logger import get_logger
import urllib3

# SSL 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SynologyFileStation:
    """Synology File Station API 클라이언트"""
    
    def __init__(self, host: str = None, port: int = 5001, username: str = None, password: str = None):
        self.logger = get_logger(__name__)
        self.settings = Settings()
        
        # 설정값 (.env에서 읽거나 직접 지정)
        self.host = host or os.getenv("SYNOLOGY_HOST", "nas.greatminds.kr")
        self.port = port or int(os.getenv("SYNOLOGY_PORT", "5001"))
        self.username = username or os.getenv("SYNOLOGY_USER", "dav")
        self.password = password or os.getenv("SYNOLOGY_PASS", "dav123")
        
        # API URLs
        self.base_url = f"https://{self.host}:{self.port}/webapi"
        self.session_id = None
        
        # SSL 검증 비활성화 (자체 서명 인증서인 경우)
        self.verify_ssl = False
        
    def login(self) -> bool:
        """Synology DSM에 로그인"""
        try:
            # 1. API 정보 가져오기
            response = requests.get(
                f"{self.base_url}/query.cgi",
                params={
                    "api": "SYNO.API.Info",
                    "version": "1",
                    "method": "query",
                    "query": "SYNO.API.Auth,SYNO.FileStation.Upload"
                },
                verify=self.verify_ssl
            )
            
            # 2. 로그인
            login_response = requests.get(
                f"{self.base_url}/auth.cgi",
                params={
                    "api": "SYNO.API.Auth",
                    "version": "3",
                    "method": "login",
                    "account": self.username,
                    "passwd": self.password,
                    "session": "FileStation",
                    "format": "sid"
                },
                verify=self.verify_ssl
            )
            
            data = login_response.json()
            if data.get("success"):
                self.session_id = data["data"]["sid"]
                self.logger.info("✅ Synology 로그인 성공")
                return True
            else:
                self.logger.error(f"❌ 로그인 실패: {data}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 로그인 오류: {e}")
            return False
    
    def upload_file(self, local_path: str, remote_folder: str = "2025-session") -> str:
        """파일을 File Station으로 업로드"""
        if not self.session_id:
            if not self.login():
                raise Exception("로그인 실패")
        
        try:
            # 경로 정리 - dav가 공유 폴더, videoRef가 하위 폴더
            if not remote_folder.startswith("/"):
                # /dav/videoRef/2025-session/세션ID 형태로 만들기
                remote_folder = f"/dav/videoRef/{remote_folder}"
            
            self.logger.info(f"📁 업로드 경로: {remote_folder}")
            
            # 원격 폴더 생성 (없으면)
            # 먼저 /dav/videoRef가 있는지 확인하고 2025-session 폴더 생성
            self.create_folder_recursive(remote_folder)
            
            # 파일 업로드
            with open(local_path, 'rb') as f:
                files = {
                    'file': (os.path.basename(local_path), f, 'application/octet-stream')
                }
                
                data = {
                    "api": "SYNO.FileStation.Upload",
                    "version": "2",
                    "method": "upload",
                    "path": remote_folder,
                    "create_parents": "true",
                    "overwrite": "true",
                    "_sid": self.session_id
                }
                
                response = requests.post(
                    f"{self.base_url}/entry.cgi",
                    data=data,
                    files=files,
                    verify=self.verify_ssl
                )
                
                result = response.json()
                if result.get("success"):
                    uploaded_path = f"{remote_folder}/{os.path.basename(local_path)}"
                    self.logger.info(f"✅ 업로드 성공: {uploaded_path}")
                    return uploaded_path
                else:
                    error_msg = f"업로드 실패: {result}"
                    self.logger.error(f"❌ {error_msg}")
                    raise Exception(error_msg)
                    
        except Exception as e:
            self.logger.error(f"❌ 업로드 오류: {e}")
            raise
    
    def create_folder_recursive(self, full_path: str):
        """경로를 재귀적으로 생성"""
        # /dav/videoRef/2025-session/세션ID 같은 경로를 단계별로 생성
        parts = full_path.strip('/').split('/')
        current_path = ""
        
        for i, part in enumerate(parts):
            if i == 0:
                # 첫 번째는 공유 폴더 (dav)이므로 이미 존재
                current_path = f"/{part}"
                continue
            
            parent_path = current_path
            current_path = f"{current_path}/{part}"
            
            # 폴더 생성 시도
            if not self.create_folder_single(parent_path, part):
                self.logger.warning(f"폴더 생성 실패 또는 이미 존재: {current_path}")
    
    def create_folder_single(self, parent_path: str, folder_name: str) -> bool:
        """단일 폴더 생성"""
        try:
            self.logger.info(f"📁 폴더 생성 시도: {parent_path}/{folder_name}")
            
            params = {
                "api": "SYNO.FileStation.CreateFolder",
                "version": "2",
                "method": "create",
                "folder_path": parent_path,
                "name": folder_name,
                "force_parent": "false",
                "_sid": self.session_id
            }
            
            response = requests.get(
                f"{self.base_url}/entry.cgi",
                params=params,
                verify=self.verify_ssl
            )
            
            result = response.json()
            if result.get("success"):
                self.logger.info(f"✅ 폴더 생성 성공: {parent_path}/{folder_name}")
                return True
            else:
                error_code = result.get('error', {}).get('code')
                if error_code == 118:  # 이미 존재
                    self.logger.info(f"📁 폴더 이미 존재: {parent_path}/{folder_name}")
                    return True
                else:
                    self.logger.error(f"❌ 폴더 생성 실패: {result}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"폴더 생성 오류: {e}")
            return False
    
    def create_folder(self, folder_path: str) -> bool:
        """폴더 생성"""
        try:
            # 경로를 부모와 폴더명으로 분리
            if folder_path.endswith('/'):
                folder_path = folder_path.rstrip('/')
            
            parent_path = os.path.dirname(folder_path)
            folder_name = os.path.basename(folder_path)
            
            # 부모 경로가 비어있으면 루트
            if not parent_path:
                parent_path = "/"
            
            self.logger.info(f"📁 폴더 생성 시도: {parent_path} / {folder_name}")
            
            params = {
                "api": "SYNO.FileStation.CreateFolder",
                "version": "2",
                "method": "create",
                "folder_path": parent_path,
                "name": folder_name,
                "force_parent": "false",  # 부모 폴더는 이미 존재해야 함
                "_sid": self.session_id
            }
            
            response = requests.get(
                f"{self.base_url}/entry.cgi",
                params=params,
                verify=self.verify_ssl
            )
            
            result = response.json()
            if result.get("success"):
                self.logger.info(f"✅ 폴더 생성 성공: {folder_path}")
                return True
            else:
                error_code = result.get('error', {}).get('code')
                if error_code == 118:  # 이미 존재
                    self.logger.info(f"📁 폴더 이미 존재: {folder_path}")
                    return True
                else:
                    self.logger.error(f"❌ 폴더 생성 실패: {result}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"폴더 생성 오류: {e}")
            return False
    
    def logout(self):
        """로그아웃"""
        if self.session_id:
            try:
                requests.get(
                    f"{self.base_url}/auth.cgi",
                    params={
                        "api": "SYNO.API.Auth",
                        "version": "1",
                        "method": "logout",
                        "session": "FileStation",
                        "_sid": self.session_id
                    },
                    verify=self.verify_ssl
                )
            except:
                pass