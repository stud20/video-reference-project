# src/pipeline/stages/cleanup_stage.py
"""정리 스테이지"""

import os
import shutil

from ..pipeline import PipelineStage, PipelineContext


class CleanupStage(PipelineStage):
    """임시 파일 정리"""
    
    def __init__(self):
        super().__init__("cleanup")
        self.cleanup_enabled = os.getenv("CLEANUP_TEMP_FILES", "false").lower() == "true"
    
    def can_skip(self, context: PipelineContext) -> bool:
        """정리 비활성화 시 스킵"""
        return not self.cleanup_enabled
    
    def execute(self, context: PipelineContext) -> PipelineContext:
        """임시 파일 정리 실행"""
        self.update_progress(99, "🗑️ 임시 파일 정리 중...", context)
        
        video = context.video_object
        
        if video and hasattr(video, 'session_dir'):
            temp_dir = f"data/temp/{video.session_id}"
            
            if os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                    self.logger.info(f"✅ 임시 파일 정리 완료: {temp_dir}")
                except Exception as e:
                    self.logger.error(f"임시 파일 정리 실패: {str(e)}")
        
        self.update_progress(100, f"✅ 영상 처리 완료: {context.video_id}", context)
        
        return context
