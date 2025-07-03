# utils/session_manager.py
"""
사용자별 세션 관리 및 작업 공간 격리
"""

import os
import uuid
import shutil
import hashlib
import threading
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import streamlit as st
from dataclasses import dataclass
from pathlib import Path
import psutil
import time

from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class UserSession:
    """사용자 세션 정보"""
    session_id: str
    user_id: str
    workspace_dir: str
    created_at: datetime
    last_active: datetime
    active_tasks: int = 0
    memory_usage: int = 0  # MB
    status: str = "active"  # active, processing, idle, expired


class SessionManager:
    """사용자 세션 관리자"""
    
    def __init__(self, max_concurrent_users: int = 15, max_concurrent_tasks: int = 8):
        self.max_concurrent_users = max_concurrent_users
        self.max_concurrent_tasks = max_concurrent_tasks
        self.sessions: Dict[str, UserSession] = {}
        self.task_queue = []
        self.lock = threading.RLock()
        self.base_workspace = Path("data/workspaces")
        self.base_workspace.mkdir(parents=True, exist_ok=True)
        
        # 시스템 리소스 모니터링
        self.system_monitor = SystemResourceMonitor()
        
        logger.info(f"SessionManager 초기화: 최대 {max_concurrent_users}명, 동시 작업 {max_concurrent_tasks}개")
    
    def get_or_create_session(self) -> UserSession:
        """현재 사용자의 세션 가져오기 또는 생성"""
        with self.lock:
            # Streamlit 세션 ID 기반 사용자 식별
            if hasattr(st, 'session_state') and hasattr(st.session_state, 'session_id'):
                session_id = st.session_state.session_id
            else:
                session_id = self._generate_session_id()
                if hasattr(st, 'session_state'):
                    st.session_state.session_id = session_id
            
            # 기존 세션 확인
            if session_id in self.sessions:
                session = self.sessions[session_id]
                session.last_active = datetime.now()
                return session
            
            # 새 세션 생성 (동시 사용자 수 체크)
            if len(self.sessions) >= self.max_concurrent_users:
                # 가장 오래된 비활성 세션 정리
                self._cleanup_inactive_sessions()
                
                if len(self.sessions) >= self.max_concurrent_users:
                    raise RuntimeError(f"최대 동시 사용자 수({self.max_concurrent_users}명)를 초과했습니다.")
            
            # 작업 공간 생성
            workspace_dir = self.base_workspace / session_id
            workspace_dir.mkdir(parents=True, exist_ok=True)
            
            # 세션 객체 생성
            user_session = UserSession(
                session_id=session_id,
                user_id=self._generate_user_id(session_id),
                workspace_dir=str(workspace_dir),
                created_at=datetime.now(),
                last_active=datetime.now()
            )
            
            self.sessions[session_id] = user_session
            logger.info(f"새 사용자 세션 생성: {session_id[:8]}... (총 {len(self.sessions)}명 접속)")
            
            return user_session
    
    def start_task(self, session_id: str, task_name: str) -> bool:
        """작업 시작 (동시 작업 수 제한)"""
        with self.lock:
            if session_id not in self.sessions:
                return False
            
            session = self.sessions[session_id]
            
            # 전체 시스템 동시 작업 수 체크
            total_active_tasks = sum(s.active_tasks for s in self.sessions.values())
            if total_active_tasks >= self.max_concurrent_tasks:
                logger.warning(f"최대 동시 작업 수({self.max_concurrent_tasks}개) 초과로 작업 대기")
                return False
            
            # 시스템 리소스 체크
            if not self.system_monitor.can_start_new_task():
                logger.warning("시스템 리소스 부족으로 작업 대기")
                return False
            
            session.active_tasks += 1
            session.status = "processing"
            session.last_active = datetime.now()
            
            logger.info(f"작업 시작: {task_name} (세션: {session_id[:8]}..., 활성 작업: {session.active_tasks}개)")
            return True
    
    def end_task(self, session_id: str, task_name: str):
        """작업 종료"""
        with self.lock:
            if session_id not in self.sessions:
                return
            
            session = self.sessions[session_id]
            session.active_tasks = max(0, session.active_tasks - 1)
            
            if session.active_tasks == 0:
                session.status = "idle"
            
            session.last_active = datetime.now()
            logger.info(f"작업 완료: {task_name} (세션: {session_id[:8]}..., 남은 작업: {session.active_tasks}개)")
    
    def mark_pipeline_completed(self, session_id: str):
        """파이프라인 완료 시 세션 상태 업데이트 - 5분 후 정리 대상이 됨"""
        with self.lock:
            if session_id not in self.sessions:
                return
            
            session = self.sessions[session_id]
            session.last_active = datetime.now()
            session.status = "completed"
            
            logger.info(f"파이프라인 완료: {session_id[:8]}... - 5분 후 정리 예정")
    
    def get_workspace_path(self, session_id: str, subdirectory: str = "") -> str:
        """작업 공간 경로 반환"""
        if session_id not in self.sessions:
            raise KeyError(f"세션을 찾을 수 없습니다: {session_id}")
        
        workspace = Path(self.sessions[session_id].workspace_dir)
        if subdirectory:
            workspace = workspace / subdirectory
            workspace.mkdir(parents=True, exist_ok=True)
        
        return str(workspace)
    
    def cleanup_session(self, session_id: str):
        """세션 정리"""
        with self.lock:
            if session_id not in self.sessions:
                return
            
            session = self.sessions[session_id]
            
            # 작업 공간 삭제
            try:
                if os.path.exists(session.workspace_dir):
                    shutil.rmtree(session.workspace_dir)
                    logger.info(f"작업 공간 삭제: {session.workspace_dir}")
            except Exception as e:
                logger.error(f"작업 공간 삭제 실패: {e}")
            
            # 세션 제거
            del self.sessions[session_id]
            logger.info(f"세션 정리 완료: {session_id[:8]}...")
    
    def _cleanup_inactive_sessions(self):
        """비활성 세션 정리"""
        now = datetime.now()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            # 5분 이상 비활성 세션 정리
            if (now - session.last_active).total_seconds() > 300:  # 5분
                if session.active_tasks == 0:  # 진행 중인 작업이 없는 경우만
                    expired_sessions.append(session_id)
                    logger.info(f"세션 만료 대상: {session_id[:8]}... (상태: {session.status}, 마지막 활동: {session.last_active.strftime('%H:%M:%S')})")
        
        for session_id in expired_sessions:
            logger.info(f"비활성 세션 정리: {session_id[:8]}...")
            self.cleanup_session(session_id)
    
    def get_session_stats(self) -> Dict[str, Any]:
        """세션 통계 정보"""
        with self.lock:
            total_sessions = len(self.sessions)
            active_sessions = len([s for s in self.sessions.values() if s.status == "active"])
            processing_sessions = len([s for s in self.sessions.values() if s.status == "processing"])
            total_tasks = sum(s.active_tasks for s in self.sessions.values())
            
            return {
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "processing_sessions": processing_sessions,
                "total_active_tasks": total_tasks,
                "max_concurrent_users": self.max_concurrent_users,
                "max_concurrent_tasks": self.max_concurrent_tasks,
                "system_resources": self.system_monitor.get_current_usage()
            }
    
    def _generate_session_id(self) -> str:
        """세션 ID 생성"""
        return str(uuid.uuid4()).replace('-', '')
    
    def _generate_user_id(self, session_id: str) -> str:
        """사용자 ID 생성 (해시 기반)"""
        return hashlib.md5(session_id.encode()).hexdigest()[:12]


