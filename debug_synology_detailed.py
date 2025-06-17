# debug_synology_detailed.py
"""Synology File Station API 상세 디버깅"""

import requests
import os
from dotenv import load_dotenv
import urllib3

# SSL 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# .env 로드
load_dotenv()

class SynologyDebugger:
    def __init__(self):
        self.host = os.getenv("SYNOLOGY_HOST", "nas.greatminds.kr")
        self.port = int(os.getenv("SYNOLOGY_PORT", "5001"))
        self.username = os.getenv("SYNOLOGY_USER", "dav")
        self.password = os.getenv("SYNOLOGY_PASS", "dav123")
        self.base_url = f"https://{self.host}:{self.port}/webapi"
        self.session_id = None
        
    def login(self):
        """로그인"""
        print("🔐 로그인 시도...")
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
        print(f"로그인 응답: {data}")
        
        if data.get("success"):
            self.session_id = data["data"]["sid"]
            print(f"✅ 로그인 성공! SID: {self.session_id[:10]}...")
            return True
        return False
    
    def list_shared_folders(self):
        """공유 폴더 목록 확인"""
        print("\n📁 공유 폴더 목록 조회...")
        
        response = requests.get(
            f"{self.base_url}/entry.cgi",
            params={
                "api": "SYNO.FileStation.List",
                "version": "2",
                "method": "list_share",
                "_sid": self.session_id
            },
            verify=False
        )
        
        data = response.json()
        if data.get("success"):
            print("✅ 공유 폴더 목록:")
            for share in data["data"]["shares"]:
                print(f"   - {share['name']} (경로: {share['path']})")
                # 권한 정보도 출력
                if 'isdir' in share:
                    print(f"     디렉토리: {share['isdir']}")
                if 'additional' in share:
                    perms = share['additional'].get('perm', {})
                    print(f"     권한: 읽기={perms.get('read')}, 쓰기={perms.get('write')}")
        else:
            print(f"❌ 오류: {data}")
    
    def list_folder_contents(self, folder_path):
        """특정 폴더 내용 확인"""
        print(f"\n📂 폴더 내용 확인: {folder_path}")
        
        response = requests.get(
            f"{self.base_url}/entry.cgi",
            params={
                "api": "SYNO.FileStation.List",
                "version": "2",
                "method": "list",
                "folder_path": folder_path,
                "_sid": self.session_id
            },
            verify=False
        )
        
        data = response.json()
        if data.get("success"):
            files = data["data"]["files"]
            if files:
                print(f"✅ {folder_path} 내용:")
                for f in files[:10]:  # 처음 10개만
                    print(f"   - {f['name']} ({'폴더' if f['isdir'] else '파일'})")
            else:
                print(f"   (빈 폴더)")
        else:
            print(f"❌ 오류: {data}")
            if data.get('error', {}).get('code') == 408:
                print("   → 폴더가 존재하지 않습니다")
    
    def create_folder_test(self, parent_path, folder_name):
        """폴더 생성 테스트"""
        print(f"\n📁 폴더 생성 테스트: {parent_path}/{folder_name}")
        
        # 방법 1: create 메서드
        response = requests.get(
            f"{self.base_url}/entry.cgi",
            params={
                "api": "SYNO.FileStation.CreateFolder",
                "version": "2",
                "method": "create",
                "folder_path": parent_path,
                "name": folder_name,
                "force_parent": "false",
                "_sid": self.session_id
            },
            verify=False
        )
        
        data = response.json()
        if data.get("success"):
            print(f"✅ 폴더 생성 성공!")
        else:
            print(f"❌ 생성 실패: {data}")
            error_code = data.get('error', {}).get('code')
            if error_code == 119:
                print("   → 에러 119: 잘못된 매개변수 (경로가 잘못되었을 수 있음)")
            elif error_code == 118:
                print("   → 에러 118: 폴더가 이미 존재함")
    
    def test_upload_path(self):
        """업로드 경로 테스트"""
        print("\n🧪 업로드 경로 테스트")
        
        # 가능한 경로들 테스트
        test_paths = [
            "/dav/videoRef",
            "/videoRef",
            "/videoRef/2025-session",
            "videoRef",
            "videoRef/2025-session",
            "/shared/videoRef",
            "/volume1/videoRef",
        ]
        
        for path in test_paths:
            print(f"\n테스트 경로: {path}")
            self.list_folder_contents(path)
    
    def run_full_debug(self):
        """전체 디버깅 실행"""
        print("🔍 Synology File Station API 전체 디버깅\n")
        
        if not self.login():
            print("❌ 로그인 실패!")
            return
        
        # 1. 공유 폴더 목록
        self.list_shared_folders()
        
        # 2. 업로드 경로 테스트
        self.test_upload_path()
        
        # 3. 2025-session 폴더 생성 시도
        print("\n📁 2025-session 폴더 생성 시도")
        # videoRef가 공유 폴더라고 가정
        self.create_folder_test("/videoRef", "2025-session")
        self.create_folder_test("videoRef", "2025-session")
        
        print("\n✅ 디버깅 완료!")
        print("\n💡 권장사항:")
        print("1. 위에서 성공한 경로를 사용하세요")
        print("2. 공유 폴더 이름이 'videoRef'가 맞는지 확인하세요")
        print("3. 필요하면 DSM에서 직접 '2025-session' 폴더를 생성하세요")

if __name__ == "__main__":
    debugger = SynologyDebugger()
    debugger.run_full_debug()