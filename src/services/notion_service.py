# src/services/notion_service.py
"""
Notion API 통합 서비스
데이터베이스와 페이지 기능을 통합하여 제공
"""

from typing import Dict, Any, List, Optional, Tuple
import time
import traceback
from .notion_database import NotionDatabaseService
from .notion_page import NotionPageService
from utils.logger import get_logger

logger = get_logger(__name__)


class NotionService:
    """Notion 통합 서비스"""
    
    def __init__(self):
        """서비스 초기화"""
        self.db_service = NotionDatabaseService()
        self.page_service = NotionPageService()
        logger.info("Notion 통합 서비스 초기화 완료")
    
    def add_video_to_database(self, video_data: Dict[str, Any], analysis_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Notion 데이터베이스에 비디오 추가 또는 업데이트"""
        try:
            video_id = video_data.get('video_id')
            if not video_id:
                return False, "video_id가 없습니다"
            
            # 기존 페이지 검색
            existing_page = self._find_existing_page(video_id)
            
            if existing_page:
                # 기존 페이지가 있으면 업데이트
                self.logger.info(f"기존 페이지 발견: {existing_page['id']}")
                return self._update_existing_page(existing_page['id'], video_data, analysis_data)
            else:
                # 새 페이지 생성
                return self._create_new_page(video_data, analysis_data)
                
        except Exception as e:
            error_msg = f"Notion 업로드 실패: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def add_video_to_database(self, video_data: Dict[str, Any], analysis_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Notion 데이터베이스에 비디오 추가 또는 업데이트"""
        try:
            video_id = video_data.get('video_id')
            if not video_id:
                return False, "video_id가 없습니다"
            
            # 기존 페이지 검색
            existing_page = self._find_existing_page(video_id)
            
            if existing_page:
                # 기존 페이지가 있으면 업데이트
                self.logger.info(f"기존 페이지 발견: {existing_page['id']}")
                return self._update_existing_page(existing_page['id'], video_data, analysis_data)
            else:
                # 새 페이지 생성
                return self._create_new_page(video_data, analysis_data)
                
        except Exception as e:
            error_msg = f"Notion 업로드 실패: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg



    def _update_existing_page(self, page_id: str, video_data: Dict[str, Any], analysis_data: Dict[str, Any]) -> Tuple[bool, str]:
        """기존 페이지 업데이트"""
        try:
            # 프로퍼티 생성 (새 페이지와 동일)
            properties = self._create_properties(video_data, analysis_data)
            
            # 페이지 업데이트
            response = self.notion.pages.update(
                page_id=page_id,
                properties=properties
            )
            
            self.logger.info(f"✅ Notion 페이지 업데이트 성공: {page_id}")
            return True, page_id
            
        except Exception as e:
            error_msg = f"페이지 업데이트 실패: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def _create_new_page(self, video_data: Dict[str, Any], analysis_data: Dict[str, Any]) -> Tuple[bool, str]:
        """새 페이지 생성"""
        try:
            properties = self._create_properties(video_data, analysis_data)
            
            # 페이지 생성
            response = self.notion.pages.create(
                parent={"database_id": self.database_id},
                properties=properties
            )
            
            page_id = response.get('id', '')
            self.logger.info(f"✅ Notion 페이지 생성 성공: {page_id}")
            return True, page_id
            
        except Exception as e:
            error_msg = f"페이지 생성 실패: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg


    def _create_properties(self, video_data: Dict[str, Any], analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Notion 프로퍼티 생성 (공통 로직)"""
        
        # 디버깅: 받은 데이터 확인
        self.logger.debug(f"video_data keys: {list(video_data.keys())}")
        self.logger.debug(f"analysis_data keys: {list(analysis_data.keys())}")
        
        # 날짜 포맷 처리
        analyzed_at = analysis_data.get('analysis_date', datetime.now().isoformat())
        if isinstance(analyzed_at, str) and len(analyzed_at) >= 10:
            analyzed_date = analyzed_at[:10]  # YYYY-MM-DD 형식만 추출
        else:
            analyzed_date = datetime.now().strftime('%Y-%m-%d')
        
        # 프로퍼티 생성
        properties = {
            "특징": {
                "title": [{
                    "text": {
                        "content": video_data.get('title', 'Untitled')[:100]
                    }
                }]
            },
            "영상 ID": {
                "rich_text": [{
                    "text": {
                        "content": video_data.get('video_id', '')
                    }
                }]
            },
            "URL": {
                "url": video_data.get('url', '')
            },
            "길이(초)": {
                "number": video_data.get('duration', 0)
            },
            "플랫폼": {
                "select": {
                    "name": self._get_platform_name(video_data)
                }
            },
            "태그 고객층": {
                "multi_select": [
                    {"name": tag[:25]} for tag in analysis_data.get('tags', [])[:10]
                ]
            },
            "분위기": {
                "rich_text": [{
                    "text": {
                        "content": self._safe_get_text(analysis_data.get('mood_tone', ''), 500)
                    }
                }]
            },
            "장르": {
                "select": {
                    "name": analysis_data.get('genre', 'Unknown')[:25]
                }
            },
            "태그": {
                "rich_text": [{
                    "text": {
                        "content": ', '.join(analysis_data.get('tags', []))[:2000]
                    }
                }]
            },
            "판단 이유": {
                "rich_text": [{
                    "text": {
                        "content": self._safe_get_text(analysis_data.get('reasoning', ''), 2000)
                    }
                }]
            },
            "남부탁": {
                "rich_text": [{
                    "text": {
                        "content": self._safe_get_text(analysis_data.get('features', ''), 2000)
                    }
                }]
            },
            "씬넬일": {
                "rich_text": [{
                    "text": {
                        "content": analysis_data.get('expression_style', '')[:100]
                    }
                }]
            },
            "카테고리": {
                "multi_select": [
                    {"name": cat[:25]} for cat in video_data.get('categories', [])[:5]
                ]
            },
            "제목": {
                "rich_text": [{
                    "text": {
                        "content": video_data.get('title', '')[:500]
                    }
                }]
            },
            "채널": {
                "rich_text": [{
                    "text": {
                        "content": video_data.get('channel', video_data.get('uploader', ''))[:100]
                    }
                }]
            },
            "미디어": {
                "files": self._prepare_media_files(video_data)
            },
            "AI 분석 완료": {
                "checkbox": True
            },
            "요약 정리 완료": {
                "checkbox": False
            },
            "언어": {
                "select": {
                    "name": self._get_language_name(video_data.get('language', ''))
                }
            },
            "조회수": {
                "number": video_data.get('view_count', 0) or 0
            },
            "좋아요": {
                "number": video_data.get('like_count', 0) or 0
            },
            "댓글수": {
                "number": video_data.get('comment_count', 0) or 0
            },
            "분석일": {
                "date": {
                    "start": analyzed_date
                }
            }
        }
        
        # None 값 필터링
        return {k: v for k, v in properties.items() if v is not None}

            

    def bulk_add_to_database(self, 
                            videos_with_analysis: List[Tuple[Dict, Dict]], 
                            progress_callback=None) -> Tuple[int, int, List[str]]:
        """
        여러 영상을 데이터베이스에 일괄 추가
        
        Args:
            videos_with_analysis: [(video_data, analysis_data), ...] 리스트
            progress_callback: 진행상황 콜백 함수
            
        Returns:
            (성공 개수, 실패 개수, 오류 메시지 리스트)
        """
        success_count = 0
        fail_count = 0
        errors = []
        
        total = len(videos_with_analysis)
        
        for i, (video_data, analysis_data) in enumerate(videos_with_analysis):
            video_id = video_data.get('video_id', 'Unknown')
            
            # 진행상황 업데이트
            if progress_callback:
                progress_callback(
                    current=i + 1,
                    total=total,
                    message=f"업로드 중... ({i+1}/{total}) - {video_id}"
                )
            
            try:
                success, result = self.add_video_to_database(video_data, analysis_data)
                
                if success:
                    success_count += 1
                    logger.info(f"✅ Notion 추가 성공: {video_id}")
                else:
                    fail_count += 1
                    errors.append(f"{video_id}: {result}")
                
                # API 제한 방지를 위한 대기
                time.sleep(0.3)
                
            except Exception as e:
                fail_count += 1
                error_msg = f"{video_id}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"추가 실패 - {error_msg}")
        
        return success_count, fail_count, errors
    

    # src/services/notion_service.py에 추가할 메서드들

    def find_video_blocks(self, video_id: str) -> List[str]:
        """
        특정 비디오 ID를 포함하는 데이터베이스 항목 찾기
        
        Args:
            video_id: 찾을 비디오 ID
            
        Returns:
            페이지 ID 리스트
        """
        try:
            # 데이터베이스에서 video_id로 검색
            response = self.db_service.client.databases.query(
                database_id=self.db_service.database_id,
                filter={
                    "property": "영상 ID",
                    "rich_text": {
                        "equals": video_id
                    }
                }
            )
            
            # 페이지 ID들 추출
            page_ids = [page['id'] for page in response.get('results', [])]
            
            logger.info(f"🔍 Notion에서 {len(page_ids)}개 페이지 발견: {video_id}")
            return page_ids
            
        except Exception as e:
            logger.error(f"Notion 검색 오류: {str(e)}")
            return []

    def delete_block(self, block_id: str) -> bool:
        """
        Notion 페이지(블록) 삭제
        
        Args:
            block_id: 삭제할 블록 ID
            
        Returns:
            성공 여부
        """
        try:
            # 페이지 아카이브 (Notion API는 실제 삭제 대신 아카이브를 사용)
            self.db_service.client.pages.update(
                page_id=block_id,
                archived=True
            )
            
            logger.info(f"✅ Notion 페이지 아카이브 완료: {block_id}")
            return True
            
        except Exception as e:
            logger.error(f"Notion 페이지 삭제 오류: {str(e)}")
            return False

    def delete_video_from_notion(self, video_id: str) -> Tuple[bool, str]:
        """
        비디오를 Notion에서 완전히 삭제
        
        Args:
            video_id: 삭제할 비디오 ID
            
        Returns:
            (성공 여부, 메시지)
        """
        try:
            # 1. 해당 비디오의 모든 페이지 찾기
            page_ids = self.find_video_blocks(video_id)
            
            if not page_ids:
                return True, "Notion에 해당 영상이 없음"
            
            # 2. 각 페이지 삭제(아카이브)
            deleted_count = 0
            failed_count = 0
            
            for page_id in page_ids:
                if self.delete_block(page_id):
                    deleted_count += 1
                else:
                    failed_count += 1
            
            # 3. 결과 반환
            if failed_count == 0:
                return True, f"{deleted_count}삭제 완료"
            elif deleted_count > 0:
                return False, f"{deleted_count}개 삭제, {failed_count}개 실패"
            else:
                return False, f"삭제 실패 ({failed_count}개)"
                
        except Exception as e:
            error_msg = f"Notion 삭제 중 오류: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def bulk_delete_from_notion(self, video_ids: List[str]) -> Tuple[int, int, List[str]]:
        """
        여러 비디오를 Notion에서 일괄 삭제
        
        Args:
            video_ids: 삭제할 비디오 ID 리스트
            
        Returns:
            (성공 개수, 실패 개수, 오류 메시지 리스트)
        """
        success_count = 0
        fail_count = 0
        errors = []
        
        for video_id in video_ids:
            try:
                success, message = self.delete_video_from_notion(video_id)
                
                if success:
                    success_count += 1
                else:
                    fail_count += 1
                    errors.append(f"{video_id}: {message}")
                    
                # API 제한 방지
                time.sleep(0.2)
                
            except Exception as e:
                fail_count += 1
                errors.append(f"{video_id}: {str(e)}")
        
        return success_count, fail_count, errors


    # 데이터베이스 서비스 메서드들을 직접 노출
    def search_videos(self, **kwargs):
        """영상 검색"""
        return self.db_service.search_videos(**kwargs)
    
    def test_connection(self):
        """연결 테스트"""
        return self.db_service.test_connection()
    
    def get_database_url(self):
        """데이터베이스 URL 반환"""
        return self.db_service.get_database_url()
    
    def get_database_properties(self):
        """데이터베이스 프로퍼티 조회"""
        return self.db_service.get_database_properties()
    
    def update_database_schema(self):
        """데이터베이스 스키마 업데이트"""
        return self.db_service.update_database_schema()



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
                st.success(f"✅ 페이지 ID: {page_id[:8]}...")
            else:
                st.warning("⚠️ 페이지 ID 미설정")
        
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
            
            # 페이지 ID 입력
            st.markdown("**부모 페이지 ID**")
            st.caption("영상 분석 결과를 추가할 Notion 페이지의 ID를 입력하세요.")
            
            page_id = st.text_input(
                "페이지 ID",
                value=current_page_id,
                placeholder="32자리 페이지 ID (예: a1b2c3d4e5f6...)",
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
                
                ### 2. 페이지 ID 찾기
                1. Notion에서 원하는 페이지 열기
                2. 우측 상단 "..." 메뉴 → "Copy link"
                3. URL에서 페이지 ID 추출:
                   - `https://notion.so/Page-Name-{페이지ID}`
                   - 하이픈(-) 제거한 32자리 문자열
                
                ### 3. 페이지 권한 설정
                1. 페이지 우측 상단 "Share" 클릭
                2. "Invite" → Integration 선택
                3. 생성한 Integration 추가
                """)
            
            # 저장 버튼
            col1, col2 = st.columns([3, 1])
            with col2:
                save_button = st.form_submit_button("💾 저장", type="primary", use_container_width=True)
            
            if save_button:
                save_notion_settings(api_key, page_id)


    def render_page_shortcuts():
        """Notion 페이지 바로가기"""
        st.subheader("📄 페이지 바로가기")
        
        page_id = os.getenv("NOTION_PARENT_PAGE_ID", "")
        
        if page_id:
            # 페이지 정보 가져오기
            page_info = get_notion_page_info(page_id)
            
            if page_info:
                st.info(f"📄 페이지: {page_info.get('title', 'Untitled')}")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("🌐 Notion에서 열기", key="open_notion_page", use_container_width=True):
                        open_notion_page(page_info.get('url'))
                
                with col2:
                    if st.button("🔄 페이지 정보 새로고침", key="refresh_page_info", use_container_width=True):
                        st.rerun()
                
                with col3:
                    if st.button("📋 URL 복사", key="copy_notion_url", use_container_width=True):
                        st.code(page_info.get('url', ''), language=None)
                        st.success("URL이 표시되었습니다. 복사해서 사용하세요.")
            else:
                st.warning("페이지 정보를 가져올 수 없습니다. API 키와 페이지 ID를 확인해주세요.")
        else:
            st.info("페이지 ID를 설정하면 바로가기 기능을 사용할 수 있습니다.")
        
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
                    
                    # 페이지 정보 가져오기
                    page_id = os.getenv("NOTION_PARENT_PAGE_ID", "")
                    if page_id:
                        page_info = get_notion_page_info(page_id)
                        if page_info:
                            st.info(f"📄 연결된 페이지: {page_info.get('title', 'Untitled')}")
                        else:
                            st.warning("페이지 정보를 가져올 수 없습니다. 페이지 ID와 권한을 확인해주세요.")
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
        """Notion 페이지 정보 가져오기"""
        try:
            from services.notion_service import NotionService
            
            notion = NotionService()
            
            # NotionService에 get_page_info가 없으므로 직접 구현
            try:
                page = notion.client.pages.retrieve(page_id)
                
                # 페이지 제목 추출
                title = "Untitled"
                if 'properties' in page:
                    for prop in page['properties'].values():
                        if prop['type'] == 'title' and prop.get('title'):
                            if len(prop['title']) > 0 and 'plain_text' in prop['title'][0]:
                                title = prop['title'][0]['plain_text']
                                break
                
                return {
                    'id': page['id'],
                    'url': page.get('url', f"https://www.notion.so/{page_id}"),
                    'title': title
                }
                
            except Exception as e:
                logger.error(f"페이지 정보 가져오기 실패: {str(e)}")
                return None
            
        except Exception as e:
            logger.error(f"NotionService 초기화 실패: {str(e)}")
            return None

    def get_page_info(self, page_id: str) -> Optional[Dict[str, Any]]:
        """페이지 정보 가져오기"""
        try:
            page = self.client.pages.retrieve(page_id)
            return {
                'id': page['id'],
                'url': page['url'],
                'title': self._extract_page_title(page)
            }
        except Exception as e:
            logger.error(f"페이지 정보 가져오기 실패: {str(e)}")
            return None
