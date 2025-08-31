# core/video/processor/vimeo_auth.py
"""Vimeo 인증 및 비공개 영상 처리"""

import os
from typing import Optional, Dict, Any

def add_authentication_options(options: dict) -> dict:
    """Vimeo 인증 옵션 추가 - 쿠키 없이"""
    
    # 기본 헤더만 설정
    if 'http_headers' not in options:
        options['http_headers'] = {}
    
    # 쿠키/인증 관련 헤더 제거, 기본 헤더만 유지
    options['http_headers'].update({
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5'
    })
    
    # 기본 다운로드 옵션만
    options.update({
        'extract_flat': False,
        'ignoreerrors': True,  # 에러 무시
        'skip_unavailable_fragments': True,
        'socket_timeout': 60,
        'no_check_certificates': True
    })
    
    return options

def get_vimeo_access_methods() -> list:
    """Vimeo 접근 방법들 우선순위 순으로 반환 - Docker 환경 최적화"""
    from core.video.processor.vimeo_patch import add_vimeo_fix, get_vimeo_player_url, extract_vimeo_id
    
    return [
        {
            'name': 'Player API 직접 우회',
            'method': lambda options: add_docker_optimized_options(options)
        },
        {
            'name': '강화된 헤더 방식',
            'method': lambda options: add_enhanced_headers(options)
        },
        {
            'name': 'JSON 강제 추출',
            'method': lambda options: add_json_force(options)
        },
        {
            'name': '기본 스크래핑',
            'method': lambda options: add_basic_scraping(options)
        }
    ]

def add_docker_optimized_options(options: dict) -> dict:
    """Docker 환경 최적화 옵션 - 쿠키 없이"""
    from core.video.processor.vimeo_patch import add_vimeo_fix
    
    options = add_vimeo_fix(options)
    options.update({
        'no_check_certificates': True,
        'prefer_insecure': True,
        'socket_timeout': 90,
        'read_timeout': 90,
        'retries': 20,
        'fragment_retries': 20,
        'sleep_interval': 5,
        'ignoreerrors': True
    })
    return options

def add_enhanced_headers(options: dict) -> dict:
    """강화된 헤더 옵션 - 쿠키 없이"""
    from core.video.processor.vimeo_patch import add_vimeo_fix
    
    options = add_vimeo_fix(options)
    if 'http_headers' not in options:
        options['http_headers'] = {}
    
    # 쿠키 관련 헤더 제거, 기본 헤더만
    options['http_headers'].update({
        'DNT': '1',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache'
    })
    return options

def add_json_force(options: dict) -> dict:
    """JSON 응답 강제 - 쿠키 없이"""
    from core.video.processor.vimeo_patch import add_vimeo_fix
    
    options = add_vimeo_fix(options)
    options.update({
        'force_json': True,
        'dump_single_json': True,
        'simulate': False,
        'skip_download': False,
        'ignoreerrors': True
    })
    return options

def add_basic_scraping(options: dict) -> dict:
    """기본 스크래핑 방식 - 쿠키 없이"""
    from core.video.processor.vimeo_patch import add_vimeo_fix
    
    options = add_vimeo_fix(options)
    options.update({
        'extract_flat': False,
        'no_warnings': False,
        'ignoreerrors': True
    })
    return options

def check_video_accessibility(url: str) -> Dict[str, Any]:
    """비디오 접근 가능성 확인 - curl_cffi 사용"""
    try:
        import curl_cffi.requests as cffi_requests
        
        # Chrome 브라우저로 모방하여 요청
        response = cffi_requests.head(
            url, 
            timeout=30,
            impersonate="chrome-110:windows-10",
            headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'DNT': '1',
                'Upgrade-Insecure-Requests': '1'
            }
        )
        
        return {
            'accessible': response.status_code == 200,
            'status_code': response.status_code,
            'requires_auth': response.status_code in [401, 403],
            'is_private': 'private' in response.headers.get('x-vimeo-privacy', '').lower(),
            'cloudflare_bypassed': response.status_code != 503,
            'used_curl_cffi': True
        }
    except ImportError:
        # curl_cffi가 없으면 기본 방법 사용
        import requests
        try:
            response = requests.head(url, timeout=10)
            return {
                'accessible': response.status_code == 200,
                'status_code': response.status_code,
                'requires_auth': response.status_code in [401, 403],
                'is_private': 'private' in response.headers.get('x-vimeo-privacy', '').lower(),
                'used_curl_cffi': False
            }
        except Exception as e:
            return {
                'accessible': False,
                'error': str(e),
                'requires_auth': True,
                'used_curl_cffi': False
            }
    except Exception as e:
        return {
            'accessible': False,
            'error': str(e),
            'requires_auth': True,
            'used_curl_cffi': True
        }

def get_auth_error_message(status_code: int) -> str:
    """인증 오류에 따른 사용자 안내 메시지"""
    messages = {
        401: "🔒 비공개 영상입니다. Vimeo에 로그인한 브라우저의 쿠키가 필요합니다.",
        403: "🚫 접근이 금지된 영상입니다. 영상 소유자의 권한이 필요합니다.", 
        404: "❌ 영상을 찾을 수 없습니다. URL을 확인해주세요.",
        429: "⏱ 요청 한도 초과. 잠시 후 다시 시도해주세요."
    }
    return messages.get(status_code, f"❌ HTTP {status_code} 오류가 발생했습니다.")