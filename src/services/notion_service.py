# src/services/notion_service.py
"""
Notion API 통합 서비스
데이터베이스와 페이지 기능을 통합하여 제공
"""

from typing import Dict, Any, List, Optional, Tuple
import time
import traceback
from .notion_database import NotionDatabaseService
from .notion_page import NotionPageService
from utils.logger import get_logger

logger = get_logger(__name__)


class NotionService:
    """Notion 통합 서비스"""
    
    def __init__(self):
        """서비스 초기화"""
        self.db_service = NotionDatabaseService()
        self.page_service = NotionPageService()
        logger.info("Notion 통합 서비스 초기화 완료")
    
    def add_video_to_database(self, 
                            video_data: Dict[str, Any], 
                            analysis_data: Dict[str, Any],
                            database_id: Optional[str] = None) -> Tuple[bool, str]:
        """
        영상 분석 결과를 Notion 데이터베이스에 추가하고 상세 페이지 생성
        
        Args:
            video_data: 영상 기본 정보
            analysis_data: AI 분석 결과
            database_id: Notion 데이터베이스 ID (옵션)
            
        Returns:
            (성공여부, 페이지ID or 에러메시지)
        """
        try:
            # 데이터베이스 ID 확인
            if database_id:
                self.db_service.database_id = database_id
            
            video_id = video_data.get('video_id', 'Unknown')
            logger.info(f"🔍 영상 처리 시작 - video_id: {video_id}")
            
            # 중복 확인
            existing_page = self.db_service.check_duplicate(video_id)
            if existing_page:
                logger.info(f"기존 레코드 발견: {video_id}")
                return self._update_existing_record(
                    existing_page['id'], 
                    video_data, 
                    analysis_data
                )
            
            # 데이터베이스 프로퍼티 생성
            properties = self.db_service.create_database_properties(video_data, analysis_data)
            
            # 페이지 내용 생성
            page_content = self.page_service.create_page_content(video_data, analysis_data)
            
            # 페이지 생성 (프로퍼티 + 내용)
            success, result = self.db_service.create_page(properties, page_content)
            
            if success:
                logger.info(f"✅ Notion 페이지 생성 성공: {result}")
            else:
                logger.error(f"❌ Notion 페이지 생성 실패: {result}")
            
            return success, result
            
        except Exception as e:
            error_msg = f"추가 중 오류: {str(e)}"
            logger.error(f"{error_msg} - Video ID: {video_data.get('video_id', 'Unknown')}")
            logger.error(f"스택 트레이스:\n{traceback.format_exc()}")
            return False, error_msg
    
    def _update_existing_record(self, 
                               page_id: str, 
                               video_data: Dict[str, Any], 
                               analysis_data: Dict[str, Any]) -> Tuple[bool, str]:
        """기존 레코드 업데이트 (프로퍼티 + 페이지 내용)"""
        try:
            # 프로퍼티 업데이트
            properties = self.db_service.create_database_properties(video_data, analysis_data)
            success, result = self.db_service.update_page(page_id, properties)
            
            if not success:
                return False, result
            
            # 페이지 내용 업데이트
            content_updated = self.page_service.update_page_content(
                page_id, 
                video_data, 
                analysis_data
            )
            
            if content_updated:
                logger.info(f"기존 레코드 업데이트 완료: {video_data['video_id']}")
                return True, f"업데이트됨: {page_id}"
            else:
                return True, f"프로퍼티만 업데이트됨: {page_id}"
            
        except Exception as e:
            error_msg = f"업데이트 오류: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def bulk_add_to_database(self, 
                            videos_with_analysis: List[Tuple[Dict, Dict]], 
                            progress_callback=None) -> Tuple[int, int, List[str]]:
        """
        여러 영상을 데이터베이스에 일괄 추가
        
        Args:
            videos_with_analysis: [(video_data, analysis_data), ...] 리스트
            progress_callback: 진행상황 콜백 함수
            
        Returns:
            (성공 개수, 실패 개수, 오류 메시지 리스트)
        """
        success_count = 0
        fail_count = 0
        errors = []
        
        total = len(videos_with_analysis)
        
        for i, (video_data, analysis_data) in enumerate(videos_with_analysis):
            video_id = video_data.get('video_id', 'Unknown')
            
            # 진행상황 업데이트
            if progress_callback:
                progress_callback(
                    current=i + 1,
                    total=total,
                    message=f"업로드 중... ({i+1}/{total}) - {video_id}"
                )
            
            try:
                success, result = self.add_video_to_database(video_data, analysis_data)
                
                if success:
                    success_count += 1
                    logger.info(f"✅ Notion 추가 성공: {video_id}")
                else:
                    fail_count += 1
                    errors.append(f"{video_id}: {result}")
                
                # API 제한 방지를 위한 대기
                time.sleep(0.3)
                
            except Exception as e:
                fail_count += 1
                error_msg = f"{video_id}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"추가 실패 - {error_msg}")
        
        return success_count, fail_count, errors
    
    # 데이터베이스 서비스 메서드들을 직접 노출
    def search_videos(self, **kwargs):
        """영상 검색"""
        return self.db_service.search_videos(**kwargs)
    
    def test_connection(self):
        """연결 테스트"""
        return self.db_service.test_connection()
    
    def get_database_url(self):
        """데이터베이스 URL 반환"""
        return self.db_service.get_database_url()
    
    def get_database_properties(self):
        """데이터베이스 프로퍼티 조회"""
        return self.db_service.get_database_properties()
    
    def update_database_schema(self):
        """데이터베이스 스키마 업데이트"""
        return self.db_service.update_database_schema()