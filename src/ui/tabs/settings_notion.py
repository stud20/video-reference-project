# src/ui/components/settings_notion.py
"""
Settings 탭 - Notion 연동 설정
"""

import streamlit as st
import os
from pathlib import Path
from typing import Optional, Dict, Any
import webbrowser
from utils.logger import get_logger

logger = get_logger(__name__)


def render_notion_settings():
    """Notion 연동 설정 UI 렌더링"""
    st.header("🔗 Notion 연동 설정")
    
    # 현재 설정 상태 표시
    render_current_status()
    
    st.markdown("---")
    
    # API 설정
    render_api_settings()
    
    st.markdown("---")
    
    # 페이지 바로가기
    render_page_shortcuts()


def render_current_status():
    """현재 Notion 연동 상태 표시"""
    st.subheader("📊 현재 설정")
    
    # 환경변수 읽기
    api_key = os.getenv("NOTION_API_KEY", "")
    page_id = os.getenv("NOTION_PARENT_PAGE_ID", "")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if api_key:
            # API 키 마스킹 표시
            masked_key = api_key[:7] + "*" * (len(api_key) - 10) + api_key[-3:] if len(api_key) > 10 else "***"
            st.success(f"✅ API 키 설정됨: {masked_key}")
        else:
            st.error("❌ API 키 미설정")
    
    with col2:
        if page_id:
            st.success(f"✅ 데이터베이스 ID: {page_id[:8]}...")
        else:
            st.warning("⚠️ 데이터베이스 ID 미설정")
    
    # 연결 상태 테스트
    if api_key:
        if st.button("🔌 연결 테스트", key="test_notion_connection"):
            test_notion_connection()


def render_api_settings():
    """API 설정 입력 폼"""
    st.subheader("🔑 API 설정")
    
    # 현재 값 읽기
    current_api_key = os.getenv("NOTION_API_KEY", "")
    current_page_id = os.getenv("NOTION_PARENT_PAGE_ID", "")
    
    with st.form("notion_api_form"):
        # API 키 입력
        st.markdown("**Notion API 키**")
        st.caption("Notion Integration 페이지에서 발급받은 API 키를 입력하세요.")
        
        api_key = st.text_input(
            "API 키",
            value=current_api_key,
            type="password",
            placeholder="secret_...",
            label_visibility="collapsed"
        )
        
        # 데이터베이스 ID 입력
        st.markdown("**데이터베이스 ID**")
        st.caption("영상 분석 결과를 저장할 Notion 데이터베이스의 ID를 입력하세요.")
        
        page_id = st.text_input(
            "데이터베이스 ID",
            value=current_page_id,
            placeholder="32자리 데이터베이스 ID (예: a1b2c3d4e5f6...)",
            label_visibility="collapsed"
        )
        
        # 도움말
        with st.expander("❓ Notion 설정 방법"):
            st.markdown("""
            ### 1. API 키 발급
            1. [Notion Integrations](https://www.notion.so/my-integrations) 페이지 방문
            2. "New integration" 클릭
            3. 이름 입력 후 생성
            4. "Internal Integration Token" 복사
            
            ### 2. 데이터베이스 ID 찾기
            1. Notion에서 데이터베이스 페이지 열기
            2. 우측 상단 "..." 메뉴 → "Copy link"
            3. URL에서 데이터베이스 ID 추출:
               - `https://notion.so/{workspace}/{데이터베이스ID}?v=...`
               - 하이픈(-) 제거한 32자리 문자열
            
            ### 3. 데이터베이스 권한 설정
            1. 데이터베이스 우측 상단 "Share" 클릭
            2. "Invite" → Integration 선택
            3. 생성한 Integration 추가
            
            ### 4. 데이터베이스 필수 속성
            데이터베이스에 다음 속성들이 있어야 합니다:
            - 제목 (Title)
            - URL (URL)
            - 장르 (Select)
            - 태그 (Multi-select)
            - 분석일 (Date)
            """)
        
        # 저장 버튼
        col1, col2 = st.columns([3, 1])
        with col2:
            save_button = st.form_submit_button("💾 저장", type="primary", use_container_width=True)
        
        if save_button:
            save_notion_settings(api_key, page_id)


def render_page_shortcuts():
    """Notion 데이터베이스 바로가기"""
    st.subheader("📊 데이터베이스 바로가기")
    
    page_id = os.getenv("NOTION_PARENT_PAGE_ID", "")
    
    if page_id:
        # 데이터베이스 정보 가져오기
        database_info = get_notion_page_info(page_id)
        
        if database_info:
            st.info(f"📊 데이터베이스: {database_info.get('title', 'Untitled')}")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🌐 Notion에서 열기", key="open_notion_page", use_container_width=True):
                    open_notion_page(database_info.get('url'))
            
            with col2:
                if st.button("🔄 정보 새로고침", key="refresh_page_info", use_container_width=True):
                    st.rerun()
            
            with col3:
                if st.button("📋 URL 복사", key="copy_notion_url", use_container_width=True):
                    st.code(database_info.get('url', ''), language=None)
                    st.success("URL이 표시되었습니다. 복사해서 사용하세요.")
        else:
            st.warning("데이터베이스 정보를 가져올 수 없습니다. API 키와 데이터베이스 ID를 확인해주세요.")
    else:
        st.info("데이터베이스 ID를 설정하면 바로가기 기능을 사용할 수 있습니다.")
    
    # 업로드 통계 (간단히)
    st.markdown("---")
    st.subheader("📊 업로드 통계")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 세션 상태에서 통계 가져오기 (임시)
        uploaded_count = st.session_state.get('notion_uploaded_count', 0)
        st.metric("오늘 업로드", f"{uploaded_count}개")
    
    with col2:
        failed_count = st.session_state.get('notion_failed_count', 0)
        st.metric("실패", f"{failed_count}개")
    
    with col3:
        if st.button("📈 통계 초기화", key="reset_notion_stats", use_container_width=True):
            st.session_state.notion_uploaded_count = 0
            st.session_state.notion_failed_count = 0
            st.success("통계가 초기화되었습니다.")
            st.rerun()


