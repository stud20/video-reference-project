# core/video/__init__.py
"""영상 처리 도메인"""

from .models import Video, VideoMetadata, Scene
from .video_downloader import VideoDownloader  # video_downloader.py 파일에서 import
from .scene_detector import SceneExtractor

# downloader 디렉토리의 클래스들도 export
from .downloader.youtube import YouTubeDownloader
from .downloader.vimeo import VimeoDownloader
from .downloader.base import VideoFetcher

__all__ = [
    'Video', 'VideoMetadata', 'Scene', 
    'VideoDownloader', 'SceneExtractor',
    'YouTubeDownloader', 'VimeoDownloader', 'VideoFetcher'
]