# core/video/processor/vimeo_cffi_auth.py
"""Vimeo curl_cffi 기반 인증 및 Cloudflare 우회"""

import os
from typing import Optional, Dict, Any, List
import curl_cffi.requests as cffi_requests
from curl_cffi import requests as cffi
from yt_dlp.networking.impersonate import ImpersonateTarget


def get_vimeo_cffi_access_methods() -> List[Dict[str, Any]]:
    """Vimeo curl_cffi 접근 방법들 우선순위 순으로 반환"""
    return [
        {
            'name': 'Chrome 110 모방',
            'impersonate': ImpersonateTarget('chrome', '110', 'windows', '10'),
            'method': lambda options: add_cffi_chrome_options(options)
        },
        {
            'name': 'Safari 15.5 모방',
            'impersonate': ImpersonateTarget('safari', '15.5', 'macos', '12'),
            'method': lambda options: add_cffi_safari_options(options)
        },
        {
            'name': 'Edge 101 모방',
            'impersonate': ImpersonateTarget('edge', '101', 'windows', '10'),
            'method': lambda options: add_cffi_edge_options(options)
        },
        {
            'name': 'Chrome 99 모방 (Fallback)',
            'impersonate': ImpersonateTarget('chrome', '99', 'windows', '10'),
            'method': lambda options: add_cffi_chrome_fallback_options(options)
        }
    ]


def add_cffi_chrome_options(options: dict) -> dict:
    """Chrome 브라우저 모방 curl_cffi 옵션"""
    options.update({
        'http_client': 'curl_cffi',
        'impersonate': ImpersonateTarget('chrome', '110', 'windows', '10'),
        
        # Chrome 특화 헤더
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'Cache-Control': 'max-age=0'
        },
        
        # 연결 설정
        'socket_timeout': 90,
        'read_timeout': 90,
        'retries': 15,
        'fragment_retries': 15,
        'sleep_interval': 3,
        'max_sleep_interval': 12,
        
        # TLS/SSL 설정
        'nocheckcertificate': False,  # curl_cffi는 정상 TLS 사용
        'prefer_insecure': False,
        
        # Cloudflare 우회 설정
        'geo_bypass': True,
        'geo_bypass_country': 'US'
    })
    
    return options


def add_cffi_safari_options(options: dict) -> dict:
    """Safari 브라우저 모방 curl_cffi 옵션"""
    options.update({
        'http_client': 'curl_cffi',
        'impersonate': ImpersonateTarget('safari', '15.5', 'macos', '12'),
        
        # Safari 특화 헤더
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        },
        
        # 연결 설정 (Safari는 좀 더 보수적)
        'socket_timeout': 60,
        'read_timeout': 60,
        'retries': 10,
        'fragment_retries': 10,
        'sleep_interval': 4,
        'max_sleep_interval': 15,
        
        'nocheckcertificate': False,
        'prefer_insecure': False,
        'geo_bypass': True,
        'geo_bypass_country': 'US'
    })
    
    return options


def add_cffi_edge_options(options: dict) -> dict:
    """Edge 브라우저 모방 curl_cffi 옵션"""
    options.update({
        'http_client': 'curl_cffi',
        'impersonate': ImpersonateTarget('edge', '101', 'windows', '10'),
        
        # Edge 특화 헤더
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36 Edg/101.0.1210.53',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Upgrade-Insecure-Requests': '1',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="101", "Microsoft Edge";v="101"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        },
        
        # 연결 설정
        'socket_timeout': 75,
        'read_timeout': 75,
        'retries': 12,
        'fragment_retries': 12,
        'sleep_interval': 2,
        'max_sleep_interval': 10,
        
        'nocheckcertificate': False,
        'prefer_insecure': False,
        'geo_bypass': True,
        'geo_bypass_country': 'US'
    })
    
    return options


def add_cffi_chrome_fallback_options(options: dict) -> dict:
    """Chrome 110 폴백 옵션 (더 안정적인 버전)"""
    options.update({
        'http_client': 'curl_cffi',
        'impersonate': ImpersonateTarget('chrome', '99', 'windows', '10'),
        
        # 더 기본적인 헤더
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        },
        
        # 보수적인 연결 설정
        'socket_timeout': 120,
        'read_timeout': 120,
        'retries': 20,
        'fragment_retries': 20,
        'sleep_interval': 5,
        'max_sleep_interval': 20,
        
        'nocheckcertificate': True,  # 폴백에서는 더 관대하게
        'prefer_insecure': False,
        'geo_bypass': True,
        'geo_bypass_country': 'US',
        
        # 추가 안정성 옵션
        'ignore_no_formats_error': True,
        'ignoreerrors': True
    })
    
    return options


