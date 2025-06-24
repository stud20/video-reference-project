# src/storage/db_manager.py

from tinydb import TinyDB, Query
from tinydb.operations import set as tdb_set
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
from dataclasses import asdict
import logging

logger = logging.getLogger(__name__)


class VideoAnalysisDB:
    """TinyDB를 사용한 영상 분석 결과 저장소"""
    
    def __init__(self, db_path: str = "data/video_analysis.json"):
        """
        데이터베이스 초기화
        
        Args:
            db_path: TinyDB 파일 경로
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # TinyDB 인스턴스 생성
        self.db = TinyDB(self.db_path, ensure_ascii=False, encoding='utf-8', indent=4)
        
        # 테이블 생성
        self.videos_table = self.db.table('videos')
        self.analyses_table = self.db.table('analyses')
        
        logger.info(f"Database initialized at: {self.db_path}")
    

    def delete_video(self, video_id: str) -> bool:
        """
        영상 및 관련 분석 결과 삭제
        
        Args:
            video_id: 삭제할 영상 ID
        
        Returns:
            삭제 성공 여부
        """
        from tinydb import Query
        Video = Query()
        Analysis = Query()
        
        try:
            # 영상 정보 삭제
            removed_videos = self.videos_table.remove(Video.video_id == video_id)
            logger.info(f"Removed {len(removed_videos)} video records for video_id: {video_id}")
            
            # 관련 분석 결과 삭제
            removed_analyses = self.analyses_table.remove(Analysis.video_id == video_id)
            logger.info(f"Removed {len(removed_analyses)} analysis records for video_id: {video_id}")
            
            return len(removed_videos) > 0 or len(removed_analyses) > 0
        except Exception as e:
            logger.error(f"Error deleting video {video_id}: {str(e)}")
            return False

    def delete_analysis(self, video_id: str) -> bool:
        """
        특정 영상의 모든 분석 결과 삭제
        
        Args:
            video_id: 영상 ID
        
        Returns:
            삭제 성공 여부
        """
        from tinydb import Query
        Analysis = Query()
        
        try:
            removed = self.analyses_table.remove(Analysis.video_id == video_id)
            logger.info(f"Removed {len(removed)} analysis records for video_id: {video_id}")
            return len(removed) > 0
        except Exception as e:
            logger.error(f"Error deleting analyses for video {video_id}: {str(e)}")
            return False
    
    # src/storage/db_manager.py의 save_video_info 함수 수정

    def save_video_info(self, video_data: Dict[str, Any]) -> int:
        """
        영상 기본 정보 저장 - 확장된 메타데이터 포함
        
        Args:
            video_data: 영상 정보 딕셔너리
                - video_id: 영상 ID
                - url: 원본 URL
                - title: 영상 제목
                - duration: 영상 길이
                - platform: youtube/vimeo
                - download_date: 다운로드 날짜
                - uploader: 업로더/채널명 (추가)
                - description: 영상 설명 (추가)
                - view_count: 조회수 (추가)
                - like_count: 좋아요 수 (추가)
                - comment_count: 댓글 수 (추가)
                - tags: YouTube 태그 (추가)
                - channel_id: 채널 ID (추가)
                - categories: 카테고리 (추가)
                - language: 언어 (추가)
                - upload_date: 업로드 날짜 (추가)
        
        Returns:
            document_id: 저장된 문서 ID
        """
        Video = Query()
        
        # 기존 데이터 확인
        existing = self.videos_table.search(Video.video_id == video_data['video_id'])
        
        # 확장된 메타데이터를 포함한 레코드 생성
        video_record = {
            'video_id': video_data['video_id'],
            'url': video_data['url'],
            'title': video_data.get('title', ''),
            'duration': video_data.get('duration', 0),
            'platform': video_data.get('platform', 'unknown'),
            'download_date': video_data.get('download_date', datetime.now().isoformat()),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            
            # 확장된 메타데이터 추가
            'uploader': video_data.get('uploader', video_data.get('channel', '')),
            'channel': video_data.get('channel', video_data.get('uploader', '')),  # 호환성
            'description': video_data.get('description', ''),
            'view_count': video_data.get('view_count', 0),
            'like_count': video_data.get('like_count', 0),
            'comment_count': video_data.get('comment_count', 0),
            'tags': video_data.get('tags', []),
            'channel_id': video_data.get('channel_id', ''),
            'categories': video_data.get('categories', []),
            'language': video_data.get('language', ''),
            'upload_date': video_data.get('upload_date', ''),
            'age_limit': video_data.get('age_limit', 0),
        }
        
        if existing:
            # 업데이트
            doc_id = existing[0].doc_id
            self.videos_table.update(
                video_record,
                doc_ids=[doc_id]
            )
            logger.info(f"Updated video info for: {video_data['video_id']}")
        else:
            # 새로 삽입
            doc_id = self.videos_table.insert(video_record)
            logger.info(f"Saved new video info for: {video_data['video_id']}")
        
        return doc_id
    
    def save_analysis_result(self, video_id: str, analysis_data: Dict[str, Any]) -> int:
        """
        AI 분석 결과 저장
        
        Args:
            video_id: 영상 ID
            analysis_data: 분석 결과 딕셔너리
                - genre: 장르
                - reasoning: 판단 이유
                - features: 특징 및 특이사항
                - tags: 태그 리스트
                - expression_style: 표현형식
                - mood_tone: 분위기와 톤
                - target_audience: 타겟 고객층
                - analyzed_scenes: 분석에 사용된 씬 정보
                - token_usage: 토큰 사용량
        
        Returns:
            document_id: 저장된 문서 ID
        """
        Analysis = Query()
        
        analysis_record = {
            'video_id': video_id,
            'genre': analysis_data.get('genre', ''),
            'reasoning': analysis_data.get('reasoning', ''),
            'features': analysis_data.get('features', ''),
            'tags': analysis_data.get('tags', []),
            'expression_style': analysis_data.get('expression_style', ''),
            'mood_tone': analysis_data.get('mood_tone', ''),
            'target_audience': analysis_data.get('target_audience', ''),
            'analyzed_scenes': analysis_data.get('analyzed_scenes', []),
            'token_usage': analysis_data.get('token_usage', {}),
            'model_used': analysis_data.get('model_used', 'gpt-4o'),
            'analysis_date': datetime.now().isoformat(),
            'version': '1.0'  # 분석 버전 관리
        }
        
        # 기존 분석 결과가 있는지 확인
        existing = self.analyses_table.search(
            (Analysis.video_id == video_id) & 
            (Analysis.version == '1.0')
        )
        
        if existing:
            # 기존 분석을 히스토리로 보관하고 새로 삽입
            doc_id = self.analyses_table.insert(analysis_record)
            logger.info(f"Saved new analysis for video: {video_id}")
        else:
            doc_id = self.analyses_table.insert(analysis_record)
            logger.info(f"Saved first analysis for video: {video_id}")
        
        return doc_id
    
    def get_video_info(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        영상 정보 조회
        
        Args:
            video_id: 영상 ID
        
        Returns:
            영상 정보 딕셔너리 또는 None
        """
        Video = Query()
        result = self.videos_table.search(Video.video_id == video_id)
        return result[0] if result else None
    
    def get_latest_analysis(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        최신 분석 결과 조회
        
        Args:
            video_id: 영상 ID
        
        Returns:
            분석 결과 딕셔너리 또는 None
        """
        Analysis = Query()
        results = self.analyses_table.search(Analysis.video_id == video_id)
        
        if not results:
            return None
        
        # 가장 최근 분석 결과 반환
        sorted_results = sorted(results, key=lambda x: x['analysis_date'], reverse=True)
        return sorted_results[0]
    
    def get_all_analyses(self, video_id: str) -> List[Dict[str, Any]]:
        """
        특정 영상의 모든 분석 히스토리 조회
        
        Args:
            video_id: 영상 ID
        
        Returns:
            분석 결과 리스트 (최신순)
        """
        Analysis = Query()
        results = self.analyses_table.search(Analysis.video_id == video_id)
        return sorted(results, key=lambda x: x['analysis_date'], reverse=True)
    
    def search_by_genre(self, genre: str) -> List[Dict[str, Any]]:
        """
        장르로 영상 검색
        
        Args:
            genre: 검색할 장르
        
        Returns:
            해당 장르의 분석 결과 리스트
        """
        Analysis = Query()
        results = self.analyses_table.search(Analysis.genre.matches(genre, flags=re.IGNORECASE))
        return results
    
    def search_by_tags(self, tags: List[str]) -> List[Dict[str, Any]]:
        """
        태그로 영상 검색
        
        Args:
            tags: 검색할 태그 리스트
        
        Returns:
            해당 태그를 포함하는 분석 결과 리스트
        """
        Analysis = Query()
        results = []
        
        for tag in tags:
            tag_results = self.analyses_table.search(
                Analysis.tags.any(lambda x: tag.lower() in x.lower())
            )
            results.extend(tag_results)
        
        # 중복 제거
        unique_results = {r.doc_id: r for r in results}
        return list(unique_results.values())
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        데이터베이스 통계 정보 조회
        
        Returns:
            통계 정보 딕셔너리
        """
        total_videos = len(self.videos_table)
        total_analyses = len(self.analyses_table)
        
        # 장르별 통계
        genre_stats = {}
        for analysis in self.analyses_table.all():
            genre = analysis.get('genre', 'Unknown')
            genre_stats[genre] = genre_stats.get(genre, 0) + 1
        
        # 태그 통계
        tag_stats = {}
        for analysis in self.analyses_table.all():
            for tag in analysis.get('tags', []):
                tag_stats[tag] = tag_stats.get(tag, 0) + 1
        
        # 상위 10개 태그
        top_tags = sorted(tag_stats.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'total_videos': total_videos,
            'total_analyses': total_analyses,
            'genre_distribution': genre_stats,
            'top_tags': top_tags,
            'db_size_bytes': self.db_path.stat().st_size if self.db_path.exists() else 0
        }
    
    def export_to_json(self, output_path: str) -> None:
        """
        전체 데이터베이스를 JSON으로 내보내기
        
        Args:
            output_path: 출력 파일 경로
        """
        export_data = {
            'videos': self.videos_table.all(),
            'analyses': self.analyses_table.all(),
            'export_date': datetime.now().isoformat()
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Database exported to: {output_path}")
    
    def close(self):
        """데이터베이스 연결 종료"""
        self.db.close()
        logger.info("Database connection closed")


# 사용 예시
if __name__ == "__main__":
    # 데이터베이스 초기화
    db = VideoAnalysisDB()
    
    # 영상 정보 저장
    video_info = {
        'video_id': 'test_video_001',
        'url': 'https://youtube.com/watch?v=test',
        'title': '테스트 영상',
        'duration': 120.5,
        'platform': 'youtube'
    }
    db.save_video_info(video_info)
    
    # 분석 결과 저장
    analysis_result = {
        'genre': '기업 홍보',
        'reasoning': '기업의 제품과 서비스를 소개하는 내용...',
        'features': '깔끔한 편집과 전문적인 나레이션...',
        'tags': ['기업홍보', '제품소개', '브랜딩'],
        'expression_style': '인포그래픽',
        'mood_tone': '전문적이고 신뢰감 있는',
        'target_audience': 'B2B 고객',
        'analyzed_scenes': ['scene_001.jpg', 'scene_002.jpg'],
        'token_usage': {'prompt': 1000, 'completion': 500, 'total': 1500}
    }
    db.save_analysis_result('test_video_001', analysis_result)
    
    # 통계 출력
    stats = db.get_statistics()
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    db.close()