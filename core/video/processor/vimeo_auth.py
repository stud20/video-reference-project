# core/video/processor/vimeo_auth.py
"""Vimeo 인증 및 비공개 영상 처리"""

import os
from typing import Optional, Dict, Any

def add_authentication_options(options: dict) -> dict:
    """Vimeo 인증 옵션 추가"""
    
    # 1. 브라우저 쿠키 사용 (가장 효과적)
    try:
        # Chrome 쿠키 우선 시도
        options['cookiesfrombrowser'] = ('chrome',)
    except:
        try:
            # Safari 쿠키 대안
            options['cookiesfrombrowser'] = ('safari',)
        except:
            # Firefox 쿠키 대안
            options['cookiesfrombrowser'] = ('firefox',)
    
    # 2. 쿠키 파일 경로 확인
    cookie_paths = [
        'cookies.txt',
        '/app/cookies.txt',
        './vimeo_cookies.txt',
        os.path.expanduser('~/Downloads/cookies.txt')
    ]
    
    for cookie_file in cookie_paths:
        if os.path.exists(cookie_file):
            options['cookiefile'] = cookie_file
            break
    
    # 3. 추가 인증 헤더
    if 'http_headers' not in options:
        options['http_headers'] = {}
    
    options['http_headers'].update({
        'Cookie': '',  # 필요시 수동 쿠키 추가
        'Authorization': '',  # 필요시 토큰 추가
    })
    
    # 4. 비공개 영상 처리 옵션
    options.update({
        'extract_flat': False,
        'ignoreerrors': False,
        'skip_unavailable_fragments': True,
        'socket_timeout': 60,
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
    """Docker 환경 최적화 옵션"""
    from core.video.processor.vimeo_patch import add_vimeo_fix
    
    options = add_vimeo_fix(options)
    options.update({
        'no_check_certificates': True,
        'prefer_insecure': True,
        'socket_timeout': 90,
        'read_timeout': 90,
        'retries': 20,
        'fragment_retries': 20,
        'sleep_interval': 5
    })
    return options

def add_enhanced_headers(options: dict) -> dict:
    """강화된 헤더 옵션"""
    from core.video.processor.vimeo_patch import add_vimeo_fix
    
    options = add_vimeo_fix(options)
    if 'http_headers' not in options:
        options['http_headers'] = {}
    
    # 더 강화된 헤더
    options['http_headers'].update({
        'DNT': '1',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="120"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"'
    })
    return options

def add_json_force(options: dict) -> dict:
    """JSON 응답 강제"""
    from core.video.processor.vimeo_patch import add_vimeo_fix
    
    options = add_vimeo_fix(options)
    options.update({
        'force_json': True,
        'dump_single_json': True,
        'simulate': False,
        'skip_download': False
    })
    return options

def add_basic_scraping(options: dict) -> dict:
    """기본 스크래핑 방식"""
    from core.video.processor.vimeo_patch import add_vimeo_fix
    
    options = add_vimeo_fix(options)
    options.update({
        'extract_flat': False,
        'no_warnings': False,
        'ignoreerrors': True
    })
    return options

def add_cookie_file(options: dict) -> dict:
    """쿠키 파일 사용"""
    cookie_paths = ['cookies.txt', '/app/cookies.txt', './vimeo_cookies.txt']
    
    for cookie_file in cookie_paths:
        if os.path.exists(cookie_file):
            options['cookiefile'] = cookie_file
            return options
    
    # 쿠키 파일이 없으면 기본 옵션 반환
    return options

def add_direct_access(options: dict) -> dict:
    """직접 접근 시도 (공개 영상용)"""
    options.update({
        'no_check_certificates': True,
        'prefer_insecure': False,
    })
    return options

def check_video_accessibility(url: str) -> Dict[str, Any]:
    """비디오 접근 가능성 확인"""
    import requests
    
    try:
        response = requests.head(url, timeout=10)
        return {
            'accessible': response.status_code == 200,
            'status_code': response.status_code,
            'requires_auth': response.status_code in [401, 403],
            'is_private': 'private' in response.headers.get('x-vimeo-privacy', '').lower()
        }
    except Exception as e:
        return {
            'accessible': False,
            'error': str(e),
            'requires_auth': True
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