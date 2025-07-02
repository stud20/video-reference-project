# integrations/notion/page.py
"""
Notion 페이지 서비스
페이지 내용 생성 및 관리
"""

from typing import Dict, Any, List
import os
from utils.logger import get_logger

logger = get_logger(__name__)


class NotionPageService:
    """
    Notion 페이지 서비스
    
    클라이언트를 공유하여 사용할 수 있도록 설계
    """
    
    def __init__(self, client=None, database_id=None):
        """
        페이지 서비스 초기화
        
        Args:
            client: Notion 클라이언트 (None이면 새로 생성)
            database_id: 데이터베이스 ID (None이면 환경변수에서 가져옴)
        """
        self.logger = get_logger(__name__)
        
        if client:
            self.client = client
            self.database_id = database_id or os.getenv('NOTION_DATABASE_ID')
        else:
            # 독립적으로 사용할 때만 NotionBaseService 생성
            from .base import NotionBaseService
            base_service = NotionBaseService(log_init=False)
            self.client = base_service.client
            self.database_id = base_service.database_id
            self.safe_get = base_service.safe_get
    
    def safe_get(self, data: Dict[str, Any], key: str, default: Any = '') -> Any:
        """안전한 값 가져오기"""
        value = data.get(key) if data else None
        return default if value is None else value
    
    def create_page_content(self, 
                          video_data: Dict[str, Any], 
                          analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        페이지 내용 생성 (레이아웃에 맞춰)
        
        Returns:
            Notion blocks 리스트
        """
        blocks = []
        
        # 1. 부제목 (장르 | 업로더 | 제목)
        subtitle = self._create_subtitle(video_data, analysis_data)
        blocks.append(self._create_heading_2(subtitle))
        
        # 2. YouTube 영상 임베드
        video_block = self._create_video_embed(video_data)
        if video_block:
            blocks.append(video_block)
        
        # 3. 2단 컬럼 레이아웃 (태그 포함)
        column_block = self._create_column_layout(video_data, analysis_data)
        blocks.append(column_block)
        
        return blocks
    
    def _create_subtitle(self, 
                        video_data: Dict[str, Any], 
                        analysis_data: Dict[str, Any]) -> str:
        """부제목 생성"""
        genre = self.safe_get(analysis_data, 'genre', 'Unknown')
        uploader = self.safe_get(video_data, 'uploader', 'Unknown')
        title = self.safe_get(video_data, 'title', 'Unknown')
        
        return f"{genre} | {uploader} | {title}"[:100]
    
    def _create_heading_2(self, text: str) -> Dict[str, Any]:
        """제목2 블록 생성"""
        return {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": text}
                }]
            }
        }
    
    def _create_heading_3(self, text: str) -> Dict[str, Any]:
        """제목3 블록 생성"""
        return {
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": text}
                }]
            }
        }
    
    def _create_paragraph(self, text: str) -> Dict[str, Any]:
        """문단 블록 생성"""
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": text}
                }]
            }
        }
    
    def _create_bulleted_list_item(self, 
                                  text: str, 
                                  bold: bool = False, 
                                  link: str = None) -> Dict[str, Any]:
        """불릿 리스트 아이템 생성"""
        rich_text = {
            "type": "text",
            "text": {"content": text}
        }
        
        if bold:
            rich_text["annotations"] = {"bold": True}
        
        if link:
            rich_text["text"]["link"] = {"url": link}
        
        return {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [rich_text]
            }
        }
    
    # notion_page.py의 _create_video_embed 메서드 수정
    def _create_video_embed(self, video_data: Dict[str, Any]) -> Dict[str, Any]:
        """비디오 임베드 블록 생성 (플랫폼별 최적화)"""
        # 가능한 모든 URL 필드 확인
        url = self.safe_get(video_data, 'url', '')
        webpage_url = self.safe_get(video_data, 'webpage_url', '')
        
        # 우선순위: webpage_url > url
        embed_url = webpage_url if webpage_url else url
        
        logger.debug(f"🎬 비디오 임베드 시도:")
        logger.debug(f"  - url: {url}")
        logger.debug(f"  - webpage_url: {webpage_url}")
        logger.debug(f"  - 선택된 URL: {embed_url}")
        
        if not embed_url:
            logger.warning("⚠️ 비디오 URL이 없습니다.")
            return None
        
        # Vimeo 또는 YouTube URL인 경우에만 임베드
        if any(domain in embed_url for domain in ['vimeo.com', 'youtube.com', 'youtu.be']):
            logger.info(f"✅ 비디오 임베드 생성: {embed_url}")
            return {
                "object": "block",
                "type": "video",
                "video": {
                    "type": "external",
                    "external": {"url": embed_url}
                }
            }
        else:
            logger.warning(f"⚠️ 지원하지 않는 비디오 URL: {embed_url}")
            return None
    
    def _create_column_layout(self, 
                            video_data: Dict[str, Any], 
                            analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """2단 컬럼 레이아웃 생성"""
        return {
            "object": "block",
            "type": "column_list",
            "column_list": {
                "children": [
                    # 왼쪽 컬럼 (70%)
                    {
                        "object": "block",
                        "type": "column",
                        "column": {
                            "children": self._create_left_column_content(analysis_data)
                        }
                    },
                    # 오른쪽 컬럼 (30%)
                    {
                        "object": "block",
                        "type": "column",
                        "column": {
                            "children": self._create_right_column_content(video_data, analysis_data)
                        }
                    }
                ]
            }
        }
    
    def _create_left_column_content(self, analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """왼쪽 컬럼 내용 생성"""
        blocks = []
        
        # 추론 결과
        blocks.append(self._create_heading_3("추론 결과"))
        reasoning = self.safe_get(analysis_data, 'reasoning', '분석 결과가 없습니다.')
        blocks.append(self._create_paragraph(reasoning[:2000]))
        
        # 특징
        blocks.append(self._create_heading_3("특징"))
        features = self.safe_get(analysis_data, 'features', '특징 정보가 없습니다.')
        blocks.append(self._create_paragraph(features[:2000]))
        
        # 분위기
        blocks.append(self._create_heading_3("분위기"))
        mood = self.safe_get(analysis_data, 'mood_tone', '분위기 정보가 없습니다.')
        blocks.append(self._create_paragraph(mood[:500]))
        
        # 타겟 고객층
        blocks.append(self._create_heading_3("타겟 고객층"))
        target = self.safe_get(analysis_data, 'target_audience', '타겟 정보가 없습니다.')
        blocks.append(self._create_paragraph(target[:500]))
        
        return blocks
    
    def _create_right_column_content(self, 
                                   video_data: Dict[str, Any], 
                                   analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """오른쪽 컬럼 내용 생성"""
        blocks = []
        
        # 빈 제목3 추가 (레이아웃 맞추기용)
        blocks.append(self._create_heading_3(""))
        
        # 업로더/제작사
        uploader = self.safe_get(video_data, 'uploader', self.safe_get(video_data, 'channel', 'Unknown'))
        blocks.append(self._create_bulleted_list_item(uploader, bold=True))
        
        # 장르
        genre = self.safe_get(analysis_data, 'genre', 'Unknown')
        blocks.append(self._create_bulleted_list_item(genre))
        
        # 표현형식
        expression = self.safe_get(analysis_data, 'expression_style', '실사')
        blocks.append(self._create_bulleted_list_item(expression))
        
        # YouTube URL
        url = self.safe_get(video_data, 'url', '')
        if url:
            blocks.append(self._create_bulleted_list_item(url, link=url))
        
        # 공백 추가 (선택사항)
        blocks.append(self._create_paragraph(""))
        
        # AI 태그 콜아웃
        tag_block = self._create_tag_callout(analysis_data)
        if tag_block:
            blocks.append(tag_block)
        
        return blocks
    
    def _create_tag_callout(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """태그 콜아웃 블록 생성"""
        ai_tags = self.safe_get(analysis_data, 'tags', [])
        
        if ai_tags and isinstance(ai_tags, list):
            # AI 태그만 사용, 각 태그 앞에 # 추가
            tag_text = " ".join([f"#{tag}" for tag in ai_tags[:20]])  # 최대 20개
            
            return {
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": tag_text}
                    }],
                    # icon 프로퍼티를 완전히 제거
                    "color": "gray_background"
                }
            }
        
        return None
    
    def update_page_content(self, 
                          page_id: str, 
                          video_data: Dict[str, Any], 
                          analysis_data: Dict[str, Any]) -> bool:
        """페이지 내용 업데이트"""
        try:
            # 먼저 기존 블록들 가져오기
            existing_blocks = self.client.blocks.children.list(page_id)
            
            # 기존 블록 삭제
            for block in existing_blocks.get('results', []):
                try:
                    self.client.blocks.delete(block['id'])
                except:
                    pass  # 삭제 실패 시 무시
            
            # 새 내용 추가
            page_content = self.create_page_content(video_data, analysis_data)
            for block in page_content:
                self.client.blocks.children.append(
                    block_id=page_id,
                    children=[block]
                )
            
            logger.info(f"페이지 내용 업데이트 완료: {page_id}")
            return True
            
        except Exception as e:
            logger.error(f"페이지 내용 업데이트 실패: {str(e)}")
            return False