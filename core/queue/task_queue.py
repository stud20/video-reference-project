# core/queue/task_queue.py
"""
비동기 작업 큐 시스템
동시 처리 제한 및 우선순위 관리
"""

import asyncio
import threading
import queue
import time
import uuid
from enum import Enum
from dataclasses import dataclass, field
from typing import Callable, Dict, Any, Optional, List
from datetime import datetime, timedelta
import concurrent.futures

from utils.logger import get_logger

logger = get_logger(__name__)


class TaskPriority(Enum):
    """작업 우선순위"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class TaskStatus(Enum):
    """작업 상태"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """작업 정의"""
    id: str
    name: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    session_id: str = ""
    
    # 상태 관리
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    result: Any = None
    
    # 콜백
    progress_callback: Optional[Callable] = None
    completion_callback: Optional[Callable] = None
    
    def __lt__(self, other):
        """우선순위 비교 (높은 우선순위가 먼저)"""
        return self.priority.value > other.priority.value


@dataclass
class TaskResult:
    """작업 결과"""
    task_id: str
    status: TaskStatus
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)


class TaskQueue:
    """작업 큐 관리자"""
    
    def __init__(self, max_workers: int = 8, max_queue_size: int = 100):
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        
        # 우선순위 큐
        self.task_queue = queue.PriorityQueue(maxsize=max_queue_size)
        
        # 실행 중인 작업 추적
        self.running_tasks: Dict[str, Task] = {}
        self.completed_tasks: Dict[str, TaskResult] = {}
        
        # 스레드 풀
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="TaskWorker"
        )
        
        # 상태 관리
        self.is_running = False
        self.lock = threading.RLock()
        
        # 통계
        self.stats = {
            "total_submitted": 0,
            "total_completed": 0,
            "total_failed": 0,
            "total_cancelled": 0
        }
        
        logger.info(f"TaskQueue 초기화: 최대 워커 {max_workers}개, 큐 크기 {max_queue_size}")
    
    def start(self):
        """큐 처리 시작"""
        if self.is_running:
            return
        
        self.is_running = True
        
        # 백그라운드에서 작업 처리
        threading.Thread(
            target=self._process_queue, 
            daemon=True, 
            name="TaskQueueProcessor"
        ).start()
        
        logger.info("TaskQueue 시작됨")
    
    def stop(self):
        """큐 처리 중지"""
        self.is_running = False
        self.executor.shutdown(wait=True)
        logger.info("TaskQueue 중지됨")
    
    def submit_task(self, 
                   name: str,
                   func: Callable,
                   args: tuple = (),
                   kwargs: dict = None,
                   priority: TaskPriority = TaskPriority.NORMAL,
                   session_id: str = "",
                   progress_callback: Optional[Callable] = None,
                   completion_callback: Optional[Callable] = None) -> str:
        """작업 제출"""
        if kwargs is None:
            kwargs = {}
        
        # 큐 크기 확인
        if self.task_queue.qsize() >= self.max_queue_size:
            raise RuntimeError(f"작업 큐가 가득함 (최대 {self.max_queue_size}개)")
        
        # 작업 생성
        task = Task(
            id=str(uuid.uuid4()),
            name=name,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            session_id=session_id,
            progress_callback=progress_callback,
            completion_callback=completion_callback
        )
        
        # 큐에 추가
        try:
            self.task_queue.put(task, timeout=1.0)
            
            with self.lock:
                self.stats["total_submitted"] += 1
            
            logger.info(f"작업 제출됨: {name} (ID: {task.id[:8]}, 우선순위: {priority.name})")
            return task.id
            
        except queue.Full:
            raise RuntimeError("작업 큐 추가 타임아웃")
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """작업 상태 조회"""
        with self.lock:
            if task_id in self.running_tasks:
                return self.running_tasks[task_id].status
            elif task_id in self.completed_tasks:
                return self.completed_tasks[task_id].status
            else:
                return None
    
    def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """작업 결과 조회"""
        with self.lock:
            return self.completed_tasks.get(task_id)
    
    def cancel_task(self, task_id: str) -> bool:
        """작업 취소 (대기 중인 작업만 가능)"""
        with self.lock:
            if task_id in self.running_tasks:
                # 실행 중인 작업은 취소 불가
                return False
            
            # 큐에서 제거 시도 (실제로는 어려움)
            # 대신 완료된 작업으로 마킹
            result = TaskResult(
                task_id=task_id,
                status=TaskStatus.CANCELLED
            )
            self.completed_tasks[task_id] = result
            self.stats["total_cancelled"] += 1
            
            logger.info(f"작업 취소됨: {task_id[:8]}")
            return True
    
    def get_queue_status(self) -> Dict[str, Any]:
        """큐 상태 정보"""
        with self.lock:
            return {
                "queue_size": self.task_queue.qsize(),
                "max_queue_size": self.max_queue_size,
                "running_tasks": len(self.running_tasks),
                "max_workers": self.max_workers,
                "is_running": self.is_running,
                "stats": self.stats.copy()
            }
    
    def get_session_tasks(self, session_id: str) -> List[Dict[str, Any]]:
        """특정 세션의 작업 목록"""
        with self.lock:
            tasks = []
            
            # 실행 중인 작업
            for task in self.running_tasks.values():
                if task.session_id == session_id:
                    tasks.append({
                        "id": task.id,
                        "name": task.name,
                        "status": task.status.value,
                        "created_at": task.created_at.isoformat(),
                        "started_at": task.started_at.isoformat() if task.started_at else None
                    })
            
            return tasks
    
    def _process_queue(self):
        """큐 처리 루프"""
        logger.info("작업 큐 처리 시작")
        
        while self.is_running:
            try:
                # 큐에서 작업 가져오기 (1초 타임아웃)
                task = self.task_queue.get(timeout=1.0)
                
                # 실행 중인 작업으로 이동
                with self.lock:
                    self.running_tasks[task.id] = task
                
                # 스레드 풀에 작업 제출
                future = self.executor.submit(self._execute_task, task)
                
                # 논블로킹으로 결과 처리
                threading.Thread(
                    target=self._handle_task_completion,
                    args=(task, future),
                    daemon=True
                ).start()
                
            except queue.Empty:
                # 타임아웃 - 계속 진행
                continue
            except Exception as e:
                logger.error(f"큐 처리 오류: {e}")
                time.sleep(1)
        
        logger.info("작업 큐 처리 종료")
    
    def _execute_task(self, task: Task) -> Any:
        """작업 실행"""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        
        logger.info(f"작업 실행 시작: {task.name} (ID: {task.id[:8]})")
        
        try:
            # 진행 상황 콜백 래퍼
            def wrapped_progress_callback(*args, **kwargs):
                if task.progress_callback:
                    task.progress_callback(*args, **kwargs)
            
            # 작업 실행
            if task.progress_callback:
                # 진행 상황 콜백이 있는 경우, kwargs에 추가
                task.kwargs['progress_callback'] = wrapped_progress_callback
            
            result = task.func(*task.args, **task.kwargs)
            
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = datetime.now()
            
            logger.info(f"작업 완료: {task.name} (ID: {task.id[:8]})")
            return result
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()
            
            logger.error(f"작업 실패: {task.name} (ID: {task.id[:8]}) - {e}")
            raise
    
    def _handle_task_completion(self, task: Task, future: concurrent.futures.Future):
        """작업 완료 처리"""
        try:
            # 결과 대기
            result = future.result()
            
            # 완료 콜백 호출
            if task.completion_callback:
                try:
                    task.completion_callback(task.id, result, None)
                except Exception as e:
                    logger.error(f"완료 콜백 오류: {e}")
            
        except Exception as e:
            # 실패 콜백 호출
            if task.completion_callback:
                try:
                    task.completion_callback(task.id, None, str(e))
                except Exception as cb_error:
                    logger.error(f"실패 콜백 오류: {cb_error}")
        
        finally:
            # 작업 정리
            with self.lock:
                # 실행 목록에서 제거
                if task.id in self.running_tasks:
                    del self.running_tasks[task.id]
                
                # 완료 목록에 추가
                execution_time = 0.0
                if task.started_at and task.completed_at:
                    execution_time = (task.completed_at - task.started_at).total_seconds()
                
                result = TaskResult(
                    task_id=task.id,
                    status=task.status,
                    result=task.result,
                    error=task.error,
                    execution_time=execution_time
                )
                
                self.completed_tasks[task.id] = result
                
                # 통계 업데이트
                if task.status == TaskStatus.COMPLETED:
                    self.stats["total_completed"] += 1
                elif task.status == TaskStatus.FAILED:
                    self.stats["total_failed"] += 1
                
                # 오래된 완료 작업 정리 (메모리 절약)
                self._cleanup_old_tasks()
    
    def _cleanup_old_tasks(self):
        """오래된 완료 작업 정리"""
        cutoff_time = datetime.now() - timedelta(hours=1)  # 1시간 이전
        
        to_remove = [
            task_id for task_id, result in self.completed_tasks.items()
            if result.created_at < cutoff_time
        ]
        
        for task_id in to_remove:
            del self.completed_tasks[task_id]
        
        if to_remove:
            logger.info(f"오래된 작업 {len(to_remove)}개 정리됨")


# 전역 작업 큐 인스턴스
_task_queue = None
_queue_lock = threading.Lock()


def get_task_queue() -> TaskQueue:
    """작업 큐 싱글톤 인스턴스 반환"""
    global _task_queue
    if _task_queue is None:
        with _queue_lock:
            if _task_queue is None:
                _task_queue = TaskQueue()
                _task_queue.start()  # 자동 시작
    return _task_queue


def submit_video_analysis_task(url: str, 
                              session_id: str,
                              model_name: str = "gpt-4o",
                              progress_callback: Optional[Callable] = None) -> str:
    """비디오 분석 작업 제출"""
    from core.handlers.video_handler import handle_video_analysis_enhanced
    
    queue = get_task_queue()
    
    # 완료 콜백 정의 - 세션 상태 업데이트
    def completion_callback(task_id: str, result: Any, error: Optional[str]):
        try:
            from utils.session_manager import get_session_manager
            session_manager = get_session_manager()
            
            if error:
                logger.error(f"작업 실패: {task_id[:8]}... - {error}")
                # 실패 시에도 작업 종료 처리
                session_manager.end_task(session_id, f"video_analysis_{url}")
            else:
                logger.info(f"작업 성공: {task_id[:8]}...")
                session_manager.end_task(session_id, f"video_analysis_{url}")
                
        except Exception as e:
            logger.error(f"완료 콜백 오류: {e}")
    
    return queue.submit_task(
        name=f"video_analysis_{url}",
        func=handle_video_analysis_enhanced,
        kwargs={
            "video_url": url,
            "precision_level": 5,
            "console_callback": progress_callback or (lambda x: None),
            "model_name": model_name
        },
        priority=TaskPriority.NORMAL,
        session_id=session_id,
        progress_callback=progress_callback,
        completion_callback=completion_callback
    )
