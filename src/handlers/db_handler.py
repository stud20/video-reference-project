# src/handlers/db_handler.py
"""
데이터베이스 관련 작업 핸들러 - 확장된 메타데이터 지원
"""

import streamlit as st
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from storage.db_manager import VideoAnalysisDB
from utils.logger import get_logger

logger = get_logger(__name__)


def get_filtered_videos(db: VideoAnalysisDB, filter_type: str, search_query: str) -> List[Dict[str, Any]]:
    """필터 및 검색 조건에 따른 영상 목록 반환 - 확장된 메타데이터 포함"""
    videos = []
    
    # 모든 비디오 정보 가져오기
    all_videos = db.videos_table.all()
    
    # 각 비디오에 대해 분석 결과 및 추가 메타데이터 추가
    for video in all_videos:
        video_id = video.get('video_id')
        if video_id:
            # 분석 결과 추가
            analysis = db.get_latest_analysis(video_id)
            if analysis:
                video['analysis_result'] = analysis
            
            # 추가 메타데이터 확인 및 기본값 설정
            if 'uploader' not in video or not video['uploader']:
                video['uploader'] = video.get('channel', 'Unknown')
            
            if 'view_count' not in video:
                video['view_count'] = 0
            
            if 'tags' not in video:
                video['tags'] = []
            
            if 'upload_date' not in video:
                video['upload_date'] = ''
                
        videos.append(video)
    
    # 필터 적용
    if filter_type == 'analyzed':
        videos = [v for v in videos if v.get('analysis_result')]
    elif filter_type == 'not_analyzed':
        videos = [v for v in videos if not v.get('analysis_result')]
    elif filter_type == 'recent':
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        videos = [v for v in videos if v.get('download_date', '') > week_ago]
    
    # 검색 적용
    if search_query:
        search_lower = search_query.lower()
        filtered_videos = []
        for video in videos:
            # 제목 검색
            title_match = search_lower in video.get('title', '').lower()
            
            # 업로더 검색
            uploader_match = search_lower in video.get('uploader', '').lower()
            
            # 장르 검색
            genre_match = False
            tag_match = False
            
            if video.get('analysis_result'):
                genre_match = search_lower in video['analysis_result'].get('genre', '').lower()
                # AI 분석 태그 검색
                tags = video['analysis_result'].get('tags', [])
                tag_match = any(search_lower in tag.lower() for tag in tags)
            
            # YouTube 태그 검색
            youtube_tags = video.get('tags', [])
            youtube_tag_match = any(search_lower in tag.lower() for tag in youtube_tags)
            
            if title_match or uploader_match or genre_match or tag_match or youtube_tag_match:
                filtered_videos.append(video)
        
        videos = filtered_videos
    
    # 최신순 정렬
    videos.sort(key=lambda x: x.get('download_date', ''), reverse=True)
    
    return videos


def delete_video_with_confirmation(video_id: str) -> bool:
    """영상 삭제 처리"""
    db = VideoAnalysisDB()
    
    try:
        from tinydb import Query
        Video = Query()
        Analysis = Query()
        
        # 영상 정보 삭제
        removed_videos = db.videos_table.remove(Video.video_id == video_id)
        # 관련 분석 결과 삭제
        removed_analyses = db.analyses_table.remove(Analysis.video_id == video_id)
        
        success = len(removed_videos) > 0 or len(removed_analyses) > 0
        
        if success:
            logger.info(f"삭제 완료 - 영상: {len(removed_videos)}개, 분석: {len(removed_analyses)}개")
        else:
            logger.warning(f"삭제할 항목을 찾을 수 없음: {video_id}")
            
        return success
        
    except Exception as e:
        logger.error(f"삭제 중 오류 발생: {str(e)}")
        return False
    finally:
        db.close()


def bulk_delete_videos(video_ids: List[str]) -> tuple[int, int]:
    """여러 영상 일괄 삭제"""
    db = VideoAnalysisDB()
    success_count = 0
    fail_count = 0
    
    try:
        from tinydb import Query
        Video = Query()
        Analysis = Query()
        
        for video_id in video_ids:
            try:
                removed_videos = db.videos_table.remove(Video.video_id == video_id)
                removed_analyses = db.analyses_table.remove(Analysis.video_id == video_id)
                
                if removed_videos or removed_analyses:
                    success_count += 1
                else:
                    fail_count += 1
                    
            except Exception as e:
                fail_count += 1
                logger.error(f"영상 {video_id} 삭제 실패: {str(e)}")
        
        return success_count, fail_count
        
    finally:
        db.close()


def update_video_info(video_id: str, title: str, uploader: str, description: str) -> bool:
    """영상 정보 업데이트 - 확장된 메타데이터 지원"""
    db = VideoAnalysisDB()
    
    try:
        from tinydb import Query
        Video = Query()
        
        # 업데이트할 데이터
        update_data = {
            'title': title,
            'uploader': uploader,
            'description': description,
            'updated_at': datetime.now().isoformat()
        }
        
        # channel 필드도 업데이트 (호환성)
        if uploader:
            update_data['channel'] = uploader
        
        db.videos_table.update(update_data, Video.video_id == video_id)
        
        return True
        
    except Exception as e:
        logger.error(f"영상 정보 업데이트 실패: {str(e)}")
        return False
    finally:
        db.close()


