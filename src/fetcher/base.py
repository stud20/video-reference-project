# src/fetcher/base.py
from abc import ABC, abstractmethod
from typing import Tuple
import os
from src.models.video import Video, VideoMetadata
from utils.logger import get_logger

class VideoFetcher(ABC):
    """비디오 다운로더 추상 클래스"""
    
    def __init__(self):
        from config.settings import Settings
        self.settings = Settings()
        self.logger = get_logger(__name__)
    
    @abstractmethod
    def is_supported(self, url: str) -> bool:
        """URL이 지원되는지 확인"""
        pass
    
    @abstractmethod
    def download(self, video: Video) -> Tuple[str, VideoMetadata]:
        """비디오 다운로드 및 메타데이터 추출"""
        pass
    
    def prepare_session_directory(self, video: Video) -> str:
        """세션 디렉토리 준비"""
        os.makedirs(video.session_dir, exist_ok=True)
        return video.session_dir
    
    def save_metadata(self, video: Video) -> str:
        """메타데이터를 파일로 저장"""
        metadata_path = os.path.join(video.session_dir, "metadata.txt")
        with open(metadata_path, "w", encoding="utf-8") as f:
            for key, value in video.metadata.to_dict().items():
                f.write(f"{key}: {value}\n")
        return metadata_path