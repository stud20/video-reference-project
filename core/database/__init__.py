# core/database/__init__.py
"""데이터베이스 관리"""

from .repository import VideoAnalysisDB as VideoRepository

__all__ = ['VideoRepository']