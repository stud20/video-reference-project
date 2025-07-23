# core/workflow/stages/ai_analyzer.py
"""AI 분석 스테이지"""

import os
from core.analysis import VideoAnalyzer
from core.analysis.providers import OpenAIProvider, ClaudeProvider, GeminiProvider
from core.database import VideoRepository

from ..pipeline import PipelineStage, PipelineContext


class AIAnalysisStage(PipelineStage):
    """AI 영상 분석"""
    
    def __init__(self, provider_name: str = "openai"):
        super().__init__("ai_analysis")
        # 환경변수에서 모델명 확인
        model_name = os.getenv("AI_MODEL_NAME", "gpt-4o")
        self.model_name = model_name
        self.provider_name = self._get_provider_from_model(model_name)
        self.analyzer = self._create_analyzer_for_model(model_name)
        self.db = VideoRepository()
    
    def _get_provider_from_model(self, model_name: str) -> str:
        """모델명에서 Provider 이름 추출"""
        if "claude" in model_name.lower():
            return "claude"
        elif "gemini" in model_name.lower():
            return "gemini"
        else:
            return "openai"
    
    def _create_analyzer_for_model(self, model_name: str) -> VideoAnalyzer:
        """모델명에 따른 Analyzer 생성"""
        # 모델별 Provider 설정
        if "claude" in model_name.lower():
            provider = ClaudeProvider(model=model_name)
        elif "gemini" in model_name.lower():
            provider = GeminiProvider(model=model_name)
        else:
            provider = OpenAIProvider(model=model_name)
        
        return VideoAnalyzer(provider=provider)
    
    def _create_analyzer(self, provider_name: str) -> VideoAnalyzer:
        """Provider에 따른 Analyzer 생성 (호환성)"""
        providers = {
            "openai": OpenAIProvider,
            "claude": ClaudeProvider,
            "gemini": GeminiProvider
        }
        
        provider_class = providers.get(provider_name, OpenAIProvider)
        provider = provider_class()
        
        return VideoAnalyzer(provider=provider)
    
    def can_skip(self, context: PipelineContext) -> bool:
        """캐시 히트 시 스킵"""
        return context.stage_results.get("cache_hit", False)
    
    def execute(self, context: PipelineContext) -> PipelineContext:
        """AI 분석 실행"""
        video = context.video_object
        
        if not video.scenes:
            self.logger.warning("분석할 씬이 없습니다")
            return context
        
        # 모델 표시명
        model_display = {
            "gemini-2.0-flash": "Google Gemini",
            "gpt-4o": "GPT-4o",
            "claude-sonnet-4-20250514": "Claude Sonnet 4"
        }.get(self.model_name, self.model_name)
        
        self.update_progress(0, f"🤖 {model_display} AI 분석 시작...", context)
        
        # custom_prompt가 있으면 analyzer에 전달
        if context.custom_prompt:
            self.analyzer.custom_prompt = context.custom_prompt
            self.logger.info(f"📝 맞춤형 분석 프롬프트 사용")
        
        # AI 분석 실행
        analysis_result = self.analyzer.analyze_video(video)
        
        # 사용된 전체 프롬프트 저장
        if hasattr(self.analyzer, 'last_full_prompt'):
            context.full_prompt_used = self.analyzer.last_full_prompt
        
        if analysis_result:
            self.update_progress(70, f"✅ AI 분석 성공: {analysis_result.get('genre', 'Unknown')}", context)
            
            # Video 객체에 저장
            video.analysis_result = analysis_result
            context.analysis_result = analysis_result
            
            # 전체 프롬프트도 Video 객체에 저장
            if hasattr(context, 'full_prompt_used'):
                video.full_prompt_used = context.full_prompt_used
            
            # DB에 저장
            analysis_data = {
                'genre': analysis_result.get('genre', ''),
                'reasoning': analysis_result.get('reasoning', ''),
                'features': analysis_result.get('features', ''),
                'tags': analysis_result.get('tags', []),
                'expression_style': analysis_result.get('expression_style', ''),
                'mood_tone': analysis_result.get('mood_tone', ''),
                'target_audience': analysis_result.get('target_audience', ''),
                'analyzed_scenes': [os.path.basename(scene.frame_path) for scene in video.scenes[:10]],
                'token_usage': {},
                'model_used': analysis_result.get('model_used', f'{self.provider_name}:unknown')
            }
            
            self.db.save_analysis_result(context.video_id, analysis_data)
            
            self.update_progress(100, "✅ AI 분석 완료", context)
        else:
            self.update_progress(80, "⚠️ AI 분석 결과가 없습니다", context)
        
        return context
