# src/services/video_service.py
from dotenv import load_dotenv
load_dotenv()  # .env 파일 로드
import os
import re
from typing import Dict, Any, Optional, Tuple, List, Callable
from datetime import datetime
from pathlib import Path

from src.fetcher.youtube import YouTubeDownloader
from src.extractor.scene_extractor import SceneExtractor
from src.analyzer.ai_analyzer import AIAnalyzer
from src.storage.storage_manager import StorageManager, StorageType
from src.storage.db_manager import VideoAnalysisDB
from src.models.video import Video, VideoMetadata, Scene
from utils.logger import get_logger

logger = get_logger(__name__)


class VideoService:
    """영상 처리 및 분석을 위한 메인 서비스 클래스"""
    
    def __init__(self, storage_type: StorageType = StorageType.SFTP):
        """
        VideoService 초기화
        
        Args:
            storage_type: 사용할 스토리지 타입
        """
        self.downloader = YouTubeDownloader()
        self.scene_extractor = SceneExtractor()
        
        # AI 분석기 안전한 초기화
        self.ai_analyzer = None
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if openai_api_key and openai_api_key.strip():
            try:
                from src.analyzer.ai_analyzer import AIAnalyzer
                self.ai_analyzer = AIAnalyzer(api_key=openai_api_key)
                logger.info("✅ AI 분석기 초기화 성공")
            except Exception as e:
                logger.error(f"❌ AI 분석기 초기화 실패: {str(e)}")
                logger.error(f"❌ 오류 타입: {type(e).__name__}")
                import traceback
                logger.error(f"❌ 스택 트레이스:\n{traceback.format_exc()}")
                self.ai_analyzer = None
        else:
            logger.warning("⚠️ OpenAI API 키가 설정되지 않음")
        
        self.storage_manager = StorageManager(storage_type)
        self.db = VideoAnalysisDB()  # TinyDB 매니저 추가
        
        # Notion 서비스 초기화 (옵션)
        self.notion_service = None
        self.auto_upload_to_notion = os.getenv("AUTO_UPLOAD_TO_NOTION", "true").lower() == "true"
        
        if self.auto_upload_to_notion:
            try:
                from src.services.notion_service import NotionService
                self.notion_service = NotionService()
                logger.info("✅ Notion 서비스 초기화 성공 (자동 업로드 활성화)")
            except Exception as e:
                logger.warning(f"⚠️ Notion 서비스 초기화 실패: {str(e)}")
                logger.warning("⚠️ 자동 Notion 업로드가 비활성화됩니다.")
                self.notion_service = None
        
        logger.info(f"VideoService 초기화 완료 - Storage: {storage_type.value}, AI: {'활성화' if self.ai_analyzer else '비활성화'}, Notion: {'활성화' if self.notion_service else '비활성화'}")
    
    def _parse_video_url(self, url: str) -> Tuple[str, str]:
        """
        URL에서 플랫폼과 비디오 ID 추출
        
        Args:
            url: 비디오 URL
            
        Returns:
            (platform, video_id) 튜플
        """
        if 'youtube.com' in url or 'youtu.be' in url:
            # YouTube ID 추출
            patterns = [
                r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
                r'youtu\.be\/([0-9A-Za-z_-]{11})',
                r'youtube\.com\/embed\/([0-9A-Za-z_-]{11})',
                r'youtube\.com\/v\/([0-9A-Za-z_-]{11})'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return 'youtube', match.group(1)
                    
        elif 'vimeo.com' in url:
            # Vimeo ID 추출
            patterns = [
                r'vimeo\.com\/(\d+)',
                r'player\.vimeo\.com\/video\/(\d+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return 'vimeo', match.group(1)
        
        raise ValueError(f"지원하지 않는 비디오 URL 형식입니다: {url}")
    
    def process_video(self, url: str, force_reanalyze: bool = False, progress_callback: Optional[Callable] = None) -> Video:
        """
        영상 다운로드, 씬 추출, AI 분석 전체 프로세스 실행
        
        Args:
            url: 분석할 영상 URL
            force_reanalyze: 기존 분석 결과가 있어도 재분석 여부
            progress_callback: 진행 상황 업데이트 콜백 함수
                              callback(step: str, progress: int, message: str)
            
        Returns:
            처리 완료된 Video 객체
        """
        try:
            # 진행 상황 업데이트 함수
            def update_progress(step: str, progress: int, message: str):
                if progress_callback:
                    progress_callback(step, progress, message)
                logger.info(message)
            
            # 1. URL 파싱
            update_progress("parsing", 5, "🔍 영상 URL 분석 중...")
            platform, video_id = self._parse_video_url(url)
            update_progress("parsing", 10, f"✅ 플랫폼 확인: {platform} - {video_id}")
            
            # 2. 기존 분석 결과 확인
            if not force_reanalyze:
                update_progress("checking", 12, "📊 기존 분석 결과 확인 중...")
                existing_analysis = self.db.get_latest_analysis(video_id)
                if existing_analysis:
                    update_progress("checking", 15, f"✅ 기존 분석 결과 발견: {video_id}")
                    # 기존 결과를 Video 객체로 변환
                    video = self._create_video_from_db(video_id, existing_analysis)
                    if video:
                        update_progress("complete", 100, "✅ 기존 분석 결과를 불러왔습니다")
                        return video
            
            # 3. 영상 다운로드
            update_progress("download", 20, "📥 영상 정보 가져오는 중...")
            
            # 다운로드 진행 상황을 추적하기 위한 래퍼
            original_download = self.downloader.download
            
            def download_with_progress(url):
                update_progress("download", 25, "📥 영상 다운로드 시작...")
                result = original_download(url)
                update_progress("download", 35, f"✅ 다운로드 완료: {result.get('title', 'Unknown')}")
                return result
            
            self.downloader.download = download_with_progress
            download_result = self.downloader.download(url)
            self.downloader.download = original_download  # 원래 함수로 복원
            
            # 4. Video 객체 생성
            update_progress("metadata", 40, "📋 메타데이터 처리 중...")
            
            # 디버깅: 다운로드 결과 확인
            logger.debug(f"다운로드 결과 키: {list(download_result.keys())}")
            logger.debug(f"업로더: {download_result.get('uploader', 'MISSING')}")
            logger.debug(f"썸네일: {download_result.get('thumbnail', 'MISSING')}")
            logger.debug(f"webpage_url: {download_result.get('webpage_url', 'MISSING')}")
            
            video = Video(
                session_id=video_id,
                url=url,
                local_path=download_result['filepath'],
                metadata=VideoMetadata(
                    title=download_result.get('title', ''),
                    duration=download_result.get('duration', 0),
                    uploader=download_result.get('uploader', ''),
                    upload_date=download_result.get('upload_date', ''),
                    description=download_result.get('description', ''),
                    view_count=download_result.get('view_count', 0),
                    like_count=download_result.get('like_count', 0),
                    video_id=video_id,
                    url=url,
                    ext=download_result.get('ext', 'mp4'),
                    thumbnail=download_result.get('thumbnail', ''),
                    webpage_url=download_result.get('webpage_url', url),
                    tags=download_result.get('tags', []),
                    categories=download_result.get('categories', []),
                    language=download_result.get('language', ''),
                    channel_id=download_result.get('channel_id', ''),
                    comment_count=download_result.get('comment_count', 0),
                    age_limit=download_result.get('age_limit', 0),
                    subtitle_files=download_result.get('subtitle_files', {}),
                    platform=platform  # 플랫폼 추가
                )
            )
            
            # session_dir 속성 추가
            video.session_dir = os.path.dirname(download_result['filepath'])
            
            # 5. DB에 영상 정보 저장
            update_progress("database", 45, "💾 데이터베이스에 정보 저장 중...")

            # 확장된 메타데이터를 모두 포함하여 저장
            video_data = {
                'video_id': video_id,
                'url': url,
                'title': video.metadata.title,
                'duration': video.metadata.duration,
                'platform': platform,
                'download_date': datetime.now().isoformat(),
                
                # 확장된 메타데이터 추가
                'uploader': video.metadata.uploader,
                'channel': video.metadata.uploader,  # 호환성을 위해 중복 저장
                'description': video.metadata.description,
                'view_count': video.metadata.view_count,
                'like_count': video.metadata.like_count,
                'comment_count': video.metadata.comment_count,
                'tags': video.metadata.tags,
                'channel_id': video.metadata.channel_id,
                'categories': video.metadata.categories,
                'language': video.metadata.language,
                'upload_date': video.metadata.upload_date,
                'age_limit': video.metadata.age_limit,
                'thumbnail': video.metadata.thumbnail,
                'webpage_url': video.metadata.webpage_url,
            }

            self.db.save_video_info(video_data)
            
            # 6. 씬 추출
            update_progress("extract", 50, "🎬 주요 씬 추출 시작...")
            scenes_result = self.scene_extractor.extract_scenes(
                video.local_path, 
                video.session_id
            )
            
            # Scene 객체로 변환
            video.scenes = []
            
            # scenes_result 처리
            if isinstance(scenes_result, dict):
                if 'scenes' in scenes_result:
                    scenes_list = scenes_result['scenes']
                elif 'selected_images' in scenes_result:
                    scenes_list = scenes_result['selected_images']
                else:
                    scenes_list = []
            elif isinstance(scenes_result, list):
                scenes_list = scenes_result
            else:
                scenes_list = []
            
            # 씬 데이터 처리
            scene_count = len(scenes_list)
            for i, scene_data in enumerate(scenes_list):
                progress = 50 + int((i / scene_count) * 10) if scene_count > 0 else 60
                update_progress("extract", progress, f"🎬 씬 처리 중... ({i+1}/{scene_count})")
                
                if isinstance(scene_data, Scene):
                    video.scenes.append(scene_data)
                elif isinstance(scene_data, dict):
                    scene = Scene(
                        timestamp=scene_data.get('timestamp', 0.0),
                        frame_path=scene_data.get('frame_path', '') or scene_data.get('path', ''),
                        scene_type=scene_data.get('type', 'mid')
                    )
                    video.scenes.append(scene)
                elif isinstance(scene_data, str):
                    scene = Scene(
                        timestamp=0.0,
                        frame_path=scene_data,
                        scene_type='mid'
                    )
                    video.scenes.append(scene)
            
            update_progress("extract", 60, f"✅ {len(video.scenes)}개 씬 추출 완료")
            
            # 7. AI 분석
            if self.ai_analyzer and video.scenes:
                try:
                    update_progress("analyze", 65, "🤖 AI 영상 분석 시작...")
                    update_progress("analyze", 70, "🤖 이미지 준비 중...")
                    
                    # AI 분석 실행
                    analysis_result = self.ai_analyzer.analyze_video(video)
                    
                    if analysis_result:
                        update_progress("analyze", 75, f"✅ AI 분석 성공: {getattr(analysis_result, 'genre', 'Unknown')}")
                        
                        # 분석 결과 저장
                        video.analysis_result = {
                            'genre': getattr(analysis_result, 'genre', ''),
                            'reasoning': getattr(analysis_result, 'reason', ''),
                            'features': getattr(analysis_result, 'features', ''),
                            'tags': getattr(analysis_result, 'tags', []),
                            'expression_style': getattr(analysis_result, 'format_type', ''),
                            'mood_tone': getattr(analysis_result, 'mood', ''),
                            'target_audience': getattr(analysis_result, 'target_audience', ''),
                            'model_used': os.getenv('OPENAI_MODEL', 'gpt-4o')
                        }
                        
                        # DB에 저장
                        update_progress("analyze", 78, "💾 분석 결과 저장 중...")
                        analysis_data = {
                            'genre': getattr(analysis_result, 'genre', ''),
                            'reasoning': getattr(analysis_result, 'reason', ''),
                            'features': getattr(analysis_result, 'features', ''),
                            'tags': getattr(analysis_result, 'tags', []),
                            'expression_style': getattr(analysis_result, 'format_type', ''),
                            'mood_tone': getattr(analysis_result, 'mood', ''),
                            'target_audience': getattr(analysis_result, 'target_audience', ''),
                            'analyzed_scenes': [os.path.basename(scene.frame_path) for scene in video.scenes[:getattr(self.ai_analyzer, 'max_images', 10)]],
                            'token_usage': {},
                            'model_used': os.getenv('OPENAI_MODEL', 'gpt-4o')
                        }
                        self.db.save_analysis_result(video_id, analysis_data)
                        update_progress("analyze", 80, "✅ AI 분석 완료")
                    else:
                        update_progress("analyze", 80, "⚠️ AI 분석 결과가 없습니다")
                        
                except Exception as e:
                    update_progress("analyze", 80, f"⚠️ AI 분석 중 오류: {str(e)}")
                    logger.error(f"AI 분석 오류: {e}")
            else:
                if not self.ai_analyzer:
                    update_progress("analyze", 80, "ℹ️ AI 분석기가 비활성화되어 있습니다")
                else:
                    update_progress("analyze", 80, "ℹ️ 추출된 씬이 없어 AI 분석을 건너뜁니다")
            
            # 8. 스토리지 업로드
            if self.storage_manager.storage_type != StorageType.LOCAL:
                update_progress("upload", 85, "📤 스토리지 업로드 시작...")
                
                # 파일 수 계산
                file_count = 1  # 비디오 파일
                file_count += len(video.scenes)  # 씬 이미지들
                if video.analysis_result:
                    file_count += 1  # 분석 결과 JSON
                
                uploaded = 0
                
                # 업로드 진행 상황을 추적하는 래퍼
                original_upload = self.storage_manager.upload_file
                
                def upload_with_progress(local_path, remote_path):
                    nonlocal uploaded
                    filename = os.path.basename(local_path)
                    update_progress("upload", 85 + int((uploaded / file_count) * 10), f"📤 업로드 중: {filename}")
                    result = original_upload(local_path, remote_path)
                    uploaded += 1
                    return result
                
                self.storage_manager.upload_file = upload_with_progress
                self._upload_to_storage(video)
                self.storage_manager.upload_file = original_upload  # 원래 함수로 복원
                
                update_progress("upload", 95, "✅ 스토리지 업로드 완료")
            else:
                update_progress("upload", 95, "ℹ️ 로컬 스토리지 사용 중")
            
            # 9. Notion 자동 업로드 (AI 분석이 완료된 경우만)
            if self.notion_service and self.auto_upload_to_notion and video.analysis_result:
                try:
                    update_progress("notion", 96, "📝 Notion 데이터베이스에 업로드 중...")
                    
                    # Video 객체에서 직접 데이터 생성 (DB를 거치지 않음!)
                    video_data_for_notion = {
                        'video_id': video.metadata.video_id,
                        'title': video.metadata.title,
                        'url': video.metadata.url,
                        'webpage_url': video.metadata.webpage_url,
                        'thumbnail': video.metadata.thumbnail,  # 이것이 핵심!
                        'platform': video.metadata.platform,
                        'duration': video.metadata.duration,
                        'uploader': video.metadata.uploader,
                        'channel': video.metadata.uploader,
                        'channel_id': video.metadata.channel_id,
                        'upload_date': video.metadata.upload_date,
                        'description': video.metadata.description,
                        'view_count': video.metadata.view_count,
                        'like_count': video.metadata.like_count,
                        'comment_count': video.metadata.comment_count,
                        'tags': video.metadata.tags,
                        'categories': video.metadata.categories,
                        'language': video.metadata.language,
                        'age_limit': video.metadata.age_limit,
                    }
                    
                    # 디버깅
                    logger.info(f"🔍 Notion으로 보낼 데이터:")
                    logger.info(f"  - platform: {video_data_for_notion['platform']}")
                    logger.info(f"  - thumbnail: {video_data_for_notion['thumbnail']}")
                    logger.info(f"  - webpage_url: {video_data_for_notion['webpage_url']}")
                    
                    # 직접 호출 (DB를 거치지 않고!)
                    success, result = self.notion_service.add_video_to_database(
                        video_data=video_data_for_notion,
                        analysis_data=video.analysis_result
                    )
                    
                    if success:
                        update_progress("notion", 98, "✅ Notion 업로드 성공!")
                        logger.info(f"Notion 페이지 ID: {result}")
                        logger.info(f"Notion 데이터베이스 URL: {self.notion_service.get_database_url()}")
                    else:
                        update_progress("notion", 98, f"⚠️ Notion 업로드 실패: {result}")
                        logger.warning(f"Notion 업로드 실패: {result}")
                    
                except Exception as e:
                    logger.error(f"Notion 업로드 중 오류: {str(e)}")
                    import traceback
                    logger.error(f"스택 트레이스:\n{traceback.format_exc()}")
                    update_progress("notion", 98, f"⚠️ Notion 업로드 오류: {str(e)}")
            
            # 10. 임시 파일 정리
            if os.getenv("CLEANUP_TEMP_FILES", "false").lower() == "true":
                update_progress("cleanup", 99, "🗑️ 임시 파일 정리 중...")
                self._cleanup_temp_files(video)
            
            update_progress("complete", 100, f"✅ 영상 처리 완료: {video_id}")
            return video
            
        except Exception as e:
            if progress_callback:
                progress_callback("error", 0, f"❌ 오류 발생: {str(e)}")
            logger.error(f"영상 처리 중 오류 발생: {str(e)}")
            raise
    
    def _create_video_from_db(self, video_id: str, analysis_data: Dict[str, Any]) -> Optional[Video]:
        """
        DB 데이터로부터 Video 객체 생성
        
        Args:
            video_id: 비디오 ID
            analysis_data: DB에서 가져온 분석 데이터
            
        Returns:
            Video 객체 또는 None
        """
        try:
            # 영상 정보 조회
            video_info = self.db.get_video_info(video_id)
            if not video_info:
                return None
            
            # Video 객체 생성
            video = Video(
                session_id=video_id,
                url=video_info['url'],
                local_path=None,
                metadata=VideoMetadata(
                    title=video_info.get('title', ''),
                    duration=video_info.get('duration', 0),
                    uploader=video_info.get('uploader', ''),
                    upload_date=video_info.get('upload_date', ''),
                    description=video_info.get('description', ''),
                    view_count=video_info.get('view_count', 0),
                    like_count=video_info.get('like_count', 0),
                    video_id=video_id,
                    url=video_info['url'],
                    ext='mp4',
                    thumbnail=video_info.get('thumbnail', ''),
                    webpage_url=video_info.get('webpage_url', video_info['url']),
                    tags=video_info.get('tags', []),
                    channel_id=video_info.get('channel_id', ''),
                    categories=video_info.get('categories', []),
                    language=video_info.get('language', ''),
                    comment_count=video_info.get('comment_count', 0),
                    age_limit=video_info.get('age_limit', 0),
                    platform=video_info.get('platform', 'youtube')
                )
            )
            
            # 분석 결과 매핑
            video.analysis_result = {
                'genre': analysis_data.get('genre', ''),
                'reasoning': analysis_data.get('reasoning', ''),
                'features': analysis_data.get('features', ''),
                'tags': analysis_data.get('tags', []),
                'expression_style': analysis_data.get('expression_style', ''),
                'mood_tone': analysis_data.get('mood_tone', ''),
                'target_audience': analysis_data.get('target_audience', ''),
                'analyzed_at': analysis_data.get('analysis_date', '')
            }
            
            return video
            
        except Exception as e:
            logger.error(f"DB에서 Video 객체 생성 실패: {str(e)}")
            return None
    
    def _upload_to_storage(self, video: Video) -> None:
        """
        영상 및 씬 이미지를 스토리지에 업로드
        
        Args:
            video: 업로드할 Video 객체
        """
        try:
            # 업로드할 파일 목록 생성
            files_to_upload = []
            
            # 비디오 파일
            if video.local_path and os.path.exists(video.local_path):
                files_to_upload.append(video.local_path)
            
            # 씬 이미지들
            for scene in video.scenes:
                if scene.frame_path and os.path.exists(scene.frame_path):
                    files_to_upload.append(scene.frame_path)
            
            # 분석 결과 JSON
            if video.analysis_result:
                analysis_path = f"data/temp/{video.session_id}/analysis_result.json"
                os.makedirs(os.path.dirname(analysis_path), exist_ok=True)
                
                import json
                with open(analysis_path, 'w', encoding='utf-8') as f:
                    json.dump(video.analysis_result, f, ensure_ascii=False, indent=2)
                files_to_upload.append(analysis_path)
            
            # 스토리지에 업로드
            remote_base_path = f"video_analysis/{video.session_id}"
            
            for file_path in files_to_upload:
                filename = os.path.basename(file_path)
                safe_filename = filename.replace('*', '_').replace('/', '_')
                remote_path = f"{remote_base_path}/{safe_filename}"
                
                success = self.storage_manager.upload_file(file_path, remote_path)
                if success:
                    logger.info(f"업로드 완료: {filename} -> {remote_path}")
                else:
                    logger.warning(f"업로드 실패: {filename}")
                    
        except Exception as e:
            logger.error(f"스토리지 업로드 중 오류: {str(e)}")
    
    def _cleanup_temp_files(self, video: Video) -> None:
        """
        임시 파일 정리
        
        Args:
            video: 정리할 Video 객체
        """
        try:
            import shutil
            temp_dir = f"data/temp/{video.session_id}"
            
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                logger.info(f"임시 파일 정리 완료: {temp_dir}")
                
        except Exception as e:
            logger.error(f"임시 파일 정리 실패: {str(e)}")
    
    def test_storage_connection(self) -> bool:
        """
        스토리지 연결 테스트
        
        Returns:
            연결 성공 여부
        """
        return self.storage_manager.test_connection()
    
    def get_analysis_history(self, video_id: str) -> List[Dict[str, Any]]:
        """
        특정 영상의 분석 히스토리 조회
        
        Args:
            video_id: 비디오 ID
            
        Returns:
            분석 결과 리스트
        """
        return self.db.get_all_analyses(video_id)
    
    def search_by_genre(self, genre: str) -> List[Dict[str, Any]]:
        """
        장르로 영상 검색
        
        Args:
            genre: 검색할 장르
            
        Returns:
            검색 결과 리스트
        """
        return self.db.search_by_genre(genre)
    
    def search_by_tags(self, tags: List[str]) -> List[Dict[str, Any]]:
        """
        태그로 영상 검색
        
        Args:
            tags: 검색할 태그 리스트
            
        Returns:
            검색 결과 리스트
        """
        return self.db.search_by_tags(tags)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        전체 통계 정보 조회
        
        Returns:
            통계 정보 딕셔너리
        """
        return self.db.get_statistics()
    
    def __del__(self):
        """소멸자: DB 연결 종료"""
        if hasattr(self, 'db'):
            self.db.close()