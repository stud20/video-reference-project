# src/pipeline/base_pipeline.py
"""Pipeline 기본 구조"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
import time

from utils.logger import get_logger


class StageStatus(Enum):
    """스테이지 상태"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PipelineContext:
    """Pipeline 실행 컨텍스트"""
    # 입력 데이터
    url: str
    force_reanalyze: bool = False
    
    # 처리 중 생성되는 데이터
    platform: Optional[str] = None
    video_id: Optional[str] = None
    video_object: Optional[Any] = None  # Video 객체
    download_result: Optional[Dict[str, Any]] = None
    scenes: Optional[List[Any]] = None
    analysis_result: Optional[Dict[str, Any]] = None
    
    # 메타데이터
    start_time: float = field(default_factory=time.time)
    stage_results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    
    def add_error(self, stage: str, error: str):
        """에러 추가"""
        self.errors.append(f"[{stage}] {error}")
    
    def set_stage_result(self, stage: str, result: Any):
        """스테이지 결과 저장"""
        self.stage_results[stage] = result


class PipelineStage(ABC):
    """Pipeline 스테이지 추상 클래스"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(f"pipeline.{name}")
        self.status = StageStatus.PENDING
        self.progress_callback: Optional[Callable] = None
    
    @abstractmethod
    def execute(self, context: PipelineContext) -> PipelineContext:
        """스테이지 실행"""
        pass
    
    def can_skip(self, context: PipelineContext) -> bool:
        """스테이지 스킵 가능 여부"""
        return False
    
    def update_progress(self, progress: int, message: str, context: PipelineContext):
        """진행 상황 업데이트"""
        if self.progress_callback:
            self.progress_callback(self.name, progress, message)
        # 로그 출력 제거 (중복 방지)
    
    def run(self, context: PipelineContext, 
            progress_callback: Optional[Callable] = None) -> PipelineContext:
        """스테이지 실행 래퍼"""
        self.progress_callback = progress_callback
        self.status = StageStatus.RUNNING
        
        try:
            # 스킵 체크
            if self.can_skip(context):
                self.logger.info(f"⏭️ {self.name} 스테이지 스킵")
                self.status = StageStatus.SKIPPED
                return context
            
            # 실행
            # self.logger.info(f"▶️ {self.name} 스테이지 시작")  # 중복 제거
            start_time = time.time()
            
            context = self.execute(context)
            
            elapsed = time.time() - start_time
            self.logger.info(f"✅ {self.name} 스테이지 완료 ({elapsed:.2f}초)")
            self.status = StageStatus.SUCCESS
            
            return context
            
        except Exception as e:
            self.status = StageStatus.FAILED
            error_msg = f"❌ {self.name} 스테이지 실패: {str(e)}"
            self.logger.error(error_msg)
            context.add_error(self.name, str(e))
            raise


class VideoPipeline:
    """비디오 처리 파이프라인"""
    
    def __init__(self):
        self.logger = get_logger("pipeline")
        self.stages: List[PipelineStage] = []
        self.progress_callback: Optional[Callable] = None
    
    def add_stage(self, stage: PipelineStage) -> 'VideoPipeline':
        """스테이지 추가"""
        self.stages.append(stage)
        return self
    
    def execute(self, 
               url: str, 
               force_reanalyze: bool = False,
               progress_callback: Optional[Callable] = None) -> PipelineContext:
        """파이프라인 실행"""
        self.progress_callback = progress_callback
        
        # 컨텍스트 생성
        context = PipelineContext(
            url=url,
            force_reanalyze=force_reanalyze
        )
        
        self.logger.info("=" * 60)
        self.logger.info(f"🚀 Pipeline 시작 - URL: {url}")
        self.logger.info(f"📊 총 {len(self.stages)}개 스테이지")
        self.logger.info("=" * 60)
        
        # 각 스테이지 실행
        for i, stage in enumerate(self.stages):
            try:
                self.logger.info(f"\n[{i+1}/{len(self.stages)}] {stage.name}")
                context = stage.run(context, progress_callback)
                
            except Exception as e:
                self.logger.error(f"Pipeline 중단: {stage.name} 실패")
                if progress_callback:
                    progress_callback("error", 0, f"❌ {stage.name} 실패: {str(e)}")
                raise
        
        # 완료
        elapsed = time.time() - context.start_time
        self.logger.info("\n" + "=" * 60)
        self.logger.info(f"✅ Pipeline 완료 (총 {elapsed:.2f}초)")
        self.logger.info("=" * 60)
        
        return context
