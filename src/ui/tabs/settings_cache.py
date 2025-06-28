# src/ui/tabs/settings_cache.py
"""
캐시 관리 모듈
"""

import streamlit as st
import os
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple
from utils.logger import get_logger

logger = get_logger(__name__)


def render_cache_management():
    """캐시 관리 렌더링"""
    st.subheader("🗑️ 캐시 관리")
    st.markdown("영상 분석 과정에서 생성된 임시 파일과 캐시를 관리합니다.")
    
    # 캐시 디렉토리 경로
    temp_dir = Path("data/temp")
    
    # 캐시 현황 분석
    cache_info = analyze_cache_directory(temp_dir)
    
    # 캐시 통계 표시
    render_cache_statistics(cache_info)
    
    # 캐시 상세 정보
    st.markdown("---")
    render_cache_details(cache_info)
    
    # 캐시 관리 액션
    st.markdown("---")
    render_cache_actions(temp_dir, cache_info)
    
    # 자동 정리 설정
    st.markdown("---")
    render_auto_cleanup_settings()


def analyze_cache_directory(temp_dir: Path) -> Dict:
    """캐시 디렉토리 분석"""
    cache_info = {
        'total_size': 0,
        'total_files': 0,
        'total_folders': 0,
        'video_sessions': [],
        'file_types': {},
        'oldest_file': None,
        'newest_file': None
    }
    
    if not temp_dir.exists():
        return cache_info
    
    # 각 비디오 세션 분석
    for session_dir in temp_dir.iterdir():
        if session_dir.is_dir():
            session_info = analyze_session_directory(session_dir)
            cache_info['video_sessions'].append(session_info)
            cache_info['total_size'] += session_info['size']
            cache_info['total_files'] += session_info['file_count']
            cache_info['total_folders'] += 1
            
            # 파일 타입별 집계
            for file_type, count in session_info['file_types'].items():
                cache_info['file_types'][file_type] = cache_info['file_types'].get(file_type, 0) + count
            
            # 가장 오래된/최신 파일 추적
            if session_info['created_time']:
                if cache_info['oldest_file'] is None or session_info['created_time'] < cache_info['oldest_file']:
                    cache_info['oldest_file'] = session_info['created_time']
                if cache_info['newest_file'] is None or session_info['created_time'] > cache_info['newest_file']:
                    cache_info['newest_file'] = session_info['created_time']
    
    return cache_info


def analyze_session_directory(session_dir: Path) -> Dict:
    """개별 세션 디렉토리 분석"""
    session_info = {
        'session_id': session_dir.name,
        'path': session_dir,
        'size': 0,
        'file_count': 0,
        'file_types': {},
        'created_time': None,
        'has_video': False,
        'has_analysis': False,
        'scene_count': 0,
        'grouped_count': 0
    }
    
    # 모든 파일 순회
    for file_path in session_dir.rglob('*'):
        if file_path.is_file():
            # 파일 크기
            file_size = file_path.stat().st_size
            session_info['size'] += file_size
            session_info['file_count'] += 1
            
            # 파일 타입별 집계
            file_ext = file_path.suffix.lower()
            if file_ext:
                session_info['file_types'][file_ext] = session_info['file_types'].get(file_ext, 0) + 1
            
            # 생성 시간
            created_time = datetime.fromtimestamp(file_path.stat().st_ctime)
            if session_info['created_time'] is None or created_time < session_info['created_time']:
                session_info['created_time'] = created_time
            
            # 특정 파일 존재 여부 체크
            if file_ext == '.mp4':
                session_info['has_video'] = True
            elif file_path.name == 'analysis_result.json':
                session_info['has_analysis'] = True
            elif 'scenes' in file_path.parts and file_ext in ['.jpg', '.jpeg', '.png']:
                session_info['scene_count'] += 1
            elif 'grouped' in file_path.parts and file_ext in ['.jpg', '.jpeg', '.png']:
                session_info['grouped_count'] += 1
    
    return session_info


def render_cache_statistics(cache_info: Dict):
    """캐시 통계 표시"""
    st.markdown("### 📊 캐시 현황")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_size_mb = cache_info['total_size'] / (1024 * 1024)
        total_size_gb = total_size_mb / 1024
        
        if total_size_gb >= 1:
            st.metric("전체 크기", f"{total_size_gb:.2f} GB")
        else:
            st.metric("전체 크기", f"{total_size_mb:.1f} MB")
    
    with col2:
        st.metric("총 파일 수", f"{cache_info['total_files']:,}개")
    
    with col3:
        st.metric("비디오 세션", f"{cache_info['total_folders']}개")
    
    with col4:
        # 캐시 수명
        if cache_info['oldest_file']:
            age = datetime.now() - cache_info['oldest_file']
            if age.days > 0:
                st.metric("가장 오래된 캐시", f"{age.days}일 전")
            else:
                hours = age.seconds // 3600
                st.metric("가장 오래된 캐시", f"{hours}시간 전")
        else:
            st.metric("가장 오래된 캐시", "-")
    
    # 파일 타입별 분포
    if cache_info['file_types']:
        st.markdown("#### 📁 파일 타입별 분포")
        
        # 주요 파일 타입만 표시
        main_types = {
            '.mp4': '🎥 비디오',
            '.jpg': '🖼️ 이미지',
            '.json': '📄 데이터',
            '.txt': '📝 텍스트'
        }
        
        cols = st.columns(len(main_types))
        for i, (ext, label) in enumerate(main_types.items()):
            with cols[i]:
                count = cache_info['file_types'].get(ext, 0)
                st.metric(label, f"{count}개")