def test_vimeo_accessibility_cffi(url: str, impersonate: str = "chrome-110:windows-10") -> Dict[str, Any]:
    """curl_cffi를 사용하여 Vimeo 접근성 테스트"""
    try:
        # curl_cffi로 직접 요청 테스트
        session = cffi.Session(impersonate=impersonate)
        
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'DNT': '1',
            'Upgrade-Insecure-Requests': '1'
        }
        
        response = session.get(url, headers=headers, timeout=30)
        
        # 응답 분석
        result = {
            'accessible': response.status_code == 200,
            'status_code': response.status_code,
            'cloudflare_blocked': 'Cloudflare' in response.text and 'challenge' in response.text.lower(),
            'requires_auth': response.status_code in [401, 403],
            'is_private': 'private' in response.text.lower() or 'password' in response.text.lower(),
            'impersonate_used': impersonate,
            'content_length': len(response.text),
            'response_headers': dict(response.headers)
        }
        
        # 성공적인 응답인 경우 추가 분석
        if response.status_code == 200:
            if 'player.vimeo.com' in response.text or 'config' in response.text:
                result['has_player_config'] = True
            if 'video' in response.text.lower():
                result['has_video_info'] = True
        
        session.close()
        return result
        
    except Exception as e:
        return {
            'accessible': False,
            'error': str(e),
            'impersonate_used': impersonate,
            'requires_auth': True
        }


def get_cffi_error_message(status_code: int, error_details: Dict[str, Any] = None) -> str:
    """curl_cffi 기반 오류 메시지 생성"""
    base_messages = {
        401: "🔒 비공개 영상입니다. 인증이 필요합니다.",
        403: "🚫 접근이 금지된 영상입니다. 영상 소유자의 권한이 필요합니다.", 
        404: "❌ 영상을 찾을 수 없습니다. URL을 확인해주세요.",
        429: "⏱ 요청 한도 초과. 잠시 후 다시 시도해주세요.",
        503: "🛡 Cloudflare 보호가 활성화되어 있습니다."
    }
    
    message = base_messages.get(status_code, f"❌ HTTP {status_code} 오류가 발생했습니다.")
    
    # curl_cffi 관련 추가 정보
    if error_details:
        if error_details.get('cloudflare_blocked'):
            message += " (Cloudflare 차단 감지됨 - 다른 브라우저 모방 시도 권장)"
        if error_details.get('impersonate_used'):
            message += f" (사용된 모방: {error_details['impersonate_used']})"
    
    return message


def add_vimeo_cffi_authentication(options: dict, impersonate = None) -> dict:
    """Vimeo용 curl_cffi 인증 옵션 추가 (통합 함수)"""
    
    # 기본 impersonate 설정 (ImpersonateTarget 객체)
    if impersonate is None:
        impersonate = ImpersonateTarget('chrome', '110', 'windows', '10')
    elif isinstance(impersonate, str):
        # 문자열인 경우 ImpersonateTarget으로 변환
        if ":" in impersonate:
            browser_part, os_part = impersonate.split(":", 1)
            if "-" in browser_part:
                client, version = browser_part.split("-", 1)
            else:
                client, version = browser_part, "110"
            
            if "-" in os_part:
                os_name, os_version = os_part.split("-", 1)
            else:
                os_name, os_version = os_part, "10"
                
            impersonate = ImpersonateTarget(client, version, os_name, os_version)
        else:
            impersonate = ImpersonateTarget(impersonate, "110", "windows", "10")
    
    # 기본 curl_cffi 설정
    options['http_client'] = 'curl_cffi'
    options['impersonate'] = impersonate
    
    # Vimeo 특화 extractor 설정
    if 'extractor_args' not in options:
        options['extractor_args'] = {}
    
    options['extractor_args']['vimeo'] = {
        'disable_android_api': ['true'],
        'disable_ios_api': ['true'],
        'force_json_api': ['true'],
        'player_url': 'https://player.vimeo.com'
    }
    
    # 브라우저별 세부 설정 적용
    client_name = impersonate.client if hasattr(impersonate, 'client') else 'chrome'
    if client_name == 'chrome':
        options = add_cffi_chrome_options(options)
    elif client_name == 'safari':
        options = add_cffi_safari_options(options)
    elif client_name == 'edge':
        options = add_cffi_edge_options(options)
    else:
        # 기본값으로 Chrome 사용
        options = add_cffi_chrome_options(options)
    
    # 공통 Cloudflare 우회 설정
    options.update({
        'quiet': True,
        'no_warnings': True,
        'skip_unavailable_fragments': True,
        'ignore_no_formats_error': True
    })
    
    return options