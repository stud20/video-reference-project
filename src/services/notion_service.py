# src/services/notion_service.py
"""
Notion API 연동 서비스
영상 분석 결과를 Notion 데이터베이스에 저장
"""

import os
import requests
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from notion_client import Client
from notion_client.errors import APIResponseError
from utils.logger import get_logger
import time

logger = get_logger(__name__)


class NotionService:
    """Notion API 연동 서비스"""
    
    def __init__(self):
        """Notion 클라이언트 초기화"""
        self.api_key = os.getenv('NOTION_API_KEY')
        self.database_id = os.getenv('NOTION_DATABASE_ID')
        
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
        
        # 데이터베이스 프로퍼티 확인 및 업데이트
        self._check_and_update_schema()
    
    def _check_and_update_schema(self):
        """데이터베이스 스키마 확인 및 업데이트"""
        try:
            # 현재 프로퍼티 확인
            current_props = self.get_database_properties()
            logger.info(f"현재 데이터베이스 프로퍼티: {list(current_props.keys())}")
            
            # 필요한 프로퍼티 확인
            required_props = self._get_database_schema()
            missing_props = [p for p in required_props if p not in current_props]
            
            if missing_props:
                logger.warning(f"누락된 프로퍼티 발견: {missing_props}")
                logger.info("자동으로 프로퍼티를 추가합니다...")
                self.update_database_schema()
            else:
                logger.info("✅ 모든 필요한 프로퍼티가 존재합니다.")
                
        except Exception as e:
            logger.error(f"스키마 확인 중 오류: {str(e)}")
    
    def _get_database_schema(self) -> Dict[str, Any]:
        """데이터베이스 스키마 정의"""
        return {
            # 기본 정보
            "제목": {"title": {}},
            "영상 ID": {"rich_text": {}},
            "URL": {"url": {}},
            "플랫폼": {
                "select": {
                    "options": [
                        {"name": "YouTube", "color": "red"},
                        {"name": "Vimeo", "color": "blue"}
                    ]
                }
            },
            "업로더": {"rich_text": {}},
            "업로드일": {"date": {}},
            
            # 통계
            "길이(초)": {"number": {"format": "number"}},
            "조회수": {"number": {"format": "number"}},
            "좋아요": {"number": {"format": "number"}},
            "댓글수": {"number": {"format": "number"}},
            
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
            
            # 태그
            "YouTube 태그": {"multi_select": {}},
            "AI 추론 태그": {"multi_select": {}},
            
            # 분석 정보
            "AI 분석 완료": {"checkbox": {}},
            "분석일": {"date": {}},
            "사용 모델": {"rich_text": {}},
            
            # 상세 내용
            "판단 이유": {"rich_text": {}},
            "특징": {"rich_text": {}},
            "설명": {"rich_text": {}},
            
            # 기타
            "언어": {"rich_text": {}},
            "카테고리": {"multi_select": {}},
            
            # 메타
            "등록일": {"created_time": {}},
            "수정일": {"last_edited_time": {}}
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
    
    def create_database_if_not_exists(self, parent_page_id: str) -> str:
        """데이터베이스가 없으면 생성"""
        try:
            # 기존 데이터베이스 확인
            self.client.databases.retrieve(self.database_id)
            logger.info(f"기존 데이터베이스 사용: {self.database_id}")
            return self.database_id
        except:
            # 데이터베이스 생성
            logger.info("새 데이터베이스 생성 중...")
            
            new_db = self.client.databases.create(
                parent={"page_id": parent_page_id},
                title=[{
                    "type": "text",
                    "text": {"content": "영상 레퍼런스 분석 DB"}
                }],
                properties=self._get_database_schema()
            )
            
            database_id = new_db["id"]
            logger.info(f"데이터베이스 생성 완료: {database_id}")
            return database_id
    
    def add_video_to_database(self, 
                             video_data: Dict[str, Any], 
                             analysis_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        영상 정보를 데이터베이스에 추가
        
        Args:
            video_data: 영상 기본 정보
            analysis_data: AI 분석 결과
            
        Returns:
            (성공여부, 메시지 또는 페이지 ID)
        """
        try:
            # 중복 체크
            existing = self._check_duplicate(video_data['video_id'])
            if existing:
                return self._update_existing_record(existing['id'], video_data, analysis_data)
            
            # 새 레코드 생성
            properties = self._create_properties(video_data, analysis_data)
            
            response = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties
            )
            
            logger.info(f"데이터베이스에 추가 성공: {video_data['video_id']}")
            return True, response['id']
            
        except APIResponseError as e:
            # APIResponseError의 속성 확인
            if hasattr(e, 'message'):
                error_msg = f"Notion API 오류: {e.message}"
            elif hasattr(e, 'code'):
                error_msg = f"Notion API 오류 (코드: {e.code}): {str(e)}"
            else:
                error_msg = f"Notion API 오류: {str(e)}"
            
            logger.error(f"{error_msg} - Video ID: {video_data['video_id']}")
            
            # 더 자세한 에러 정보 로깅
            if hasattr(e, '__dict__'):
                logger.debug(f"에러 상세: {e.__dict__}")
            
            return False, error_msg
        except Exception as e:
            error_msg = f"추가 중 오류: {str(e)}"
            logger.error(f"{error_msg} - Video ID: {video_data['video_id']}")
            return False, error_msg
    
    def _check_duplicate(self, video_id: str) -> Optional[Dict[str, Any]]:
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
    
    def _update_existing_record(self, 
                               page_id: str, 
                               video_data: Dict[str, Any], 
                               analysis_data: Dict[str, Any]) -> Tuple[bool, str]:
        """기존 레코드 업데이트"""
        try:
            properties = self._create_properties(video_data, analysis_data)
            
            self.client.pages.update(
                page_id=page_id,
                properties=properties
            )
            
            logger.info(f"기존 레코드 업데이트: {video_data['video_id']}")
            return True, f"업데이트됨: {page_id}"
            
        except Exception as e:
            error_msg = f"업데이트 오류: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def _create_properties(self, 
                          video_data: Dict[str, Any], 
                          analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Notion 프로퍼티 생성"""
        
        # 디버깅: 받은 데이터 확인
        logger.debug(f"video_data 키들: {list(video_data.keys())}")
        logger.debug(f"업로더: {video_data.get('uploader', 'NOT FOUND')}")
        logger.debug(f"태그: {video_data.get('tags', [])}")
        logger.debug(f"언어: {video_data.get('language', 'NOT FOUND')}")
        logger.debug(f"설명: {video_data.get('description', 'NOT FOUND')[:100] if video_data.get('description') else 'NOT FOUND'}")
        logger.debug(f"댓글수: {video_data.get('comment_count', 'NOT FOUND')}")
        logger.debug(f"업로드일: {video_data.get('upload_date', 'NOT FOUND')}")
        
        # YouTube 태그와 AI 태그 분리
        youtube_tags = video_data.get('tags', [])[:20]  # 최대 20개
        ai_tags = []
        
        if analysis_data and analysis_data.get('tags'):
            all_analysis_tags = analysis_data['tags']
            # YouTube 태그에 없는 것만 AI 태그로
            ai_tags = [tag for tag in all_analysis_tags if tag not in youtube_tags][:20]
        
        # 업로드 날짜 처리
        upload_date = None
        if video_data.get('upload_date'):
            try:
                # YYYYMMDD 형식을 ISO 형식으로 변환
                date_str = video_data['upload_date']
                if len(date_str) >= 8:
                    upload_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            except:
                pass
        
        properties = {
            # 기본 정보
            "제목": {
                "title": [{
                    "text": {"content": video_data.get('title', 'Unknown')[:100]}
                }]
            },
            "영상 ID": {
                "rich_text": [{
                    "text": {"content": video_data['video_id']}
                }]
            },
            "URL": {
                "url": video_data.get('url', '')
            },
            "플랫폼": {
                "select": {
                    "name": "YouTube" if video_data.get('platform') == 'youtube' else "Vimeo"
                }
            },
            "업로더": {
                "rich_text": [{
                    "text": {"content": video_data.get('uploader', 'Unknown')[:100]}
                }]
            },
            
            # 통계
            "길이(초)": {
                "number": video_data.get('duration', 0)
            },
            "조회수": {
                "number": video_data.get('view_count', 0)
            },
            "좋아요": {
                "number": video_data.get('like_count', 0)
            },
            "댓글수": {
                "number": video_data.get('comment_count', 0)
            },
            
            # 태그
            "YouTube 태그": {
                "multi_select": [
                    {"name": tag[:100]} for tag in youtube_tags if tag and len(tag) > 1
                ]
            },
            
            # 기타 정보
            "언어": {
                "rich_text": [{
                    "text": {"content": video_data.get('language', '')[:50]}
                }]
            },
            "카테고리": {
                "multi_select": [
                    {"name": cat[:100]} for cat in video_data.get('categories', [])[:10]
                ]
            }
        }
        
        # 업로드 날짜 추가
        if upload_date:
            properties["업로드일"] = {"date": {"start": upload_date}}
        
        # 설명 추가 (2000자 제한)
        if video_data.get('description'):
            properties["설명"] = {
                "rich_text": [{
                    "text": {"content": video_data['description'][:2000]}
                }]
            }
        
        # AI 분석 결과가 있는 경우
        if analysis_data:
            properties.update({
                "AI 분석 완료": {"checkbox": True},
                "장르": {
                    "select": {"name": analysis_data.get('genre', 'Unknown')}
                },
                "표현형식": {
                    "select": {"name": analysis_data.get('expression_style', '실사')}
                },
                "분위기": {
                    "rich_text": [{
                        "text": {"content": analysis_data.get('mood_tone', '')[:500]}
                    }]
                },
                "타겟 고객층": {
                    "rich_text": [{
                        "text": {"content": analysis_data.get('target_audience', '')[:500]}
                    }]
                },
                "AI 추론 태그": {
                    "multi_select": [
                        {"name": tag[:100]} for tag in ai_tags if tag and len(tag) > 1
                    ]
                },
                "판단 이유": {
                    "rich_text": [{
                        "text": {"content": analysis_data.get('reasoning', '')[:2000]}
                    }]
                },
                "특징": {
                    "rich_text": [{
                        "text": {"content": analysis_data.get('features', '')[:2000]}
                    }]
                },
                "사용 모델": {
                    "rich_text": [{
                        "text": {"content": analysis_data.get('model_used', 'gpt-4o')}
                    }]
                },
                "분석일": {
                    "date": {"start": datetime.now().date().isoformat()}
                }
            })
        else:
            properties["AI 분석 완료"] = {"checkbox": False}
        
        return properties
    
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
            video_id = video_data['video_id']
            
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
                    logger.info(f"Notion DB 추가 성공: {video_id}")
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
    
    def search_videos(self, 
                     genre: Optional[str] = None,
                     platform: Optional[str] = None,
                     analyzed_only: bool = False) -> List[Dict[str, Any]]:
        """데이터베이스에서 영상 검색"""
        try:
            filter_conditions = []
            
            if genre:
                filter_conditions.append({
                    "property": "장르",
                    "select": {"equals": genre}
                })
            
            if platform:
                filter_conditions.append({
                    "property": "플랫폼", 
                    "select": {"equals": platform}
                })
            
            if analyzed_only:
                filter_conditions.append({
                    "property": "AI 분석 완료",
                    "checkbox": {"equals": True}
                })
            
            filter_obj = None
            if len(filter_conditions) > 1:
                filter_obj = {"and": filter_conditions}
            elif filter_conditions:
                filter_obj = filter_conditions[0]
            
            response = self.client.databases.query(
                database_id=self.database_id,
                filter=filter_obj,
                sorts=[{
                    "property": "등록일",
                    "direction": "descending"
                }]
            )
            
            return response['results']
            
        except Exception as e:
            logger.error(f"검색 중 오류: {str(e)}")
            return []
    
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