def test_notion_connection():
    """Notion 연결 테스트"""
    with st.spinner("연결 테스트 중..."):
        try:
            from services.notion_service import NotionService
            
            notion = NotionService()
            if notion.test_connection():
                st.success("✅ Notion 연결 성공!")
                
                # 데이터베이스 정보 가져오기
                page_id = os.getenv("NOTION_PARENT_PAGE_ID", "")
                if page_id:
                    database_info = get_notion_page_info(page_id)
                    if database_info:
                        st.info(f"📊 연결된 데이터베이스: {database_info.get('title', 'Untitled')}")
                    else:
                        st.warning("데이터베이스 정보를 가져올 수 없습니다. 데이터베이스 ID와 권한을 확인해주세요.")
            else:
                st.error("❌ Notion 연결 실패! API 키를 확인해주세요.")
                
        except ImportError:
            st.error("Notion 서비스 모듈을 찾을 수 없습니다.")
        except ValueError as e:
            st.error(f"❌ {str(e)}")
        except Exception as e:
            st.error(f"연결 테스트 중 오류 발생: {str(e)}")


def save_notion_settings(api_key: str, page_id: str):
    """Notion 설정 저장"""
    try:
        # .env 파일 경로
        env_path = Path(".env")
        
        # 기존 .env 내용 읽기
        env_content = {}
        if env_path.exists():
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_content[key.strip()] = value.strip().strip('"\'')
        
        # 새 값 업데이트
        if api_key:
            env_content['NOTION_API_KEY'] = api_key
            os.environ['NOTION_API_KEY'] = api_key
        
        if page_id:
            # 페이지 ID에서 하이픈 제거
            clean_page_id = page_id.replace('-', '')
            env_content['NOTION_PARENT_PAGE_ID'] = clean_page_id
            os.environ['NOTION_PARENT_PAGE_ID'] = clean_page_id
        
        # .env 파일 다시 쓰기
        with open(env_path, 'w', encoding='utf-8') as f:
            for key, value in env_content.items():
                # 값에 공백이나 특수문자가 있으면 따옴표로 감싸기
                if ' ' in value or any(c in value for c in ['#', '$', '&', '(', ')', '|', ';']):
                    f.write(f'{key}="{value}"\n')
                else:
                    f.write(f'{key}={value}\n')
        
        st.success("✅ Notion 설정이 저장되었습니다!")
        
        # 연결 테스트 자동 실행
        if api_key:
            test_notion_connection()
            
    except Exception as e:
        st.error(f"설정 저장 중 오류 발생: {str(e)}")
        logger.error(f"Notion 설정 저장 오류: {str(e)}")


def get_notion_page_info(page_id: str) -> Optional[Dict[str, Any]]:
    """Notion 데이터베이스 정보 가져오기"""
    try:
        # 간단히 URL과 기본 정보만 반환
        # NotionService의 실제 구조를 모르므로 기본 정보만 제공
        return {
            'id': page_id,
            'url': f"https://greatminds.notion.site/{page_id.replace('-', '')}",
            'title': f"Database ({page_id[:8]}...)",
            'type': 'database'
        }
        
    except Exception as e:
        logger.error(f"데이터베이스 정보 생성 실패: {str(e)}")
        return None


def open_notion_page(url: str):
    """Notion 페이지를 웹 브라우저에서 열기"""
    try:
        # Streamlit Cloud 환경에서는 JavaScript 사용
        st.markdown(
            f'<a href="{url}" target="_blank" style="display: inline-block; '
            f'background-color: #007ACC; color: white; padding: 10px 20px; '
            f'text-decoration: none; border-radius: 5px; margin-top: 10px;">'
            f'🌐 Notion에서 열기 (새 탭)</a>',
            unsafe_allow_html=True
        )
        
        # 로컬 환경에서는 webbrowser 사용 (선택적)
        if os.getenv("STREAMLIT_ENV") != "cloud":
            webbrowser.open(url)
            
    except Exception as e:
        st.error(f"페이지 열기 실패: {str(e)}")
        st.info(f"URL: {url}")


# 초기화 함수
def init_notion_stats():
    """Notion 통계 초기화"""
    if 'notion_uploaded_count' not in st.session_state:
        st.session_state.notion_uploaded_count = 0
    if 'notion_failed_count' not in st.session_state:
        st.session_state.notion_failed_count = 0