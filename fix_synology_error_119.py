# fix_synology_error_119.py
"""Synology API 에러 119 해결을 위한 디버깅"""

import requests
import os
import json
from dotenv import load_dotenv
import urllib3

# SSL 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv()

class SynologyError119Fixer:
    def __init__(self):
        self.host = os.getenv("SYNOLOGY_HOST", "nas.greatminds.kr")
        self.port = int(os.getenv("SYNOLOGY_PORT", "5001"))
        self.username = os.getenv("SYNOLOGY_USER", "dav")
        self.password = os.getenv("SYNOLOGY_PASS", "dav123")
        self.base_url = f"https://{self.host}:{self.port}/webapi"
        self.session_id = None
        
    def login(self):
        """로그인"""
        print("🔐 로그인 중...")
        
        # API 정보 먼저 확인
        info_response = requests.get(
            f"{self.base_url}/query.cgi",
            params={
                "api": "SYNO.API.Info",
                "version": "1",
                "method": "query",
                "query": "SYNO.FileStation.Upload,SYNO.FileStation.List"
            },
            verify=False
        )
        
        print(f"API 정보: {json.dumps(info_response.json(), indent=2)}")
        
        # 로그인
        response = requests.get(
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
            verify=False
        )
        
        data = response.json()
        if data.get("success"):
            self.session_id = data["data"]["sid"]
            print(f"✅ 로그인 성공!")
            return True
        else:
            print(f"❌ 로그인 실패: {data}")
            return False
    
    def test_list_folder(self):
        """폴더 목록 조회로 경로 확인"""
        print("\n📁 폴더 목록 테스트")
        
        test_paths = [
            "/",           # 루트
            "/dav",        # dav 공유 폴더
            "/dav/videoRef",  # videoRef 폴더
        ]
        
        for path in test_paths:
            print(f"\n테스트 경로: {path}")
            response = requests.get(
                f"{self.base_url}/entry.cgi",
                params={
                    "api": "SYNO.FileStation.List",
                    "version": "2",
                    "method": "list",
                    "folder_path": path,
                    "_sid": self.session_id
                },
                verify=False
            )
            
            data = response.json()
            print(f"응답: {json.dumps(data, indent=2)}")
            
            if data.get("success"):
                print("✅ 성공!")
                files = data.get("data", {}).get("files", [])
                for f in files[:5]:
                    print(f"  - {f['path']}/{f['name']} ({'dir' if f['isdir'] else 'file'})")
    
    def test_upload_methods(self):
        """다양한 업로드 방법 테스트"""
        print("\n📤 업로드 방법 테스트")
        
        # 테스트 파일 생성
        test_file = "test_119.txt"
        with open(test_file, "w") as f:
            f.write("Error 119 test file")
        
        # 방법 1: dest_folder_path 사용
        print("\n1️⃣ dest_folder_path 매개변수 사용")
        with open(test_file, 'rb') as f:
            files = {'file': (test_file, f, 'text/plain')}
            
            response = requests.post(
                f"{self.base_url}/entry.cgi",
                data={
                    "api": "SYNO.FileStation.Upload",
                    "version": "2",
                    "method": "upload",
                    "dest_folder_path": "/dav/videoRef",  # path 대신 dest_folder_path
                    "create_parents": "false",
                    "overwrite": "true",
                    "_sid": self.session_id
                },
                files=files,
                verify=False
            )
            
            print(f"응답: {response.json()}")
        
        # 방법 2: 다른 버전 사용
        print("\n2️⃣ API 버전 1 사용")
        with open(test_file, 'rb') as f:
            files = {'file': (test_file, f, 'text/plain')}
            
            response = requests.post(
                f"{self.base_url}/entry.cgi",
                data={
                    "api": "SYNO.FileStation.Upload",
                    "version": "1",  # 버전 1
                    "method": "upload",
                    "dest_folder_path": "/dav/videoRef",
                    "overwrite": "true",
                    "_sid": self.session_id
                },
                files=files,
                verify=False
            )
            
            print(f"응답: {response.json()}")
        
        # 방법 3: multipart 명시
        print("\n3️⃣ Content-Type 명시")
        with open(test_file, 'rb') as f:
            files = {
                'file': ('test_119.txt', f, 'application/octet-stream')
            }
            
            # FormData 스타일
            data = {
                "api": "SYNO.FileStation.Upload",
                "version": "2",
                "method": "upload",
                "path": "/dav/videoRef",
                "_sid": self.session_id
            }
            
            response = requests.post(
                f"{self.base_url}/entry.cgi",
                data=data,
                files=files,
                verify=False
            )
            
            print(f"응답: {response.json()}")
        
        # 정리
        os.remove(test_file)
    
    def test_create_folder_then_upload(self):
        """폴더 생성 후 업로드 테스트"""
        print("\n📁 폴더 생성 후 업로드 테스트")
        
        # 1. 2025-session 폴더 생성
        print("폴더 생성 시도...")
        response = requests.get(
            f"{self.base_url}/entry.cgi",
            params={
                "api": "SYNO.FileStation.CreateFolder",
                "version": "2",
                "method": "create",
                "folder_path": "/dav/videoRef",
                "name": "2025-session-test",
                "_sid": self.session_id
            },
            verify=False
        )
        
        print(f"폴더 생성 응답: {response.json()}")
        
        # 2. 생성된 폴더에 업로드
        test_file = "upload_test.txt"
        with open(test_file, "w") as f:
            f.write("Upload after folder creation")
        
        with open(test_file, 'rb') as f:
            files = {'file': (test_file, f)}
            
            response = requests.post(
                f"{self.base_url}/entry.cgi",
                data={
                    "api": "SYNO.FileStation.Upload",
                    "version": "2",
                    "method": "upload",
                    "dest_folder_path": "/dav/videoRef/2025-session-test",
                    "_sid": self.session_id
                },
                files=files,
                verify=False
            )
            
            print(f"업로드 응답: {response.json()}")
        
        os.remove(test_file)
    
    def run_diagnosis(self):
        """전체 진단 실행"""
        print("🔍 Synology API 에러 119 진단\n")
        
        if not self.login():
            return
        
        # 1. 폴더 목록 확인
        self.test_list_folder()
        
        # 2. 다양한 업로드 방법 테스트
        self.test_upload_methods()
        
        # 3. 폴더 생성 후 업로드
        self.test_create_folder_then_upload()
        
        print("\n✅ 진단 완료!")
        print("\n💡 해결 방법:")
        print("1. 'path' 대신 'dest_folder_path' 매개변수 사용")
        print("2. API 버전을 1로 변경 시도")
        print("3. 폴더가 존재하는지 먼저 확인")
        print("4. create_parents를 'false'로 설정")

if __name__ == "__main__":
    fixer = SynologyError119Fixer()
    fixer.run_diagnosis()