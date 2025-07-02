# src/pipeline/stages/cache_check_stage.py
"""캐시 확인 스테이지"""

from core.database.repository import VideoAnalysisDB
from core.video.models import Video, VideoMetadata

from ..pipeline import PipelineStage, PipelineContext


class CacheCheckStage(PipelineStage):
    """기존 분석 결과 확인"""
    
    def __init__(self):
        super().__init__("cache_check")
        self.db = VideoAnalysisDB()
    
    def execute(self, context: PipelineContext) -> PipelineContext:
        """캐시 확인 실행"""
        self.update_progress(12, "📊 기존 분석 결과 확인 중...", context)
        
        if context.force_reanalyze:
            self.logger.info("강제 재분석 모드 - 캐시 무시")
            return context
        
        # 기존 분석 결과 확인
        existing_analysis = self.db.get_latest_analysis(context.video_id)
        
        if existing_analysis:
            self.update_progress(15, f"✅ 기존 분석 결과 발견: {context.video_id}", context)
            
            # 기존 결과를 Video 객체로 변환
            video = self._create_video_from_db(context.video_id, existing_analysis)
            
            if video:
                context.video_object = video
                context.analysis_result = video.analysis_result
                
                # 캐시 히트 - 이후 스테이지들을 스킵할 수 있도록 표시
                context.set_stage_result("cache_hit", True)
                self.update_progress(100, "✅ 기존 분석 결과를 불러왔습니다", context)
        
        return context
    
    def _create_video_from_db(self, video_id: str, analysis_data: dict) -> Video:
        """DB에서 Video 객체 생성"""
        # 영상 정보 조회
        video_info = self.db.get_video_info(video_id)
        if not video_info:
            return None
        
        # Video 객체 생성
        video = Video(
            session_id=video_id,
            url=video_info['url'],
            local_path=None,
            metadata=VideoMetadata(
                title=video_info.get('title', ''),
                duration=video_info.get('duration', 0),
                uploader=video_info.get('uploader', ''),
                upload_date=video_info.get('upload_date', ''),
                description=video_info.get('description', ''),
                view_count=video_info.get('view_count', 0),
                like_count=video_info.get('like_count', 0),
                video_id=video_id,
                url=video_info['url'],
                ext='mp4',
                thumbnail=video_info.get('thumbnail', ''),
                webpage_url=video_info.get('webpage_url', video_info['url']),
                tags=video_info.get('tags', []),
                platform=video_info.get('platform', 'youtube')
            )
        )
        
        # 분석 결과 매핑
        video.analysis_result = {
            'genre': analysis_data.get('genre', ''),
            'reasoning': analysis_data.get('reasoning', ''),
            'features': analysis_data.get('features', ''),
            'tags': analysis_data.get('tags', []),
            'expression_style': analysis_data.get('expression_style', ''),
            'mood_tone': analysis_data.get('mood_tone', ''),
            'target_audience': analysis_data.get('target_audience', ''),
            'analyzed_at': analysis_data.get('analysis_date', '')
        }
        
        return video
