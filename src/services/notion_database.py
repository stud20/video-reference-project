# src/services/notion_database.py
"""
Notion 데이터베이스 서비스
데이터베이스 항목 생성 및 관리
"""

from typing import Dict, Any, List, Optional, Tuple
from notion_client.errors import APIResponseError
from .notion_base import NotionBaseService
from utils.logger import get_logger

logger = get_logger(__name__)


class NotionDatabaseService(NotionBaseService):
    """Notion 데이터베이스 서비스"""
    
    def __init__(self):
        """서비스 초기화"""
        super().__init__()
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
    
    def get_youtube_thumbnail_url(self, video_id: str, quality: str = 'hqdefault') -> str:
        """
        YouTube 썸네일 URL 생성
        
        Args:
            video_id: YouTube 비디오 ID
            quality: 썸네일 품질
                - maxresdefault: 1280x720 (HD) - 모든 영상에 없을 수 있음
                - sddefault: 640x480
                - hqdefault: 480x360 (권장)
                - mqdefault: 320x180
                - default: 120x90
        
        Returns:
            썸네일 URL
        """
        return f"https://img.youtube.com/vi/{video_id}/{quality}.jpg"
    
    def create_database_properties(self, 
                                 video_data: Dict[str, Any], 
                                 analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """데이터베이스 프로퍼티 생성"""
        
        # 기본 속성
        properties = {
            "제목": {
                "title": [{
                    "text": {"content": self.safe_get(video_data, 'title', 'Unknown')[:100]}
                }]
            },
            "영상 ID": {
                "rich_text": [{
                    "text": {"content": self.safe_get(video_data, 'video_id', 'Unknown')}
                }]
            },
            "URL": {
                "url": self.safe_get(video_data, 'url', '')
            },
            "플랫폼": {
                "select": {
                    "name": "YouTube" if self.safe_get(video_data, 'platform', '').lower() == 'youtube' else "Vimeo"
                }
            },
            "업로더": {
                "rich_text": [{
                    "text": {"content": self.safe_get(video_data, 'uploader', self.safe_get(video_data, 'channel', 'Unknown'))[:100]}
                }]
            },
            "길이(초)": {
                "number": int(self.safe_get(video_data, 'duration', 0))
            }
        }
        
        # 썸네일 추가 (플랫폼 통합 처리)
        video_thumbnail = self._get_video_thumbnail(video_data)
        if video_thumbnail:
            video_id = self.safe_get(video_data, 'video_id', 'unknown')
            properties["썸네일"] = {
                "files": [{
                    "type": "external",
                    "name": f"{video_id}_thumbnail.jpg",
                    "external": {
                        "url": video_thumbnail
                    }
                }]
            }
            logger.debug(f"썸네일 URL 추가: {video_thumbnail}")
        
        # 통합 태그 처리
        all_tags = []
        
        # 플랫폼 태그 추가
        platform_tags = video_data.get('tags', [])
        if platform_tags and isinstance(platform_tags, list):
            all_tags.extend([tag for tag in platform_tags if tag and len(str(tag).strip()) > 1])
        
        # AI 추론 태그 추가
        if analysis_data:
            ai_tags = analysis_data.get('tags', [])
            if ai_tags and isinstance(ai_tags, list):
                all_tags.extend([tag for tag in ai_tags if tag and len(str(tag).strip()) > 1])
        
        # 중복 제거 및 최대 30개로 제한
        unique_tags = list(dict.fromkeys(all_tags))[:30]
        
        if unique_tags:
            properties["태그"] = {
                "multi_select": [{"name": str(tag)[:100]} for tag in unique_tags]
            }
        
        # 기타 정보
        if video_data.get('description'):
            properties["설명"] = {
                "rich_text": [{
                    "text": {"content": str(video_data['description'])[:2000]}
                }]
            }
        
        if video_data.get('language'):
            properties["언어"] = {
                "rich_text": [{
                    "text": {"content": str(video_data['language'])[:50]}
                }]
            }
        
        categories = video_data.get('categories', [])
        if categories and isinstance(categories, list):
            properties["카테고리"] = {
                "multi_select": [
                    {"name": str(cat)[:100]} for cat in categories[:10] if cat
                ]
            }
        
        # AI 분석 결과
        if analysis_data:
            properties.update({
                "AI 분석 완료": {"checkbox": True},
                "장르": {
                    "select": {"name": self.safe_get(analysis_data, 'genre', 'Unknown')}
                },
                "표현형식": {
                    "select": {"name": self.safe_get(analysis_data, 'expression_style', '실사')}
                },
                "분위기": {
                    "rich_text": [{
                        "text": {"content": self.safe_get(analysis_data, 'mood_tone', '')[:500]}
                    }]
                },
                "타겟 고객층": {
                    "rich_text": [{
                        "text": {"content": self.safe_get(analysis_data, 'target_audience', '')[:500]}
                    }]
                },
                "판단 이유": {
                    "rich_text": [{
                        "text": {"content": self.safe_get(analysis_data, 'reasoning', '')[:2000]}
                    }]
                },
                "특징": {
                    "rich_text": [{
                        "text": {"content": self.safe_get(analysis_data, 'features', '')[:2000]}
                    }]
                }
            })
        else:
            properties["AI 분석 완료"] = {"checkbox": False}
        
        return properties
    
    # notion_database.py의 _get_video_thumbnail 메서드 수정
    def _get_video_thumbnail(self, video_data: Dict[str, Any]) -> str:
        """
        비디오 썸네일 URL 가져오기 (자체 서버에서)
        """
        # session_id 가져오기 (video_id와 동일)
        session_id = self.safe_get(video_data, 'session_id', self.safe_get(video_data, 'video_id', ''))
        
        if not session_id:
            logger.warning("⚠️ session_id를 찾을 수 없어 썸네일 URL 생성 불가")
            return ''
        
        # 자체 서버 URL 생성
        base_url = "https://sof.greatminds.kr"
        thumbnail_url = f"{base_url}/{session_id}/{session_id}_Thumbnail.jpg"
        
        logger.debug(f"🖼️ 썸네일 URL (자체 서버): {thumbnail_url}")
        return thumbnail_url
    
    def create_page(self, 
                   properties: Dict[str, Any], 
                   children: List[Dict[str, Any]] = None) -> Tuple[bool, str]:
        """페이지 생성"""
        try:
            params = {
                "parent": {"database_id": self.database_id},
                "properties": properties
            }
            
            if children:
                params["children"] = children
            
            response = self.client.pages.create(**params)
            page_id = response['id']
            
            return True, page_id
            
        except APIResponseError as e:
            error_msg = f"Notion API 오류: {e.code if hasattr(e, 'code') else 'Unknown'} - {str(e)}"
            if hasattr(e, 'body'):
                logger.error(f"에러 상세: {e.body}")
            return False, error_msg
            
        except Exception as e:
            error_msg = f"페이지 생성 중 오류: {str(e)}"
            return False, error_msg
    
    def update_page(self, 
                   page_id: str, 
                   properties: Dict[str, Any]) -> Tuple[bool, str]:
        """페이지 프로퍼티 업데이트"""
        try:
            self.client.pages.update(
                page_id=page_id,
                properties=properties
            )
            return True, f"업데이트됨: {page_id}"
            
        except Exception as e:
            error_msg = f"업데이트 오류: {str(e)}"
            return False, error_msg
    
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
                    "property": "제목",
                    "direction": "ascending"
                }]
            )
            
            return response['results']
            
        except Exception as e:
            logger.error(f"검색 중 오류: {str(e)}")
            return []