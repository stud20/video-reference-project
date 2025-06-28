# src/ui/tabs/analyze_function_recom.py
"""
재추론 기능 모듈
"""

import streamlit as st
import os
from typing import List, Set
from ui.styles import get_enhanced_styles
from storage.db_manager import VideoAnalysisDB
from utils.logger import get_logger

logger = get_logger(__name__)


def render_reanalysis_section(video):
    """재추론 섹션 렌더링"""
    if not st.session_state.get('show_reanalysis', False):
        return
    
    # 디버깅: video 타입 확인
    logger.info(f"render_reanalysis_section - video type: {type(video)}")
    
    # video 객체 검증
    if not video or not hasattr(video, 'session_id'):
        st.error("재추론을 위한 올바른 비디오 정보가 없습니다.")
        logger.error(f"Invalid video object for reanalysis: {type(video)}")
        return
    
    st.markdown("---")
    st.markdown("### 🔄 재추론을 위한 이미지 선택")
    st.info("최대 10개까지 이미지를 선택할 수 있습니다.")
    
    # 선택된 이미지 추적
    if 'selected_images_for_reanalysis' not in st.session_state:
        st.session_state.selected_images_for_reanalysis = set()
    
    # 씬 정보 준비
    base_url = "https://sof.greatminds.kr"
    session_id = video.session_id
    all_scene_numbers = get_all_scene_numbers(video)
    
    # 선택된 이미지 개수 표시
    selected_count = len(st.session_state.selected_images_for_reanalysis)
    col1, col2 = st.columns([3, 1])
    with col1:
        st.metric("선택된 이미지", f"{selected_count} / 10")
    with col2:
        if st.button("❌ 선택 초기화", use_container_width=True):
            st.session_state.selected_images_for_reanalysis.clear()
            st.rerun()
    
    # 이미지 그리드 표시
    render_selectable_image_grid(base_url, session_id, all_scene_numbers)
    
    # 재추론 실행 버튼
    if selected_count > 0:
        st.markdown("---")
        if st.button("🚀 선택한 이미지로 재추론", type="primary", use_container_width=True):
            execute_reanalysis(video)
    else:
        st.warning("이미지를 선택해주세요.")


