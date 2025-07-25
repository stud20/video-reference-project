# src/pipeline/stages/extraction_stage.py
"""씬 추출 스테이지"""

from core.video.scene_detector import SceneExtractor
from core.video.models import Scene

from ..pipeline import PipelineStage, PipelineContext


class SceneExtractionStage(PipelineStage):
    """씬 추출"""
    
    def __init__(self):
        super().__init__("scene_extraction")
        self.extractor = SceneExtractor()
    
    def can_skip(self, context: PipelineContext) -> bool:
        """캐시 히트 시 스킵"""
        return context.stage_results.get("cache_hit", False)
    
    def execute(self, context: PipelineContext) -> PipelineContext:
        """씬 추출 실행"""
        self.update_progress(0, "🎞️ 장면 추출 시작...", context)
        
        video = context.video_object
        
        # 씬 추출 (내부 progress callback 없이)
        is_short_form = video.metadata.is_short_form if video.metadata else False
        scenes_result = self.extractor.extract_scenes(
            video.local_path,
            video.session_id,
            progress_callback=None,
            is_short_form=is_short_form
        )
        
        # Scene 객체로 변환
        video.scenes = []
        
        if isinstance(scenes_result, dict):
            # 새로운 반환 형식
            all_scenes = scenes_result.get('all_scenes', [])
            grouped_scenes = scenes_result.get('grouped_scenes', [])
            
            self.logger.info(f"📊 씬 추출 결과: 전체 {len(all_scenes)}개, 그룹화 {len(grouped_scenes)}개")
            
            # AI 분석을 위해 그룹화된 씬 사용
            scenes_to_use = grouped_scenes if grouped_scenes else all_scenes[:10]
            
            for scene_data in scenes_to_use:
                if isinstance(scene_data, Scene):
                    video.scenes.append(scene_data)
                elif isinstance(scene_data, dict):
                    scene = Scene(
                        timestamp=scene_data.get('timestamp', 0.0),
                        frame_path=scene_data.get('frame_path', '') or scene_data.get('path', ''),
                        scene_type=scene_data.get('type', 'mid')
                    )
                    video.scenes.append(scene)
        
        context.scenes = video.scenes
        
        self.update_progress(100, f"✅ {len(video.scenes)}개 씬 추출 완료", context)
        
        return context
