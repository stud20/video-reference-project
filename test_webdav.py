# test_webdav.py
"""WebDAV 연결 및 업로드 테스트 스크립트"""

from src.storage.webdav_client import WebDAVStorage
from utils.logger import get_logger

logger = get_logger(__name__)

def test_webdav_connection():
    """WebDAV 연결 테스트"""
    print("🔧 WebDAV 연결 테스트 시작...")
    
    storage = WebDAVStorage()
    
    # 1. 연결 테스트
    if storage.test_connection():
        print("✅ WebDAV 연결 성공!")
    else:
        print("❌ WebDAV 연결 실패!")
        return False
    
    # 2. 루트 디렉토리 목록 확인
    print("\n📁 루트 디렉토리 목록:")
    try:
        files = storage.list_files("/")
        for f in files[:10]:  # 처음 10개만 표시
            print(f"  - {f}")
    except Exception as e:
        print(f"❌ 목록 조회 실패: {e}")
    
    # 3. 2025-session 폴더 확인/생성
    print("\n📁 2025-session 폴더 확인...")
    try:
        storage._ensure_remote_directory("2025-session")
        print("✅ 2025-session 폴더 준비 완료")
    except Exception as e:
        print(f"❌ 폴더 생성 실패: {e}")
    
    # 4. 테스트 파일 업로드
    print("\n📤 테스트 파일 업로드...")
    try:
        # 테스트 파일 생성
        import os
        os.makedirs("data/temp", exist_ok=True)
        test_file = "data/temp/test.txt"
        with open(test_file, "w") as f:
            f.write("WebDAV 업로드 테스트 파일입니다.")
        
        # 업로드
        remote_path = storage.upload_file(test_file, "2025-session/test/")
        print(f"✅ 테스트 파일 업로드 성공: {remote_path}")
        
        # 정리
        os.remove(test_file)
        
    except Exception as e:
        print(f"❌ 테스트 파일 업로드 실패: {e}")
        import traceback
        traceback.print_exc()
    
    return True

if __name__ == "__main__":
    test_webdav_connection()