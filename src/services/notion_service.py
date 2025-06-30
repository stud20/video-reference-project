# src/services/notion_service.py
"""
Notion API 통합 서비스
데이터베이스와 페이지 기능을 통합하여 제공
"""

import os
import time
import traceback
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from notion_client import Client
from utils.logger import get_logger

logger = get_logger(__name__)


class NotionService:
    """Notion 통합 서비스"""
        
    def __init__(self):
        """NotionService 초기화"""
        import os
        from notion_client import Client
        
        # 환경변수 체크
        api_key = os.getenv("NOTION_API_KEY")
        database_id = os.getenv("NOTION_DATABASE_ID")
        
        if not api_key:
            raise ValueError("NOTION_API_KEY 환경변수가 설정되지 않았습니다.")
        
        if not database_id:
            raise ValueError("NOTION_DATABASE_ID 환경변수가 설정되지 않았습니다.")
        
        # 속성 설정
        self.api_key = api_key
        self.database_id = database_id
        self.logger = get_logger(__name__)
        
        # Notion 클라이언트 초기화
        self.client = Client(auth=self.api_key)
        self.notion = self.client  # 호환성을 위해 둘 다 설정
        
        self.logger.info("NotionService 초기화 완료")
    
    def add_video_to_database(self, video_data: Dict[str, Any], analysis_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Notion 데이터베이스에 비디오 추가 또는 업데이트"""
        try:
            video_id = video_data.get('video_id')
            if not video_id:
                return False, "video_id가 없습니다"
            
            # 기존 페이지 검색
            existing_page = self._find_existing_page(video_id)
            
            if existing_page:
                # 기존 페이지가 있으면 업데이트
                self.logger.info(f"기존 페이지 발견: {existing_page['id']}")
                return self._update_existing_page(existing_page['id'], video_data, analysis_data)
            else:
                # 새 페이지 생성
                return self._create_new_page(video_data, analysis_data)
                
        except Exception as e:
            error_msg = f"Notion 업로드 실패: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def _update_existing_page(self, page_id: str, video_data: Dict[str, Any], analysis_data: Dict[str, Any]) -> Tuple[bool, str]:
        """기존 페이지 업데이트"""
        try:
            # 프로퍼티 생성 (새 페이지와 동일)
            properties = self._create_properties(video_data, analysis_data)
            
            # 페이지 업데이트
            response = self.notion.pages.update(
                page_id=page_id,
                properties=properties
            )
            
            self.logger.info(f"✅ Notion 페이지 업데이트 성공: {page_id}")
            return True, page_id
            
        except Exception as e:
            error_msg = f"페이지 업데이트 실패: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def _create_new_page(self, video_data: Dict[str, Any], analysis_data: Dict[str, Any]) -> Tuple[bool, str]:
        """새 페이지 생성"""
        try:
            properties = self._create_properties(video_data, analysis_data)
            
            # 페이지 생성
            response = self.notion.pages.create(
                parent={"database_id": self.database_id},
                properties=properties
            )
            
            page_id = response.get('id', '')
            self.logger.info(f"✅ Notion 페이지 생성 성공: {page_id}")
            return True, page_id
            
        except Exception as e:
            error_msg = f"페이지 생성 실패: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def _create_properties(self, video_data: Dict[str, Any], analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Notion 프로퍼티 생성 (공통 로직)"""
        
        # 디버깅: 받은 데이터 확인
        self.logger.debug(f"video_data keys: {list(video_data.keys())}")
        self.logger.debug(f"analysis_data keys: {list(analysis_data.keys())}")
        
        # 프로퍼티 생성
        properties = {
            # 기본 정보
            "제목": {
                "title": [{
                    "text": {
                        "content": video_data.get('title', 'Untitled')[:100]
                    }
                }]
            },
            "영상 ID": {
                "rich_text": [{
                    "text": {
                        "content": video_data.get('video_id', '')
                    }
                }]
            },
            "URL": {
                "url": video_data.get('url', '')
            },
            "썸네일": {
                "files": self._prepare_media_files(video_data)
            },
            "플랫폼": {
                "select": {
                    "name": self._get_platform_name(video_data)
                }
            },
            "업로더": {
                "rich_text": [{
                    "text": {
                        "content": video_data.get('uploader', video_data.get('channel', 'Unknown'))[:100]
                    }
                }]
            },
            "길이(초)": {
                "number": video_data.get('duration', 0) or 0
            },
            
            # AI 분석 결과
            "장르": {
                "select": {
                    "name": analysis_data.get('genre', 'Unknown')[:100]
                }
            },
            "표현형식": {
                "select": {
                    "name": analysis_data.get('expression_style', '실사')[:100]
                }
            },
            "분위기": {
                "rich_text": [{
                    "text": {
                        "content": self._safe_get_text(analysis_data.get('mood_tone', ''), 2000)
                    }
                }]
            },
            "타겟 고객층": {
                "rich_text": [{
                    "text": {
                        "content": self._safe_get_text(analysis_data.get('target_audience', ''), 2000)
                    }
                }]
            },
            
            # 태그 (통합)
            "태그": {
                "multi_select": [
                    {"name": tag[:100]} for tag in analysis_data.get('tags', [])[:100]
                ]
            },
            
            # AI 분석 정보
            "AI 분석 완료": {
                "checkbox": True if analysis_data else False
            },
            
            # 상세 내용
            "판단 이유": {
                "rich_text": [{
                    "text": {
                        "content": self._safe_get_text(analysis_data.get('reasoning', ''), 2000)
                    }
                }]
            },
            "특징": {
                "rich_text": [{
                    "text": {
                        "content": self._safe_get_text(analysis_data.get('features', ''), 2000)
                    }
                }]
            },
            "설명": {
                "rich_text": [{
                    "text": {
                        "content": self._safe_get_text(video_data.get('description', ''), 2000)
                    }
                }]
            },
            
            # 기타
            "언어": {
                "rich_text": [{
                    "text": {
                        "content": video_data.get('language', '')[:50]
                    }
                }]
            },
            "카테고리": {
                "multi_select": [
                    {"name": cat[:100]} for cat in video_data.get('categories', [])[:100]
                ]
            }
        }
        
        # None 값 필터링
        filtered_properties = {}
        for key, value in properties.items():
            if value is not None:
                # multi_select의 경우 빈 리스트 체크
                if key in ["태그", "카테고리"] and isinstance(value.get("multi_select"), list):
                    if len(value["multi_select"]) > 0:
                        filtered_properties[key] = value
                # files의 경우 빈 리스트 체크
                elif key == "썸네일" and isinstance(value.get("files"), list):
                    if len(value["files"]) > 0:
                        filtered_properties[key] = value
                else:
                    filtered_properties[key] = value
        
        return filtered_properties

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
            # 데이터베이스에서 video_id로 검색
            response = self.client.databases.query(
                database_id=self.database_id,
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

    def test_connection(self) -> bool:
        """Notion 연결 테스트"""
        try:
            db = self.client.databases.retrieve(self.database_id)
            self.logger.info("Notion 연결 테스트 성공")
            return True
        except Exception as e:
            self.logger.error(f"Notion 연결 실패: {str(e)}")
            return False

    def get_database_url(self) -> str:
        """데이터베이스 URL 반환"""
        return f"https://www.notion.so/{self.database_id.replace('-', '')}"

    def get_database_properties(self) -> Dict[str, str]:
        """데이터베이스 프로퍼티 조회"""
        try:
            db = self.client.databases.retrieve(self.database_id)
            properties = db.get('properties', {})
            
            result = {}
            for name, prop in properties.items():
                prop_type = prop.get('type', 'unknown')
                result[name] = prop_type
            
            return result
        except Exception as e:
            self.logger.error(f"프로퍼티 조회 실패: {str(e)}")
            return {}

    # 헬퍼 메서드들
    def _find_existing_page(self, video_id: str) -> Optional[Dict[str, Any]]:
        """기존 페이지 찾기"""
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
            
            if response['results']:
                return response['results'][0]
            return None
            
        except Exception as e:
            self.logger.error(f"페이지 검색 오류: {str(e)}")
            return None

    def _get_platform_name(self, video_data: Dict[str, Any]) -> str:
        """플랫폼 이름 추출"""
        platform = video_data.get('platform', '').lower()
        if 'youtube' in platform:
            return 'YouTube'
        elif 'vimeo' in platform:
            return 'Vimeo'
        return 'Unknown'

    def _safe_get_text(self, text: str, max_length: int) -> str:
        """텍스트 안전하게 자르기"""
        if not text:
            return ''
        return text[:max_length]

    def _get_language_name(self, language_code: str) -> str:
        """언어 코드를 읽기 쉬운 이름으로 변환"""
        language_map = {
            'ko': '한국어',
            'en': '영어',
            'ja': '일본어',
            'zh': '중국어',
            'es': '스페인어',
            'fr': '프랑스어',
            'de': '독일어',
        }
        return language_map.get(language_code, language_code or 'Unknown')

    def _prepare_media_files(self, video_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """미디어 파일 준비 (썸네일)"""
        files = []
        
        # 자체 서버 썸네일 URL
        video_id = video_data.get('video_id', '')
        if video_id:
            thumbnail_url = f"https://ref.greatminds.kr/{video_id}/{video_id}_Thumbnail.jpg"
            files.append({
                "type": "external",
                "name": f"{video_id}_thumbnail.jpg",
                "external": {
                    "url": thumbnail_url
                }
            })
        
        return files