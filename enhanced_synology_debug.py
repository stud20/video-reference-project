# enhanced_synology_debug.py
"""Synology API 통합 테스트 및 디버깅 스크립트"""

import requests
import os
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import urllib3

# SSL 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# .env 로드
load_dotenv()

class EnhancedSynologyDebugger:
    def __init__(self):
        self.host = os.getenv("SYNOLOGY_HOST", "nas.greatminds.kr")
        self.port = int(os.getenv("SYNOLOGY_PORT", "5001"))
        self.username = os.getenv("SYNOLOGY_USER", "ysk")
        self.password = os.getenv("SYNOLOGY_PASS", "qy1KG5cG3d!")
        self.base_url = f"https://{self.host}:{self.port}/webapi"
        self.session_id = None
        self.api_info = {}
        
    def discover_apis(self):
        """사용 가능한 API 목록 확인"""
        print("🔍 사용 가능한 API 탐색...")
        response = requests.get(
            f"{self.base_url}/query.cgi",
            params={
                "api": "SYNO.API.Info",
                "version": "1",
                "method": "query",
                "query": "all"
            },
            verify=False
        )
        
        data = response.json()
        if data.get("success"):
            self.api_info = data["data"]
            print("✅ 주요 API 목록:")
            
            # 파일 관련 API만 필터링
            file_apis = {k: v for k, v in self.api_info.items() if 'File' in k or 'Upload' in k}
            for api_name, info in sorted(file_apis.items()):
                print(f"   - {api_name}: v{info['minVersion']}-{info['maxVersion']} ({info['path']})")
        else:
            print(f"❌ API 탐색 실패: {data}")
    
    def login(self):
        """향상된 로그인 (다양한 버전 시도)"""
        print("\n🔐 로그인 시도...")
        
        # 다양한 API 버전 시도
        versions = ["6", "3", "2", "1"]
        
        for version in versions:
            print(f"   API v{version} 시도...", end="")
            response = requests.get(
                f"{self.base_url}/auth.cgi",
                params={
                    "api": "SYNO.API.Auth",
                    "version": version,
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
                print(f" ✅ 성공! (SID: {self.session_id[:10]}...)")
                return True
            else:
                print(f" ❌ 실패 (에러: {data.get('error', {}).get('code')})")
        
        return False
    
    def test_file_upload_methods(self):
        """다양한 업로드 방법 테스트"""
        print("\n📤 파일 업로드 방법 테스트")
        
        # 1. Upload API 확인
        print("\n1️⃣ Upload API 테스트")
        response = requests.post(
            f"{self.base_url}/entry.cgi",
            data={
                "api": "SYNO.FileStation.Upload",
                "version": "2",
                "method": "upload",
                "path": "/videoRef",
                "_sid": self.session_id
            },
            files={
                "file": ("test.txt", b"Hello Synology!", "text/plain")
            },
            verify=False
        )
        print(f"   Upload API 응답: {response.json()}")
        
        # 2. Create + Write 방식
        print("\n2️⃣ Create + Write 방식 테스트")
        # 파일 생성
        create_response = requests.get(
            f"{self.base_url}/entry.cgi",
            params={
                "api": "SYNO.FileStation.Create",
                "version": "2",
                "method": "create",
                "folder_path": "/videoRef",
                "name": "test_create.txt",
                "overwrite": "true",
                "_sid": self.session_id
            },
            verify=False
        )
        print(f"   Create 응답: {create_response.json()}")
    
    def test_folder_operations(self):
        """폴더 작업 테스트"""
        print("\n📁 폴더 작업 테스트")
        
        # 공유 폴더 목록
        print("\n공유 폴더 목록:")
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
            shares = data["data"]["shares"]
            video_ref_found = False
            
            for share in shares:
                print(f"   - {share['name']} (경로: {share['path']})")
                if share['name'] == 'videoRef':
                    video_ref_found = True
                    
                    # 권한 확인
                    if 'additional' in share and 'perm' in share['additional']:
                        perms = share['additional']['perm']
                        print(f"     권한: 읽기={perms.get('read')}, 쓰기={perms.get('write')}")
            
            if not video_ref_found:
                print("\n⚠️  'videoRef' 공유 폴더를 찾을 수 없습니다!")
                print("   'videoRef'는 'dav' 공유 폴더 내의 하위 폴더입니다.")
                print("   '/dav/videoRef' 경로를 사용하세요.")
    
    def test_sftp_connection(self):
        """SFTP 연결 테스트 (현재 사용 중)"""
        print("\n🔌 SFTP 연결 테스트")
        try:
            import paramiko
            
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            ssh.connect(
                hostname=self.host,
                port=22,
                username=self.username,
                password=self.password
            )
            
            sftp = ssh.open_sftp()
            print("✅ SFTP 연결 성공!")
            
            # 디렉토리 목록
            print("\nSFTP 루트 디렉토리:")
            for item in sftp.listdir():
                print(f"   - {item}")
            
            # dav 폴더 접근
            try:
                sftp.chdir('dav')
                print("\n✅ dav 폴더 접근 가능!")
                print("dav 폴더 내용:")
                for item in sftp.listdir():
                    print(f"   - {item}")
                
                # videoRef 폴더 확인
                try:
                    sftp.chdir('videoRef')
                    print("\n✅ videoRef 폴더 접근 가능!")
                    print("현재 경로:", sftp.getcwd())
                    print("videoRef 폴더 내용:")
                    for item in sftp.listdir()[:10]:  # 처음 10개만
                        print(f"   - {item}")
                except:
                    print("\n❌ videoRef 폴더 접근 불가")
                    print("💡 dav 폴더 내에 videoRef 폴더를 생성하세요")
            except:
                print("\n❌ dav 폴더 접근 불가")
            
            sftp.close()
            ssh.close()
            
        except ImportError:
            print("❌ paramiko 설치 필요: pip install paramiko")
        except Exception as e:
            print(f"❌ SFTP 연결 실패: {e}")
    
    def suggest_storage_solution(self):
        """최적 스토리지 솔루션 제안"""
        print("\n💡 추천 스토리지 솔루션")
        print("\n현재 상황을 고려한 추천:")
        
        print("\n1. **SFTP (현재 사용 중) - 안정적**")
        print("   ✅ 장점: 표준 프로토콜, 안정적, 대용량 파일 처리 우수")
        print("   ❌ 단점: 메타데이터 관리 별도 필요")
        
        print("\n2. **Synology Drive API - 추천**")
        print("   ✅ 장점: 버전관리, 동기화, 팀 협업 기능")
        print("   ❌ 단점: 추가 패키지 설치 필요")
        print("   설치: DSM > 패키지 센터 > Synology Drive Server")
        
        print("\n3. **S3 Compatible (MinIO) - 확장성**")
        print("   ✅ 장점: AWS S3 호환, boto3 사용 가능")
        print("   ❌ 단점: 추가 설정 필요")
        
        print("\n4. **하이브리드 방식 - 최적**")
        print("   - 파일 저장: SFTP (현재 그대로)")
        print("   - 메타데이터: MariaDB/PostgreSQL")
        print("   - 썸네일: File Station API")
        print("   - 검색: Elasticsearch (선택사항)")
    
    def run_complete_test(self):
        """전체 테스트 실행"""
        print("="*50)
        print("🚀 Synology 스토리지 통합 테스트")
        print("="*50)
        
        # 1. API 탐색
        self.discover_apis()
        
        # 2. 로그인
        if not self.login():
            print("\n❌ 로그인 실패! 자격 증명을 확인하세요.")
            return
        
        # 3. 폴더 작업
        self.test_folder_operations()
        
        # 4. 업로드 방법 테스트
        self.test_file_upload_methods()
        
        # 5. SFTP 테스트
        self.test_sftp_connection()
        
        # 6. 솔루션 제안
        self.suggest_storage_solution()
        
        print("\n="*50)
        print("✅ 테스트 완료!")
        print("="*50)

if __name__ == "__main__":
    debugger = EnhancedSynologyDebugger()
    debugger.run_complete_test()