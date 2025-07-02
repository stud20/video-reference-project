# src/models/video.py
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class VideoMetadata:
    """영상 메타데이터 - 확장된 버전"""
    video_id: str
    title: str
    url: str
    duration: float  # 초 단위
    uploader: str = "Unknown"  # 채널명
    channel_id: str = ""
    description: str = ""  # 영상 설명
    upload_date: str = ""
    platform: str = "unknown"
    view_count: int = 0  # 조회수
    like_count: int = 0  # 좋아요 수
    comment_count: int = 0  # 댓글 수
    tags: List[str] = field(default_factory=list)  # 영상 태그
    categories: List[str] = field(default_factory=list)  # 카테고리
    language: str = ""  # 언어
    subtitle_files: Dict[str, str] = field(default_factory=dict)  # 자막 파일 경로
    age_limit: int = 0  # 연령 제한
    ext: str = "mp4"  # 파일 확장자
    thumbnail: str = ""  # 썸네일 URL
    webpage_url: str = ""  # 웹페이지 URL
    
    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            'video_id': self.video_id,
            'title': self.title,
            'url': self.url,
            'duration': self.duration,
            'uploader': self.uploader,
            'channel_id': self.channel_id,
            'description': self.description,
            'upload_date': self.upload_date,
            'platform': self.platform,
            'view_count': self.view_count,
            'like_count': self.like_count,
            'comment_count': self.comment_count,
            'tags': self.tags,
            'categories': self.categories,
            'language': self.language,
            'age_limit': self.age_limit,
            'ext': self.ext,
            'thumbnail': self.thumbnail,
            'webpage_url': self.webpage_url,
            'subtitle_files': self.subtitle_files,
        }


@dataclass
class Scene:
    """비디오 씬 정보"""
    timestamp: float  # 초 단위
    frame_path: str
    scene_type: str = "mid"  # "start", "mid", "end"
    confidence: float = 0.0  # 씬 전환 신뢰도
    grouped_path: Optional[str] = None  # 그룹화된 씬 경로 추가
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'timestamp': self.timestamp,
            'frame_path': self.frame_path,
            'scene_type': self.scene_type,
            'confidence': self.confidence,
            'grouped_path': self.grouped_path
        }



@dataclass
class Video:
    """비디오 정보를 담는 메인 클래스"""
    session_id: str  # 고유 세션 ID (video_id와 동일)
    url: str  # 원본 URL
    local_path: Optional[str] = None  # 로컬 저장 경로
    metadata: Optional[VideoMetadata] = None  # 메타데이터
    scenes: List[Scene] = field(default_factory=list)  # 추출된 모든 씬들
    grouped_scenes: List[Scene] = field(default_factory=list)  # 그룹화된 대표 씬들 (추가)
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
            'grouped_scenes': [scene.to_dict() for scene in self.grouped_scenes],  # 추가
            'analysis_result': self.analysis_result,
            'created_at': self.created_at.isoformat(),
            'session_dir': self.session_dir
        }
    
    def get_scene_count(self) -> int:
        """추출된 전체 씬 개수 반환"""
        return len(self.scenes)
    
    def get_grouped_scene_count(self) -> int:  # 추가
        """그룹화된 씬 개수 반환"""
        return len(self.grouped_scenes)
    
    def get_analysis_scene_count(self) -> int:  # 추가
        """AI 분석에 사용된 씬 개수 반환"""
        return len(self.grouped_scenes) if self.grouped_scenes else 0
    
    def get_duration_str(self) -> str:
        """시간을 MM:SS 형식으로 반환"""
        if self.metadata and self.metadata.duration:
            minutes = int(self.metadata.duration // 60)
            seconds = int(self.metadata.duration % 60)
            return f"{minutes:02d}:{seconds:02d}"
        return "00:00"
    
    def is_analyzed(self) -> bool:
        """AI 분석이 완료되었는지 확인"""
        return self.analysis_result is not None
    
    def get_tags(self) -> List[str]:
        """분석 결과에서 태그 추출"""
        if self.analysis_result and 'tags' in self.analysis_result:
            return self.analysis_result['tags']
        # 메타데이터에서 태그 가져오기 (YouTube 태그)
        elif self.metadata and self.metadata.tags:
            return self.metadata.tags
        return []
    
    def get_genre(self) -> str:
        """분석 결과에서 장르 추출"""
        if self.analysis_result and 'genre' in self.analysis_result:
            return self.analysis_result['genre']
        return "미분석"