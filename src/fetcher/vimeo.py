# src/fetcher/vimeo.py
import yt_dlp
import os
from typing import Tuple
from src.fetcher.base import VideoFetcher
from src.models.video import Video, VideoMetadata
import re

class VimeoFetcher(VideoFetcher):
    """Vimeo 비디오 다운로더"""
    
    def is_supported(self, url: str) -> bool:
        """Vimeo URL인지 확인"""
        vimeo_patterns = [
            r'(https?://)?(www\.)?vimeo\.com/',
            r'(https?://)?player\.vimeo\.com/video/'
        ]
        return any(re.match(pattern, url) for pattern in vimeo_patterns)
    
    def download(self, video: Video) -> Tuple[str, VideoMetadata]:
        """Vimeo 비디오 다운로드"""
        # 세션 디렉토리 준비
        output_dir = self.prepare_session_directory(video)
        
        # yt-dlp 설정 (Vimeo도 yt-dlp로 다운로드 가능)
        ydl_opts = {
            'outtmpl': os.path.join(output_dir, 'video.%(ext)s'),
            'format': self.settings.video.quality,
            'writesubtitles': True,
            'subtitleslangs': self.settings.video.subtitle_languages,
            'quiet': not self.settings.DEBUG,
            'no_warnings': not self.settings.DEBUG,
        }
        
        # 다운로드 실행
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video.url, download=True)
        
        # 메타데이터 생성
        metadata = VideoMetadata(
            title=info.get("title"),
            description=info.get("description"),
            uploader=info.get("uploader"),
            upload_date=info.get("upload_date"),
            duration=info.get("duration"),
            ext=info.get("ext"),
            video_id=info.get("id"),
            webpage_url=info.get("webpage_url")
        )
        
        # 비디오 파일 경로
        video_path = os.path.join(output_dir, f"video.{info['ext']}")
        
        # Video 객체 업데이트
        video.local_path = video_path
        video.metadata = metadata
        
        return video_path, metadata