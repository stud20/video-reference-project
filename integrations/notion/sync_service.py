# integrations/notion/sync_service.py
"""
Notion 동기화 서비스
로컬 데이터베이스와 Notion 데이터베이스 간 동기화 기능
"""

from typing import Dict, Any, List, Tuple, Optional
from integrations.notion.database import NotionDatabaseService
from integrations.notion.base import NotionBaseService
from integrations.notion.client import NotionService
from core.database.repository import VideoAnalysisDB
from utils.logger import get_logger
import streamlit as st

logger = get_logger(__name__)


class NotionSyncService:
    """Notion 동기화 서비스"""

    def __init__(self):
        """서비스 초기화"""
        self.notion_base = NotionBaseService(log_init=False)
        self.notion_db = NotionDatabaseService(log_init=False)
        self.notion_service = NotionService()
        self.local_db = VideoAnalysisDB()

    def get_all_notion_items(self) -> List[Dict[str, Any]]:
        """
        Notion 데이터베이스의 모든 항목 조회

        Returns:
            Notion 페이지 리스트
        """
        try:
            all_items = []
            has_more = True
            start_cursor = None

            while has_more:
                response = self.notion_base.client.databases.query(
                    database_id=self.notion_base.database_id,
                    start_cursor=start_cursor,
                    page_size=100
                )

                all_items.extend(response['results'])
                has_more = response['has_more']
                start_cursor = response.get('next_cursor')

            logger.info(f"Notion에서 {len(all_items)}개 항목 조회 완료")
            return all_items

        except Exception as e:
            logger.error(f"❌ Notion 항목 조회 중 오류: {str(e)}")
            import traceback
            logger.error(f"상세 오류: {traceback.format_exc()}")
            return None  # 오류 발생 시 None 반환하여 호출자가 인지할 수 있도록

    def extract_video_id_from_notion(self, page: Dict[str, Any]) -> Optional[str]:
        """
        Notion 페이지에서 비디오 ID 추출

        Args:
            page: Notion 페이지 객체

        Returns:
            비디오 ID 또는 None (빈 문자열은 None으로 변환)
        """
        try:
            properties = page.get('properties', {})
            video_id_prop = properties.get('영상 ID', {})

            if video_id_prop.get('rich_text'):
                if len(video_id_prop['rich_text']) > 0:
                    video_id = video_id_prop['rich_text'][0].get('text', {}).get('content', '')
                    # 빈 문자열은 None으로 반환
                    return video_id.strip() if video_id and video_id.strip() else None

            return None

        except Exception as e:
            logger.error(f"비디오 ID 추출 실패: {str(e)}")
            return None

    def find_missing_items(self) -> Tuple[List[Dict], List[str], Dict[str, int]]:
        """
        로컬 DB에는 있지만 Notion에 없는 항목 찾기

        Returns:
            (missing_items, duplicate_video_ids, stats)
            - missing_items: Notion에 없는 항목들
            - duplicate_video_ids: Notion에서 중복된 비디오 ID들
            - stats: 통계 정보
        """
        try:
            # 로컬 DB의 모든 비디오 가져오기
            local_videos = self.local_db.get_all_videos()
            logger.info(f"로컬 DB에서 {len(local_videos)}개 비디오 조회")

            # Notion의 모든 항목 가져오기
            notion_items = self.get_all_notion_items()

            # Notion API 오류 체크
            if notion_items is None:
                logger.error("⚠️ Notion API 호출 실패 - 동기화 중단")
                raise Exception("Notion API 호출 실패. API 키와 데이터베이스 ID를 확인하세요.")

            logger.info(f"Notion에서 {len(notion_items)}개 항목 조회")

            # Notion에 있는 비디오 ID 추출
            notion_video_ids = []
            video_id_counts = {}

            for item in notion_items:
                video_id = self.extract_video_id_from_notion(item)
                # extract 메서드가 이미 None이나 빈 문자열을 필터링함
                if video_id:
                    notion_video_ids.append(video_id)
                    video_id_counts[video_id] = video_id_counts.get(video_id, 0) + 1

            # 중복된 비디오 ID 찾기
            duplicate_ids = [vid for vid, count in video_id_counts.items() if count > 1]

            # 누락된 항목 찾기
            missing_items = []
            for video in local_videos:
                video_id = video.get('video_id', '').strip()
                # video_id가 존재하고, Notion에 없는 경우
                if video_id and video_id not in notion_video_ids:
                    missing_items.append(video)

            # 통계 정보
            stats = {
                'total_local': len(local_videos),
                'total_notion': len(notion_items),
                'unique_notion': len(set(notion_video_ids)),
                'missing_count': len(missing_items),
                'duplicate_count': len(duplicate_ids)
            }

            logger.info(f"동기화 분석 완료: 로컬={stats['total_local']}, "
                       f"Notion={stats['total_notion']}, 누락={stats['missing_count']}, "
                       f"중복={stats['duplicate_count']}")

            return missing_items, duplicate_ids, stats

        except Exception as e:
            logger.error(f"누락 항목 찾기 실패: {str(e)}")
            return [], [], {}

    def sync_missing_items(self, missing_items: List[Dict[str, Any]],
                          progress_callback=None) -> Tuple[int, int, List[str]]:
        """
        누락된 항목들을 Notion에 업로드

        Args:
            missing_items: 업로드할 항목들
            progress_callback: 진행 상태 콜백 함수

        Returns:
            (success_count, fail_count, errors)
        """
        success_count = 0
        fail_count = 0
        errors = []

        for i, video in enumerate(missing_items):
            try:
                # 진행 상태 콜백
                if progress_callback:
                    progress_callback(i + 1, len(missing_items), video.get('title', 'Unknown'))

                # 분석 데이터 확인 (None인 경우 빈 딕셔너리 전달)
                analysis_data = video.get('analysis_result')
                if analysis_data is None:
                    analysis_data = {}

                # 디버그 로그
                video_id = video.get('video_id', 'Unknown')
                platform = video.get('platform', 'Unknown')
                logger.info(f"🔄 동기화 시도: [{platform}] {video.get('title', 'Unknown')[:50]} (ID: {video_id})")

                # Notion에 업로드
                success, message = self.notion_service.add_video_to_database(
                    video_data=video,
                    analysis_data=analysis_data
                )

                if success:
                    success_count += 1
                    logger.info(f"✅ Notion 동기화 성공: [{platform}] {video.get('title', 'Unknown')}")
                else:
                    fail_count += 1
                    error_msg = f"[{platform}] {video.get('title', 'Unknown')}: {message}"
                    errors.append(error_msg)
                    logger.error(f"❌ Notion 동기화 실패: {error_msg}")

            except Exception as e:
                fail_count += 1
                error_msg = f"{video.get('title', 'Unknown')}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"❌ 동기화 중 오류: {error_msg}")

        return success_count, fail_count, errors

    def sync_all_to_notion(self) -> Tuple[int, int, List[str], Dict[str, Any]]:
        """
        전체 동기화 실행

        Returns:
            (success_count, fail_count, errors, stats)
        """
        try:
            # 누락 항목 찾기
            missing_items, duplicate_ids, stats = self.find_missing_items()

            if not missing_items:
                logger.info("동기화할 누락 항목이 없습니다.")
                return 0, 0, [], stats

            # 누락 항목 동기화
            success_count, fail_count, errors = self.sync_missing_items(missing_items)

            return success_count, fail_count, errors, stats

        except Exception as e:
            logger.error(f"전체 동기화 실패: {str(e)}")
            return 0, 0, [str(e)], {}

    def remove_duplicates_in_notion(self, duplicate_ids: List[str]) -> Tuple[int, List[str]]:
        """
        Notion에서 중복된 항목 제거 (최신 항목만 남기고 삭제)

        Args:
            duplicate_ids: 중복된 비디오 ID 리스트

        Returns:
            (removed_count, errors)
        """
        removed_count = 0
        errors = []

        for video_id in duplicate_ids:
            try:
                # 해당 비디오 ID를 가진 모든 페이지 조회
                response = self.notion_base.client.databases.query(
                    database_id=self.notion_base.database_id,
                    filter={
                        "property": "영상 ID",
                        "rich_text": {"equals": video_id}
                    }
                )

                pages = response['results']
                if len(pages) <= 1:
                    continue

                # 생성일 기준으로 정렬 (최신순)
                pages.sort(key=lambda x: x.get('created_time', ''), reverse=True)

                # 첫 번째(최신)를 제외하고 나머지 삭제
                for page in pages[1:]:
                    try:
                        self.notion_base.client.pages.update(
                            page_id=page['id'],
                            archived=True
                        )
                        removed_count += 1
                        logger.info(f"중복 항목 삭제: {video_id} (Page ID: {page['id']})")
                    except Exception as e:
                        errors.append(f"{video_id}: {str(e)}")

            except Exception as e:
                errors.append(f"{video_id}: {str(e)}")
                logger.error(f"중복 제거 실패: {str(e)}")

        return removed_count, errors