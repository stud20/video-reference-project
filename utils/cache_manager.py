# utils/cache_manager.py
"""
지능형 캐싱 시스템
Redis + 로컬 메모리 캐시 하이브리드
"""

import os
import json
import pickle
import hashlib
import threading
import time
from typing import Any, Optional, Dict, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from functools import wraps

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class CacheEntry:
    """캐시 엔트리"""
    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: datetime = None
    size_bytes: int = 0
    
    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = self.created_at
        if isinstance(self.value, (str, bytes)):
            self.size_bytes = len(self.value)
        else:
            # 대략적인 크기 계산
            try:
                self.size_bytes = len(pickle.dumps(self.value))
            except:
                self.size_bytes = 1000  # 기본값
    
    def is_expired(self) -> bool:
        """만료 여부 확인"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def access(self):
        """접근 기록"""
        self.access_count += 1
        self.last_accessed = datetime.now()


class MemoryCache:
    """메모리 기반 캐시"""
    
    def __init__(self, max_size_mb: int = 100, max_entries: int = 1000):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.max_entries = max_entries
        self.cache: Dict[str, CacheEntry] = {}
        self.lock = threading.RLock()
        
        # 통계
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_size_bytes": 0
        }
        
        logger.info(f"MemoryCache 초기화: 최대 {max_size_mb}MB, {max_entries}개 엔트리")
    
    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 조회"""
        with self.lock:
            if key not in self.cache:
                self.stats["misses"] += 1
                return None
            
            entry = self.cache[key]
            
            # 만료 확인
            if entry.is_expired():
                del self.cache[key]
                self.stats["misses"] += 1
                self._update_total_size()
                return None
            
            # 접근 기록
            entry.access()
            self.stats["hits"] += 1
            
            return entry.value
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        """캐시에 값 저장"""
        with self.lock:
            # 만료 시간 계산
            expires_at = None
            if ttl_seconds:
                expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
            
            # 엔트리 생성
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                expires_at=expires_at
            )
            
            # 크기 확인 및 정리
            self._ensure_space(entry.size_bytes)
            
            # 저장
            self.cache[key] = entry
            self._update_total_size()
            
            logger.debug(f"캐시 저장: {key} ({entry.size_bytes} bytes)")
    
    def delete(self, key: str) -> bool:
        """캐시에서 값 삭제"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                self._update_total_size()
                return True
            return False
    
    def clear(self):
        """캐시 전체 삭제"""
        with self.lock:
            self.cache.clear()
            self.stats["total_size_bytes"] = 0
            logger.info("메모리 캐시 전체 삭제")
    
    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계"""
        with self.lock:
            hit_rate = 0.0
            total_requests = self.stats["hits"] + self.stats["misses"]
            if total_requests > 0:
                hit_rate = self.stats["hits"] / total_requests
            
            return {
                **self.stats,
                "entries_count": len(self.cache),
                "max_entries": self.max_entries,
                "max_size_mb": self.max_size_bytes / (1024 * 1024),
                "hit_rate": hit_rate
            }
    
    def _ensure_space(self, required_bytes: int):
        """공간 확보 (LRU 기반 정리)"""
        # 만료된 엔트리 먼저 정리
        self._cleanup_expired()
        
        # 크기 확인
        while (self.stats["total_size_bytes"] + required_bytes > self.max_size_bytes or
               len(self.cache) >= self.max_entries):
            
            if not self.cache:
                break
            
            # LRU 정책: 가장 오래 전에 접근된 항목 제거
            lru_key = min(self.cache.keys(), 
                         key=lambda k: self.cache[k].last_accessed)
            
            del self.cache[lru_key]
            self.stats["evictions"] += 1
            
        self._update_total_size()
    
    def _cleanup_expired(self):
        """만료된 엔트리 정리"""
        expired_keys = [
            key for key, entry in self.cache.items()
            if entry.is_expired()
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.debug(f"만료된 캐시 엔트리 {len(expired_keys)}개 정리")
    
    def _update_total_size(self):
        """전체 크기 업데이트"""
        self.stats["total_size_bytes"] = sum(
            entry.size_bytes for entry in self.cache.values()
        )


class RedisCache:
    """Redis 기반 캐시"""
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0, 
                 password: Optional[str] = None, prefix: str = "video_ref:"):
        self.prefix = prefix
        self.redis_client = None
        self.available = False
        
        if not REDIS_AVAILABLE:
            logger.warning("Redis 라이브러리가 설치되지 않음 - Redis 캐시 비활성화")
            return
        
        try:
            self.redis_client = redis.Redis(
                host=host, port=port, db=db, password=password,
                decode_responses=False,  # bytes로 처리
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            # 연결 테스트
            self.redis_client.ping()
            self.available = True
            logger.info(f"Redis 캐시 연결 성공: {host}:{port}")
            
        except Exception as e:
            logger.warning(f"Redis 연결 실패: {e} - 로컬 캐시만 사용")
            self.available = False
    
    def _make_key(self, key: str) -> str:
        """키에 prefix 추가"""
        return f"{self.prefix}{key}"
    
    def get(self, key: str) -> Optional[Any]:
        """Redis에서 값 조회"""
        if not self.available:
            return None
        
        try:
            redis_key = self._make_key(key)
            data = self.redis_client.get(redis_key)
            
            if data is None:
                return None
            
            # 역직렬화
            return pickle.loads(data)
            
        except Exception as e:
            logger.error(f"Redis GET 오류: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        """Redis에 값 저장"""
        if not self.available:
            return
        
        try:
            redis_key = self._make_key(key)
            data = pickle.dumps(value)
            
            if ttl_seconds:
                self.redis_client.setex(redis_key, ttl_seconds, data)
            else:
                self.redis_client.set(redis_key, data)
                
        except Exception as e:
            logger.error(f"Redis SET 오류: {e}")
    
    def delete(self, key: str) -> bool:
        """Redis에서 값 삭제"""
        if not self.available:
            return False
        
        try:
            redis_key = self._make_key(key)
            result = self.redis_client.delete(redis_key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Redis DELETE 오류: {e}")
            return False
    
    def clear_pattern(self, pattern: str = "*"):
        """패턴 매칭으로 키 삭제"""
        if not self.available:
            return
        
        try:
            redis_pattern = self._make_key(pattern)
            keys = self.redis_client.keys(redis_pattern)
            
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Redis 패턴 삭제: {pattern} ({len(keys)}개 키)")
                
        except Exception as e:
            logger.error(f"Redis 패턴 삭제 오류: {e}")


class HybridCache:
    """메모리 + Redis 하이브리드 캐시"""
    
    def __init__(self, 
                 memory_cache_mb: int = 50,
                 redis_host: str = "localhost",
                 redis_port: int = 6379,
                 redis_password: Optional[str] = None):
        
        # 레벨 1: 메모리 캐시 (빠름)
        self.memory_cache = MemoryCache(max_size_mb=memory_cache_mb)
        
        # 레벨 2: Redis 캐시 (지속성)
        self.redis_cache = RedisCache(
            host=redis_host, 
            port=redis_port, 
            password=redis_password
        )
        
        logger.info("HybridCache 초기화 완료")
    
    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 조회 (메모리 -> Redis 순)"""
        # 1. 메모리 캐시 확인
        value = self.memory_cache.get(key)
        if value is not None:
            return value
        
        # 2. Redis 캐시 확인
        value = self.redis_cache.get(key)
        if value is not None:
            # 메모리 캐시에 복사 (자주 사용되는 데이터)
            self.memory_cache.set(key, value, ttl_seconds=300)  # 5분
            return value
        
        return None
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        """캐시에 값 저장 (양쪽 모두)"""
        # 메모리 캐시에 저장
        self.memory_cache.set(key, value, ttl_seconds)
        
        # Redis 캐시에 저장
        self.redis_cache.set(key, value, ttl_seconds)
    
    def delete(self, key: str) -> bool:
        """캐시에서 값 삭제"""
        mem_deleted = self.memory_cache.delete(key)
        redis_deleted = self.redis_cache.delete(key)
        return mem_deleted or redis_deleted
    
    def clear(self):
        """전체 캐시 삭제"""
        self.memory_cache.clear()
        self.redis_cache.clear_pattern("*")
    
    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계"""
        return {
            "memory_cache": self.memory_cache.get_stats(),
            "redis_available": self.redis_cache.available
        }


class CacheManager:
    """캐시 관리자"""
    
    def __init__(self):
        # Redis 설정 (환경변수에서)
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_password = os.getenv("REDIS_PASSWORD")
        
        self.cache = HybridCache(
            memory_cache_mb=50,
            redis_host=redis_host,
            redis_port=redis_port,
            redis_password=redis_password
        )
        
        logger.info("CacheManager 초기화 완료")
    
    def _make_cache_key(self, prefix: str, identifier: str) -> str:
        """캐시 키 생성"""
        # URL이나 긴 식별자는 해시로 변환
        if len(identifier) > 100:
            identifier = hashlib.md5(identifier.encode()).hexdigest()
        
        return f"{prefix}:{identifier}"
    
    def get_video_analysis(self, video_url: str) -> Optional[Dict[str, Any]]:
        """비디오 분석 결과 캐시 조회"""
        key = self._make_cache_key("analysis", video_url)
        return self.cache.get(key)
    
    def set_video_analysis(self, video_url: str, analysis_result: Dict[str, Any], 
                          ttl_hours: int = 24):
        """비디오 분석 결과 캐시 저장"""
        key = self._make_cache_key("analysis", video_url)
        ttl_seconds = ttl_hours * 3600
        self.cache.set(key, analysis_result, ttl_seconds)
        logger.info(f"분석 결과 캐시됨: {video_url}")
    
    def get_video_metadata(self, video_url: str) -> Optional[Dict[str, Any]]:
        """비디오 메타데이터 캐시 조회"""
        key = self._make_cache_key("metadata", video_url)
        return self.cache.get(key)
    
    def set_video_metadata(self, video_url: str, metadata: Dict[str, Any],
                          ttl_hours: int = 168):  # 1주일
        """비디오 메타데이터 캐시 저장"""
        key = self._make_cache_key("metadata", video_url)
        ttl_seconds = ttl_hours * 3600
        self.cache.set(key, metadata, ttl_seconds)
    
    def get_scene_images(self, video_id: str) -> Optional[List[str]]:
        """씬 이미지 경로 캐시 조회"""
        key = self._make_cache_key("scenes", video_id)
        return self.cache.get(key)
    
    def set_scene_images(self, video_id: str, image_paths: List[str],
                        ttl_hours: int = 72):  # 3일
        """씬 이미지 경로 캐시 저장"""
        key = self._make_cache_key("scenes", video_id)
        ttl_seconds = ttl_hours * 3600
        self.cache.set(key, image_paths, ttl_seconds)
    
    def invalidate_video(self, video_url: str):
        """특정 비디오 관련 캐시 무효화"""
        video_id = hashlib.md5(video_url.encode()).hexdigest()
        
        keys_to_delete = [
            self._make_cache_key("analysis", video_url),
            self._make_cache_key("metadata", video_url),
            self._make_cache_key("scenes", video_id)
        ]
        
        for key in keys_to_delete:
            self.cache.delete(key)
        
        logger.info(f"비디오 캐시 무효화: {video_url}")
    
    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계"""
        return self.cache.get_stats()
    
    def cleanup(self):
        """캐시 정리"""
        # 메모리 캐시의 만료된 항목 정리는 자동으로 수행됨
        pass


# 싱글톤 인스턴스
_cache_manager = None
_cache_lock = threading.Lock()


def get_cache_manager() -> CacheManager:
    """캐시 매니저 싱글톤 인스턴스 반환"""
    global _cache_manager
    if _cache_manager is None:
        with _cache_lock:
            if _cache_manager is None:
                _cache_manager = CacheManager()
    return _cache_manager


def cached(ttl_seconds: int = 3600, key_func: Optional[Callable] = None):
    """함수 결과 캐싱 데코레이터"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache_manager()
            
            # 캐시 키 생성
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # 기본 키 생성 (함수명 + 인수 해시)
                key_parts = [func.__name__]
                if args:
                    key_parts.append(hashlib.md5(str(args).encode()).hexdigest()[:8])
                if kwargs:
                    key_parts.append(hashlib.md5(str(kwargs).encode()).hexdigest()[:8])
                cache_key = ":".join(key_parts)
            
            # 캐시에서 조회
            cached_result = cache.cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"캐시 히트: {func.__name__}")
                return cached_result
            
            # 함수 실행
            result = func(*args, **kwargs)
            
            # 결과 캐싱
            cache.cache.set(cache_key, result, ttl_seconds)
            logger.debug(f"함수 결과 캐시됨: {func.__name__}")
            
            return result
        
        return wrapper
    return decorator
