# src/ui/tabs/database_edit.py
"""
Database 탭의 편집 관련 기능
"""

import streamlit as st
from typing import Dict, Any
from storage.db_manager import VideoAnalysisDB
from handlers.db_handler import update_video_info, update_analysis_result
from utils.logger import get_logger
from utils.constants import GENRES

logger = get_logger(__name__)

def render_editable_card_info(video: Dict[str, Any]):
    """편집 가능한 카드 정보 렌더링"""
    video_id = video.get('video_id')
    
    # 기존 값들
    current_title = video.get('title', '')
    current_uploader = video.get('uploader', '')
    
    # 분석 결과
    analysis = video.get('analysis_result', {})
    current_genre = analysis.get('genre', '')
    current_expression = analysis.get('expression_style', '')
    current_reasoning = analysis.get('reasoning', '')
    current_features = analysis.get('features', '')
    current_mood = analysis.get('mood_tone', '')
    current_target = analysis.get('target_audience', '')
    
    # 편집 폼
    with st.container():
        # 제목 편집
        new_title = st.text_input(
            "제목", 
            value=current_title, 
            key=f"edit_title_{video_id}",
            label_visibility="collapsed",
            placeholder="제목 입력"
        )
        
        # 메타 정보 편집 (업로더, 장르, 표현형식)
        col1, col2, col3 = st.columns([2, 2, 2])
        
        with col1:
            new_uploader = st.text_input(
                "업로더",
                value=current_uploader,
                key=f"edit_uploader_{video_id}",
                label_visibility="collapsed",
                placeholder="업로더"
            )
        
        with col2:
            # 장르 선택
            if analysis:
                # 현재 장르의 인덱스 찾기
                genre_index = 0
                if current_genre in GENRES:
                    genre_index = GENRES.index(current_genre)
                
                new_genre = st.selectbox(
                    "장르",
                    options=GENRES,
                    index=genre_index,
                    key=f"edit_genre_{video_id}",
                    label_visibility="collapsed"
                )
            else:
                new_genre = None
        
        with col3:
            # 표현형식 선택
            if analysis:
                expression_types = ["2D", "3D", "실사", "혼합형", "스톱모션", "타이포그래피"]
                expression_index = 0
                if current_expression in expression_types:
                    expression_index = expression_types.index(current_expression)
                
                new_expression = st.selectbox(
                    "표현형식",
                    options=expression_types,
                    index=expression_index,
                    key=f"edit_expression_{video_id}",
                    label_visibility="collapsed"
                )
            else:
                new_expression = None
        
        # 분석 결과가 있는 경우 상세 편집
        if analysis:
            # 판단 이유
            new_reasoning = st.text_area(
                "💭 판단 이유",
                value=current_reasoning,
                key=f"edit_reasoning_{video_id}",
                height=100,
                label_visibility="visible",
                placeholder="장르 판단 이유를 입력하세요"
            )
            
            # 특징
            new_features = st.text_area(
                "✨ 특징",
                value=current_features,
                key=f"edit_features_{video_id}",
                height=100,
                label_visibility="visible",
                placeholder="영상의 특징 및 특이사항을 입력하세요"
            )
            
            # 분위기 (text_area로 변경)
            new_mood = st.text_area(
                "🎭 분위기",
                value=current_mood,
                key=f"edit_mood_{video_id}",
                height=70,
                label_visibility="visible",
                placeholder="분위기/톤"
            )
            
            # 타겟 고객층 (text_area로 변경)
            new_target = st.text_area(
                "🎯 타겟 고객층",
                value=current_target,
                key=f"edit_target_{video_id}",
                height=70,
                label_visibility="visible",
                placeholder="타겟 고객층"
            )
        else:
            new_genre = None
            new_expression = None
            new_reasoning = None
            new_features = None
            new_mood = None
            new_target = None
    
    # 편집된 데이터를 세션 상태에 저장
    st.session_state[f'edited_data_{video_id}'] = {
        'title': new_title,
        'uploader': new_uploader,
        'genre': new_genre,
        'expression_style': new_expression,
        'reasoning': new_reasoning,
        'features': new_features,
        'mood': new_mood,
        'target_audience': new_target
    }

