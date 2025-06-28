# src/ui/tabs/settings_notion.py

import streamlit as st
import os
from pathlib import Path
from typing import Optional, Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)


def render_notion_settings():
    """Notion 연동 설정 UI 렌더링"""
    st.header("🔗 Notion 연동 설정")
    
    # 현재 설정 상태 표시
    render_current_status()
    
    st.markdown("---")
    
    # API 설정 (읽기 전용)
    render_api_settings_readonly()
    
    st.markdown("---")
    
    # 연동 정보 및 바로가기
    render_connection_info()


def render_current_status():
    """현재 Notion 연동 상태 표시"""
    st.subheader("📊 현재 설정")
    
    # 환경변수 읽기
    api_key = os.getenv("NOTION_API_KEY", "")
    database_id = os.getenv("NOTION_DATABASE_ID", "")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if api_key:
            st.success("✅ API 키 설정됨")
        else:
            st.error("❌ API 키 미설정")
    
    with col2:
        if database_id:
            st.success("✅ Database 연결됨")
        else:
            st.error("❌ Database 미설정")
    
    with col3:
        # 연결 테스트
        if api_key and database_id:
            if st.button("🔌 연결 테스트", key="test_notion_connection", use_container_width=True):
                test_notion_connection()


def render_api_settings_readonly():
    """API 설정 표시 (읽기 전용)"""
    st.subheader("🔑 API 설정")
    
    current_api_key = os.getenv("NOTION_API_KEY", "")
    current_database_id = os.getenv("NOTION_DATABASE_ID", "")
    
    if current_api_key or current_database_id:
        # 설정이 있는 경우 - 읽기 전용으로 표시
        col1, col2 = st.columns(2)
        
        with col1:
            if current_api_key:
                # 마스킹된 키 표시
                masked_key = current_api_key[:10] + "*" * 20 + current_api_key[-5:]
                st.text_input(
                    "Notion API 키",
                    value=masked_key,
                    disabled=True,
                    help="API 키는 보안을 위해 마스킹되어 표시됩니다"
                )
            else:
                st.text_input(
                    "Notion API 키",
                    value="미설정",
                    disabled=True
                )
        
        with col2:
            if current_database_id:
                # Database ID 일부만 표시
                masked_db_id = current_database_id[:8] + "..." + current_database_id[-4:]
                st.text_input(
                    "Database ID",
                    value=masked_db_id,
                    disabled=True,
                    help="Database ID는 일부만 표시됩니다"
                )
            else:
                st.text_input(
                    "Database ID",
                    value="미설정",
                    disabled=True
                )
        
        # 변경 안내
        with st.expander("⚙️ API 설정 변경 방법", expanded=False):
            st.markdown("""
            ### API 설정을 변경하려면:
            
            1. **프로젝트 루트의 `.env` 파일을 열어주세요**
               ```
               NOTION_API_KEY=your_api_key_here
               NOTION_DATABASE_ID=your_database_id_here
               ```
            
            2. **값을 수정한 후 저장하세요**
            
            3. **Streamlit 앱을 재시작하세요**
               - 터미널에서 `Ctrl+C`로 중지
               - `streamlit run app.py` 다시 실행
            
            ⚠️ **주의사항**:
            - API 키는 절대 외부에 노출되지 않도록 주의하세요
            - `.env` 파일은 Git에 커밋하지 마세요
            - 변경은 시스템 관리자만 수행해야 합니다
            """)
            
    
    else:
        # 초기 설정이 필요한 경우
        render_initial_setup_guide()


def render_initial_setup_guide():
    """초기 설정 가이드"""
    st.info("📝 Notion API가 아직 설정되지 않았습니다.")
    
    with st.expander("🚀 초기 설정 가이드", expanded=True):
        st.markdown("""
        ### 1. Notion API 키 발급
        1. [Notion Integrations](https://www.notion.so/my-integrations) 페이지 방문
        2. "New integration" 클릭
        3. 이름 입력 후 생성
        4. "Internal Integration Token" 복사
        
        ### 2. Database 생성 및 ID 찾기
        1. Notion에서 새 Database 페이지 생성
        2. 우측 상단 "..." → "Copy link"
        3. URL에서 Database ID 추출:
           ```
           https://notion.so/workspace/1234567890abcdef...
                                      ^^^^^^^^^^^^^^^^^ (이 부분)
           ```
        
        ### 3. .env 파일 생성
        프로젝트 루트에 `.env` 파일을 생성하고 다음 내용 추가:
        ```
        NOTION_API_KEY=secret_xxxxxxxxxxxxx
        NOTION_DATABASE_ID=1234567890abcdef
        ```
        
        ### 4. Database 권한 설정
        1. Database 페이지에서 "Share" 클릭
        2. "Invite" → 생성한 Integration 선택
        3. "Full access" 권한 부여
        """)
        
        # .env 템플릿 다운로드
        if st.button("📥 .env 템플릿 다운로드"):
            env_template = """# Notion API 설정
NOTION_API_KEY=secret_your_api_key_here
NOTION_DATABASE_ID=your_database_id_here

# 기타 설정
OPENAI_API_KEY=your_openai_key_here
"""
            st.download_button(
                label="💾 .env 템플릿 저장",
                data=env_template,
                file_name=".env.template",
                mime="text/plain"
            )


