# src/pipeline/stages/notion_stage.py
"""Notion 업로드 스테이지"""

import os

from ..pipeline import PipelineStage, PipelineContext


class NotionUploadStage(PipelineStage):
    """Notion 데이터베이스 업로드"""
    
    def __init__(self):
        super().__init__("notion_upload")
        self.notion_service = None
        self.auto_upload = os.getenv("AUTO_UPLOAD_TO_NOTION", "true").lower() == "true"
        
        # Notion 서비스 초기화
        if self.auto_upload:
            try:
                from integrations.notion import get_notion_service
                self.notion_service = get_notion_service()
                self.logger.info("✅ Notion 서비스 초기화 성공")
            except Exception as e:
                self.logger.warning(f"⚠️ Notion 서비스 초기화 실패: {str(e)}")
                self.notion_service = None
    
    def can_skip(self, context: PipelineContext) -> bool:
        """Notion 비활성화 또는 분석 결과 없을 때 스킵"""
        return (not self.notion_service or 
                not self.auto_upload or
                not context.analysis_result)
    
    def execute(self, context: PipelineContext) -> PipelineContext:
        """Notion 업로드 실행"""
        self.update_progress(96, "📝 Notion 데이터베이스에 업로드 중...", context)
        
        video = context.video_object
        
        # Video 객체에서 데이터 준비
        video_data = {
            'video_id': video.metadata.video_id,
            'title': video.metadata.title,
            'url': video.metadata.url,
            'webpage_url': video.metadata.webpage_url,
            'thumbnail': video.metadata.thumbnail,
            'platform': video.metadata.platform,
            'duration': video.metadata.duration,
            'uploader': video.metadata.uploader,
            'channel': video.metadata.uploader,
            'channel_id': video.metadata.channel_id,
            'upload_date': video.metadata.upload_date,
            'description': video.metadata.description,
            'view_count': video.metadata.view_count,
            'like_count': video.metadata.like_count,
            'comment_count': video.metadata.comment_count,
            'tags': video.metadata.tags,
            'categories': video.metadata.categories,
            'language': video.metadata.language,
            'age_limit': video.metadata.age_limit,
        }
        
        # Notion 업로드
        success, result = self.notion_service.add_video_to_database(
            video_data=video_data,
            analysis_data=context.analysis_result
        )
        
        if success:
            self.update_progress(98, "✅ Notion 업로드/업데이트 성공!", context)
            self.logger.info(f"Notion 페이지: {result}")
        else:
            self.update_progress(98, f"⚠️ Notion 업로드 실패: {result}", context)
            self.logger.warning(f"Notion 업로드 실패: {result}")
        
        return context