def render_cache_details(cache_info: Dict):
    """캐시 상세 정보"""
    with st.expander("📋 세션별 상세 정보"):
        if not cache_info['video_sessions']:
            st.info("캐시된 비디오 세션이 없습니다.")
            return
        
        # 세션을 크기순으로 정렬
        sorted_sessions = sorted(cache_info['video_sessions'], 
                               key=lambda x: x['size'], 
                               reverse=True)
        
        for session in sorted_sessions[:10]:  # 상위 10개만 표시
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
            
            with col1:
                st.text(f"📁 {session['session_id']}")
            
            with col2:
                size_mb = session['size'] / (1024 * 1024)
                st.text(f"{size_mb:.1f} MB")
            
            with col3:
                st.text(f"{session['file_count']} 파일")
            
            with col4:
                # 상태 아이콘
                icons = []
                if session['has_video']:
                    icons.append("🎥")
                if session['has_analysis']:
                    icons.append("✅")
                st.text(" ".join(icons) if icons else "-")
            
            with col5:
                if session['created_time']:
                    age = datetime.now() - session['created_time']
                    if age.days > 0:
                        st.text(f"{age.days}일 전")
                    else:
                        st.text(f"{age.seconds // 3600}시간 전")
        
        if len(cache_info['video_sessions']) > 10:
            st.caption(f"... 외 {len(cache_info['video_sessions']) - 10}개 세션")


def render_cache_actions(temp_dir: Path, cache_info: Dict):
    """캐시 관리 액션"""
    st.markdown("### 🧹 캐시 정리")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🗑️ 전체 캐시 삭제", type="secondary", use_container_width=True):
            if cache_info['total_size'] > 0:
                with st.spinner("캐시 삭제 중..."):
                    deleted_size, deleted_count = clean_all_cache(temp_dir)
                    st.success(f"✅ {deleted_size:.1f} MB, {deleted_count}개 파일 삭제 완료!")
                    time.sleep(1)
                    st.rerun()
            else:
                st.info("삭제할 캐시가 없습니다.")
    
    with col2:
        if st.button("📅 오래된 캐시 삭제", use_container_width=True):
            # 7일 이상 된 캐시 삭제
            with st.spinner("오래된 캐시 삭제 중..."):
                deleted_size, deleted_count = clean_old_cache(temp_dir, days=7)
                if deleted_count > 0:
                    st.success(f"✅ 7일 이상 된 캐시 {deleted_size:.1f} MB 삭제!")
                else:
                    st.info("7일 이상 된 캐시가 없습니다.")
    
    with col3:
        if st.button("🎯 선택적 삭제", use_container_width=True):
            st.session_state['show_selective_delete'] = True
    
    # 선택적 삭제 UI
    if st.session_state.get('show_selective_delete', False):
        render_selective_delete(cache_info)
    
    # 삭제 옵션
    with st.expander("⚙️ 삭제 옵션"):
        col1, col2 = st.columns(2)
        
        with col1:
            days_threshold = st.number_input(
                "캐시 보관 기간 (일)",
                min_value=1,
                max_value=30,
                value=7,
                help="이 기간보다 오래된 캐시를 삭제합니다"
            )
        
        with col2:
            keep_analyzed = st.checkbox(
                "분석 완료 세션 유지",
                value=True,
                help="AI 분석이 완료된 세션은 삭제하지 않습니다"
            )
        
        if st.button("🧹 맞춤 정리 실행", type="primary"):
            with st.spinner("맞춤 정리 중..."):
                deleted_size, deleted_count = clean_cache_with_options(
                    temp_dir, 
                    days_threshold, 
                    keep_analyzed
                )
                st.success(f"✅ {deleted_size:.1f} MB, {deleted_count}개 파일 삭제!")


