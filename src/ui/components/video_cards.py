# src/ui/components/video_cards.py
"""
비디오 카드 UI 컴포넌트 - 확장된 메타데이터 지원
"""

import streamlit as st
from typing import Dict, Any, List
from handlers.db_handler import trigger_reanalysis


def render_video_card(video: Dict[str, Any]):
    """개별 영상 카드 렌더링 - 확장된 메타데이터 표시"""
    video_id = video['video_id']
    is_selected = video_id in st.session_state.selected_videos
    
    # 카드 컨테이너
    with st.container():
        # 체크박스와 기본 정보
        col1, col2, col3, col4 = st.columns([0.5, 3.5, 2.5, 1.5])
        
        with col1:
            selected = st.checkbox(
                "선택",
                value=is_selected, 
                key=f"select_{video_id}",
                label_visibility="collapsed"
            )
            if selected and video_id not in st.session_state.selected_videos:
                st.session_state.selected_videos.append(video_id)
            elif not selected and video_id in st.session_state.selected_videos:
                st.session_state.selected_videos.remove(video_id)
        
        with col2:
            render_video_info_enhanced(video)
        
        with col3:
            render_analysis_info_enhanced(video)
        
        with col4:
            render_action_buttons(video_id, video.get('analysis_result'))
        
        st.markdown("---")


def render_video_info_enhanced(video: Dict[str, Any]):
    """비디오 기본 정보 렌더링 - 확장된 버전"""
    # 제목
    title = video.get('title', 'Unknown')
    if len(title) > 50:
        title = title[:50] + "..."
    st.markdown(f"**📹 {title}**")
    
    # ID와 플랫폼
    platform = video.get('platform', 'unknown')
    platform_emoji = "📺" if platform == "youtube" else "🎬" if platform == "vimeo" else "🎥"
    st.caption(f"{platform_emoji} ID: {video['video_id']}")
    
    # 업로더/채널명 (확장된 정보 사용)
    uploader = video.get('uploader', video.get('channel', 'Unknown'))
    if uploader and uploader != 'Unknown':
        st.caption(f"👤 업로더: {uploader}")
    else:
        st.caption("👤 업로더: Unknown")
    
    # 길이와 조회수
    duration = video.get('duration', 0)
    view_count = video.get('view_count', 0)
    
    info_parts = [f"⏱️ {duration//60}분 {duration%60}초"]
    if view_count > 0:
        if view_count >= 1000000:
            info_parts.append(f"👁️ {view_count/1000000:.1f}M회")
        elif view_count >= 1000:
            info_parts.append(f"👁️ {view_count/1000:.1f}K회")
        else:
            info_parts.append(f"👁️ {view_count}회")
    
    st.caption(" | ".join(info_parts))
    
    # 업로드 날짜
    upload_date = video.get('upload_date', '')
    if upload_date and len(upload_date) >= 8:
        year = upload_date[:4]
        month = upload_date[4:6]
        day = upload_date[6:8]
        st.caption(f"📅 업로드: {year}-{month}-{day}")


def render_analysis_info_enhanced(video: Dict[str, Any]):
    """분석 결과 정보 렌더링 - 확장된 버전"""
    if video.get('analysis_result'):
        analysis = video['analysis_result']
        st.success("✅ AI 분석 완료")
        
        # 장르와 표현형식
        genre = analysis.get('genre', 'Unknown')
        expression_style = analysis.get('expression_style', '')
        
        genre_info = f"**장르**: {genre}"
        if expression_style:
            genre_info += f" ({expression_style})"
        st.write(genre_info)
        
        # 분위기
        mood = analysis.get('mood_tone', 'Unknown')
        if mood and mood != 'Unknown':
            st.write(f"**분위기**: {mood}")
        
        # 태그 표시 (YouTube 태그와 AI 태그 구분)
        render_tags_with_source(video, analysis)
        
        # 분석 날짜 (작게 표시)
        analysis_date = analysis.get('analysis_date', '')
        if analysis_date:
            st.caption(f"분석: {analysis_date[:10]}")
    else:
        st.warning("⚠️ 분석 미완료")
        
        # YouTube 태그만 있는 경우 표시
        if video.get('tags'):
            st.caption("YouTube 태그:")
            render_youtube_tags_only(video.get('tags', []))


