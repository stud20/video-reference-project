# src/fetcher/youtube.py
import yt_dlp
import os
from typing import Tuple
from src.fetcher.base import VideoFetcher
from src.models.video import Video, VideoMetadata
from utils.logger import get_logger
import re

class YouTubeFetcher(VideoFetcher):
    """YouTube 비디오 다운로더"""
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger(__name__)
    
    def is_supported(self, url: str) -> bool:
        """YouTube URL인지 확인"""
        youtube_patterns = [
            r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/',
            r'(https?://)?(www\.)?youtube\.com/watch\?v=',
            r'(https?://)?(www\.)?youtu\.be/'
        ]
        return any(re.match(pattern, url) for pattern in youtube_patterns)
    
    def download(self, video: Video) -> Tuple[str, VideoMetadata]:
        """YouTube 비디오 다운로드"""
        # 세션 디렉토리 준비
        output_dir = self.prepare_session_directory(video)
        output_path = os.path.join(output_dir, 'video.%(ext)s')
        
        # download_options 사용
        from src.fetcher.download_options import DownloadOptions
        from src.fetcher.video_processor import VideoProcessor
        
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
            
            # 실제 다운로드된 파일 경로 찾기
            downloaded_file = ydl.prepare_filename(info)
            # 확장자가 변경되었을 수 있으므로 확인
            if not os.path.exists(downloaded_file):
                # mp4로 변환되었을 가능성
                base_name = os.path.splitext(downloaded_file)[0]
                for ext in ['.mp4', '.webm', '.mkv']:
                    test_file = base_name + ext
                    if os.path.exists(test_file):
                        downloaded_file = test_file
                        break
        
        # 비디오 후처리 (코덱 확인 및 재인코딩)
        processor = VideoProcessor()
        final_video_path = processor.process_video(downloaded_file)
        
        # 메타데이터 생성
        metadata = VideoMetadata(
            title=info.get("title"),
            description=info.get("description"),
            uploader=info.get("uploader"),
            upload_date=info.get("upload_date"),
            duration=info.get("duration"),
            ext=os.path.splitext(final_video_path)[1][1:],  # 최종 확장자
            video_id=info.get("id"),
            webpage_url=info.get("webpage_url")
        )
        
        # 파일 크기 확인
        if os.path.exists(final_video_path):
            file_size = os.path.getsize(final_video_path) / (1024 * 1024)  # MB
            self.logger.info(f"📊 최종 파일 크기: {file_size:.1f} MB")
        
        # Video 객체 업데이트
        video.local_path = final_video_path
        video.metadata = metadata
        
        self.logger.info(f"✅ 다운로드 완료: {final_video_path}")
        
        return final_video_path, metadata