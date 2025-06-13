# src/services/video_service.py
from typing import Optional, List
from src.models.video import Video
from src.fetcher.youtube import YouTubeFetcher
from src.fetcher.vimeo import VimeoFetcher
from src.storage.webdav_client import WebDAVStorage
from utils.logger import get_logger

class VideoService:
    """비디오 처리 서비스 - 다운로드, 분석, 저장을 통합 관리"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.fetchers = [YouTubeFetcher(), VimeoFetcher()]
        self.storage = WebDAVStorage()
    
    def get_fetcher(self, url: str):
        """URL에 맞는 다운로더 선택"""
        for fetcher in self.fetchers:
            if fetcher.is_supported(url):
                return fetcher
        raise ValueError(f"지원하지 않는 URL입니다: {url}")
    
    def process_video(self, url: str) -> Video:
        """비디오 처리 전체 워크플로우"""
        # 1. Video 객체 생성
        video = Video(session_id="", url=url)
        self.logger.info(f"🎬 비디오 처리 시작: {url}")
        
        try:
            # 2. 적절한 다운로더 선택
            fetcher = self.get_fetcher(url)
            self.logger.info(f"📥 다운로더 선택: {fetcher.__class__.__name__}")
            
            # 3. 비디오 다운로드
            video_path, metadata = fetcher.download(video)
            self.logger.info(f"✅ 다운로드 완료: {video_path}")
            
            # 4. 메타데이터 저장
            metadata_path = fetcher.save_metadata(video)
            
            # 5. NAS 업로드
            self._upload_to_nas(video, [video_path, metadata_path])
            
            return video
            
        except Exception as e:
            self.logger.error(f"❌ 비디오 처리 실패: {e}")
            raise
    
    def _upload_to_nas(self, video: Video, files: List[str]):
        """NAS에 파일 업로드"""
        remote_folder = f"2025-session/{video.session_id}/"
        
        for file_path in files:
            try:
                self.storage.upload_file(file_path, remote_folder)
            except Exception as e:
                self.logger.error(f"업로드 실패: {file_path}, 오류: {e}")
                raise