def render_tags_with_source(video: Dict[str, Any], analysis: Dict[str, Any]):
    """태그 렌더링 - YouTube와 AI 태그 구분"""
    all_tags = analysis.get('tags', [])
    youtube_tags = video.get('tags', [])
    
    if not all_tags and not youtube_tags:
        return
    
    # AI 추론 태그 구분
    ai_tags = []
    for tag in all_tags:
        if tag not in youtube_tags:
            ai_tags.append(tag)
    
    # 태그 HTML 생성
    tag_html = '<div style="margin-top: 5px;">'
    
    # YouTube 태그 (파란색, 최대 3개)
    youtube_display_count = 0
    for tag in youtube_tags[:3]:
        if tag and len(tag) > 1:
            tag_html += f'<span style="background-color: #007ACC; color: white; padding: 3px 8px; margin: 2px; border-radius: 12px; font-size: 12px; display: inline-block;">#{tag}</span>'
            youtube_display_count += 1
    
    # AI 태그 (초록색, 최대 3개)
    ai_display_count = 0
    for tag in ai_tags[:3]:
        if tag and len(tag) > 1:
            tag_html += f'<span style="background-color: #28a745; color: white; padding: 3px 8px; margin: 2px; border-radius: 12px; font-size: 12px; display: inline-block;">#{tag}</span>'
            ai_display_count += 1
    
    # 남은 태그 수 표시
    remaining = len(all_tags) - youtube_display_count - ai_display_count
    if remaining > 0:
        tag_html += f'<span style="background-color: #6c757d; color: white; padding: 3px 8px; margin: 2px; border-radius: 12px; font-size: 12px; display: inline-block;">+{remaining}</span>'
    
    tag_html += '</div>'
    
    st.markdown(tag_html, unsafe_allow_html=True)


def render_youtube_tags_only(tags: List[str], max_display: int = 4):
    """YouTube 태그만 표시"""
    if not tags:
        return
    
    tag_html = '<div style="margin-top: 5px;">'
    
    for i, tag in enumerate(tags[:max_display]):
        if tag and len(tag) > 1:
            tag_html += f'<span style="background-color: #007ACC; color: white; padding: 3px 8px; margin: 2px; border-radius: 12px; font-size: 12px; display: inline-block;">#{tag}</span>'
    
    if len(tags) > max_display:
        tag_html += f'<span style="background-color: #6c757d; color: white; padding: 3px 8px; margin: 2px; border-radius: 12px; font-size: 12px; display: inline-block;">+{len(tags) - max_display}</span>'
    
    tag_html += '</div>'
    st.markdown(tag_html, unsafe_allow_html=True)


def render_tags(tags: list, max_display: int = 5):
    """태그 렌더링 - 기존 호환성 유지"""
    if not tags:
        return
    
    # 태그를 하나의 HTML 문자열로 결합
    tag_html = '<div class="tag-container">'
    
    displayed_count = 0
    for i, tag in enumerate(tags):
        if i < max_display:
            tag_html += f'<span class="tag">#{tag}</span>'
            displayed_count += 1
    
    if len(tags) > max_display:
        tag_html += f'<span class="tag">+{len(tags) - max_display}</span>'
    
    tag_html += '</div>'
    
    # 한 번에 렌더링
    st.markdown(tag_html, unsafe_allow_html=True)


