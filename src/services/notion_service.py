# src/services/notion_service.py
"""
Notion API 연동 서비스
영상 분석 결과를 Notion 페이지에 추가 (특정 형식)
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
        self.parent_page_id = os.getenv('NOTION_PARENT_PAGE_ID')
        
        if not self.api_key:
            raise ValueError("NOTION_API_KEY 환경변수가 필요합니다.")
        
        if not self.parent_page_id:
            logger.warning("NOTION_PARENT_PAGE_ID가 설정되지 않았습니다.")
        
        self.client = Client(auth=self.api_key)
        logger.info("Notion 클라이언트 초기화 완료")
    
    def add_video_analysis_to_page(self, 
                                  video_data: Dict[str, Any], 
                                  analysis_data: Dict[str, Any],
                                  parent_page_id: Optional[str] = None) -> Tuple[bool, str]:
        """
        영상 분석 결과를 페이지에 추가 (특정 형식)
        
        Args:
            video_data: 영상 기본 정보
            analysis_data: AI 분석 결과
            parent_page_id: 콘텐츠를 추가할 페이지 ID
            
        Returns:
            (성공여부, 메시지)
        """
        try:
            page_id = parent_page_id or self.parent_page_id
            if not page_id:
                return False, "부모 페이지 ID가 지정되지 않았습니다."
            
            # 콘텐츠 블록 생성
            blocks = self._create_content_blocks(video_data, analysis_data)
            
            # 페이지에 블록 추가
            self.client.blocks.children.append(
                block_id=page_id,
                children=blocks
            )
            
            logger.info(f"페이지에 콘텐츠 추가 성공: {video_data['video_id']}")
            return True, f"페이지에 추가됨"
            
        except APIResponseError as e:
            error_msg = f"Notion API 오류: {e.message}"
            logger.error(f"{error_msg} - Video ID: {video_data['video_id']}")
            return False, error_msg
        except Exception as e:
            error_msg = f"콘텐츠 추가 오류: {str(e)}"
            logger.error(f"{error_msg} - Video ID: {video_data['video_id']}")
            return False, error_msg
    
    def _create_content_blocks(self, 
                              video_data: Dict[str, Any], 
                              analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """페이지 콘텐츠 블록 생성 (특정 형식)"""
        blocks = []
        
        # 1. 제목 (H2, 볼드체)
        title = video_data.get('title', 'Unknown')
        duration = video_data.get('duration', 0)
        duration_str = f"{duration//60}:{duration%60:02d}"
        
        # 업로더/채널명
        uploader = video_data.get('uploader', video_data.get('channel', 'Unknown'))
        
        # 제목 형식: "TVC 45s | BMW | THE 7" 스타일로
        genre = analysis_data.get('genre', 'TVC')
        brand_or_uploader = uploader if uploader != 'Unknown' else ''
        
        # 제목 구성
        if brand_or_uploader:
            formatted_title = f"{genre} {duration_str}s | {brand_or_uploader} | {title}"
        else:
            formatted_title = f"{genre} {duration_str}s | {title}"
        
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{
                    "text": {"content": formatted_title[:100]},
                    "annotations": {"bold": True}
                }]
            }
        })
        
        # 2. YouTube 동영상 임베드
        youtube_url = f"https://www.youtube.com/watch?v={video_data['video_id']}"
        blocks.append({
            "object": "block",
            "type": "embed",
            "embed": {
                "url": youtube_url
            }
        })
        
        # 3. 2단 레이아웃 시작 (column_list)
        column_blocks = []
        
        # 왼쪽 컬럼 (68.75% 너비) - 분석 내용
        left_column_blocks = []
        
        # 추론 결과 (H3)
        left_column_blocks.append({
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [{"text": {"content": "추론 결과"}}]
            }
        })
        
        # 추론 결과 내용 (reasoning)
        reasoning_text = analysis_data.get('reasoning', '분석 결과가 없습니다.')
        left_column_blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"text": {"content": reasoning_text}}]
            }
        })
        
        # 특징 (H3)
        left_column_blocks.append({
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [{"text": {"content": "특징"}}]
            }
        })
        
        # 특징 내용
        features_text = analysis_data.get('features', '특징 정보가 없습니다.')
        left_column_blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"text": {"content": features_text}}]
            }
        })
        
        # 분위기 (H3)
        left_column_blocks.append({
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [{"text": {"content": "분위기"}}]
            }
        })
        
        # 분위기 내용
        mood_text = analysis_data.get('mood_tone', '분위기 정보가 없습니다.')
        left_column_blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"text": {"content": mood_text}}]
            }
        })
        
        # 타겟 고객층 (H3)
        left_column_blocks.append({
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [{"text": {"content": "타겟 고객층"}}]
            }
        })
        
        # 타겟 고객층 내용
        target_text = analysis_data.get('target_audience', '타겟 고객층 정보가 없습니다.')
        left_column_blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"text": {"content": target_text}}]
            }
        })
        
        # 오른쪽 컬럼 (31.25% 너비) - 메타 정보
        right_column_blocks = []
        
        # 업로더/채널 (볼드체 bullet)
        if uploader and uploader != 'Unknown':
            right_column_blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{
                        "text": {"content": uploader},
                        "annotations": {"bold": True}
                    }]
                }
            })
        
        # 장르 (bullet)
        right_column_blocks.append({
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": genre}}]
            }
        })
        
        # 표현형식 (bullet)
        expression_style = analysis_data.get('expression_style', '실사')
        right_column_blocks.append({
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": expression_style}}]
            }
        })
        
        # YouTube 링크 (bullet)
        right_column_blocks.append({
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{
                    "text": {
                        "content": youtube_url,
                        "link": {"url": youtube_url}
                    }
                }]
            }
        })
        
        # 태그 (bullet 형태로 표시)
        if analysis_data.get('tags'):
            tags = analysis_data['tags'][:10]  # 최대 10개만
            for tag in tags:
                if tag and len(tag) > 1:
                    right_column_blocks.append({
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [{
                                "text": {"content": f"#{tag}"},
                                "annotations": {
                                    "color": "blue"  # 태그 색상
                                }
                            }]
                        }
                    })
        
        # 2단 레이아웃 생성
        blocks.append({
            "object": "block",
            "type": "column_list",
            "column_list": {
                "children": [
                    {
                        "object": "block",
                        "type": "column",
                        "column": {
                            "children": left_column_blocks
                        }
                    },
                    {
                        "object": "block",
                        "type": "column",
                        "column": {
                            "children": right_column_blocks
                        }
                    }
                ]
            }
        })
        
        return blocks
    
    def bulk_add_to_page(self, 
                        videos_with_analysis: List[Tuple[Dict, Dict]], 
                        parent_page_id: Optional[str] = None,
                        progress_callback=None,
                        prepend: bool = True) -> Tuple[int, int, List[str]]:
        """
        여러 영상을 기존 페이지에 일괄 추가
        
        Args:
            videos_with_analysis: [(video_data, analysis_data), ...] 리스트
            parent_page_id: 콘텐츠를 추가할 페이지 ID
            progress_callback: 진행상황 콜백 함수
            prepend: True면 페이지 상단에 추가, False면 하단에 추가
            
        Returns:
            (성공 개수, 실패 개수, 오류 메시지 리스트)
        """
        success_count = 0
        fail_count = 0
        errors = []
        
        total = len(videos_with_analysis)
        page_id = parent_page_id or self.parent_page_id
        
        if not page_id:
            return 0, total, ["부모 페이지 ID가 지정되지 않았습니다."]
        
        # prepend 모드일 때는 역순으로 처리 (나중 것이 위로 가도록)
        if prepend:
            videos_with_analysis = list(reversed(videos_with_analysis))
        
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
                # 콘텐츠 블록 생성
                blocks = self._create_content_blocks(video_data, analysis_data)
                
                if prepend:
                    # 페이지 상단에 추가하려면 기존 블록들을 가져와서 순서 조정
                    self._prepend_blocks_to_page(page_id, blocks)
                else:
                    # 페이지 하단에 추가
                    self.client.blocks.children.append(
                        block_id=page_id,
                        children=blocks
                    )
                
                success_count += 1
                logger.info(f"Notion 업로드 성공: {video_id}")
                
                # API 제한 방지를 위한 대기
                time.sleep(0.5)  # prepend는 더 많은 API 호출이 필요하므로 대기시간 증가
                
            except Exception as e:
                fail_count += 1
                error_msg = f"{video_id}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"업로드 실패 - {error_msg}")
        
        return success_count, fail_count, errors
    
    def _prepend_blocks_to_page(self, page_id: str, new_blocks: List[Dict[str, Any]]):
        """페이지 상단에 블록 추가"""
        try:
            # 페이지의 첫 번째 자식 블록 ID 가져오기
            page_content = self.client.blocks.children.list(page_id)
            
            if page_content['results']:
                # 첫 번째 블록 앞에 삽입
                first_block_id = page_content['results'][0]['id']
                
                # 블록을 하나씩 첫 번째 위치에 삽입
                for block in reversed(new_blocks):  # 역순으로 삽입해야 올바른 순서
                    self.client.blocks.children.append(
                        block_id=page_id,
                        children=[block],
                        after=None  # 맨 앞에 삽입
                    )
                    time.sleep(0.1)  # API 제한 방지
            else:
                # 페이지가 비어있으면 그냥 추가
                self.client.blocks.children.append(
                    block_id=page_id,
                    children=new_blocks
                )
        except Exception as e:
            # prepend 실패 시 append로 폴백
            logger.warning(f"상단 추가 실패, 하단에 추가합니다: {str(e)}")
            self.client.blocks.children.append(
                block_id=page_id,
                children=new_blocks
            )
    
    def test_connection(self) -> bool:
        """Notion 연결 테스트"""
        try:
            user = self.client.users.me()
            logger.info(f"Notion 연결 성공: {user.get('name', 'Unknown User')}")
            return True
        except Exception as e:
            logger.error(f"Notion 연결 실패: {str(e)}")
            return False
    
    def get_page_info(self, page_id: str) -> Optional[Dict[str, Any]]:
        """페이지 정보 가져오기"""
        try:
            page = self.client.pages.retrieve(page_id)
            return {
                'id': page['id'],
                'url': page['url'],
                'title': self._extract_page_title(page)
            }
        except Exception as e:
            logger.error(f"페이지 정보 가져오기 실패: {str(e)}")
            return None
    
    def _extract_page_title(self, page: Dict[str, Any]) -> str:
        """페이지 객체에서 제목 추출"""
        try:
            if 'properties' in page and 'title' in page['properties']:
                title_prop = page['properties']['title']
                if 'title' in title_prop and len(title_prop['title']) > 0:
                    return title_prop['title'][0]['plain_text']
        except:
            pass
        return "Untitled"