def render_connection_info():
    """연동 정보 및 바로가기"""
    api_key = os.getenv("NOTION_API_KEY", "")
    database_id = os.getenv("NOTION_DATABASE_ID", "")
    
    if api_key and database_id:
        st.subheader("📄 연동 정보")
        
        # Database 정보 가져오기
        db_info = get_database_info()
        
        if db_info:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.info(f"📊 Database: **{db_info.get('title', 'Untitled')}**")
                
                # 프로퍼티 정보
                with st.expander("Database 프로퍼티", expanded=False):
                    properties = db_info.get('properties', {})
                    if properties:
                        for prop_name, prop_type in properties.items():
                            st.text(f"• {prop_name}: {prop_type}")
                    else:
                        st.text("프로퍼티 정보를 가져올 수 없습니다.")
            
            with col2:
                # Notion에서 열기 버튼
                if st.button("🌐 Notion에서 열기", key="open_notion_db", use_container_width=True):
                    db_url = f"https://www.notion.so/{database_id.replace('-', '')}"
                    st.markdown(f'<a href="{db_url}" target="_blank">Database 열기</a>', unsafe_allow_html=True)
                    st.info("위 링크를 클릭하세요")
                
        else:
            st.warning("Database 정보를 가져올 수 없습니다.")
    else:
        st.info("API 설정이 완료되면 연동 정보가 표시됩니다.")


def test_notion_connection():
    """Notion 연결 테스트"""
    with st.spinner("연결 테스트 중..."):
        try:
            from services.notion_service import NotionService
            
            notion = NotionService()
            if notion.test_connection():
                st.success("✅ Notion 연결 성공!")
                
                # Database 정보 표시
                db_info = get_database_info()
                if db_info:
                    st.info(f"연결된 Database: **{db_info.get('title', 'Untitled')}**")
                    
            else:
                st.error("❌ Notion 연결 실패! 설정을 확인해주세요.")
                
        except ValueError as e:
            st.error(f"❌ {str(e)}")
        except Exception as e:
            st.error(f"연결 테스트 중 오류: {str(e)}")


def get_database_info() -> Optional[Dict[str, Any]]:
    """Database 정보 가져오기"""
    try:
        from services.notion_service import NotionService
        
        notion = NotionService()
        
        # Database 정보 조회
        db_props = notion.get_database_properties()
        
        # Database 제목은 별도로 가져와야 함
        database_id = os.getenv("NOTION_DATABASE_ID", "")
        
        return {
            'id': database_id,
            'title': 'Video Analysis Database',  # 실제 제목 가져오기는 추가 구현 필요
            'properties': db_props
        }
        
    except Exception as e:
        logger.error(f"Database 정보 조회 실패: {str(e)}")
        return None


# 사용자가 실수로 설정을 변경하지 못하도록 추가 보호
def render_settings_protection_notice():
    """설정 보호 안내"""
    st.markdown("""
    <div style="background-color: #fef3c7; padding: 15px; border-radius: 10px; margin: 10px 0;">
        <p style="color: #92400e; margin: 0;">
            <strong>🔒 보안 안내</strong><br>
            API 설정은 시스템 보안을 위해 읽기 전용으로 표시됩니다.<br>
            설정 변경이 필요한 경우 시스템 관리자에게 문의하세요.
        </p>
    </div>
    """, unsafe_allow_html=True)


def init_notion_stats():
    """Notion 통계 초기화"""
    if 'notion_upload_count' not in st.session_state:
        st.session_state.notion_upload_count = 0
    
    if 'notion_failed_count' not in st.session_state:
        st.session_state.notion_failed_count = 0
    
    if 'notion_last_upload' not in st.session_state:
        st.session_state.notion_last_upload = None