def update_analysis_result(video_id: str, analysis_data: Dict[str, Any]) -> bool:
    """분석 결과 업데이트"""
    db = VideoAnalysisDB()
    
    try:
        # 새로운 분석 결과로 저장
        updated_analysis = {
            'video_id': video_id,
            'genre': analysis_data.get('genre', ''),
            'reasoning': analysis_data.get('reasoning', ''),
            'features': analysis_data.get('features', ''),
            'tags': analysis_data.get('tags', []),
            'mood_tone': analysis_data.get('mood_tone', ''),
            'target_audience': analysis_data.get('target_audience', ''),
            'expression_style': analysis_data.get('expression_style', ''),
            'analyzed_scenes': analysis_data.get('analyzed_scenes', []),
            'token_usage': analysis_data.get('token_usage', {}),
            'model_used': analysis_data.get('model_used', 'gpt-4o'),
            'analysis_date': datetime.now().isoformat(),
            'version': '1.0'
        }
        
        db.save_analysis_result(video_id, updated_analysis)
        return True
        
    except Exception as e:
        logger.error(f"분석 결과 업데이트 실패: {str(e)}")
        return False
    finally:
        db.close()


def delete_analysis_results(video_id: str) -> bool:
    """분석 결과 삭제"""
    db = VideoAnalysisDB()
    
    try:
        from tinydb import Query
        Analysis = Query()
        
        removed = db.analyses_table.remove(Analysis.video_id == video_id)
        return len(removed) > 0
        
    except Exception as e:
        logger.error(f"분석 결과 삭제 실패: {str(e)}")
        return False
    finally:
        db.close()


def export_selected_videos(video_ids: List[str]) -> str:
    """선택된 영상들 내보내기 - 확장된 메타데이터 포함"""
    db = VideoAnalysisDB()
    exported_data = []
    
    try:
        for video_id in video_ids:
            video_info = db.get_video_info(video_id)
            analysis_info = db.get_latest_analysis(video_id)
            
            # 전체 메타데이터 포함
            export_item = {
                'video_info': video_info,
                'analysis_result': analysis_info,
                'metadata': {
                    'exported_at': datetime.now().isoformat(),
                    'video_id': video_id,
                    'has_analysis': analysis_info is not None
                }
            }
            
            exported_data.append(export_item)
        
        # 내보내기 파일 생성
        export_filename = f"video_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        export_path = f"data/export/{export_filename}"
        
        os.makedirs("data/export", exist_ok=True)
        
        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(exported_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"영상 {len(video_ids)}개 내보내기 완료: {export_path}")
        return export_path
        
    except Exception as e:
        logger.error(f"내보내기 실패: {str(e)}")
        raise
    finally:
        db.close()


def search_videos_by_genre(genre: str) -> List[Dict[str, Any]]:
    """장르로 영상 검색"""
    db = VideoAnalysisDB()
    
    try:
        if genre == "전체":
            return []
        return db.search_by_genre(genre)
    finally:
        db.close()


def search_videos_by_tags(tags: List[str]) -> List[Dict[str, Any]]:
    """태그로 영상 검색"""
    db = VideoAnalysisDB()
    
    try:
        return db.search_by_tags(tags)
    finally:
        db.close()


def get_recent_analyses(limit: int = 5) -> List[Dict[str, Any]]:
    """최근 분석 결과 가져오기"""
    db = VideoAnalysisDB()
    
    try:
        all_analyses = db.analyses_table.all()
        all_analyses.sort(key=lambda x: x.get('analysis_date', ''), reverse=True)
        return all_analyses[:limit]
    finally:
        db.close()


def trigger_reanalysis(video_id: str, video_service) -> bool:
    """영상 재분석 트리거"""
    db = VideoAnalysisDB()
    
    try:
        video_info = db.get_video_info(video_id)
        if video_info and video_info.get('url'):
            # force_reanalyze=True로 재분석 실행
            result = video_service.process_video(video_info['url'], force_reanalyze=True)
            return True
        else:
            logger.error(f"영상 URL을 찾을 수 없음: {video_id}")
            return False
            
    except Exception as e:
        logger.error(f"재분석 실패: {str(e)}")
        return False
    finally:
        db.close()


def bulk_reanalyze_videos(video_ids: List[str], video_service) -> tuple[int, int]:
    """여러 영상 일괄 재분석"""
    db = VideoAnalysisDB()
    success_count = 0
    fail_count = 0
    
    try:
        for video_id in video_ids:
            try:
                video_info = db.get_video_info(video_id)
                if video_info and video_info.get('url'):
                    video_service.process_video(video_info['url'], force_reanalyze=True)
                    success_count += 1
                else:
                    fail_count += 1
                    logger.warning(f"영상 {video_id}의 URL을 찾을 수 없음")
            except Exception as e:
                fail_count += 1
                logger.error(f"영상 {video_id} 재분석 실패: {str(e)}")
        
        return success_count, fail_count
        
    finally:
        db.close()