def render_selective_delete(cache_info: Dict):
    """선택적 삭제 UI"""
    st.markdown("#### 🎯 세션 선택 삭제")
    
    # 삭제할 세션 선택
    selected_sessions = []
    
    for session in cache_info['video_sessions']:
        col1, col2, col3 = st.columns([0.5, 3, 1])
        
        with col1:
            if st.checkbox("", key=f"del_{session['session_id']}"):
                selected_sessions.append(session)
        
        with col2:
            st.text(f"{session['session_id']} ({session['size'] / (1024*1024):.1f} MB)")
        
        with col3:
            status = []
            if session['has_video']:
                status.append("🎥")
            if session['has_analysis']:
                status.append("✅")
            st.text(" ".join(status))
    
    if selected_sessions:
        if st.button(f"🗑️ 선택한 {len(selected_sessions)}개 세션 삭제", type="secondary"):
            total_deleted_size = 0
            for session in selected_sessions:
                try:
                    shutil.rmtree(session['path'])
                    total_deleted_size += session['size']
                except Exception as e:
                    st.error(f"삭제 실패: {session['session_id']} - {str(e)}")
            
            st.success(f"✅ {total_deleted_size / (1024*1024):.1f} MB 삭제 완료!")
            st.session_state['show_selective_delete'] = False
            time.sleep(1)
            st.rerun()


def render_auto_cleanup_settings():
    """자동 정리 설정"""
    st.markdown("### ⚙️ 자동 정리 설정")
    
    col1, col2 = st.columns(2)
    
    with col1:
        auto_cleanup = st.checkbox(
            "서버 업로드 후 자동 삭제",
            value=os.getenv("AUTO_CLEANUP", "false").lower() == "true",
            help="분석 완료 후 로컬 파일을 자동으로 삭제합니다"
        )
        
        if auto_cleanup:
            os.environ["AUTO_CLEANUP"] = "true"
        else:
            os.environ["AUTO_CLEANUP"] = "false"
    
    with col2:
        cleanup_delay = st.selectbox(
            "자동 삭제 지연 시간",
            options=["즉시", "1시간 후", "24시간 후", "7일 후"],
            index=0,
            disabled=not auto_cleanup
        )
    
    # 캐시 정책 설정
    st.markdown("#### 📋 캐시 정책")
    
    col3, col4 = st.columns(2)
    
    with col3:
        max_cache_size_gb = st.number_input(
            "최대 캐시 크기 (GB)",
            min_value=1,
            max_value=100,
            value=10,
            help="이 크기를 초과하면 오래된 캐시부터 자동 삭제됩니다"
        )
    
    with col4:
        cache_retention_days = st.number_input(
            "기본 보관 기간 (일)",
            min_value=1,
            max_value=90,
            value=30,
            help="이 기간이 지난 캐시는 자동으로 삭제됩니다"
        )
    
    # 예외 설정
    with st.expander("🛡️ 보호 설정"):
        st.checkbox("AI 분석 완료 세션 보호", value=True)
        st.checkbox("최근 24시간 내 세션 보호", value=True)
        st.checkbox("10MB 이상 대용량 비디오 보호", value=False)


# 유틸리티 함수들
def clean_all_cache(temp_dir: Path) -> Tuple[float, int]:
    """전체 캐시 삭제"""
    total_size = 0
    total_files = 0
    
    if temp_dir.exists():
        for session_dir in temp_dir.iterdir():
            if session_dir.is_dir():
                session_size, file_count = get_directory_size(session_dir)
                total_size += session_size
                total_files += file_count
                shutil.rmtree(session_dir)
    
    return total_size / (1024 * 1024), total_files


def clean_old_cache(temp_dir: Path, days: int) -> Tuple[float, int]:
    """오래된 캐시 삭제"""
    total_size = 0
    total_files = 0
    cutoff_date = datetime.now() - timedelta(days=days)
    
    if temp_dir.exists():
        for session_dir in temp_dir.iterdir():
            if session_dir.is_dir():
                # 디렉토리 생성 시간 확인
                created_time = datetime.fromtimestamp(session_dir.stat().st_ctime)
                if created_time < cutoff_date:
                    session_size, file_count = get_directory_size(session_dir)
                    total_size += session_size
                    total_files += file_count
                    shutil.rmtree(session_dir)
    
    return total_size / (1024 * 1024), total_files


def clean_cache_with_options(temp_dir: Path, days: int, keep_analyzed: bool) -> Tuple[float, int]:
    """옵션에 따른 캐시 정리"""
    total_size = 0
    total_files = 0
    cutoff_date = datetime.now() - timedelta(days=days)
    
    if temp_dir.exists():
        for session_dir in temp_dir.iterdir():
            if session_dir.is_dir():
                created_time = datetime.fromtimestamp(session_dir.stat().st_ctime)
                
                # 기간 체크
                if created_time >= cutoff_date:
                    continue
                
                # 분석 완료 체크
                if keep_analyzed:
                    analysis_file = session_dir / "analysis_result.json"
                    if analysis_file.exists():
                        continue
                
                # 삭제 실행
                session_size, file_count = get_directory_size(session_dir)
                total_size += session_size
                total_files += file_count
                shutil.rmtree(session_dir)
    
    return total_size / (1024 * 1024), total_files


def get_directory_size(path: Path) -> Tuple[int, int]:
    """디렉토리 크기와 파일 수 계산"""
    total_size = 0
    file_count = 0
    
    for file_path in path.rglob('*'):
        if file_path.is_file():
            total_size += file_path.stat().st_size
            file_count += 1
    
    return total_size, file_count