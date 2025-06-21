# src/fetcher/youtube.py
import yt_dlp
import os
import re
from typing import Dict, Any, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class YouTubeDownloader:
    """YouTube/Vimeo 비디오 다운로더 (단순화된 버전)"""
    
    def __init__(self):
        self.logger = logger
        self.temp_dir = "data/temp"
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def is_supported(self, url: str) -> bool:
        """지원하는 URL인지 확인"""
        patterns = [
            # YouTube
            r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/',
            r'(https?://)?(www\.)?youtube\.com/watch\?v=',
            r'(https?://)?(www\.)?youtu\.be/',
            # Vimeo
            r'(https?://)?(www\.)?vimeo\.com/\d+',
            r'(https?://)?player\.vimeo\.com/video/\d+'
        ]
        return any(re.match(pattern, url) for pattern in patterns)
    
    def _sanitize_filename(self, title: str, max_length: int = 100) -> str:
        """파일명으로 사용할 수 있도록 제목 정리"""
        # 특수문자를 언더스코어로 치환
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
        # 연속된 언더스코어를 하나로
        safe_title = re.sub(r'_+', '_', safe_title)
        # 앞뒤 공백 및 언더스코어 제거
        safe_title = safe_title.strip('_ ')
        # 최대 길이 제한
        return safe_title[:max_length]
    
    def download(self, url: str) -> Dict[str, Any]:
        """
        비디오 다운로드
        
        Args:
            url: 다운로드할 비디오 URL
            
        Returns:
            다운로드 결과 딕셔너리
            {
                'filepath': str,  # 다운로드된 파일 경로
                'video_id': str,  # 비디오 ID
                'title': str,     # 비디오 제목
                'duration': int,  # 영상 길이(초)
                'uploader': str,  # 업로더
                'upload_date': str,  # 업로드 날짜
                'description': str,  # 설명
                'view_count': int,   # 조회수
                'like_count': int,   # 좋아요 수
                'ext': str          # 파일 확장자
            }
        """
        try:
            # 1. 먼저 정보만 추출
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                video_id = info.get('id', '')
                video_title = info.get('title', 'untitled')
            
            if not video_id:
                raise ValueError("비디오 ID를 추출할 수 없습니다.")
            
            # 2. 다운로드 디렉토리 생성
            output_dir = os.path.join(self.temp_dir, video_id)
            os.makedirs(output_dir, exist_ok=True)
            
            # 3. 파일명 생성
            safe_title = self._sanitize_filename(video_title)
            output_template = os.path.join(output_dir, f'{safe_title}.%(ext)s')
            
            # 4. 다운로드 옵션 설정
            quality_option = os.getenv("VIDEO_QUALITY", "best")
            ydl_opts = self._get_download_options(output_template, quality_option)
            
            self.logger.info(f"📥 다운로드 시작: {url} (품질: {quality_option})")
            self.logger.info(f"📁 저장 위치: {output_dir}")
            
            # 5. 다운로드 실행
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                # 실제 다운로드된 파일 경로 찾기
                downloaded_file = ydl.prepare_filename(info)
                
                # 확장자가 변경되었을 수 있으므로 확인
                if not os.path.exists(downloaded_file):
                    base_name = os.path.splitext(downloaded_file)[0]
                    for ext in ['.mp4', '.webm', '.mkv', '.mov']:
                        test_file = base_name + ext
                        if os.path.exists(test_file):
                            downloaded_file = test_file
                            break
            
            if not os.path.exists(downloaded_file):
                raise FileNotFoundError(f"다운로드된 파일을 찾을 수 없습니다: {downloaded_file}")
            
            # 6. 파일 크기 확인
            file_size = os.path.getsize(downloaded_file) / (1024 * 1024)  # MB
            self.logger.info(f"📊 파일 크기: {file_size:.1f} MB")
            
            # 7. 결과 반환
            result = {
                'filepath': downloaded_file,
                'video_id': video_id,
                'title': info.get('title', ''),
                'duration': info.get('duration', 0),
                'uploader': info.get('uploader', ''),
                'upload_date': info.get('upload_date', ''),
                'description': info.get('description', ''),
                'view_count': info.get('view_count', 0),
                'like_count': info.get('like_count', 0),
                'ext': os.path.splitext(downloaded_file)[1][1:],  # 확장자 (점 제외)
                'thumbnail': info.get('thumbnail', ''),
                'webpage_url': info.get('webpage_url', url)
            }
            
            self.logger.info(f"✅ 다운로드 완료: {safe_title}")
            return result
            
        except Exception as e:
            self.logger.error(f"다운로드 실패: {str(e)}")
            raise
    
    def _get_download_options(self, output_template: str, quality: str = "best") -> Dict[str, Any]:
        """
        다운로드 옵션 생성
        
        Args:
            output_template: 출력 파일 템플릿
            quality: 품질 옵션 (best, balanced, fast)
            
        Returns:
            yt-dlp 옵션 딕셔너리
        """
        base_opts = {
            'outtmpl': output_template,
            'quiet': not os.getenv('DEBUG', 'false').lower() == 'true',
            'no_warnings': not os.getenv('DEBUG', 'false').lower() == 'true',
            'extract_flat': False,
            'force_generic_extractor': False,
        }
        
        if quality == "fast":
            # 빠른 다운로드 - 720p 이하 MP4만
            opts = {
                **base_opts,
                'format': 'best[height<=720][ext=mp4]/best[height<=720]/best',
                'merge_output_format': 'mp4',
            }
        elif quality == "balanced":
            # 균형잡힌 품질 - 1080p 이하
            opts = {
                **base_opts,
                'format': 'best[height<=1080]/best',
                'merge_output_format': 'mp4',
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }]
            }
        else:  # best
            # 최고 품질
            opts = {
                **base_opts,
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'merge_output_format': 'mp4',
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }]
            }
        
        # 추가 옵션
        opts.update({
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'no_color': True,
            'noprogress': base_opts['quiet'],
        })
        
        return opts
    
    def get_video_info(self, url: str) -> Dict[str, Any]:
        """
        다운로드 없이 비디오 정보만 추출
        
        Args:
            url: 비디오 URL
            
        Returns:
            비디오 정보 딕셔너리
        """
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                
                return {
                    'video_id': info.get('id', ''),
                    'title': info.get('title', ''),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', ''),
                    'upload_date': info.get('upload_date', ''),
                    'description': info.get('description', ''),
                    'view_count': info.get('view_count', 0),
                    'like_count': info.get('like_count', 0),
                    'thumbnail': info.get('thumbnail', ''),
                    'webpage_url': info.get('webpage_url', url)
                }
                
        except Exception as e:
            self.logger.error(f"정보 추출 실패: {str(e)}")
            raise