# src/ui/components/analysis_display.py
"""
분석 결과 표시 UI 컴포넌트
"""

import streamlit as st
import os
from typing import Dict, Any, Optional, List
from utils.constants import PRECISION_DESCRIPTIONS


def display_analysis_results(video):
    """분석 결과 전체 표시 - expander 레벨 조정"""
    st.header("📋 분석 결과")
    
    # 메타데이터 표시
    with st.expander("📄 영상 메타데이터", expanded=True):
        if video.metadata:
            metadata_dict = video.metadata.to_dict()
            
            # 주요 정보를 보기 좋게 표시
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("제목", metadata_dict.get('title', 'N/A'))
                st.metric("업로더", metadata_dict.get('uploader', 'N/A'))
                st.metric("길이", f"{metadata_dict.get('duration', 0) // 60}분 {metadata_dict.get('duration', 0) % 60}초")
            with col_b:
                st.metric("업로드 날짜", metadata_dict.get('upload_date', 'N/A'))
                st.metric("비디오 ID", metadata_dict.get('video_id', 'N/A'))
                st.metric("형식", metadata_dict.get('ext', 'N/A'))
            
            # 분석 정보 추가
            current_precision = int(os.getenv("SCENE_PRECISION_LEVEL", "5"))
            st.info(f"🎯 **사용된 정밀도 레벨**: {current_precision} - {PRECISION_DESCRIPTIONS[current_precision]}")
            
            # 설명
            if metadata_dict.get('description'):
                st.text_area("설명", metadata_dict['description'], height=100, disabled=True)
    
    # 씬 이미지 표시 (썸네일 포함)
    if video.scenes or (video.metadata and video.metadata.thumbnail):
        with st.expander("🎬 추출된 씬 이미지", expanded=True):
            display_scene_images_with_thumbnail(video)
    
    # AI 분석 결과 표시 (expander 없이)
    if video.analysis_result:
        st.markdown("---")
        display_ai_analysis_enhanced(video)
    
    # 세션 정보
    st.markdown("---")
    with st.expander("🔧 기술 정보", expanded=False):
        display_technical_info_content(video)


def display_scene_images_with_thumbnail(video):
    """썸네일과 씬 이미지를 함께 표시"""
    current_precision = int(os.getenv("SCENE_PRECISION_LEVEL", "5"))
    
    # 썸네일과 씬 개수 정보
    thumbnail_count = 1 if (video.metadata and video.metadata.thumbnail) else 0
    scene_count = len(video.scenes) if video.scenes else 0
    total_images = thumbnail_count + scene_count
    
    st.write(f"총 {total_images}개의 이미지 (썸네일 {thumbnail_count}개, 씬 {scene_count}개) - 정밀도 레벨: {current_precision}")
    
    # 이미지 그리드로 표시
    cols = st.columns(3)  # 3열로 표시
    img_index = 0
    
    # 썸네일 먼저 표시
    if video.metadata and video.metadata.thumbnail:
        thumbnail_path = None
        
        # 썸네일 경로 확인
        if os.path.exists(video.metadata.thumbnail):
            thumbnail_path = video.metadata.thumbnail
        else:
            # session_dir에서 썸네일 찾기
            if hasattr(video, 'session_dir') and video.session_dir:
                possible_extensions = ['.jpg', '.jpeg', '.png', '.webp']
                for ext in possible_extensions:
                    test_path = os.path.join(video.session_dir, f"thumbnail{ext}")
                    if os.path.exists(test_path):
                        thumbnail_path = test_path
                        break
        
        if thumbnail_path:
            with cols[img_index % 3]:
                st.image(thumbnail_path, 
                       caption="📌 썸네일",
                       use_container_width=True)
                img_index += 1
    
    # 씬 이미지 표시
    if video.scenes:
        for i, scene in enumerate(video.scenes):
            with cols[img_index % 3]:
                if os.path.exists(scene.frame_path):
                    st.image(scene.frame_path, 
                           caption=f"씬 {i+1} ({scene.timestamp:.1f}초)",
                           use_container_width=True)
                else:
                    st.warning(f"씬 {i+1} 이미지를 찾을 수 없습니다")
                img_index += 1


def display_scene_images_content(video):
    """씬 이미지 내용만 표시 (expander 없이) - 기존 호환성 유지"""
    display_scene_images_with_thumbnail(video)


