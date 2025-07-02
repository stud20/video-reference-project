# core/workflow/__init__.py
"""영상 처리 워크플로우"""

from .pipeline import VideoPipeline, PipelineContext, PipelineStage
from .coordinator import VideoProcessor
from .stages import *


def create_default_pipeline(provider: str = "openai") -> VideoPipeline:
    """기본 파이프라인 생성"""
    pipeline = VideoPipeline()
    
    # 순서대로 스테이지 추가
    pipeline.add_stage(URLParseStage())
    pipeline.add_stage(CacheCheckStage())
    pipeline.add_stage(DownloadStage())
    pipeline.add_stage(MetadataStage())
    pipeline.add_stage(SceneExtractionStage())
    pipeline.add_stage(AIAnalysisStage(provider_name=provider))
    pipeline.add_stage(StorageUploadStage())
    pipeline.add_stage(NotionUploadStage())
    pipeline.add_stage(CleanupStage())
    
    return pipeline


__all__ = [
    'VideoPipeline', 'PipelineContext', 'PipelineStage', 
    'VideoProcessor', 'create_default_pipeline',
    # 스테이지들
    'URLParseStage', 'CacheCheckStage', 'DownloadStage',
    'MetadataStage', 'SceneExtractionStage', 'AIAnalysisStage',
    'StorageUploadStage', 'NotionUploadStage', 'CleanupStage'
]