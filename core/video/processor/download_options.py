# core/video/processor/download_options.py
"""yt-dlp 다운로드 옵션 설정 - macOS 재생 호환성 중심"""

import os



class DownloadOptions:
    """다양한 품질 옵션 제공 - macOS 호환성 우선"""
    
    # macOS에서 재생 불가능한 코덱들
    NON_PLAYABLE_CODECS = {"vp9", "vp8", "av1", "vp09", "vp08", "vp10"}
    
    @staticmethod
    def get_cookies_file_mp4_options(output_path: str, subtitle_langs: list = None) -> dict:
        """쿠키 파일 사용 옵션: cookies.txt 파일 사용"""
        options = DownloadOptions.get_best_mp4_options(output_path, subtitle_langs)
        
        # 브라우저 쿠키 옵션 제거
        if 'cookiesfrombrowser' in options:
            del options['cookiesfrombrowser']
        
        # 쿠키 파일 설정
        options['cookiefile'] = 'cookies.txt'
        
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
        """쿠키 없이 다운로드 시도 - Player Response 에러 회피"""
        options = DownloadOptions.get_best_mp4_options(output_path, subtitle_langs)
        
        # 쿠키 옵션 제거
        if 'cookiesfrombrowser' in options:
            del options['cookiesfrombrowser']
        if 'cookiefile' in options:
            del options['cookiefile']
            
        # 더 방어적인 설정
        options.update({
            'sleep_interval': 3,
            'max_sleep_interval': 10,
            'retries': 10,
            'fragment_retries': 10,
            
            # 추가 Player Response 회피 옵션
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web', 'tv_embedded'],
                    'player_skip': ['configs', 'webpage'],
                    'include_live_dash': False,
                    'skip_hls': True,
                }
            },
            
            # 더 많은 User-Agent 순환
            'user_agent_list': [
                'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15',
                'Mozilla/5.0 (Android 11; Mobile; rv:91.0) Gecko/91.0 Firefox/91.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            ]
        })
        
        return options
    def get_best_mp4_options(output_path: str, subtitle_langs: list = None) -> dict:
        """최고 품질 MP4 다운로드 옵션 - H.264 우선 + 403 에러 방지"""
        return {
            'outtmpl': output_path,
            
            # 포맷 선택 - H.264(avc1) 비디오 + AAC(mp4a) 오디오 우선
            'format': (
                # 1. H.264 + AAC 조합 (macOS 네이티브 재생)
                'bv*[vcodec^=avc1]+ba[acodec^=mp4a]/'
                # 2. 최고 품질 MP4
                'best[ext=mp4]/'
                # 3. H.264 비디오 + 최고 오디오
                'bv*[vcodec^=avc1]+ba/best'
            ),
            
            # === 403 에러 + Player Response 에러 방지 옵션 ===
            # User-Agent - 최신 Chrome 브라우저로 위장
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            
            # 요청 간격 설정 - 차단 회피
            'sleep_interval': 2,          # 최소 대기 시간 증가
            'max_sleep_interval': 8,      # 최대 대기 시간 증가
            'sleep_interval_requests': 2, # 요청 간 대기 시간 증가
            
            # 에러 처리 강화
            'ignoreerrors': False,        
            'retries': 5,                 # 재시도 횟수 증가
            'fragment_retries': 5,        
            'retry_sleep_functions': {    # 재시도 간격 설정
                'http': lambda n: min(2 ** n, 10),
                'fragment': lambda n: min(2 ** n, 10),
            },
            
            # YouTube 우회 전용 헤더
            'http_headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"macOS"',
            },
            # 쿠키 설정 - Chrome 우선 시도
            'cookiesfrombrowser': ('chrome',),   # Chrome 쿠키 우선 사용
            # 'cookiesfrombrowser': ('safari',),   # Chrome 실패 시 Safari 대체
            # 'cookiefile': 'cookies.txt',         # 수동 쿠키 파일
            
            # Player Response 추출 관련 옵션
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],  # 여러 클라이언트 시도
                    'player_skip': ['configs'],           # 설정 건너뛰기
                    'include_live_dash': False,           # 라이브 스트림 제외
                }
            },
            
            # 네트워크 최적화
            'concurrent_fragment_downloads': 1,  # 동시 다운로드 제한
            'buffersize': 1024 * 16,            # 버퍼 크기 조정
            
            # 수동 쿠키 파일 사용 (대안)
            # 'cookiefile': 'cookies.txt',
            
            # 지역 우회
            'geo_bypass': True,
            # 'geo_bypass_country': 'US',
            
            # === 기존 옵션들 ===
            # 후처리 - H.264로 재인코딩
            'postprocessors': [
                {
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                },
                {
                    'key': 'FFmpegMetadata',
                    'add_metadata': True,
                },
                {
                    'key': 'FFmpegEmbedSubtitle',  # 자막 임베드 (선택사항)
                    'already_have_subtitle': False,
                },
                {
                    'key': 'FFmpegThumbnailsConvertor',
                    'format': 'jpg',
                }
            ],
            
            # 후처리 옵션
            'postprocessor_args': {
                'FFmpegVideoConvertor': [
                    '-c:v', 'libx264',      # H.264 코덱
                    '-c:a', 'aac',          # AAC 오디오
                    '-preset', 'medium',    # 인코딩 속도/품질 균형
                    '-crf', '23',          # 품질 (낮을수록 좋음, 18-28 추천)
                    '-movflags', '+faststart',  # 웹 스트리밍 최적화
                ]
            },
            
            # 병합 설정
            'merge_output_format': 'mp4',
            'prefer_ffmpeg': True,
            'keepvideo': False,
            
            # 자막 - 비활성화 (오류 방지)
            'writesubtitles': False,
            'writeautomaticsub': False,
            # 'subtitleslangs': subtitle_langs or ['ko', 'en'],
            'embedsubtitles': False,  # 별도 파일로 저장
            
            # 썸네일
            'writethumbnail': True,
            'embedthumbnail': True,
            
            # 네트워크 설정
            'socket_timeout': 30,         # 소켓 타임아웃
            'http_chunk_size': 10485760,  # 10MB 청크 (안정성)
            
            # 디버깅 옵션 (필요시 활성화)
            'verbose': False,
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