def save_edited_data(video_id: str) -> bool:
    """편집된 데이터 저장"""
    edited_data = st.session_state.get(f'edited_data_{video_id}')
    if not edited_data:
        return False
    
    try:
        # 기본 정보 업데이트
        success = update_video_info(
            video_id,
            edited_data.get('title', ''),
            edited_data.get('uploader', ''),
            ''  # description은 비어있음
        )
        
        if not success:
            st.error("기본 정보 업데이트 실패")
            return False
        
        # 분석 결과가 있는 경우 업데이트
        if edited_data.get('genre') is not None:
            # 현재 분석 결과 가져오기
            db = VideoAnalysisDB()
            current_analysis = db.get_latest_analysis(video_id)
            db.close()
            
            if current_analysis:
                # 업데이트할 분석 데이터
                updated_analysis = current_analysis.copy()
                updated_analysis['genre'] = edited_data['genre']
                updated_analysis['expression_style'] = edited_data.get('expression_style', '')
                updated_analysis['reasoning'] = edited_data.get('reasoning', '')
                updated_analysis['features'] = edited_data.get('features', '')
                updated_analysis['mood_tone'] = edited_data.get('mood', '')
                updated_analysis['target_audience'] = edited_data.get('target_audience', '')
                
                success = update_analysis_result(video_id, updated_analysis)
                if not success:
                    st.error("분석 결과 업데이트 실패")
                    return False
        
        # Notion 데이터베이스 업데이트
        try:
            from services.notion_service import NotionService
            
            # 로컬 DB에서 전체 데이터 가져오기
            db = VideoAnalysisDB()
            video_data = db.get_video_info(video_id)
            analysis_data = db.get_latest_analysis(video_id)
            db.close()
            
            if video_data and analysis_data:
                # Notion 서비스 초기화
                notion_service = NotionService()
                
                # 편집된 데이터로 업데이트
                video_data['title'] = edited_data.get('title', video_data.get('title', ''))
                video_data['uploader'] = edited_data.get('uploader', video_data.get('uploader', ''))
                
                analysis_data['genre'] = edited_data.get('genre', analysis_data.get('genre', ''))
                analysis_data['expression_style'] = edited_data.get('expression_style', analysis_data.get('expression_style', ''))
                analysis_data['reasoning'] = edited_data.get('reasoning', analysis_data.get('reasoning', ''))
                analysis_data['features'] = edited_data.get('features', analysis_data.get('features', ''))
                analysis_data['mood_tone'] = edited_data.get('mood', analysis_data.get('mood_tone', ''))
                analysis_data['target_audience'] = edited_data.get('target_audience', analysis_data.get('target_audience', ''))
                
                # Notion에 업데이트
                notion_success, notion_result = notion_service.add_video_to_database(video_data, analysis_data)
                
                if notion_success:
                    logger.info(f"Notion 업데이트 성공: {video_id}")
                else:
                    logger.warning(f"Notion 업데이트 실패: {notion_result}")
                    # Notion 업데이트 실패해도 로컬 업데이트는 성공으로 처리
                    
        except ImportError:
            logger.warning("Notion 서비스를 사용할 수 없습니다. 로컬 DB만 업데이트됩니다.")
        except Exception as e:
            logger.error(f"Notion 업데이트 중 오류: {str(e)}")
            # Notion 오류가 있어도 로컬 업데이트는 성공으로 처리
        
        # 편집 데이터 정리
        if f'edited_data_{video_id}' in st.session_state:
            del st.session_state[f'edited_data_{video_id}']
        
        logger.info(f"편집 데이터 저장 완료: {video_id}")
        return True
        
    except Exception as e:
        logger.error(f"편집 데이터 저장 실패: {str(e)}")
        st.error(f"저장 실패: {str(e)}")
        return False

def toggle_edit_mode(video_id: str):
    """편집 모드 토글"""
    current_edit = st.session_state.get('edit_mode')
    
    if current_edit == video_id:
        # 편집 모드 종료
        st.session_state.edit_mode = None
        # 편집 데이터 정리
        if f'edited_data_{video_id}' in st.session_state:
            del st.session_state[f'edited_data_{video_id}']
    else:
        # 다른 카드 편집 중이면 먼저 정리
        if current_edit and f'edited_data_{current_edit}' in st.session_state:
            del st.session_state[f'edited_data_{current_edit}']
        # 새로운 편집 모드 시작
        st.session_state.edit_mode = video_id