class SystemResourceMonitor:
    """시스템 리소스 모니터링"""
    
    def __init__(self, max_cpu_percent: float = 70.0, max_memory_percent: float = 80.0):
        self.max_cpu_percent = max_cpu_percent
        self.max_memory_percent = max_memory_percent
    
    def can_start_new_task(self) -> bool:
        """새 작업 시작 가능 여부"""
        try:
            # CPU 사용률 체크
            cpu_percent = psutil.cpu_percent(interval=0.1)
            if cpu_percent > self.max_cpu_percent:
                logger.warning(f"CPU 사용률 과부하: {cpu_percent:.1f}%")
                return False
            
            # 메모리 사용률 체크
            memory = psutil.virtual_memory()
            if memory.percent > self.max_memory_percent:
                logger.warning(f"메모리 사용률 과부하: {memory.percent:.1f}%")
                return False
            
            return True
        except Exception as e:
            logger.error(f"시스템 리소스 모니터링 오류: {e}")
            return True  # 모니터링 실패 시 작업 허용
    
    def get_current_usage(self) -> Dict[str, float]:
        """현재 시스템 사용률"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "available_memory_mb": memory.available / (1024 * 1024)
            }
        except Exception as e:
            logger.error(f"시스템 사용률 조회 오류: {e}")
            return {"error": str(e)}


# 전역 세션 매니저 인스턴스
session_manager = SessionManager()


def get_session_manager() -> SessionManager:
    """세션 매니저 인스턴스 반환"""
    return session_manager


def get_current_session() -> UserSession:
    """현재 사용자 세션 반환"""
    return session_manager.get_or_create_session()


def get_user_workspace(subdirectory: str = "") -> str:
    """현재 사용자의 작업 공간 경로 반환"""
    session = get_current_session()
    return session_manager.get_workspace_path(session.session_id, subdirectory)
