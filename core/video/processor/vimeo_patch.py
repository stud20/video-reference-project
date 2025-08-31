# core/video/processor/vimeo_patch.py
"""Vimeo OAuth 문제 해결을 위한 패치"""

def add_vimeo_fix(options: dict) -> dict:
    """모든 다운로드 옵션에 Vimeo OAuth 수정 추가"""
    if 'extractor_args' not in options:
        options['extractor_args'] = {}
    
    # 2025년 1월 기준 최신 해결책 - Docker/Linux 환경 최적화
    options['extractor_args']['vimeo'] = {
        'player_url': 'https://player.vimeo.com',
        'disable_android_api': ['true'],
        'disable_ios_api': ['true'],
        'force_json_api': ['true']  # JSON API 강제 사용
    }
    
    # Vimeo 전용 헤더 추가 (Docker 환경 최적화)
    if 'http_headers' not in options:
        options['http_headers'] = {}
    
    options['http_headers'].update({
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://vimeo.com/',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0'
    })
    
    # Docker/Linux 환경 최적화 옵션
    options.update({
        'geo_bypass': True,
        'nocheckcertificate': True,
        'sleep_interval': 3,  # Docker 환경에서 더 긴 간격
        'retries': 15,  # 재시도 횟수 대폭 증가
        'fragment_retries': 15,
        'socket_timeout': 60,
        'read_timeout': 60,
        'prefer_insecure': False,
        'force_json': True  # JSON 응답 강제
    })
    
    return options

def get_vimeo_player_url(video_id: str) -> str:
    """Vimeo 비디오 ID로 player URL 생성"""
    return f"https://player.vimeo.com/video/{video_id}"

def extract_vimeo_id(url: str) -> str:
    """Vimeo URL에서 비디오 ID 추출"""
    import re
    patterns = [
        r'vimeo\.com/(\d+)',
        r'player\.vimeo\.com/video/(\d+)',
        r'vimeo\.com/[^/]+/(\d+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None