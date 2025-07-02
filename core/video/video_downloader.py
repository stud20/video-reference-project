# core/video/downloader.py
"""통합 비디오 다운로더 - YouTube, Vimeo 지원"""

from typing import Dict, Any, Optional
import os
import yt_dlp
from utils.logger import get_logger


class VideoDownloader:
    """통합 비디오 다운로더"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.download_dir = "data/videos"
        os.makedirs(self.download_dir, exist_ok=True)
    
    def download(self, url: str) -> Dict[str, Any]:
        """비디오 다운로드
        
        Args:
            url: YouTube 또는 Vimeo URL
            
        Returns:
            다운로드 정보 딕셔너리
        """
        # URL에 따라 적절한 다운로더 선택
        if 'youtube.com' in url or 'youtu.be' in url:
            return self._download_youtube(url)
        elif 'vimeo.com' in url:
            return self._download_vimeo(url)
        else:
            raise ValueError(f"지원하지 않는 URL: {url}")
    
    def _download_youtube(self, url: str) -> Dict[str, Any]:
        """YouTube 다운로드"""
        from core.video.downloader.youtube import YouTubeDownloader
        downloader = YouTubeDownloader()
        return downloader.download_legacy(url)
    
    def _download_vimeo(self, url: str) -> Dict[str, Any]:
        """Vimeo 다운로드"""
        from core.video.downloader.vimeo import VimeoDownloader
        downloader = VimeoDownloader()
        # VimeoDownloader는 Video 객체를 받으므로 임시 Video 객체 생성
        from core.video.models import Video
        video = Video(session_id="temp", url=url, local_path="")
        video.session_dir = os.path.join(self.download_dir, "temp")
        filepath, metadata = downloader.download(video)
        # Dict 형태로 변환
        return {
            'filepath': filepath,
            'video_id': metadata.video_id,
            'title': metadata.title,
            'duration': metadata.duration,
            'uploader': metadata.uploader,
            'channel_id': metadata.channel_id,
            'upload_date': metadata.upload_date,
            'description': metadata.description,
            'view_count': metadata.view_count,
            'like_count': metadata.like_count,
            'comment_count': metadata.comment_count,
            'tags': metadata.tags,
            'categories': metadata.categories,
            'language': metadata.language,
            'age_limit': metadata.age_limit,
            'ext': metadata.ext,
            'thumbnail': metadata.thumbnail,
            'webpage_url': metadata.webpage_url,
            'subtitle_files': metadata.subtitle_files,
            'platform': metadata.platform
        }
