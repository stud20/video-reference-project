# src/models/video.py
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
import uuid

@dataclass
class VideoMetadata:
    """비디오 메타데이터"""
    title: str
    description: Optional[str] = None
    uploader: Optional[str] = None
    upload_date: Optional[str] = None
    duration: Optional[int] = None
    ext: Optional[str] = None
    video_id: Optional[str] = None
    webpage_url: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {k: v for k, v in self.__dict__.items() if v is not None}

@dataclass
class Scene:
    """비디오 장면 정보"""
    timestamp: float
    frame_path: str
    description: Optional[str] = None
    objects: List[str] = field(default_factory=list)

@dataclass
class Video:
    """비디오 전체 정보"""
    session_id: str  # 이제 video_id로 사용
    url: str
    local_path: Optional[str] = None
    metadata: Optional[VideoMetadata] = None
    scenes: List[Scene] = field(default_factory=list)
    analysis_result: Optional[Dict] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        # session_id는 이제 video_id로 설정됨
        if not self.session_id:
            self.session_id = str(uuid.uuid4())[:8]
    
    @property
    def session_dir(self) -> str:
        """세션 디렉토리 경로 (video_id 기반)"""
        from config.settings import Settings
        import os
        return os.path.join(Settings.paths.temp_dir, self.session_id)