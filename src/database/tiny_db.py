# src/database/tiny_db.py
"""TinyDB를 사용한 간단한 데이터베이스"""

from tinydb import TinyDB, Query
from datetime import datetime
from typing import List, Dict, Optional
import os

class VideoTinyDB:
    """TinyDB 기반 영상 데이터베이스"""
    
    def __init__(self, db_path: str = "data/database/videos.json"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db = TinyDB(db_path, ensure_ascii=False, indent=2)
        self.videos = self.db.table('videos')
        self.Video = Query()
    
    def add_video(self, video_data: Dict) -> int:
        """영상 추가"""
        video_data['created_at'] = datetime.now().isoformat()
        video_data['updated_at'] = datetime.now().isoformat()
        
        # 중복 체크
        if 'url' in video_data:
            existing = self.videos.search(self.Video.url == video_data['url'])
            if existing:
                # 업데이트
                return self.videos.update(video_data, self.Video.url == video_data['url'])[0]
        
        return self.videos.insert(video_data)
    
    def get_video(self, doc_id: int) -> Optional[Dict]:
        """ID로 영상 조회"""
        return self.videos.get(doc_id=doc_id)
    
    def get_all_videos(self) -> List[Dict]:
        """모든 영상 조회"""
        return self.videos.all()
    
    def search_by_genre(self, genre: str) -> List[Dict]:
        """장르로 검색"""
        return self.videos.search(
            self.Video.analysis_result.genre == genre
        )
    
    def search_by_tag(self, tag: str) -> List[Dict]:
        """태그로 검색"""
        return self.videos.search(
            self.Video.analysis_result.tags.any([tag])
        )
    
    def search_by_multiple_tags(self, tags: List[str]) -> List[Dict]:
        """여러 태그로 검색"""
        results = []
        for tag in tags:
            results.extend(self.search_by_tag(tag))
        
        # 중복 제거
        seen = set()
        unique_results = []
        for r in results:
            if r.doc_id not in seen:
                seen.add(r.doc_id)
                unique_results.append(r)
        
        return unique_results
    
    def get_by_url(self, url: str) -> Optional[Dict]:
        """URL로 조회"""
        results = self.videos.search(self.Video.url == url)
        return results[0] if results else None
    
    def get_recent_videos(self, limit: int = 10) -> List[Dict]:
        """최근 영상 조회"""
        all_videos = self.videos.all()
        # created_at으로 정렬
        sorted_videos = sorted(
            all_videos, 
            key=lambda x: x.get('created_at', ''), 
            reverse=True
        )
        return sorted_videos[:limit]
    
    def search_by_mood(self, mood_keyword: str) -> List[Dict]:
        """분위기로 검색"""
        return self.videos.search(
            self.Video.analysis_result.mood.matches(f'.*{mood_keyword}.*', flags=re.IGNORECASE)
        )
    
    def get_statistics(self) -> Dict:
        """통계 정보"""
        all_videos = self.videos.all()
        
        # 장르별 통계
        genres = {}
        tags_count = {}
        
        for video in all_videos:
            # 장르
            genre = video.get('analysis_result', {}).get('genre', '미분류')
            genres[genre] = genres.get(genre, 0) + 1
            
            # 태그
            tags = video.get('analysis_result', {}).get('tags', [])
            for tag in tags:
                tags_count[tag] = tags_count.get(tag, 0) + 1
        
        # 인기 태그 Top 10
        popular_tags = sorted(tags_count.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'total_videos': len(all_videos),
            'genres': genres,
            'popular_tags': popular_tags
        }
    
    def update_video(self, doc_id: int, updates: Dict) -> bool:
        """영상 업데이트"""
        updates['updated_at'] = datetime.now().isoformat()
        result = self.videos.update(updates, doc_ids=[doc_id])
        return len(result) > 0
    
    def delete_video(self, doc_id: int) -> bool:
        """영상 삭제"""
        result = self.videos.remove(doc_ids=[doc_id])
        return len(result) > 0
    
    def advanced_search(self, 
                       genre: Optional[str] = None,
                       tags: Optional[List[str]] = None,
                       date_from: Optional[str] = None,
                       date_to: Optional[str] = None) -> List[Dict]:
        """고급 검색"""
        results = self.videos.all()
        
        # 장르 필터
        if genre:
            results = [r for r in results if r.get('analysis_result', {}).get('genre') == genre]
        
        # 태그 필터 (AND 조건)
        if tags:
            for tag in tags:
                results = [r for r in results if tag in r.get('analysis_result', {}).get('tags', [])]
        
        # 날짜 필터
        if date_from:
            results = [r for r in results if r.get('created_at', '') >= date_from]
        if date_to:
            results = [r for r in results if r.get('created_at', '') <= date_to]
        
        return results