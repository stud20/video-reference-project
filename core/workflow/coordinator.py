# core/workflow/coordinator.py
"""
비디오 처리 워크플로우 조율자
"""

import os
from typing import Optional, Callable, List, Dict, Any

from core.database import VideoRepository
from utils.logger import get_logger


class VideoProcessor:
    """비디오 처리 조율자"""
    
    def __init__(self, ai_provider: str = "openai"):
        """
        VideoProcessor 초기화
        
        Args:
            ai_provider: 사용할 AI Provider ("openai", "claude", "gemini")
        """
        self.logger = get_logger(__name__)
        self.ai_provider = ai_provider
        self.db = VideoRepository()
        
        # Pipeline 초기화는 나중에 (순환 참조 방지)
        self._pipeline = None
        
    @property
    def pipeline(self):
        """Pipeline 지연 로딩"""
        if self._pipeline is None:
            from . import create_default_pipeline
            self._pipeline = create_default_pipeline(provider=self.ai_provider)
            self.logger.info("=" * 60)
            self.logger.info("📊 VideoProcessor 초기화 완료")
            self.logger.info(f"  - AI Provider: {self.ai_provider}")
            self.logger.info(f"  - Pipeline 스테이지: {len(self._pipeline.stages)}개")
            self.logger.info("=" * 60)
        return self._pipeline
    
    def process(self, 
                url: str, 
                force_reanalyze: bool = False,
                progress_callback: Optional[Callable] = None) -> Any:
        """
        영상 처리 실행
        
        Args:
            url: 분석할 영상 URL
            force_reanalyze: 기존 분석 결과가 있어도 재분석 여부
            progress_callback: 진행 상황 콜백 (stage, progress, message)
            
        Returns:
            처리 완료된 Video 객체
        """
        try:
            # Pipeline 실행
            context = self.pipeline.execute(
                url=url,
                force_reanalyze=force_reanalyze,
                progress_callback=progress_callback
            )
            
            # Video 객체 반환
            return context.video_object
            
        except Exception as e:
            self.logger.error(f"영상 처리 중 오류 발생: {str(e)}")
            raise
    
    def get_analysis_history(self, video_id: str) -> List[Dict[str, Any]]:
        """특정 영상의 분석 히스토리 조회"""
        return self.db.get_all_analyses(video_id)
    
    def search_by_genre(self, genre: str) -> List[Dict[str, Any]]:
        """장르로 영상 검색"""
        return self.db.search_by_genre(genre)
    
    def search_by_tags(self, tags: List[str]) -> List[Dict[str, Any]]:
        """태그로 영상 검색"""
        return self.db.search_by_tags(tags)
    
    def get_statistics(self) -> Dict[str, Any]:
        """전체 통계 정보 조회"""
        return self.db.get_statistics()
    
    def switch_provider(self, provider: str):
        """AI Provider 변경"""
        self.ai_provider = provider
        self._pipeline = None  # 재초기화를 위해 None으로 설정
        self.logger.info(f"✅ AI Provider 변경: {provider}")
    
    def __del__(self):
        """소멸자: DB 연결 종료"""
        if hasattr(self, 'db'):
            self.db.close()
