# core/video/processor/vimeo_patch.py
"""Vimeo OAuth 문제 해결을 위한 패치"""

def add_vimeo_fix(options: dict) -> dict:
    """모든 다운로드 옵션에 Vimeo OAuth 수정 추가"""
    if 'extractor_args' not in options:
        options['extractor_args'] = {}
    
    options['extractor_args']['vimeo'] = {
        'disable_android_api': ['true']
    }
    
    # Vimeo 전용 헤더 추가
    if 'http_headers' not in options:
        options['http_headers'] = {}
    
    options['http_headers'].update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://vimeo.com/'
    })
    
    return options