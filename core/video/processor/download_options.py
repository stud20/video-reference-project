# core/video/processor/download_options.py
"""yt-dlp 다운로드 옵션 설정 - macOS 재생 호환성 중심"""

import os

class DownloadOptions:
    """다양한 품질 옵션 제공 - macOS 호환성 우선"""
    
    # macOS에서 재생 불가능한 코덱들
    NON_PLAYABLE_CODECS = {"vp9", "vp8", "av1", "vp09", "vp08", "vp10"}
    
    @staticmethod
    def get_best_mp4_options(output_path: str, subtitle_langs: list = None) -> dict:
        """최고 품질 MP4 다운로드 옵션 - H.264 우선"""
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
            'retries': 5,
            'fragment_retries': 10,
            'continuedl': True,
            
            # 기타 옵션
            'quiet': False,
            'no_warnings': False,
            'ignoreerrors': False,
            
            # HTTP 헤더 (일부 사이트 필요)
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'
            }
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