def render_selectable_image_grid(base_url: str, session_id: str, scene_numbers: Set[int]):
    """선택 가능한 이미지 그리드 렌더링 - Streamlit 네이티브 방식"""
    
    # CSS 스타일 정의
    st.markdown("""
    <style>
    /* 이미지 컨테이너 기본 스타일 */
    .image-container {
        position: relative;
        border: 3px solid transparent;
        border-radius: 8px;
        padding: 5px;
        transition: all 0.3s ease;
        background-color: transparent;
    }
    
    /* 선택된 이미지 스타일 */
    .image-container.selected {
        border-color: #1976d2 !important;
        background-color: rgba(25, 118, 210, 0.05);
        box-shadow: 0 0 15px rgba(25, 118, 210, 0.3);
    }
    
    /* 선택 표시 배지 */
    .selection-badge {
        position: absolute;
        top: 10px;
        right: 10px;
        background-color: #1976d2;
        color: white;
        width: 30px;
        height: 30px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 18px;
        z-index: 10;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
    }
    
    /* 이미지 스타일 */
    .image-container img {
        width: 100%;
        height: auto;
        display: block;
        border-radius: 4px;
    }
    
    /* 버튼 간격 조정 */
    .stButton > button {
        margin-top: 5px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 썸네일 포함한 모든 이미지 준비
    all_images = []
    
    # 썸네일 추가
    thumbnail_url = f"{base_url}/{session_id}/{session_id}_Thumbnail.jpg"
    all_images.append({
        'url': thumbnail_url,
        'id': 'thumbnail',
        'label': 'Thumbnail'
    })
    
    # 씬 이미지들 추가
    for scene_num in sorted(scene_numbers):
        scene_url = f"{base_url}/{session_id}/scene_{scene_num:04d}.jpg"
        all_images.append({
            'url': scene_url,
            'id': f'scene_{scene_num:04d}',
            'label': f'Scene {scene_num}'
        })
    
    # 5열 그리드로 이미지 표시
    num_cols = 5
    for i in range(0, len(all_images), num_cols):
        cols = st.columns(num_cols)
        
        for j, col in enumerate(cols):
            if i + j < len(all_images):
                img = all_images[i + j]
                
                with col:
                    # 선택 상태 확인
                    is_selected = img['id'] in st.session_state.selected_images_for_reanalysis
                    
                    # 컨테이너에 고유 ID 부여
                    container_id = f"img_container_{img['id']}"
                    
                    # HTML 컨테이너로 이미지와 선택 표시를 감싸기
                    container_class = "image-container selected" if is_selected else "image-container"
                    
                    # 전체 HTML 구조를 한 번에 렌더링
                    html_content = f"""
                    <div id="{container_id}" class="{container_class}">
                        <img src="{img['url']}" alt="{img['label']}">
                        {"<div class='selection-badge'>✓</div>" if is_selected else ""}
                    </div>
                    """
                    
                    st.markdown(html_content, unsafe_allow_html=True)
                    
                    # 토글 버튼
                    button_label = "✓ 선택 해제" if is_selected else "선택"
                    button_type = "secondary" if is_selected else "primary"
                    
                    if st.button(
                        button_label,
                        key=f"toggle_img_{img['id']}",
                        use_container_width=True,
                        type=button_type
                    ):
                        toggle_image_selection(img['id'])
                        st.rerun()


def toggle_image_selection(image_id: str):
    """이미지 선택 상태 토글"""
    if image_id in st.session_state.selected_images_for_reanalysis:
        st.session_state.selected_images_for_reanalysis.remove(image_id)
    else:
        if len(st.session_state.selected_images_for_reanalysis) < 10:
            st.session_state.selected_images_for_reanalysis.add(image_id)
        else:
            st.warning("최대 10개까지만 선택할 수 있습니다.")


def get_all_scene_numbers(video) -> Set[int]:
    """실제 존재하는 모든 씬 번호 추출"""
    all_nums = set()
    
    scenes_dir = os.path.join("data/temp", video.session_id, "scenes")
    
    if os.path.exists(scenes_dir):
        for filename in os.listdir(scenes_dir):
            if filename.startswith('scene_') and filename.endswith('.jpg'):
                try:
                    scene_num = int(filename.replace('scene_', '').replace('.jpg', ''))
                    all_nums.add(scene_num)
                except:
                    continue
    
    return all_nums


def execute_reanalysis(video):
    """재추론 실행"""
    selected_images = st.session_state.selected_images_for_reanalysis
    
    if not selected_images:
        st.error("선택된 이미지가 없습니다.")
        return
    
    # 콘솔창 표시
    st.markdown("### 💻 재추론 진행 상황")
    console_container = st.container()
    
    with console_container:
        console_placeholder = st.empty()
        
    # 콘솔 메시지 리스트
    console_messages = []
    
    def update_console(message: str, emoji: str = "ℹ️"):
        """콘솔 업데이트 함수"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        console_messages.append(f"[{timestamp}] {emoji} {message}")
        
        # 최근 10개 메시지만 표시
        display_messages = console_messages[-10:]
        console_text = "\n".join(display_messages)
        
        console_placeholder.markdown(
            f"""
            <div style="
                background-color: #1e1e1e;
                color: #00ff00;
                padding: 15px;
                border-radius: 5px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 14px;
                height: 200px;
                overflow-y: auto;
                white-space: pre-wrap;
            ">
{console_text}
            </div>
            """,
            unsafe_allow_html=True
        )
    
    try:
        update_console(f"재추론 시작 - {len(selected_images)}개 이미지 선택됨", "🚀")
        
        # 선택된 이미지 목록 표시
        for img_id in selected_images:
            update_console(f"선택된 이미지: {img_id}", "📸")
        
        # 선택된 이미지들의 Scene 객체 생성
        from src.models.video import Scene
        selected_scenes = []
        
        update_console("이미지 파일 준비 중...", "🔍")
        
        for img_id in selected_images:
            if img_id == 'thumbnail':
                # 썸네일은 분석에서 제외 (AI 분석기에서 자동으로 처리됨)
                update_console("썸네일은 자동으로 포함됩니다", "ℹ️")
                continue
                
            if img_id.startswith('scene_'):
                scene_path = os.path.join("data/temp", video.session_id, "scenes", f"{img_id}.jpg")
                
                if os.path.exists(scene_path):
                    scene = Scene(
                        timestamp=0.0,  # 재추론시에는 timestamp가 중요하지 않음
                        frame_path=scene_path,
                        scene_type='selected'
                    )
                    selected_scenes.append(scene)
                    update_console(f"{img_id} 준비 완료", "✅")
                else:
                    logger.warning(f"Scene file not found: {scene_path}")
                    update_console(f"{img_id} 파일을 찾을 수 없습니다", "⚠️")
        
        if not selected_scenes:
            st.error("선택한 이미지 파일을 찾을 수 없습니다.")
            return
        
        update_console(f"총 {len(selected_scenes)}개 씬 준비 완료", "📋")
        
        # AI 분석기 가져오기
        update_console("AI 분석기 초기화 중...", "🤖")
        
        if hasattr(st.session_state, 'video_service') and st.session_state.video_service.ai_analyzer:
            ai_analyzer = st.session_state.video_service.ai_analyzer
            
            # 기존 scenes를 백업 (무드보드를 위해)
            original_scenes = video.scenes.copy() if hasattr(video, 'scenes') else []
            
            # 재추론을 위해 선택된 씬들로 교체
            video.scenes = selected_scenes
            
            update_console("AI 분석 시작...", "🧠")
            update_console("이미지 특징 추출 중...", "🔬")
            
            # 재분석 실행
            new_result = ai_analyzer.analyze_video(video)
            
            # 원본 씬 정보는 별도 속성에 보관
            video.original_scenes = original_scenes
            
            if new_result:
                update_console("AI 분석 완료!", "✅")
                update_console(f"장르: {new_result.genre}", "🎭")
                
                # 이전 결과 백업 (디버깅용)
                old_genre = video.analysis_result.get('genre') if video.analysis_result else 'None'
                old_reasoning = video.analysis_result.get('reasoning')[:50] if video.analysis_result else 'None'
                
                logger.info(f"Before update - Genre: {old_genre}, Reasoning: {old_reasoning}...")
                
                # DB 업데이트
                update_console("데이터베이스 업데이트 중...", "💾")
                db = VideoAnalysisDB()
                
                # 기존 분석 결과 삭제하지 않고 새로운 버전으로 저장
                # (TinyDB는 버전 관리를 지원하므로 기존 결과도 보존됨)
                
                # 새로운 분석 결과 저장
                analysis_data = {
                    'genre': getattr(new_result, 'genre', ''),
                    'reasoning': getattr(new_result, 'reason', ''),
                    'features': getattr(new_result, 'features', ''),
                    'tags': getattr(new_result, 'tags', []),
                    'expression_style': getattr(new_result, 'format_type', ''),
                    'mood_tone': getattr(new_result, 'mood', ''),
                    'target_audience': getattr(new_result, 'target_audience', ''),
                    'analyzed_scenes': [os.path.basename(s.frame_path) for s in selected_scenes],
                    'model_used': os.getenv('OPENAI_MODEL', 'gpt-4o'),
                    'reanalysis': True,  # 재분석 플래그
                    'selected_images': list(selected_images)  # 선택된 이미지 ID 저장
                }
                
                db.save_analysis_result(video.session_id, analysis_data)
                
                # 영상 정보도 함께 가져오기 (Notion 업데이트용)
                video_info = db.get_video_info(video.session_id)
                
                db.close()
                
                update_console("데이터베이스 업데이트 완료", "✅")
                
                # Video 객체의 analysis_result 업데이트
                video.analysis_result = {
                    'genre': getattr(new_result, 'genre', ''),
                    'reasoning': getattr(new_result, 'reason', ''),
                    'features': getattr(new_result, 'features', ''),
                    'tags': getattr(new_result, 'tags', []),
                    'expression_style': getattr(new_result, 'format_type', ''),
                    'mood_tone': getattr(new_result, 'mood', ''),
                    'target_audience': getattr(new_result, 'target_audience', ''),
                }
                
                # 필름스트립을 위해 선택된 씬들로 video.scenes 업데이트
                video.scenes = selected_scenes  # 재추론에 사용된 씬들로 교체
                
                # 재추론 플래그 설정
                video.is_reanalyzed = True
                video.reanalyzed_images = list(selected_images)
                
                # 디버깅: 업데이트 확인
                logger.info(f"Updated analysis_result: {video.analysis_result['genre']}")
                logger.info(f"Updated scenes count: {len(video.scenes)}")
                
                # Notion 업데이트
                update_console("Notion 업데이트 시작...", "📝")
                try:
                    from services.notion_service import NotionService
                    
                    # Notion 서비스 초기화
                    notion = NotionService()
                    
                    # 연결 테스트
                    if not notion.test_connection():
                        update_console("Notion 연결 실패", "❌")
                        logger.error("Notion connection failed")
                        return
                    
                    update_console("Notion 연결 확인됨", "✅")
                    
                    # 영상 정보와 분석 결과를 함께 전달
                    if video_info:
                        # video_info에 필요한 필드가 없으면 추가
                        if 'uploader' not in video_info and hasattr(video.metadata, 'uploader'):
                            video_info['uploader'] = video.metadata.uploader
                        if 'channel' not in video_info and hasattr(video.metadata, 'uploader'):
                            video_info['channel'] = video.metadata.uploader
                        if 'view_count' not in video_info and hasattr(video.metadata, 'view_count'):
                            video_info['view_count'] = video.metadata.view_count
                        if 'tags' not in video_info and hasattr(video.metadata, 'tags'):
                            video_info['tags'] = video.metadata.tags
                        if 'description' not in video_info and hasattr(video.metadata, 'description'):
                            video_info['description'] = video.metadata.description
                        if 'upload_date' not in video_info and hasattr(video.metadata, 'upload_date'):
                            video_info['upload_date'] = video.metadata.upload_date
                        if 'like_count' not in video_info and hasattr(video.metadata, 'like_count'):
                            video_info['like_count'] = video.metadata.like_count
                        if 'comment_count' not in video_info and hasattr(video.metadata, 'comment_count'):
                            video_info['comment_count'] = video.metadata.comment_count
                        if 'language' not in video_info and hasattr(video.metadata, 'language'):
                            video_info['language'] = video.metadata.language
                        if 'categories' not in video_info and hasattr(video.metadata, 'categories'):
                            video_info['categories'] = video.metadata.categories
                        
                        # webpage_url 추가 (Vimeo 지원)
                        if 'webpage_url' not in video_info and hasattr(video.metadata, 'webpage_url'):
                            video_info['webpage_url'] = video.metadata.webpage_url
                        
                        # thumbnail 추가
                        if 'thumbnail' not in video_info and hasattr(video.metadata, 'thumbnail'):
                            video_info['thumbnail'] = video.metadata.thumbnail
                        
                        update_console(f"Video ID: {video.session_id} 데이터베이스에 추가 중...", "📄")
                        
                        # Notion 데이터베이스에 추가 (새로운 메서드 사용)
                        success, message = notion.add_video_to_database(
                            video_info,
                            analysis_data
                        )
                        
                        if success:
                            update_console("Notion 데이터베이스 업데이트 성공!", "✅")
                            update_console(f"페이지 ID: {message}", "📋")
                            logger.info(f"Notion updated successfully for video: {video.session_id}")
                            
                            # 데이터베이스 URL 표시
                            db_url = notion.get_database_url()
                            update_console(f"데이터베이스 보기: {db_url}", "🔗")
                        else:
                            update_console(f"Notion 업데이트 실패: {message}", "❌")
                            logger.error(f"Notion update failed: {message}")
                    else:
                        update_console("영상 정보를 찾을 수 없습니다", "❌")
                        logger.error(f"Video info not found for: {video.session_id}")
                        
                except ImportError as e:
                    update_console("Notion 서비스를 찾을 수 없습니다", "⚠️")
                    logger.error(f"Notion service import error: {str(e)}")
                except ValueError as e:
                    update_console(f"Notion 설정 오류: {str(e)}", "❌")
                    logger.error(f"Notion configuration error: {str(e)}")
                    update_console("환경변수를 확인하세요: NOTION_API_KEY, NOTION_DATABASE_ID", "⚠️")
                except Exception as e:
                    update_console(f"Notion 업데이트 오류: {str(e)}", "❌")
                    logger.error(f"Notion update error: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                
                # 중요: Video 객체 전체를 세션 상태에 저장
                st.session_state.analysis_result = video  # Video 객체를 저장!
                
                # 업데이트 시간 기록
                from datetime import datetime
                st.session_state.last_analysis_time = datetime.now().strftime("%H:%M:%S")
                
                # 디버깅: 저장 후 확인
                logger.info(f"After saving - session analysis_result type: {type(st.session_state.analysis_result)}")
                logger.info(f"New genre in session: {st.session_state.analysis_result.analysis_result.get('genre')}")
                
                st.session_state.selected_images_for_reanalysis.clear()
                st.session_state.show_reanalysis = False
                
                # 분석 상태를 completed로 설정
                from utils.session_state import set_analysis_state
                set_analysis_state('completed')
                
                update_console("모든 처리가 완료되었습니다!", "🎉")
                st.success("✅ 재추론이 완료되었습니다!")
                st.balloons()
                
                # 캐시 클리어 (중요!)
                st.cache_data.clear()
                
                # 페이지 새로고침
                st.rerun()
            else:
                update_console("재추론에 실패했습니다", "❌")
                st.error("재추론에 실패했습니다.")
        else:
            update_console("AI 분석기를 사용할 수 없습니다", "❌")
            st.error("AI 분석기를 사용할 수 없습니다.")
            
    except Exception as e:
        update_console(f"오류 발생: {str(e)}", "❌")
        st.error(f"재추론 중 오류 발생: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())