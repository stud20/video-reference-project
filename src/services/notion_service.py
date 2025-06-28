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
        """
        try:
            # 데이터베이스 ID 확인
            if database_id:
                self.db_service.database_id = database_id
            
            video_id = video_data.get('video_id', 'Unknown')
            logger.info(f"🔍 영상 처리 시작 - video_id: {video_id}")
            
            # 디버깅: 입력 데이터 확인
            logger.debug(f"📊 video_data 키: {list(video_data.keys())}")
            logger.debug(f"🌐 플랫폼: {video_data.get('platform')}")
            logger.debug(f"🔗 URL: {video_data.get('url')}")
            logger.debug(f"📄 webpage_url: {video_data.get('webpage_url')}")
            logger.debug(f"🖼️ thumbnail: {video_data.get('thumbnail')}")
            
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
    

    # src/services/notion_service.py에 추가할 메서드들

    def find_video_blocks(self, video_id: str) -> List[str]:
        """
        특정 비디오 ID를 포함하는 데이터베이스 항목 찾기
        
        Args:
            video_id: 찾을 비디오 ID
            
        Returns:
            페이지 ID 리스트
        """
        try:
            # 데이터베이스에서 video_id로 검색
            response = self.db_service.client.databases.query(
                database_id=self.db_service.database_id,
                filter={
                    "property": "영상 ID",
                    "rich_text": {
                        "equals": video_id
                    }
                }
            )
            
            # 페이지 ID들 추출
            page_ids = [page['id'] for page in response.get('results', [])]
            
            logger.info(f"🔍 Notion에서 {len(page_ids)}개 페이지 발견: {video_id}")
            return page_ids
            
        except Exception as e:
            logger.error(f"Notion 검색 오류: {str(e)}")
            return []

    def delete_block(self, block_id: str) -> bool:
        """
        Notion 페이지(블록) 삭제
        
        Args:
            block_id: 삭제할 블록 ID
            
        Returns:
            성공 여부
        """
        try:
            # 페이지 아카이브 (Notion API는 실제 삭제 대신 아카이브를 사용)
            self.db_service.client.pages.update(
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
            # 1. 해당 비디오의 모든 페이지 찾기
            page_ids = self.find_video_blocks(video_id)
            
            if not page_ids:
                return True, "Notion에 해당 영상이 없음"
            
            # 2. 각 페이지 삭제(아카이브)
            deleted_count = 0
            failed_count = 0
            
            for page_id in page_ids:
                if self.delete_block(page_id):
                    deleted_count += 1
                else:
                    failed_count += 1
            
            # 3. 결과 반환
            if failed_count == 0:
                return True, f"{deleted_count}삭제 완료"
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