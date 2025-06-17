# debug_webdav.py
"""WebDAV 연결 상세 디버깅"""

from webdav3.client import Client
import requests
from requests.auth import HTTPBasicAuth

def test_webdav_detailed():
    print("🔍 WebDAV 상세 테스트 시작...\n")
    
    # 설정값
    hostname = "https://nas.greatminds.kr:5006"
    username = "dav"
    password = "dav123"
    webdav_root = "/dav/videoRef/"
    
    # 1. 기본 HTTP 연결 테스트
    print("1️⃣ 기본 HTTP 연결 테스트")
    try:
        # SSL 검증 비활성화 옵션 추가
        response = requests.get(
            hostname + webdav_root,
            auth=HTTPBasicAuth(username, password),
            verify=False,  # SSL 인증서 검증 비활성화
            timeout=10
        )
        print(f"   상태 코드: {response.status_code}")
        print(f"   응답 헤더: {dict(response.headers)}")
        if response.status_code == 403:
            print("   ❌ 403 Forbidden - 권한 문제")
        elif response.status_code == 401:
            print("   ❌ 401 Unauthorized - 인증 실패")
        elif response.status_code == 200:
            print("   ✅ 연결 성공!")
    except Exception as e:
        print(f"   ❌ 연결 실패: {e}")
    
    print("\n2️⃣ WebDAV 클라이언트 테스트")
    
    # 다양한 경로 조합 시도
    test_paths = [
        "/dav/videoRef/",
        "/dav/",
        "/videoRef/",
        "/"
    ]
    
    for test_root in test_paths:
        print(f"\n   테스트 경로: {test_root}")
        try:
            options = {
                'webdav_hostname': hostname,
                'webdav_login': username,
                'webdav_password': password,
                'webdav_root': test_root,
                'verify': False  # SSL 검증 비활성화
            }
            
            client = Client(options)
            
            # 연결 테스트
            files = client.list("/")
            print(f"   ✅ 성공! 파일 목록: {files[:3]}...")  # 처음 3개만
            print(f"   → 이 경로를 사용하세요: {test_root}")
            break
            
        except Exception as e:
            error_msg = str(e)
            if "403" in error_msg:
                print(f"   ❌ 403 Forbidden - 이 경로에 접근 권한 없음")
            elif "404" in error_msg:
                print(f"   ❌ 404 Not Found - 경로가 존재하지 않음")
            elif "401" in error_msg:
                print(f"   ❌ 401 Unauthorized - 인증 실패")
            else:
                print(f"   ❌ 오류: {error_msg}")
    
    print("\n3️⃣ 대체 방법 제안")
    print("   다음을 시도해보세요:")
    print("   1. NAS 관리자에게 문의하여:")
    print("      - 올바른 WebDAV URL 확인")
    print("      - 사용자 권한 확인")
    print("      - 올바른 경로 확인")
    print("   2. 다른 WebDAV 클라이언트로 테스트:")
    print("      - Mac: Finder에서 'Go > Connect to Server' (Cmd+K)")
    print("      - Windows: 네트워크 드라이브 연결")
    print("   3. 임시로 로컬 저장소 사용")

if __name__ == "__main__":
    # SSL 경고 무시
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    test_webdav_detailed()