def render_action_buttons(video_id: str, has_analysis: bool):
    """액션 버튼 렌더링"""
    # 버튼을 수평으로 배치
    btn_cols = st.columns(5)
    
    with btn_cols[0]:
        if st.button("✏️", key=f"edit_{video_id}", help="편집", use_container_width=True):
            st.session_state.edit_video_id = video_id
            st.rerun()
    
    with btn_cols[1]:
        if st.button("👁️", key=f"view_{video_id}", help="상세보기", use_container_width=True):
            st.session_state.show_video_details = video_id
            st.rerun()
    
    with btn_cols[2]:
        if st.button("🗑️", key=f"delete_{video_id}", help="삭제", use_container_width=True):
            st.session_state.confirm_delete = video_id
            st.rerun()
    
    with btn_cols[3]:
        # 재분석 버튼 (분석이 없는 경우만)
        if not has_analysis:
            if st.button("🔄", key=f"reanalyze_{video_id}", help="재분석", use_container_width=True):
                with st.spinner(f"영상 {video_id} 재분석 중..."):
                    video_service = st.session_state.video_service
                    if trigger_reanalysis(video_id, video_service):
                        st.success(f"✅ 영상 {video_id} 재분석이 완료되었습니다!")
                    else:
                        st.error("재분석 중 오류가 발생했습니다.")
                st.rerun()
        else:
            # Notion 업로드 버튼 (분석이 있는 경우)
            if st.button("📝", key=f"notion_{video_id}", help="Notion 업로드", use_container_width=True):
                try:
                    from services.notion_service import NotionService
                    from storage.db_manager import VideoAnalysisDB
                    
                    notion = NotionService()
                    
                    # 데이터 가져오기
                    db = VideoAnalysisDB()
                    video_data = db.get_video_info(video_id)
                    analysis_data = db.get_latest_analysis(video_id)
                    db.close()
                    
                    if video_data and analysis_data:
                        # 데이터베이스에 업로드 (기존 add_video_analysis_to_page 대신)
                        success, result = notion.add_video_to_database(
                            video_data,
                            analysis_data
                        )
                        
                        if success:
                            st.success(f"✅ Notion DB 업로드 성공!")
                            # 데이터베이스 URL 표시
                            db_url = notion.get_database_url()
                            st.info(f"📊 [데이터베이스 보기]({db_url})")
                        else:
                            st.error(f"업로드 실패: {result}")
                    else:
                        st.error("데이터를 가져올 수 없습니다.")
                        
                except ImportError:
                    st.error("Notion 서비스를 사용할 수 없습니다.")
                except ValueError as e:
                    st.error(f"Notion 설정 오류: {str(e)}")
                    st.info("필요한 환경변수: NOTION_API_KEY, NOTION_DATABASE_ID")
                except Exception as e:
                    st.error(f"Notion 업로드 오류: {str(e)}")


def render_video_card_compact(video: Dict[str, Any]):
    """컴팩트한 비디오 카드 (리스트용)"""
    video_id = video['video_id']
    
    with st.container():
        col1, col2, col3 = st.columns([3, 2, 1])
        
        with col1:
            title = video.get('title', 'Unknown')[:30]
            st.write(f"**{title}...**")
            
            # 업로더와 조회수
            uploader = video.get('uploader', 'Unknown')
            view_count = video.get('view_count', 0)
            
            info_parts = [video_id, f"{video.get('duration', 0)//60}분"]
            if uploader != 'Unknown':
                info_parts.append(uploader)
            if view_count > 0:
                info_parts.append(f"{view_count:,}회")
            
            st.caption(" | ".join(info_parts))
        
        with col2:
            if video.get('analysis_result'):
                analysis = video['analysis_result']
                genre = analysis.get('genre', 'Unknown')
                expression = analysis.get('expression_style', '')
                
                genre_text = f"🎬 {genre}"
                if expression:
                    genre_text += f" ({expression})"
                st.write(genre_text)
            else:
                st.write("⚠️ 미분석")
        
        with col3:
            if st.button("보기", key=f"view_compact_{video_id}"):
                st.session_state.show_video_details = video_id
                st.rerun()