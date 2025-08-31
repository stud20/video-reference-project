# core/video/processor/vimeo_patch.py
"""Vimeo OAuth 문제 해결을 위한 패치"""

def add_vimeo_fix(options: dict) -> dict:
    """모든 다운로드 옵션에 Vimeo OAuth 수정 추가"""
    if 'extractor_args' not in options:
        options['extractor_args'] = {}
    
    # 2025년 1월 기준 최신 해결책
    options['extractor_args']['vimeo'] = {
        'api_url': 'https://player.vimeo.com/video/',  # player API 사용
        'player_url': 'https://player.vimeo.com',
        'disable_android_api': ['true'],
        'disable_ios_api': ['true']  # iOS API도 비활성화
    }
    
    # Vimeo 전용 헤더 추가 (더 강화)
    if 'http_headers' not in options:
        options['http_headers'] = {}
    
    options['http_headers'].update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://vimeo.com/',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })
    
    # 추가 안정성 옵션
    options.update({
        'geo_bypass': True,
        'nocheckcertificate': True,
        'sleep_interval': 2,  # 요청 간격 증가
        'retries': 10,  # 재시도 횟수 증가
        'fragment_retries': 10
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