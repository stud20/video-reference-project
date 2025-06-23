# src/fetcher/vimeo.py
import yt_dlp
import os
from typing import Tuple
from src.fetcher.base import VideoFetcher
from src.models.video import Video, VideoMetadata
from utils.logger import get_logger
import re

class VimeoFetcher(VideoFetcher):
    """Vimeo 비디오 다운로더"""
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger(__name__)
    
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
        output_path = os.path.join(output_dir, 'video.%(ext)s')
        
        # download_options 사용
        from src.fetcher.download_options import DownloadOptions
        
        # 설정에서 품질 옵션 가져오기 (기본값: best)
        quality_option = os.getenv("VIDEO_QUALITY", "best")
        
        if quality_option == "balanced":
            ydl_opts = DownloadOptions.get_balanced_mp4_options(
                output_path, 
                self.settings.video.subtitle_languages
            )
        elif quality_option == "fast":
            ydl_opts = DownloadOptions.get_fast_mp4_options(output_path)
        else:  # best
            ydl_opts = DownloadOptions.get_best_mp4_options(
                output_path,
                self.settings.video.subtitle_languages
            )
        
        # 디버그 모드 설정 반영
        ydl_opts['quiet'] = not self.settings.DEBUG
        ydl_opts['no_warnings'] = not self.settings.DEBUG
        
        # 다운로드 실행
        self.logger.info(f"📥 다운로드 시작: {video.url} (품질: {quality_option})")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video.url, download=True)
        
        # 메타데이터 생성
        metadata = VideoMetadata(
            title=info.get("title"),
            description=info.get("description"),
            uploader=info.get("uploader"),
            upload_date=info.get("upload_date"),
            duration=info.get("duration"),
            ext="mp4",  # 항상 mp4로 설정
            video_id=info.get("id"),
            webpage_url=info.get("webpage_url")
        )
        
        # 비디오 파일 경로 (mp4로 고정)
        video_path = os.path.join(output_dir, "video.mp4")
        
        # 파일이 존재하는지 확인 (변환 실패 시 원본 파일 찾기)
        if not os.path.exists(video_path):
            # 다른 확장자로 저장되었을 수 있음
            for ext in ['webm', 'mkv', 'mov', info.get('ext', '')]:
                alt_path = os.path.join(output_dir, f"video.{ext}")
                if os.path.exists(alt_path):
                    self.logger.warning(f"MP4 변환 실패, {ext} 파일 사용")
                    video_path = alt_path
                    metadata.ext = ext
                    break
        
        # 파일 크기 확인
        if os.path.exists(video_path):
            file_size = os.path.getsize(video_path) / (1024 * 1024)  # MB
            self.logger.info(f"📊 파일 크기: {file_size:.1f} MB")
        
        # Video 객체 업데이트
        video.local_path = video_path
        video.metadata = metadata
        
        self.logger.info(f"✅ 다운로드 완료: {video_path} (포맷: {metadata.ext})")
        
        return video_path, metadata