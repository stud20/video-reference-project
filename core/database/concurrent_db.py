# core/database/concurrent_db.py
"""
동시성을 지원하는 개선된 데이터베이스 시스템
SQLite + 커넥션 풀링 + 트랜잭션 관리
"""

import sqlite3
import threading
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
from contextlib import contextmanager
import queue
import time
from dataclasses import dataclass, asdict

from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class VideoRecord:
    """비디오 레코드 데이터 클래스"""
    id: Optional[int] = None
    url: str = ""
    title: str = ""
    platform: str = ""
    video_id: str = ""
    duration: Optional[float] = None
    view_count: Optional[int] = None
    upload_date: Optional[str] = None
    genre: str = ""
    mood: str = ""
    tags: List[str] = None
    analysis_result: Dict[str, Any] = None
    thumbnail_path: str = ""
    scenes_count: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.analysis_result is None:
            self.analysis_result = {}
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.now().isoformat()


class ConnectionPool:
    """SQLite 커넥션 풀"""
    
    def __init__(self, db_path: str, max_connections: int = 10):
        self.db_path = db_path
        self.max_connections = max_connections
        self.pool = queue.Queue(maxsize=max_connections)
        self.lock = threading.Lock()
        self._create_connections()
    
    def _create_connections(self):
        """커넥션 풀 초기화"""
        for _ in range(self.max_connections):
            conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0,  # 30초 타임아웃
                isolation_level=None  # 자동 커밋 활성화
            )
            conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환
            # WAL 모드 활성화 (동시 읽기/쓰기 성능 향상)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")  # 성능 향상
            conn.execute("PRAGMA cache_size=10000")    # 캐시 크기 증가
            self.pool.put(conn)
    
    @contextmanager
    def get_connection(self):
        """커넥션 가져오기 (컨텍스트 매니저)"""
        conn = None
        try:
            conn = self.pool.get(timeout=10)  # 10초 대기
            yield conn
        except queue.Empty:
            raise RuntimeError("데이터베이스 연결 풀이 가득참 - 잠시 후 다시 시도해주세요")
        except Exception as e:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                self.pool.put(conn)
    
    def close_all(self):
        """모든 커넥션 종료"""
        while not self.pool.empty():
            try:
                conn = self.pool.get_nowait()
                conn.close()
            except queue.Empty:
                break


