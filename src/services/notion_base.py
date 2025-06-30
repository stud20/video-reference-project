# src/services/notion_base.py
"""
Notion API 기본 서비스
공통 기능 및 데이터베이스 스키마 관리
"""

import os
from typing import Dict, Any, Optional
from notion_client import Client
from notion_client.errors import APIResponseError
from utils.logger import get_logger

# logger를 모듈 레벨에서 정의
logger = get_logger(__name__)


class NotionBaseService:
    """Notion API 기본 서비스"""
    
    def __init__(self):
        """Notion 클라이언트 초기화"""
        self.api_key = os.getenv('NOTION_API_KEY')
        self.database_id = os.getenv('NOTION_DATABASE_ID')
        self.logger = get_logger(__name__)

        if not self.api_key:
            raise ValueError("NOTION_API_KEY 환경변수가 필요합니다.")
        
        if not self.database_id:
            raise ValueError("NOTION_DATABASE_ID 환경변수가 필요합니다.")
        
        # 데이터베이스 ID 형식 검증 (32자리 16진수)
        clean_db_id = self.database_id.replace('-', '')
        if len(clean_db_id) != 32:
            raise ValueError(f"NOTION_DATABASE_ID 형식이 올바르지 않습니다. 32자리여야 합니다. (현재: {len(clean_db_id)}자리)")
        
        self.client = Client(auth=self.api_key)
        logger.info(f"Notion 클라이언트 초기화 완료 (DB ID: {self.database_id[:8]}...)")
    
    def safe_get(self, data: Optional[Dict], key: str, default: Any = '') -> Any:
        """안전한 값 가져오기"""
        value = data.get(key) if data else None
        return default if value is None else value
    
    def _get_database_schema(self) -> Dict[str, Any]:
        """데이터베이스 스키마 정의"""
        return {
            # 기본 정보
            "제목": {"title": {}},
            "영상 ID": {"rich_text": {}},
            "URL": {"url": {}},
            "썸네일": {"files": {}},  # 썸네일 추가
            "플랫폼": {
                "select": {
                    "options": [
                        {"name": "YouTube", "color": "red"},
                        {"name": "Vimeo", "color": "blue"}
                    ]
                }
            },
            "업로더": {"rich_text": {}},
            "길이(초)": {"number": {"format": "number"}},
            
            # AI 분석 결과
            "장르": {
                "select": {
                    "options": [
                        {"name": genre, "color": self._get_genre_color(genre)} 
                        for genre in [
                            "2D애니메이션", "3D애니메이션", "모션그래픽", "인터뷰", 
                            "스팟광고", "VLOG", "유튜브콘텐츠", "다큐멘터리", 
                            "브랜드필름", "TVC", "뮤직비디오", "교육콘텐츠",
                            "제품소개", "이벤트영상", "웹드라마", "바이럴영상"
                        ]
                    ]
                }
            },
            "표현형식": {
                "select": {
                    "options": [
                        {"name": "2D", "color": "purple"},
                        {"name": "3D", "color": "pink"},
                        {"name": "실사", "color": "green"},
                        {"name": "혼합형", "color": "yellow"},
                        {"name": "스톱모션", "color": "orange"},
                        {"name": "타이포그래피", "color": "gray"}
                    ]
                }
            },
            "분위기": {"rich_text": {}},
            "타겟 고객층": {"rich_text": {}},
            
            # 태그 (통합)
            "태그": {"multi_select": {}},
            
            # AI 분석 정보
            "AI 분석 완료": {"checkbox": {}},
            
            # 상세 내용
            "판단 이유": {"rich_text": {}},
            "특징": {"rich_text": {}},
            "설명": {"rich_text": {}},
            
            # 기타
            "언어": {"rich_text": {}},
            "카테고리": {"multi_select": {}},
        }
    
    def _get_genre_color(self, genre: str) -> str:
        """장르별 색상 지정"""
        color_map = {
            "2D애니메이션": "blue",
            "3D애니메이션": "purple", 
            "모션그래픽": "pink",
            "인터뷰": "green",
            "스팟광고": "red",
            "VLOG": "yellow",
            "유튜브콘텐츠": "orange",
            "다큐멘터리": "brown",
            "브랜드필름": "gray",
            "TVC": "default",
            "뮤직비디오": "pink",
            "교육콘텐츠": "green",
            "제품소개": "blue",
            "이벤트영상": "purple",
            "웹드라마": "red",
            "바이럴영상": "yellow"
        }
        return color_map.get(genre, "default")
    
    def get_database_properties(self) -> Dict[str, str]:
        """현재 데이터베이스의 프로퍼티 목록 조회"""
        try:
            db = self.client.databases.retrieve(self.database_id)
            properties = db.get('properties', {})
            
            result = {}
            for name, prop in properties.items():
                prop_type = prop.get('type', 'unknown')
                result[name] = prop_type
            
            return result
        except Exception as e:
            logger.error(f"프로퍼티 조회 실패: {str(e)}")
            return {}
    
    def update_database_schema(self) -> bool:
        """기존 데이터베이스에 필요한 프로퍼티 추가/업데이트"""
        try:
            logger.info("데이터베이스 스키마 업데이트 시작...")
            
            # 현재 데이터베이스 정보 가져오기
            current_db = self.client.databases.retrieve(self.database_id)
            current_properties = current_db.get('properties', {})
            
            # 필요한 프로퍼티 정의
            required_properties = self._get_database_schema()
            
            # 업데이트할 프로퍼티만 추출 (기존에 없는 것들)
            properties_to_update = {}
            for prop_name, prop_config in required_properties.items():
                if prop_name not in current_properties:
                    properties_to_update[prop_name] = prop_config
                    logger.info(f"새 프로퍼티 추가: {prop_name}")
            
            if properties_to_update:
                # 데이터베이스 업데이트
                self.client.databases.update(
                    database_id=self.database_id,
                    properties=properties_to_update
                )
                logger.info(f"✅ {len(properties_to_update)}개 프로퍼티 추가 완료")
                return True
            else:
                logger.info("모든 필요한 프로퍼티가 이미 존재합니다.")
                return True
                
        except Exception as e:
            logger.error(f"스키마 업데이트 실패: {str(e)}")
            return False
    
    def test_connection(self) -> bool:
        """Notion 연결 테스트"""
        try:
            # 데이터베이스 정보 가져오기
            db = self.client.databases.retrieve(self.database_id)
            db_title = "Unknown"
            
            # 타이틀 추출 시도
            if db.get('title') and len(db['title']) > 0:
                if 'plain_text' in db['title'][0]:
                    db_title = db['title'][0]['plain_text']
                elif 'text' in db['title'][0]:
                    db_title = db['title'][0]['text'].get('content', 'Unknown')
            
            logger.info(f"Notion 데이터베이스 연결 성공: {db_title}")
            return True
        except APIResponseError as e:
            if hasattr(e, 'code') and e.code == 'object_not_found':
                logger.error(f"데이터베이스를 찾을 수 없습니다. ID를 확인하세요: {self.database_id}")
            elif hasattr(e, 'code') and e.code == 'unauthorized':
                logger.error("API 키가 유효하지 않거나 데이터베이스 접근 권한이 없습니다.")
            else:
                logger.error(f"Notion 연결 실패: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Notion 연결 실패: {str(e)}")
            return False
    
    def get_database_url(self) -> str:
        """데이터베이스 URL 반환"""
        return f"https://www.notion.so/{self.database_id.replace('-', '')}"
    
    def check_duplicate(self, video_id: str) -> Optional[Dict[str, Any]]:
        """중복 영상 확인"""
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
            logger.error(f"중복 확인 중 오류: {str(e)}")
            return None