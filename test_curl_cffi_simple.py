#!/usr/bin/env python3
"""
간단한 curl_cffi + yt-dlp 테스트 스크립트
의존성 없이 독립 실행 가능
"""

import yt_dlp
from yt_dlp.networking.impersonate import ImpersonateTarget

def test_impersonate_targets():
    """지원되는 ImpersonateTarget들 테스트"""
    print("=== ImpersonateTarget 테스트 ===")
    
    # yt-dlp에서 지원하는 타겟들 (앞서 확인한 것들)
    supported_targets = [
        ImpersonateTarget('chrome', '110', 'windows', '10'),
        ImpersonateTarget('chrome', '107', 'windows', '10'),
        ImpersonateTarget('chrome', '104', 'windows', '10'),
        ImpersonateTarget('chrome', '101', 'windows', '10'),
        ImpersonateTarget('chrome', '100', 'windows', '10'),
        ImpersonateTarget('chrome', '99', 'windows', '10'),
        ImpersonateTarget('safari', '15.5', 'macos', '12'),
        ImpersonateTarget('safari', '15.3', 'macos', '11'),
        ImpersonateTarget('edge', '101', 'windows', '10'),
        ImpersonateTarget('edge', '99', 'windows', '10'),
        ImpersonateTarget('chrome', '99', 'android', '12')
    ]
    
    for target in supported_targets:
        try:
            opts = {
                'http_client': 'curl_cffi',
                'impersonate': target,
                'quiet': True
            }
            ydl = yt_dlp.YoutubeDL(opts)
            print(f"✅ {target}: SUCCESS")
        except Exception as e:
            print(f"❌ {target}: FAILED - {e}")

def test_youtube_with_curl_cffi():
    """YouTube URL을 curl_cffi로 테스트"""
    print("\n=== YouTube + curl_cffi 테스트 ===")
    
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    target = ImpersonateTarget('chrome', '110', 'windows', '10')
    
    try:
        opts = {
            'http_client': 'curl_cffi',
            'impersonate': target,
            'quiet': False,
            'verbose': True,
            'skip_download': True  # 메타데이터만
        }
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(test_url, download=False)
            
        print(f"✅ YouTube 메타데이터 추출 성공")
        print(f"   제목: {info.get('title', 'Unknown')}")
        print(f"   채널: {info.get('uploader', 'Unknown')}")
        print(f"   길이: {info.get('duration', 0)}초")
        print(f"   조회수: {info.get('view_count', 0):,}")
        
        return True
        
    except Exception as e:
        print(f"❌ YouTube 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_vimeo_with_curl_cffi():
    """Vimeo URL을 curl_cffi로 테스트"""
    print("\n=== Vimeo + curl_cffi 테스트 ===")
    
    test_url = "https://vimeo.com/274860274"  # 공개 영상
    target = ImpersonateTarget('chrome', '110', 'windows', '10')
    
    try:
        opts = {
            'http_client': 'curl_cffi',
            'impersonate': target,
            'quiet': False,
            'verbose': True,
            'skip_download': True,  # 메타데이터만
            
            # Vimeo 특화 설정
            'extractor_args': {
                'vimeo': {
                    'disable_android_api': ['true'],
                    'disable_ios_api': ['true'],
                    'force_json_api': ['true']
                }
            },
            
            # 추가 헤더
            'http_headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'DNT': '1',
                'Upgrade-Insecure-Requests': '1'
            }
        }
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(test_url, download=False)
            
        print(f"✅ Vimeo 메타데이터 추출 성공")
        print(f"   제목: {info.get('title', 'Unknown')}")
        print(f"   업로더: {info.get('uploader', 'Unknown')}")
        print(f"   길이: {info.get('duration', 0)}초")
        print(f"   조회수: {info.get('view_count', 0):,}")
        
        return True
        
    except Exception as e:
        print(f"❌ Vimeo 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_string_to_target_conversion():
    """문자열을 ImpersonateTarget으로 변환하는 로직 테스트"""
    print("\n=== 문자열 변환 로직 테스트 ===")
    
    test_cases = [
        "chrome-110:windows-10",
        "safari-15.5:macos-12", 
        "edge-101:windows-10",
        "chrome-99:windows-10",
        "chrome",
        "firefox"
    ]
    
    for test_str in test_cases:
        try:
            # 변환 로직 (download_options.py에서 가져온 것)
            if ":" in test_str:
                browser_part, os_part = test_str.split(":", 1)
                if "-" in browser_part:
                    client, version = browser_part.split("-", 1)
                else:
                    client, version = browser_part, "110"
                
                if "-" in os_part:
                    os_name, os_version = os_part.split("-", 1) 
                else:
                    os_name, os_version = os_part, "10"
                    
                target = ImpersonateTarget(client, version, os_name, os_version)
            else:
                target = ImpersonateTarget(test_str, "110", "windows", "10")
            
            print(f"✅ '{test_str}' -> {target}")
            
            # yt-dlp로 실제 테스트
            opts = {'http_client': 'curl_cffi', 'impersonate': target, 'quiet': True}
            ydl = yt_dlp.YoutubeDL(opts)
            print(f"   yt-dlp 초기화: SUCCESS")
            
        except Exception as e:
            print(f"❌ '{test_str}' 변환 실패: {e}")

def test_download_with_different_targets():
    """다양한 타겟으로 실제 다운로드 테스트"""
    print("\n=== 다양한 타겟 다운로드 테스트 ===")
    
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    targets_to_test = [
        ImpersonateTarget('chrome', '110', 'windows', '10'),
        ImpersonateTarget('safari', '15.5', 'macos', '12'),
        ImpersonateTarget('edge', '101', 'windows', '10')
    ]
    
    for target in targets_to_test:
        try:
            opts = {
                'http_client': 'curl_cffi',
                'impersonate': target,
                'quiet': True,
                'skip_download': True
            }
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(test_url, download=False)
                
            print(f"✅ {target}: 메타데이터 추출 성공")
            
        except Exception as e:
            print(f"❌ {target}: 실패 - {e}")

if __name__ == "__main__":
    print("curl_cffi + yt-dlp 수정사항 검증 테스트\n")
    
    test_impersonate_targets()
    test_string_to_target_conversion()
    
    youtube_success = test_youtube_with_curl_cffi()
    vimeo_success = test_vimeo_with_curl_cffi()
    
    test_download_with_different_targets()
    
    print(f"\n=== 최종 결과 ===")
    print(f"YouTube + curl_cffi: {'✅ SUCCESS' if youtube_success else '❌ FAILED'}")
    print(f"Vimeo + curl_cffi: {'✅ SUCCESS' if vimeo_success else '❌ FAILED'}")
    
    if youtube_success and vimeo_success:
        print("\n🎉 모든 테스트 통과! curl_cffi 통합이 성공적으로 수정되었습니다.")
    else:
        print("\n⚠️ 일부 테스트 실패. 추가 수정이 필요할 수 있습니다.")