def display_ai_analysis_enhanced(video):
    """AI 분석 결과 표시 - YouTube 태그 구분 표시"""
    analysis_result = video.analysis_result
    
    # expander 없이 바로 표시
    st.markdown("### 🤖 AI 분석 결과")
    
    # 상단 주요 정보
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📌 주요 정보")
        st.info(f"**장르**: {analysis_result.get('genre', 'N/A')}")
        st.info(f"**표현 형식**: {analysis_result.get('expression_style', 'N/A')}")
    
    with col2:
        st.subheader("🎭 분위기 및 타겟")
        if analysis_result.get('mood_tone'):
            st.info(f"**분위기**: {analysis_result['mood_tone']}")
        if analysis_result.get('target_audience'):
            st.info(f"**타겟 고객층**: {analysis_result['target_audience']}")
    
    # 구분선
    st.markdown("---")
    
    # 판단 이유
    if analysis_result.get('reasoning'):
        st.subheader("📝 장르 판단 이유")
        reason_text = analysis_result['reasoning']
        st.markdown(f"""
        <div style="background-color: #262730; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
            <p style="font-size: 16px; line-height: 1.6; white-space: pre-wrap; color: #fafafa;">{reason_text}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 특징 및 특이사항
    if analysis_result.get('features'):
        st.subheader("🎯 특징 및 특이사항")
        features_text = analysis_result['features']
        st.markdown(f"""
        <div style="background-color: #1a3a52; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
            <p style="font-size: 16px; line-height: 1.6; white-space: pre-wrap; color: #fafafa;">{features_text}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 태그 표시 (YouTube 태그와 AI 추론 태그 구분)
    display_tags_separated(video)
    
    # 분석 품질 정보
    display_analysis_quality(analysis_result)
    
    # 원본 데이터는 별도 섹션으로 (expander가 아닌)
    if st.checkbox("🔍 원본 분석 데이터 보기", key="show_raw_analysis"):
        st.json(analysis_result)


def display_tags_separated(video):
    """YouTube 태그와 AI 추론 태그를 구분하여 표시"""
    st.subheader("🏷️ 태그")
    
    # 전체 태그 가져오기
    all_tags = video.analysis_result.get('tags', [])
    youtube_tags = []
    ai_tags = []
    
    # YouTube 태그 가져오기
    if video.metadata and video.metadata.tags:
        youtube_tags = [tag for tag in video.metadata.tags if tag and len(tag) > 1]
    
    # AI 추론 태그 구분 (YouTube 태그에 없는 것들)
    for tag in all_tags:
        if tag not in youtube_tags:
            ai_tags.append(tag)
    
    # 태그 표시
    tag_html = '<div style="margin-top: 10px;">'
    
    # YouTube 태그 표시 (파란색)
    if youtube_tags:
        tag_html += '<div style="margin-bottom: 10px;"><strong>YouTube 태그:</strong></div>'
        for tag in youtube_tags[:10]:  # 최대 10개
            tag_html += f'<span style="background-color: #007ACC; color: white; padding: 5px 15px; margin: 5px; border-radius: 20px; font-size: 14px; display: inline-block; font-weight: 500;">#{tag}</span>'
    
    # AI 추론 태그 표시 (초록색)
    if ai_tags:
        tag_html += '<div style="margin-top: 15px; margin-bottom: 10px;"><strong>AI 추론 태그:</strong></div>'
        for tag in ai_tags[:10]:  # 최대 10개
            tag_html += f'<span style="background-color: #28a745; color: white; padding: 5px 15px; margin: 5px; border-radius: 20px; font-size: 14px; display: inline-block; font-weight: 500;">#{tag}</span>'
    
    tag_html += '</div>'
    
    # 태그 통계
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("전체 태그", f"{len(all_tags)}개")
    with col2:
        st.metric("YouTube 태그", f"{len(youtube_tags)}개")
    with col3:
        st.metric("AI 추론 태그", f"{len(ai_tags)}개")
    
    st.markdown(tag_html, unsafe_allow_html=True)


def display_ai_analysis(analysis_result: Dict[str, Any]):
    """AI 분석 결과 표시 - 기존 함수 (호환성 유지)"""
    # expander 없이 바로 표시
    st.markdown("### 🤖 AI 분석 결과")
    
    # 상단 주요 정보
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📌 주요 정보")
        st.info(f"**장르**: {analysis_result.get('genre', 'N/A')}")
        st.info(f"**표현 형식**: {analysis_result.get('expression_style', 'N/A')}")
    
    with col2:
        st.subheader("🎭 분위기 및 타겟")
        if analysis_result.get('mood_tone'):
            st.info(f"**분위기**: {analysis_result['mood_tone']}")
        if analysis_result.get('target_audience'):
            st.info(f"**타겟 고객층**: {analysis_result['target_audience']}")
    
    # 구분선
    st.markdown("---")
    
    # 판단 이유
    if analysis_result.get('reasoning'):
        st.subheader("📝 장르 판단 이유")
        reason_text = analysis_result['reasoning']
        st.markdown(f"""
        <div style="background-color: #262730; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
            <p style="font-size: 16px; line-height: 1.6; white-space: pre-wrap; color: #fafafa;">{reason_text}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 특징 및 특이사항
    if analysis_result.get('features'):
        st.subheader("🎯 특징 및 특이사항")
        features_text = analysis_result['features']
        st.markdown(f"""
        <div style="background-color: #1a3a52; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
            <p style="font-size: 16px; line-height: 1.6; white-space: pre-wrap; color: #fafafa;">{features_text}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 태그 표시
    tags = analysis_result.get('tags', [])
    if tags:
        st.subheader("🏷️ 태그")
        # 모든 태그를 하나의 HTML 블록으로 생성
        tag_html = '<div style="margin-top: 10px;">'
        for tag in tags:
            tag_html += f'<span style="background-color: #007ACC; color: white; padding: 5px 15px; margin: 5px; border-radius: 20px; font-size: 14px; display: inline-block; font-weight: 500;">#{tag}</span>'
        tag_html += '</div>'
        st.markdown(tag_html, unsafe_allow_html=True)
    
    # 분석 품질 정보
    display_analysis_quality(analysis_result)
    
    # 원본 데이터는 별도 섹션으로 (expander가 아닌)
    if st.checkbox("🔍 원본 분석 데이터 보기", key="show_raw_analysis"):
        st.json(analysis_result)


def display_tags_simple(tags: list):
    """태그 표시 - 간단한 버전"""
    if tags:
        st.subheader("🏷️ 태그")
        
        # 태그를 한 줄로 표시
        tags_text = " ".join([f"#{tag}" for tag in tags])
        st.info(tags_text)
        
        # 또는 버튼 스타일로 표시
        cols = st.columns(min(len(tags), 5))
        for i, tag in enumerate(tags):
            with cols[i % min(len(tags), 5)]:
                st.button(f"#{tag}", key=f"tag_{i}", disabled=True)


def display_analysis_quality(analysis_result: Dict[str, Any]):
    """분석 품질 정보 표시"""
    st.markdown("---")
    quality_col1, quality_col2, quality_col3 = st.columns(3)
    
    with quality_col1:
        reason_length = len(analysis_result.get('reasoning', ''))
        if reason_length >= 200:
            st.success(f"✅ 판단 이유: {reason_length}자")
        else:
            st.warning(f"⚠️ 판단 이유: {reason_length}자 (200자 미만)")
    
    with quality_col2:
        features_length = len(analysis_result.get('features', ''))
        if features_length >= 200:
            st.success(f"✅ 특징 설명: {features_length}자")
        else:
            st.warning(f"⚠️ 특징 설명: {features_length}자 (200자 미만)")
    
    with quality_col3:
        tag_count = len(analysis_result.get('tags', []))
        if tag_count >= 10:
            st.success(f"✅ 태그 수: {tag_count}개")
        else:
            st.warning(f"⚠️ 태그 수: {tag_count}개 (10개 미만)")


def display_video_metadata(video):
    """영상 메타데이터 표시"""
    with st.expander("📄 영상 메타데이터", expanded=True):
        if video.metadata:
            metadata_dict = video.metadata.to_dict()
            
            # 주요 정보를 보기 좋게 표시
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("제목", metadata_dict.get('title', 'N/A'))
                st.metric("업로더", metadata_dict.get('uploader', 'N/A'))
                st.metric("길이", f"{metadata_dict.get('duration', 0) // 60}분 {metadata_dict.get('duration', 0) % 60}초")
            with col_b:
                st.metric("업로드 날짜", metadata_dict.get('upload_date', 'N/A'))
                st.metric("비디오 ID", metadata_dict.get('video_id', 'N/A'))
                st.metric("형식", metadata_dict.get('ext', 'N/A'))
            
            # 분석 정보 추가
            current_precision = int(os.getenv("SCENE_PRECISION_LEVEL", "5"))
            st.info(f"🎯 **사용된 정밀도 레벨**: {current_precision} - {PRECISION_DESCRIPTIONS[current_precision]}")
            
            # 설명
            if metadata_dict.get('description'):
                st.text_area("설명", metadata_dict['description'], height=100, disabled=True)


def display_scene_images(video):
    """추출된 씬 이미지 표시 - 기존 함수 (호환성 유지)"""
    with st.expander("🎬 추출된 씬 이미지", expanded=True):
        display_scene_images_with_thumbnail(video)


def display_technical_info(video):
    """기술 정보 표시"""
    with st.expander("🔧 기술 정보"):
        display_technical_info_content(video)


def display_technical_info_content(video):
    """기술 정보 내용만 표시 (expander 없이)"""
    st.info(f"📁 세션 ID (Video ID): {video.session_id}")
    st.info(f"🎯 사용된 정밀도 레벨: {int(os.getenv('SCENE_PRECISION_LEVEL', '5'))}")
    st.info(f"💾 저장 위치: {st.session_state.storage_type.value}")
    if video.local_path:
        st.text(f"📄 비디오 경로: {video.local_path}")
    if video.scenes:
        st.text(f"🎬 추출된 씬 수: {len(video.scenes)}개")


def show_video_details(video: Dict[str, Any]):
    """영상 상세 정보 표시 (모달용)"""
    st.markdown("### 👁️ 영상 상세 정보")
    
    with st.expander("📄 기본 정보", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**제목**: {video.get('title', 'Unknown')}")
            st.write(f"**업로더**: {video.get('uploader', 'Unknown')}")
            st.write(f"**플랫폼**: {video.get('platform', 'Unknown')}")
        with col2:
            duration = video.get('duration', 0)
            st.write(f"**길이**: {duration//60}분 {duration%60}초")
            view_count = video.get('view_count')
            if view_count:
                st.write(f"**조회수**: {view_count:,}회")
            else:
                st.write("**조회수**: Unknown")
            st.write(f"**다운로드**: {video.get('download_date', 'Unknown')[:10]}")
        
        if video.get('description'):
            st.write("**설명**:")
            desc = video['description']
            if len(desc) > 500:
                st.write(desc[:500] + "...")
            else:
                st.write(desc)
    
    # AI 분석 결과
    if video.get('analysis_result'):
        display_analysis_summary(video['analysis_result'])


def display_analysis_summary(analysis: Dict[str, Any]):
    """AI 분석 결과 요약 표시"""
    with st.expander("🤖 AI 분석 결과", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**장르**: {analysis.get('genre', 'Unknown')}")
            st.write(f"**표현형식**: {analysis.get('expression_style', 'Unknown')}")
            st.write(f"**분위기**: {analysis.get('mood_tone', 'Unknown')}")
        with col2:
            st.write(f"**타겟 고객층**: {analysis.get('target_audience', 'Unknown')}")
            st.write(f"**분석 날짜**: {analysis.get('analysis_date', 'Unknown')[:10]}")
            st.write(f"**사용 모델**: {analysis.get('model_used', 'Unknown')}")
        
        if analysis.get('reasoning'):
            st.write("**판단 이유**:")
            st.info(analysis['reasoning'])
        
        if analysis.get('features'):
            st.write("**특징 및 특이사항**:")
            st.info(analysis['features'])
        
        if analysis.get('tags'):
            st.write("**태그**:")
            tag_html = '<div class="tag-container">'
            for tag in analysis['tags']:
                tag_html += f'<span class="tag">#{tag}</span>'
            tag_html += '</div>'
            st.markdown(tag_html, unsafe_allow_html=True)


def display_search_results():
    """검색 결과 표시"""
    if 'search_result' in st.session_state:
        result = st.session_state['search_result']
        display_single_search_result(result)
        del st.session_state['search_result']
    
    if 'search_results' in st.session_state:
        results = st.session_state['search_results']
        display_multiple_search_results(results)
        del st.session_state['search_results']


def display_single_search_result(result: Dict[str, Any]):
    """단일 검색 결과 표시"""
    st.markdown("### 🔍 검색 결과")
    
    with st.container():
        st.markdown(f"""
        <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
            <h4>📹 {result['video_id']}</h4>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("장르", result['genre'])
            st.caption(f"표현형식: {result.get('expression_style', 'N/A')}")
        with col2:
            st.metric("분위기", result.get('mood_tone', 'N/A'))
            st.caption(f"타겟: {result.get('target_audience', 'N/A')}")
        with col3:
            st.metric("분석 날짜", result.get('analysis_date', 'N/A')[:10])
            st.caption(f"모델: {result.get('model_used', 'N/A')}")
        
        # 상세 정보
        with st.expander("📝 상세 정보 보기"):
            if result.get('reasoning'):
                st.markdown("**판단 이유**")
                st.info(result['reasoning'])
            
            if result.get('features'):
                st.markdown("**특징 및 특이사항**")
                st.info(result['features'])
            
            if result.get('tags'):
                display_tags(result['tags'])


def display_multiple_search_results(results: list):
    """다중 검색 결과 표시"""
    st.markdown(f"### 🔍 검색 결과 ({len(results)}개)")
    
    for result in results:
        with st.expander(f"📹 {result['video_id']} - {result['genre']}"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**분석 날짜**: {result.get('analysis_date', 'N/A')[:10]}")
                st.write(f"**분위기**: {result.get('mood_tone', 'N/A')}")
                st.write(f"**타겟**: {result.get('target_audience', 'N/A')}")
            with col2:
                st.write(f"**표현형식**: {result.get('expression_style', 'N/A')}")
                tags = result.get('tags', [])
                if tags:
                    st.write(f"**태그**: {', '.join(tags[:5])}...")
                else:
                    st.write("**태그**: 없음")