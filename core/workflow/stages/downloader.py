# src/pipeline/stages/download_stage.py
"""다운로드 스테이지"""

import os
from core.video.downloader.youtube import YouTubeDownloader
from core.video.models import Video, VideoMetadata

from ..pipeline import PipelineStage, PipelineContext


class DownloadStage(PipelineStage):
    """영상 다운로드"""
    
    def __init__(self):
        super().__init__("download")
        self.downloader = YouTubeDownloader()
    
    def can_skip(self, context: PipelineContext) -> bool:
        """캐시 히트 시 스킵"""
        return context.stage_results.get("cache_hit", False)
    
    def execute(self, context: PipelineContext) -> PipelineContext:
        """다운로드 실행"""
        self.update_progress(0, "📥 영상 다운로드 시작...", context)
        
        # 다운로드 실행 (내부 progress callback 없이)
        download_result = self.downloader.download_legacy(context.url, None)
        
        context.download_result = download_result
        
        # Video 객체 생성
        video = Video(
            session_id=context.video_id,
            url=context.url,
            local_path=download_result['filepath'],
            metadata=VideoMetadata(
                title=download_result.get('title', ''),
                duration=download_result.get('duration', 0),
                uploader=download_result.get('uploader', ''),
                upload_date=download_result.get('upload_date', ''),
                description=download_result.get('description', ''),
                view_count=download_result.get('view_count', 0),
                like_count=download_result.get('like_count', 0),
                video_id=context.video_id,
                url=context.url,
                ext=download_result.get('ext', 'mp4'),
                thumbnail=download_result.get('thumbnail', ''),
                webpage_url=download_result.get('webpage_url', context.url),
                tags=download_result.get('tags', []),
                categories=download_result.get('categories', []),
                language=download_result.get('language', ''),
                channel_id=download_result.get('channel_id', ''),
                comment_count=download_result.get('comment_count', 0),
                age_limit=download_result.get('age_limit', 0),
                subtitle_files=download_result.get('subtitle_files', {}),
                platform=context.platform
            )
        )
        
        # session_dir 수정 - video_id를 사용하여 올바른 경로 설정
        video.session_dir = os.path.join("data/temp", context.video_id)
        self.logger.info(f"📁 세션 디렉토리 설정: {video.session_dir}")
        video.scenes = []  # 씬은 나중에 추출
        
        context.video_object = video
        
        self.update_progress(100, f"✅ 다운로드 완료: {video.metadata.title}", context)
        
        return context
