# core/video/processor/download_options.py
"""yt-dlp 다운로드 옵션 설정 - macOS 재생 호환성 중심"""

import os
from typing import Union

try:
    from yt_dlp.networking.impersonate import ImpersonateTarget
    CURL_CFFI_AVAILABLE = True
except ImportError:
    ImpersonateTarget = None
    CURL_CFFI_AVAILABLE = False



class DownloadOptions:
    """다양한 품질 옵션 제공 - macOS 호환성 우선"""
    
    # macOS에서 재생 불가능한 코덱들
    NON_PLAYABLE_CODECS = {"vp9", "vp8", "av1", "vp09", "vp08", "vp10"}
    
    @staticmethod
    def get_curl_cffi_options(output_path: str, impersonate: str = "chrome-110:windows-10", subtitle_langs: list = None) -> dict:
        """curl_cffi를 사용한 브라우저 모방 옵션 - Cloudflare 우회 특화"""
        
        # impersonate 문자열을 ImpersonateTarget 객체로 변환
        if isinstance(impersonate, str):
            if ":" in impersonate:
                # "chrome-110:windows-10" 형식 파싱
                browser_part, os_part = impersonate.split(":", 1)
                if "-" in browser_part:
                    client, version = browser_part.split("-", 1)
                else:
                    client, version = browser_part, "110"
                
                if "-" in os_part:
                    os_name, os_version = os_part.split("-", 1) 
                else:
                    os_name, os_version = os_part, "10"
                    
                impersonate_target = ImpersonateTarget(client, version, os_name, os_version)
            else:
                # 단순 브라우저명인 경우 기본값 사용
                impersonate_target = ImpersonateTarget(impersonate, "110", "windows", "10")
        else:
            # 이미 ImpersonateTarget 객체인 경우
            impersonate_target = impersonate
        
        return {
            'outtmpl': output_path,
            
            # 고품질 우선 포맷 선택
            'format': (
                'best[height>=720][ext=mp4]/'  # 최소 720p MP4
                'bv*[vcodec^=avc1]+ba/'        # H.264 조합
                'best[ext=mp4]/'               # MP4 폴백
                'best'                         # 최종 폴백
            ),
            
            # curl_cffi 사용 설정 - ImpersonateTarget 객체만으로 충분
            'impersonate': impersonate_target if CURL_CFFI_AVAILABLE else None,
            
            # 브라우저 모방 헤더 (curl_cffi가 자동으로 설정하지만 추가 보강)
            'http_headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9,ko;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0'
            },
            
            # 연결 설정
            'socket_timeout': 60,
            'read_timeout': 60,
            'retries': 10,
            'fragment_retries': 10,
            'sleep_interval': 2,
            'max_sleep_interval': 8,
            
            # 지역 우회
            'geo_bypass': True,
            'geo_bypass_country': 'US',
            
            # SSL/TLS 설정
            'nocheckcertificate': True,
            'prefer_insecure': False,  # curl_cffi는 정상적인 TLS 사용
            
            # Vimeo OAuth 문제 해결
            'extractor_args': {
                'vimeo': {
                    'disable_android_api': ['true'],
                    'disable_ios_api': ['true'],
                    'force_json_api': ['true']
                }
            },
            
            # 디버그 설정
            'verbose': False,
            'quiet': True,
            'no_warnings': True
        }
    
    @staticmethod
    def get_aggressive_bypass_options(output_path: str, subtitle_langs: list = None) -> dict:
        """최강 우회 옵션 - curl_cffi 기본 사용"""
        # 기본적으로 curl_cffi 옵션을 사용
        return DownloadOptions.get_curl_cffi_options(output_path, "chrome-110:windows-10", subtitle_langs)
    
    
    
    @staticmethod
    def get_no_cookies_mp4_options(output_path: str, subtitle_langs: list = None) -> dict:
        """쿠키 없이 다운로드 시도 - 고품질 유지"""
        return {
            'outtmpl': output_path,
            'format': (
                'best[height>=720][ext=mp4]/'  # 최소 720p MP4
                'bv*[vcodec^=avc1]+ba/'        # H.264 조합
                'best[ext=mp4]/'               # MP4 폴백
                'best'                         # 최종 폴백
            ),
            'sleep_interval': 2,
            'max_sleep_interval': 8,
            'retries': 3,
            'fragment_retries': 3,
            'geo_bypass': True,
            'quiet': True,
            'no_warnings': True,
        }
    @staticmethod
    def get_best_mp4_options(output_path: str, subtitle_langs: list = None) -> dict:
        """최고 품질 MP4 다운로드 옵션 - 고화질 우선"""
        return {
            'outtmpl': output_path,
            
            # 포맷 선택 - 고화질 우선 (1080p 이상)
            'format': (
                'bv*[height>=1080][vcodec^=avc1]+ba[acodec^=mp4a]/'  # H.264 1080p+ 우선
                'best[height>=1080][ext=mp4]/'                      # 1080p+ MP4
                'bv*[vcodec^=avc1]+ba[acodec^=mp4a]/'              # H.264 AAC 조합
                'best[ext=mp4]/'                                    # MP4 폴백
                'best'                                              # 최종 폴백
            ),
            
            
            # 기본적인 설정만
            'sleep_interval': 1,
            'max_sleep_interval': 5,
            'retries': 3,
            'fragment_retries': 3,
            
            # 지역 우회
            'geo_bypass': True,
            
            # 후처리 - 간단하게
            'postprocessors': [
                {
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }
            ],
            
            # 병합 설정
            'merge_output_format': 'mp4',
            'prefer_ffmpeg': True,
            'keepvideo': False,
            
            # 자막/썸네일 비활성화 (안정성)
            'writesubtitles': False,
            'writeautomaticsub': False,
            'embedsubtitles': False,
            'writethumbnail': True,
            'embedthumbnail': True,
            
            # 기본 설정
            'quiet': True,
            'no_warnings': True,
        }
    
    @staticmethod
    def get_balanced_mp4_options(output_path: str, subtitle_langs: list = None) -> dict:
        """균형잡힌 품질 MP4 (720p, H.264 우선)"""
        return {
            'outtmpl': output_path,
            
            # 720p H.264 우선
            'format': (
                'bv*[height<=720][vcodec^=avc1]+ba[acodec^=mp4a]/'
                'best[height<=720][ext=mp4]/'
                'bv*[height<=720]+ba/best[height<=720]/best'
            ),
            
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
            
            'postprocessor_args': {
                'FFmpegVideoConvertor': [
                    '-c:v', 'libx264',
                    '-c:a', 'aac',
                    '-preset', 'faster',    # 더 빠른 인코딩
                    '-crf', '25',          # 약간 낮은 품질
                    '-movflags', '+faststart',
                ]
            },
            
            'merge_output_format': 'mp4',
            'prefer_ffmpeg': True,
            'keepvideo': False,
            
            'writesubtitles': False,  # 자막 비활성화
            'writeautomaticsub': False,
            # 'subtitleslangs': subtitle_langs or ['ko', 'en'],
            
            'retries': 3,
            'fragment_retries': 5,
            
            'quiet': True,
            'no_warnings': True,
        }
    
    @staticmethod
    def get_fast_mp4_options(output_path: str) -> dict:
        """빠른 다운로드 MP4 (H.264만, 재인코딩 최소화)"""
        return {
            'outtmpl': output_path,
            
            # H.264 MP4만 선택 (재인코딩 최소화)
            'format': 'bv*[vcodec^=avc1]+ba[acodec^=mp4a]/best[ext=mp4]',
            
            # 재인코딩 없이 컨테이너만 변경
            'postprocessors': [{
                'key': 'FFmpegVideoRemuxer',
                'container': 'mp4',
            }],
            
            'merge_output_format': 'mp4',
            'keepvideo': False,
            
            'writesubtitles': False,  # 자막 비활성화
            'writethumbnail': False,
            
            'retries': 3,
            'fragment_retries': 3,
            
            'quiet': True,
            'no_warnings': True,
        }
    
    @staticmethod
    def check_codec_compatibility(codec: str) -> bool:
        """macOS에서 재생 가능한 코덱인지 확인"""
        if not codec:
            return True
        return codec.lower() not in DownloadOptions.NON_PLAYABLE_CODECS
    
    @staticmethod
    def get_reencode_args() -> list:
        """재인코딩용 FFmpeg 인자"""
        return [
            '-c:v', 'libx264',      # H.264 코덱
            '-c:a', 'aac',          # AAC 오디오
            '-preset', 'fast',      # 빠른 인코딩
            '-crf', '23',          # 품질 설정
            '-movflags', '+faststart',  # 스트리밍 최적화
        ]