class ConcurrentVideoDatabase:
    """동시성을 지원하는 비디오 데이터베이스"""
    
    def __init__(self, db_path: str = "data/database/videos.db", max_connections: int = 10):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # 커넥션 풀 초기화
        self.pool = ConnectionPool(db_path, max_connections)
        
        # 테이블 생성
        self._create_tables()
        
        # 성능 카운터
        self._query_count = 0
        self._lock = threading.Lock()
        
        logger.info(f"ConcurrentVideoDatabase 초기화: {db_path} (커넥션 풀: {max_connections})")
    
    def _create_tables(self):
        """테이블 생성"""
        with self.pool.get_connection() as conn:
            # videos 테이블
            conn.execute("""
                CREATE TABLE IF NOT EXISTS videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    title TEXT,
                    platform TEXT,
                    video_id TEXT,
                    duration REAL,
                    view_count INTEGER,
                    upload_date TEXT,
                    genre TEXT,
                    mood TEXT,
                    tags TEXT,  -- JSON 배열
                    analysis_result TEXT,  -- JSON 객체
                    thumbnail_path TEXT,
                    scenes_count INTEGER DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT,
                    UNIQUE(url)
                )
            """)
            
            # 인덱스 생성 (검색 성능 향상)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_videos_url ON videos(url)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_videos_platform ON videos(platform)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_videos_genre ON videos(genre)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_videos_created_at ON videos(created_at)")
            
            conn.commit()
    
    def add_video(self, video: VideoRecord) -> int:
        """비디오 추가 또는 업데이트"""
        with self._query_context():
            with self.pool.get_connection() as conn:
                try:
                    # JSON 직렬화
                    tags_json = json.dumps(video.tags, ensure_ascii=False)
                    analysis_json = json.dumps(video.analysis_result, ensure_ascii=False)
                    
                    # 중복 체크 및 업데이트/삽입
                    existing = conn.execute(
                        "SELECT id FROM videos WHERE url = ?",
                        (video.url,)
                    ).fetchone()
                    
                    if existing:
                        # 업데이트
                        video.updated_at = datetime.now().isoformat()
                        conn.execute("""
                            UPDATE videos SET
                                title = ?, platform = ?, video_id = ?, duration = ?,
                                view_count = ?, upload_date = ?, genre = ?, mood = ?,
                                tags = ?, analysis_result = ?, thumbnail_path = ?,
                                scenes_count = ?, updated_at = ?
                            WHERE url = ?
                        """, (
                            video.title, video.platform, video.video_id, video.duration,
                            video.view_count, video.upload_date, video.genre, video.mood,
                            tags_json, analysis_json, video.thumbnail_path,
                            video.scenes_count, video.updated_at, video.url
                        ))
                        
                        video_id = existing['id']
                        logger.info(f"비디오 업데이트: {video.title} (ID: {video_id})")
                    else:
                        # 삽입
                        cursor = conn.execute("""
                            INSERT INTO videos (
                                url, title, platform, video_id, duration, view_count,
                                upload_date, genre, mood, tags, analysis_result,
                                thumbnail_path, scenes_count, created_at, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            video.url, video.title, video.platform, video.video_id,
                            video.duration, video.view_count, video.upload_date,
                            video.genre, video.mood, tags_json, analysis_json,
                            video.thumbnail_path, video.scenes_count,
                            video.created_at, video.updated_at
                        ))
                        
                        video_id = cursor.lastrowid
                        logger.info(f"새 비디오 추가: {video.title} (ID: {video_id})")
                    
                    conn.commit()
                    return video_id
                    
                except Exception as e:
                    conn.rollback()
                    logger.error(f"비디오 추가/업데이트 실패: {e}")
                    raise
    
    def get_video_by_url(self, url: str) -> Optional[VideoRecord]:
        """URL로 비디오 조회"""
        with self._query_context():
            with self.pool.get_connection() as conn:
                row = conn.execute(
                    "SELECT * FROM videos WHERE url = ?",
                    (url,)
                ).fetchone()
                
                return self._row_to_video_record(row) if row else None
    
    def get_video_by_id(self, video_id: int) -> Optional[VideoRecord]:
        """ID로 비디오 조회"""
        with self._query_context():
            with self.pool.get_connection() as conn:
                row = conn.execute(
                    "SELECT * FROM videos WHERE id = ?",
                    (video_id,)
                ).fetchone()
                
                return self._row_to_video_record(row) if row else None
    
    def search_videos(self, 
                     genre: Optional[str] = None,
                     tags: Optional[List[str]] = None,
                     keyword: Optional[str] = None,
                     limit: int = 50,
                     offset: int = 0) -> List[VideoRecord]:
        """고급 비디오 검색"""
        with self._query_context():
            with self.pool.get_connection() as conn:
                where_clauses = []
                params = []
                
                # 장르 필터
                if genre:
                    where_clauses.append("genre = ?")
                    params.append(genre)
                
                # 키워드 검색 (제목)
                if keyword:
                    where_clauses.append("title LIKE ?")
                    params.append(f"%{keyword}%")
                
                # 태그 검색 (JSON 포함 검색)
                if tags:
                    for tag in tags:
                        where_clauses.append("tags LIKE ?")
                        params.append(f"%{tag}%")
                
                # SQL 구성
                where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
                sql = f"""
                    SELECT * FROM videos 
                    WHERE {where_sql}
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """
                params.extend([limit, offset])
                
                rows = conn.execute(sql, params).fetchall()
                return [self._row_to_video_record(row) for row in rows]
    
    def get_recent_videos(self, limit: int = 20) -> List[VideoRecord]:
        """최근 비디오 조회"""
        with self._query_context():
            with self.pool.get_connection() as conn:
                rows = conn.execute(
                    "SELECT * FROM videos ORDER BY created_at DESC LIMIT ?",
                    (limit,)
                ).fetchall()
                
                return [self._row_to_video_record(row) for row in rows]
    
    def get_statistics(self) -> Dict[str, Any]:
        """데이터베이스 통계"""
        with self._query_context():
            with self.pool.get_connection() as conn:
                # 전체 비디오 수
                total_count = conn.execute("SELECT COUNT(*) as count FROM videos").fetchone()['count']
                
                # 장르별 통계
                genre_stats = conn.execute("""
                    SELECT genre, COUNT(*) as count 
                    FROM videos 
                    WHERE genre != '' 
                    GROUP BY genre 
                    ORDER BY count DESC
                """).fetchall()
                
                # 플랫폼별 통계
                platform_stats = conn.execute("""
                    SELECT platform, COUNT(*) as count 
                    FROM videos 
                    GROUP BY platform 
                    ORDER BY count DESC
                """).fetchall()
                
                return {
                    "total_videos": total_count,
                    "genres": [{"genre": row["genre"], "count": row["count"]} for row in genre_stats],
                    "platforms": [{"platform": row["platform"], "count": row["count"]} for row in platform_stats],
                    "query_count": self._query_count
                }
    
    def delete_video(self, video_id: int) -> bool:
        """비디오 삭제"""
        with self._query_context():
            with self.pool.get_connection() as conn:
                try:
                    result = conn.execute("DELETE FROM videos WHERE id = ?", (video_id,))
                    conn.commit()
                    
                    deleted = result.rowcount > 0
                    if deleted:
                        logger.info(f"비디오 삭제됨: ID {video_id}")
                    
                    return deleted
                    
                except Exception as e:
                    conn.rollback()
                    logger.error(f"비디오 삭제 실패: {e}")
                    raise
    
    def _row_to_video_record(self, row: sqlite3.Row) -> VideoRecord:
        """데이터베이스 행을 VideoRecord로 변환"""
        if not row:
            return None
        
        try:
            tags = json.loads(row['tags']) if row['tags'] else []
            analysis_result = json.loads(row['analysis_result']) if row['analysis_result'] else {}
        except json.JSONDecodeError:
            tags = []
            analysis_result = {}
        
        return VideoRecord(
            id=row['id'],
            url=row['url'],
            title=row['title'],
            platform=row['platform'],
            video_id=row['video_id'],
            duration=row['duration'],
            view_count=row['view_count'],
            upload_date=row['upload_date'],
            genre=row['genre'],
            mood=row['mood'],
            tags=tags,
            analysis_result=analysis_result,
            thumbnail_path=row['thumbnail_path'],
            scenes_count=row['scenes_count'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
    
    @contextmanager
    def _query_context(self):
        """쿼리 실행 컨텍스트 (통계 수집)"""
        with self._lock:
            self._query_count += 1
        yield
    
    def close(self):
        """데이터베이스 연결 종료"""
        self.pool.close_all()
        logger.info("데이터베이스 연결 종료")


# 싱글톤 인스턴스
_db_instance = None
_db_lock = threading.Lock()


def get_database() -> ConcurrentVideoDatabase:
    """데이터베이스 싱글톤 인스턴스 반환"""
    global _db_instance
    if _db_instance is None:
        with _db_lock:
            if _db_instance is None:
                _db_instance = ConcurrentVideoDatabase()
    return _db_instance
