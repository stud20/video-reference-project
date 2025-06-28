# src/ui/tabs/database_delete.py
"""
Database 탭의 삭제 기능 관리 모듈
- 두 번 클릭 삭제
- Notion 연동 삭제
- 관련 파일 정리
"""

import streamlit as st
import time
from typing import Optional, Tuple
from storage.db_manager import VideoAnalysisDB
from services.notion_service import NotionService
from utils.logger import get_logger
import os
import shutil

logger = get_logger(__name__)


class DeleteManager:
    """비디오 삭제 관리 클래스"""
    
    def __init__(self):
        self.logger = logger
        self.timeout_seconds = 3.0  # 삭제 확인 타임아웃
    
    def handle_delete_button(self, video_id: str) -> bool:
        """
        삭제 버튼 핸들링 - 두 번 클릭 방식
        
        Returns:
            True if deletion should proceed
        """
        # 삭제 상태 초기화
        if 'delete_confirm_states' not in st.session_state:
            st.session_state.delete_confirm_states = {}
        
        # 현재 시간
        current_time = time.time()
        
        # 이전 상태 확인
        if video_id in st.session_state.delete_confirm_states:
            last_click_time = st.session_state.delete_confirm_states[video_id]
            
            # 타임아웃 체크
            if current_time - last_click_time > self.timeout_seconds:
                # 타임아웃 - 첫 번째 클릭으로 처리
                st.session_state.delete_confirm_states[video_id] = current_time
                return False
            else:
                # 두 번째 클릭 - 삭제 진행
                del st.session_state.delete_confirm_states[video_id]
                return True
        else:
            # 첫 번째 클릭
            st.session_state.delete_confirm_states[video_id] = current_time
            return False
    
    def delete_video_complete(self, video_id: str, delete_notion: bool = True, delete_files: bool = False) -> Tuple[bool, str]:
        """
        비디오 완전 삭제 - DB, Notion, 파일
        
        Args:
            video_id: 삭제할 비디오 ID
            delete_notion: Notion에서도 삭제할지 여부
            delete_files: 로컬/서버 파일도 삭제할지 여부
            
        Returns:
            (성공여부, 메시지)
        """
        errors = []
        successes = []
        
        # 1. DB에서 삭제
        try:
            if self._delete_from_db(video_id):
                successes.append("DB 삭제")
            else:
                errors.append("DB 삭제 실패")
        except Exception as e:
            errors.append(f"DB 삭제 오류: {str(e)}")
        
        # 2. Notion에서 삭제 (옵션)
        if delete_notion:
            try:
                notion_result = self._delete_from_notion(video_id)
                if notion_result[0]:
                    successes.append("Notion 삭제")
                else:
                    errors.append(f"Notion: {notion_result[1]}")
            except Exception as e:
                errors.append(f"Notion 삭제 오류: {str(e)}")
        
        # 3. 파일 삭제 (옵션)
        if delete_files:
            try:
                files_deleted = self._delete_files(video_id)
                if files_deleted > 0:
                    successes.append(f"{files_deleted}개 파일 삭제")
            except Exception as e:
                errors.append(f"파일 삭제 오류: {str(e)}")
        
        # 결과 반환
        if errors:
            return False, f"부분 실패: {', '.join(errors)}"
        else:
            return True, f"완료: {', '.join(successes)}"
    
    def _delete_from_db(self, video_id: str) -> bool:
        """DB에서 삭제"""
        db = VideoAnalysisDB()
        try:
            from tinydb import Query
            Video = Query()
            Analysis = Query()
            
            # 영상 정보 삭제
            removed_videos = db.videos_table.remove(Video.video_id == video_id)
            # 분석 결과 삭제
            removed_analyses = db.analyses_table.remove(Analysis.video_id == video_id)
            
            success = len(removed_videos) > 0 or len(removed_analyses) > 0
            
            if success:
                self.logger.info(f"DB 삭제 완료 - 영상: {len(removed_videos)}, 분석: {len(removed_analyses)}")
            
            return success
            
        finally:
            db.close()
    
    def _delete_from_notion(self, video_id: str) -> Tuple[bool, str]:
        """Notion에서 삭제"""
        try:
            notion = NotionService()
            # 통합된 삭제 메서드 사용
            return notion.delete_video_from_notion(video_id)
                
        except Exception as e:
            self.logger.error(f"Notion 삭제 오류: {str(e)}")
            return False, str(e)
    
    def _delete_files(self, video_id: str) -> int:
        """로컬 파일 삭제"""
        deleted_count = 0
        
        # 임시 디렉토리 확인
        temp_dirs = [
            f"data/temp/{video_id}",
            f"results/videos/{video_id}",
        ]
        
        for dir_path in temp_dirs:
            if os.path.exists(dir_path):
                try:
                    shutil.rmtree(dir_path)
                    deleted_count += 1
                    self.logger.info(f"디렉토리 삭제: {dir_path}")
                except Exception as e:
                    self.logger.error(f"디렉토리 삭제 실패: {dir_path} - {str(e)}")
        
        return deleted_count
    
    def bulk_delete(self, video_ids: list, delete_notion: bool = True, delete_files: bool = False) -> Tuple[int, int, list]:
        """
        일괄 삭제
        
        Returns:
            (성공 개수, 실패 개수, 오류 메시지 리스트)
        """
        success_count = 0
        fail_count = 0
        errors = []
        
        # 진행률 표시
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, video_id in enumerate(video_ids):
            status_text.text(f"삭제 중... ({i+1}/{len(video_ids)}) - {video_id}")
            progress_bar.progress((i + 1) / len(video_ids))
            
            success, message = self.delete_video_complete(video_id, delete_notion, delete_files)
            
            if success:
                success_count += 1
            else:
                fail_count += 1
                errors.append(f"{video_id}: {message}")
        
        progress_bar.empty()
        status_text.empty()
        
        return success_count, fail_count, errors


# 전역 인스턴스
delete_manager = DeleteManager()


def get_delete_button_text(video_id: str) -> str:
    """삭제 버튼 텍스트 가져오기"""
    if 'delete_confirm_states' not in st.session_state:
        return "🗑️"
    
    if video_id in st.session_state.delete_confirm_states:
        current_time = time.time()
        last_click = st.session_state.delete_confirm_states[video_id]
        
        if current_time - last_click <= delete_manager.timeout_seconds:
            return "❌"  # 정말 삭제?
    
    return "🗑️"


def get_delete_button_type(video_id: str) -> str:
    """삭제 버튼 타입 가져오기"""
    if 'delete_confirm_states' not in st.session_state:
        return "secondary"
    
    if video_id in st.session_state.delete_confirm_states:
        current_time = time.time()
        last_click = st.session_state.delete_confirm_states[video_id]
        
        if current_time - last_click <= delete_manager.timeout_seconds:
            return "primary"  # 강조 표시
    
    return "secondary"