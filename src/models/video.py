# src/models/video.py
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class VideoMetadata:
    """비디오 메타데이터"""
    title: str = ""
    duration: int = 0  # 초 단위
    uploader: str = ""
    upload_date: str = ""
    description: str = ""
    video_id: str = ""
    ext: str = "mp4"
    view_count: int = 0  # 추가
    like_count: int = 0  # 추가
    thumbnail: str = ""  # 추가
    webpage_url: str = ""  # 추가
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'title': self.title,
            'duration': self.duration,
            'uploader': self.uploader,
            'upload_date': self.upload_date,
            'description': self.description,
            'video_id': self.video_id,
            'ext': self.ext,
            'view_count': self.view_count,
            'like_count': self.like_count,
            'thumbnail': self.thumbnail,
            'webpage_url': self.webpage_url
        }


@dataclass
class Scene:
    """비디오 씬 정보"""
    timestamp: float  # 초 단위
    frame_path: str
    scene_type: str = "mid"  # "start", "mid", "end"
    confidence: float = 0.0  # 씬 전환 신뢰도
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'timestamp': self.timestamp,
            'frame_path': self.frame_path,
            'scene_type': self.scene_type,
            'confidence': self.confidence
        }


@dataclass
class Video:
    """비디오 정보를 담는 메인 클래스"""
    session_id: str  # 고유 세션 ID (video_id와 동일)
    url: str  # 원본 URL
    local_path: Optional[str] = None  # 로컬 저장 경로
    metadata: Optional[VideoMetadata] = None  # 메타데이터
    scenes: List[Scene] = field(default_factory=list)  # 추출된 씬들
    analysis_result: Optional[Dict[str, Any]] = None  # AI 분석 결과
    created_at: datetime = field(default_factory=datetime.now)
    session_dir: Optional[str] = None  # 세션 디렉토리 경로 (ai_analyzer가 사용)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'session_id': self.session_id,
            'url': self.url,
            'local_path': self.local_path,
            'metadata': self.metadata.to_dict() if self.metadata else None,
            'scenes': [scene.to_dict() for scene in self.scenes],
            'analysis_result': self.analysis_result,
            'created_at': self.created_at.isoformat()
        }
    
    def get_scene_count(self) -> int:
        """추출된 씬 개수 반환"""
        return len(self.scenes)
    
    def get_duration_str(self) -> str:
        """시간을 MM:SS 형식으로 반환"""
        if self.metadata and self.metadata.duration:
            minutes = self.metadata.duration // 60
            seconds = self.metadata.duration % 60
            return f"{minutes:02d}:{seconds:02d}"
        return "00:00"
    
    def is_analyzed(self) -> bool:
        """AI 분석이 완료되었는지 확인"""
        return self.analysis_result is not None
    
    def get_tags(self) -> List[str]:
        """분석 결과에서 태그 추출"""
        if self.analysis_result and 'tags' in self.analysis_result:
            return self.analysis_result['tags']
        return []
    
    def get_genre(self) -> str:
        """분석 결과에서 장르 추출"""
        if self.analysis_result and 'genre' in self.analysis_result:
            return self.analysis_result['genre']
        return "미분석"