# core/video/processor/download_options.py
"""yt-dlp 다운로드 옵션 설정 - macOS 재생 호환성 중심"""

import os



class DownloadOptions:
    """다양한 품질 옵션 제공 - macOS 호환성 우선"""
    
    # macOS에서 재생 불가능한 코덱들
    NON_PLAYABLE_CODECS = {"vp9", "vp8", "av1", "vp09", "vp08", "vp10"}
    
    @staticmethod
    def get_aggressive_bypass_options(output_path: str, subtitle_langs: list = None) -> dict:
        """최강 우회 옵션 - 고품질 유지하면서 안정적인 접근"""
        return {
            'outtmpl': output_path,
            
            # 고품질 우선 포맷 선택
            'format': (
                'best[height>=720][ext=mp4]/'  # 최소 720p MP4
                'bv*[vcodec^=avc1]+ba/'        # H.264 조합
                'best[ext=mp4]/'               # MP4 폴백
                'best'                         # 최종 폴백
            ),
            
            # 기본 User-Agent
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            
            # 적당한 요청 간격
            'sleep_interval': 3,
            'max_sleep_interval': 10,
            
            # 적당한 재시도
            'retries': 5,
            'fragment_retries': 5,
            
            # 지역 우회만
            'geo_bypass': True,
            
            # 기본 설정만
            'no_warnings': False,
            'ignoreerrors': False,
        }
    
    @staticmethod
    def get_cookies_file_mp4_options(output_path: str, subtitle_langs: list = None) -> dict:
        """쿠키 파일 사용 옵션: cookies.txt 파일 사용"""
        options = DownloadOptions.get_best_mp4_options(output_path, subtitle_langs)
        
        # 브라우저 쿠키 옵션 제거
        if 'cookiesfrombrowser' in options:
            del options['cookiesfrombrowser']
        
        # 쿠키 파일 설정 - 프로젝트 루트부터 확인
        import os
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        cookie_paths = [
            os.path.join(project_root, 'cookies.txt'),  # 프로젝트 루트
            '/app/video-reference-project/cookies.txt',  # Docker 환경 정확한 경로
            'cookies.txt',  # 현재 디렉토리
            '/app/cookies.txt',  # Docker 환경
            './cookies.txt'  # 상대 경로
        ]
        cookie_file = None
        
        for path in cookie_paths:
            if os.path.exists(path):
                cookie_file = path
                break
                
        if cookie_file:
            options['cookiefile'] = cookie_file
            print(f"🍪 쿠키 파일 사용: {cookie_file}")
        else:
            # 파일이 없으면 기본값 사용
            options['cookiefile'] = 'cookies.txt'
            print("⚠️ 쿠키 파일을 찾을 수 없어 기본값 사용")
        
        return options
    
    @staticmethod
    def get_safari_mp4_options(output_path: str, subtitle_langs: list = None) -> dict:
        """대체 옵션: Safari 쿠키 사용"""
        options = DownloadOptions.get_best_mp4_options(output_path, subtitle_langs)
        
        # Chrome 쿠키를 Safari로 대체
        options['cookiesfrombrowser'] = ('safari',)
        
        return options
    
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
            
            # 쿠키 설정 - Chrome 우선 시도
            'cookiesfrombrowser': ('chrome',),
            
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