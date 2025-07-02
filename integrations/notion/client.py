# integrations/notion/client.py
"""
Notion API 통합 서비스
NotionDatabaseService와 NotionPageService를 조합하여 완전한 기능 제공
"""

import time
from typing import Dict, Any, List, Optional, Tuple
from .database import NotionDatabaseService
from .page import NotionPageService
from utils.logger import get_logger

logger = get_logger(__name__)


class NotionService(NotionDatabaseService):
    """
    Notion 통합 서비스
    데이터베이스와 페이지 기능을 모두 제공
    """
    
    def __init__(self):
        """NotionService 초기화"""
        super().__init__(log_init=True)  # 메인 초기화만 로그
        # 페이지 서비스 초기화 (클라이언트 공유)
        self.page_service = NotionPageService(
            client=self.client, 
            database_id=self.database_id
        )
        # safe_get 메서드 공유
        self.page_service.safe_get = self.safe_get
        # 호환성을 위한 속성
        self.notion = self.client
        logger.info("NotionService 초기화 완료")
    
    def add_video_to_database(self, 
                            video_data: Dict[str, Any], 
                            analysis_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Notion 데이터베이스에 비디오 추가 또는 업데이트
        페이지 내용도 함께 생성/업데이트
        
        Args:
            video_data: 비디오 정보
            analysis_data: AI 분석 결과
            
        Returns:
            (성공 여부, 결과 메시지 또는 page_id)
        """
        try:
            video_id = video_data.get('video_id')
            if not video_id:
                return False, "video_id가 없습니다"
            
            # 기존 페이지 검색 (부모 클래스의 메서드 활용)
            existing_page = self.check_duplicate(video_id)
            
            # 프로퍼티 생성 (부모 클래스의 메서드 활용)
            properties = self.create_database_properties(video_data, analysis_data)
            
            # 페이지 내용 생성 (page_service 활용)
            page_content = self.page_service.create_page_content(video_data, analysis_data)
            
            if existing_page:
                # 기존 페이지 업데이트
                page_id = existing_page['id']
                logger.info(f"기존 페이지 발견: {page_id}")
                
                # 프로퍼티 업데이트
                success, result = self.update_page(page_id, properties)
                if success:
                    # 페이지 내용도 업데이트
                    self.page_service.update_page_content(page_id, video_data, analysis_data)
                return success, result
            else:
                # 새 페이지 생성 (프로퍼티와 내용 함께)
                return self.create_page(properties, page_content)
                
        except Exception as e:
            error_msg = f"Notion 업로드 실패: {str(e)}"
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
    
    def find_video_blocks(self, video_id: str) -> List[str]:
        """
        특정 비디오 ID를 포함하는 데이터베이스 항목 찾기
        
        Args:
            video_id: 찾을 비디오 ID
            
        Returns:
            페이지 ID 리스트
        """
        try:
            response = self.client.databases.query(
                database_id=self.database_id,
                filter={
                    "property": "영상 ID",
                    "rich_text": {
                        "equals": video_id
                    }
                }
            )
            
            page_ids = [page['id'] for page in response.get('results', [])]
            logger.info(f"🔍 Notion에서 {len(page_ids)}개 페이지 발견: {video_id}")
            return page_ids
            
        except Exception as e:
            logger.error(f"Notion 검색 오류: {str(e)}")
            return []
    
    def delete_block(self, block_id: str) -> bool:
        """
        Notion 페이지(블록) 삭제 (아카이브)
        
        Args:
            block_id: 삭제할 블록 ID
            
        Returns:
            성공 여부
        """
        try:
            self.client.pages.update(
                page_id=block_id,
                archived=True
            )
            logger.info(f"✅ Notion 페이지 아카이브 완료: {block_id}")
            return True
            
        except Exception as e:
            logger.error(f"Notion 페이지 삭제 오류: {str(e)}")
            return False
    
    def delete_video_from_notion(self, video_id: str) -> Tuple[bool, str]:
        """
        비디오를 Notion에서 완전히 삭제
        
        Args:
            video_id: 삭제할 비디오 ID
            
        Returns:
            (성공 여부, 메시지)
        """
        try:
            # 해당 비디오의 모든 페이지 찾기
            page_ids = self.find_video_blocks(video_id)
            
            if not page_ids:
                return True, "Notion에 해당 영상이 없음"
            
            # 각 페이지 삭제(아카이브)
            deleted_count = 0
            failed_count = 0
            
            for page_id in page_ids:
                if self.delete_block(page_id):
                    deleted_count += 1
                else:
                    failed_count += 1
            
            # 결과 반환
            if failed_count == 0:
                return True, f"{deleted_count}개 삭제 완료"
            elif deleted_count > 0:
                return False, f"{deleted_count}개 삭제, {failed_count}개 실패"
            else:
                return False, f"삭제 실패 ({failed_count}개)"
                
        except Exception as e:
            error_msg = f"Notion 삭제 중 오류: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def bulk_delete_from_notion(self, video_ids: List[str]) -> Tuple[int, int, List[str]]:
        """
        여러 비디오를 Notion에서 일괄 삭제
        
        Args:
            video_ids: 삭제할 비디오 ID 리스트
            
        Returns:
            (성공 개수, 실패 개수, 오류 메시지 리스트)
        """
        success_count = 0
        fail_count = 0
        errors = []
        
        for video_id in video_ids:
            try:
                success, message = self.delete_video_from_notion(video_id)
                
                if success:
                    success_count += 1
                else:
                    fail_count += 1
                    errors.append(f"{video_id}: {message}")
                    
                # API 제한 방지
                time.sleep(0.2)
                
            except Exception as e:
                fail_count += 1
                errors.append(f"{video_id}: {str(e)}")
        
        return success_count, fail_count, errors
    
    # NotionDatabaseService에서 상속받는 메서드들:
    # - get_database_properties()
    # - test_connection()
    # - get_database_url()
    # - create_database_properties()
    # - create_page()
    # - update_page()
    # - search_videos()
    # - _get_video_thumbnail()
    # - safe_get()
    
    # NotionPageService를 통해 사용하는 메서드들:
    # - create_page_content()
    # - update_page_content()