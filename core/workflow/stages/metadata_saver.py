# src/pipeline/stages/metadata_stage.py
"""메타데이터 처리 스테이지"""

from datetime import datetime
from core.database.repository import VideoAnalysisDB

from ..pipeline import PipelineStage, PipelineContext


class MetadataStage(PipelineStage):
    """메타데이터 저장"""
    
    def __init__(self):
        super().__init__("metadata")
        self.db = VideoAnalysisDB()
    
    def can_skip(self, context: PipelineContext) -> bool:
        """캐시 히트 시 스킵"""
        return context.stage_results.get("cache_hit", False)
    
    def execute(self, context: PipelineContext) -> PipelineContext:
        """메타데이터 처리"""
        self.update_progress(40, "📋 메타데이터 처리 중...", context)
        
        video = context.video_object
        
        # DB에 영상 정보 저장
        self.update_progress(45, "💾 데이터베이스에 정보 저장 중...", context)
        
        video_data = {
            'video_id': context.video_id,
            'url': context.url,
            'title': video.metadata.title,
            'duration': video.metadata.duration,
            'platform': context.platform,
            'download_date': datetime.now().isoformat(),
            
            # 확장된 메타데이터
            'uploader': video.metadata.uploader,
            'channel': video.metadata.uploader,
            'description': video.metadata.description,
            'view_count': video.metadata.view_count,
            'like_count': video.metadata.like_count,
            'comment_count': video.metadata.comment_count,
            'tags': video.metadata.tags,
            'channel_id': video.metadata.channel_id,
            'categories': video.metadata.categories,
            'language': video.metadata.language,
            'upload_date': video.metadata.upload_date,
            'age_limit': video.metadata.age_limit,
            'thumbnail': video.metadata.thumbnail,
            'webpage_url': video.metadata.webpage_url,
        }
        
        self.db.save_video_info(video_data)
        
        return context
