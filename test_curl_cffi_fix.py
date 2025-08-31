#!/usr/bin/env python3
"""
curl_cffi + yt-dlp 통합 테스트 스크립트
수정된 ImpersonateTarget 사용법 검증
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import yt_dlp
from yt_dlp.networking.impersonate import ImpersonateTarget
from core.video.processor.download_options import DownloadOptions
from core.video.processor.vimeo_cffi_auth import (
    get_vimeo_cffi_access_methods, 
    add_vimeo_cffi_authentication,
    test_vimeo_accessibility_cffi
)

def test_download_options():
    """DownloadOptions의 curl_cffi 옵션 테스트"""
    print("=== DownloadOptions curl_cffi 테스트 ===")
    
    try:
        # 문자열 형식으로 테스트
        opts = DownloadOptions.get_curl_cffi_options("test.%(ext)s", "chrome-110:windows-10")
        print("✅ get_curl_cffi_options with string: SUCCESS")
        print(f"   impersonate type: {type(opts['impersonate'])}")
        print(f"   impersonate value: {opts['impersonate']}")
        
        # yt-dlp로 실제 초기화 테스트
        ydl = yt_dlp.YoutubeDL(opts)
        print("✅ yt-dlp initialization: SUCCESS")
        
    except Exception as e:
        print(f"❌ DownloadOptions test failed: {e}")
        import traceback
        traceback.print_exc()

def test_vimeo_cffi_methods():
    """Vimeo curl_cffi 접근 방법들 테스트"""
    print("\n=== Vimeo curl_cffi 방법들 테스트 ===")
    
    try:
        methods = get_vimeo_cffi_access_methods()
        print(f"✅ 총 {len(methods)}개 방법 로드됨")
        
        for i, method in enumerate(methods):
            print(f"\n방법 {i+1}: {method['name']}")
            print(f"   impersonate type: {type(method['impersonate'])}")
            print(f"   impersonate value: {method['impersonate']}")
            
            try:
                # 기본 옵션으로 시작
                base_opts = {"quiet": True}
                # 방법별 옵션 적용
                final_opts = method['method'](base_opts)
                
                # yt-dlp 초기화 테스트
                ydl = yt_dlp.YoutubeDL(final_opts)
                print(f"   ✅ yt-dlp 초기화: SUCCESS")
                
            except Exception as e:
                print(f"   ❌ 실패: {e}")
                
    except Exception as e:
        print(f"❌ Vimeo methods test failed: {e}")
        import traceback
        traceback.print_exc()

def test_vimeo_authentication():
    """Vimeo 인증 함수 테스트"""
    print("\n=== Vimeo 인증 함수 테스트 ===")
    
    try:
        # 기본 옵션
        base_opts = {"quiet": True}
        
        # 문자열 impersonate로 테스트
        opts1 = add_vimeo_cffi_authentication(base_opts.copy(), "chrome-110:windows-10")
        print("✅ 문자열 impersonate: SUCCESS")
        print(f"   impersonate type: {type(opts1['impersonate'])}")
        
        # None으로 테스트 (기본값)
        opts2 = add_vimeo_cffi_authentication(base_opts.copy(), None)
        print("✅ None impersonate (기본값): SUCCESS")
        print(f"   impersonate type: {type(opts2['impersonate'])}")
        
        # ImpersonateTarget 직접 전달
        target = ImpersonateTarget('safari', '15.5', 'macos', '12')
        opts3 = add_vimeo_cffi_authentication(base_opts.copy(), target)
        print("✅ ImpersonateTarget 직접 전달: SUCCESS")
        print(f"   impersonate type: {type(opts3['impersonate'])}")
        
        # 모든 옵션으로 yt-dlp 초기화 테스트
        for i, opts in enumerate([opts1, opts2, opts3], 1):
            try:
                ydl = yt_dlp.YoutubeDL(opts)
                print(f"   ✅ 옵션 {i} yt-dlp 초기화: SUCCESS")
            except Exception as e:
                print(f"   ❌ 옵션 {i} 실패: {e}")
                
    except Exception as e:
        print(f"❌ Vimeo authentication test failed: {e}")
        import traceback
        traceback.print_exc()

def test_real_download():
    """실제 다운로드 테스트 (메타데이터만)"""
    print("\n=== 실제 다운로드 테스트 (메타데이터) ===")
    
    test_urls = [
        ("YouTube", "https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
        ("Vimeo", "https://vimeo.com/274860274")
    ]
    
    for platform, url in test_urls:
        print(f"\n{platform} 테스트: {url}")
        
        try:
            # curl_cffi 옵션 사용
            opts = DownloadOptions.get_curl_cffi_options("test.%(ext)s")
            # 다운로드 없이 메타데이터만
            opts['skip_download'] = True
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'Unknown')
                duration = info.get('duration', 0)
                print(f"   ✅ {platform} 메타데이터 추출 성공")
                print(f"   제목: {title}")
                print(f"   길이: {duration}초")
                
        except Exception as e:
            print(f"   ❌ {platform} 실패: {e}")

def test_accessibility():
    """Vimeo 접근성 테스트"""
    print("\n=== Vimeo 접근성 테스트 ===")
    
    test_url = "https://vimeo.com/274860274"
    
    try:
        result = test_vimeo_accessibility_cffi(test_url, "chrome-110:windows-10")
        print(f"URL: {test_url}")
        print(f"접근 가능: {result.get('accessible', False)}")
        print(f"상태 코드: {result.get('status_code', 'Unknown')}")
        print(f"Cloudflare 차단: {result.get('cloudflare_blocked', False)}")
        print(f"인증 필요: {result.get('requires_auth', False)}")
        
        if result.get('error'):
            print(f"오류: {result['error']}")
            
    except Exception as e:
        print(f"❌ 접근성 테스트 실패: {e}")

if __name__ == "__main__":
    print("curl_cffi + yt-dlp 통합 테스트 시작\n")
    
    # 각 테스트 실행
    test_download_options()
    test_vimeo_cffi_methods() 
    test_vimeo_authentication()
    test_real_download()
    test_accessibility()
    
    print("\n=== 테스트 완료 ===")