# src/services/video_service.py
from dotenv import load_dotenv
load_dotenv()  # .env 파일 로드
import os
import re
from typing import Dict, Any, Optional, Tuple, List
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
        
        logger.info(f"VideoService 초기화 완료 - Storage: {storage_type.value}, AI: {'활성화' if self.ai_analyzer else '비활성화'}")
    
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
    
    def process_video(self, url: str, force_reanalyze: bool = False) -> Video:
        """
        영상 다운로드, 씬 추출, AI 분석 전체 프로세스 실행
        
        Args:
            url: 분석할 영상 URL
            force_reanalyze: 기존 분석 결과가 있어도 재분석 여부
            
        Returns:
            처리 완료된 Video 객체
        """
        try:
            # 1. URL 파싱
            platform, video_id = self._parse_video_url(url)
            logger.info(f"영상 처리 시작: {platform} - {video_id}")
            
            # 2. 기존 분석 결과 확인
            if not force_reanalyze:
                existing_analysis = self.db.get_latest_analysis(video_id)
                if existing_analysis:
                    logger.info(f"기존 분석 결과 발견: {video_id}")
                    # 기존 결과를 Video 객체로 변환
                    video = self._create_video_from_db(video_id, existing_analysis)
                    if video:
                        return video
            
            # 3. 영상 다운로드
            logger.info(f"영상 다운로드 시작: {url}")
            download_result = self.downloader.download(url)
            
            # 4. Video 객체 생성
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
                    ext=download_result.get('ext', 'mp4'),
                    thumbnail=download_result.get('thumbnail', ''),
                    webpage_url=download_result.get('webpage_url', url)
                )
            )
            
            # session_dir 속성 추가 (ai_analyzer가 사용)
            video.session_dir = os.path.dirname(download_result['filepath'])
            
            # 5. DB에 영상 정보 저장
            video_data = {
                'video_id': video_id,
                'url': url,
                'title': video.metadata.title,
                'duration': video.metadata.duration,
                'platform': platform,
                'download_date': datetime.now().isoformat(),
                'uploader': video.metadata.uploader,
                'description': video.metadata.description,
                'view_count': video.metadata.view_count
            }
            self.db.save_video_info(video_data)
            
            # 6. 씬 추출
            logger.info("씬 추출 시작")
            scenes_result = self.scene_extractor.extract_scenes(
                video.local_path, 
                video.session_id
            )
            
            # Scene 객체로 변환
            video.scenes = []
            
            # scenes_result가 딕셔너리인지 확인
            if isinstance(scenes_result, dict):
                # 'scenes' 키가 있는 경우
                if 'scenes' in scenes_result:
                    scenes_list = scenes_result['scenes']
                # 'selected_images' 키만 있는 경우
                elif 'selected_images' in scenes_result:
                    scenes_list = scenes_result['selected_images']
                else:
                    logger.warning("씬 추출 결과에서 scenes 또는 selected_images를 찾을 수 없습니다")
                    scenes_list = []
            # scenes_result가 리스트인 경우
            elif isinstance(scenes_result, list):
                scenes_list = scenes_result
            else:
                logger.error(f"예상치 못한 씬 추출 결과 타입: {type(scenes_result)}")
                scenes_list = []
            
            # 씬 데이터 처리
            for scene_data in scenes_list:
                # 이미 Scene 객체인 경우
                if isinstance(scene_data, Scene):
                    video.scenes.append(scene_data)
                # scene_data가 딕셔너리인 경우
                elif isinstance(scene_data, dict):
                    scene = Scene(
                        timestamp=scene_data.get('timestamp', 0.0),
                        frame_path=scene_data.get('frame_path', '') or scene_data.get('path', ''),
                        scene_type=scene_data.get('type', 'mid')
                    )
                    video.scenes.append(scene)
                # scene_data가 문자열(경로)인 경우
                elif isinstance(scene_data, str):
                    scene = Scene(
                        timestamp=0.0,  # 타임스탬프 정보 없음
                        frame_path=scene_data,
                        scene_type='mid'
                    )
                    video.scenes.append(scene)
                else:
                    logger.warning(f"알 수 없는 씬 데이터 타입: {type(scene_data)}")
                    continue
            
            # 7. AI 분석 (수정된 부분)
            logger.info(f"🤖 AI 분석기 상태 확인: {self.ai_analyzer is not None}")
            logger.info(f"🎬 추출된 씬 수: {len(video.scenes) if video.scenes else 0}")
            logger.info(f"🔑 OpenAI API 키 설정: {'있음' if os.getenv('OPENAI_API_KEY') else '없음'}")
            
            if self.ai_analyzer and video.scenes:
                try:
                    logger.info("🤖 AI 영상 분석 시작")
                    
                    # AIAnalyzer는 Video 객체를 직접 받음
                    analysis_result = self.ai_analyzer.analyze_video(video)
                    
                    logger.info(f"🔍 AI 분석 결과 타입: {type(analysis_result)}")
                    
                    if analysis_result:
                        logger.info(f"✅ AI 분석 성공: {getattr(analysis_result, 'genre', 'Unknown')}")
                        
                        # analysis_result는 AnalysisResult 객체
                        video.analysis_result = {
                            'genre': getattr(analysis_result, 'genre', ''),
                            'reasoning': getattr(analysis_result, 'reason', ''),  # 'reason' -> 'reasoning'
                            'features': getattr(analysis_result, 'features', ''),
                            'tags': getattr(analysis_result, 'tags', []),
                            'expression_style': getattr(analysis_result, 'format_type', ''),  # 'format_type' -> 'expression_style'
                            'mood_tone': getattr(analysis_result, 'mood', ''),  # 'mood' -> 'mood_tone'
                            'target_audience': getattr(analysis_result, 'target_audience', '')
                        }
                        
                        # 8. 분석 결과 DB에 저장
                        analysis_data = {
                            'genre': getattr(analysis_result, 'genre', ''),
                            'reasoning': getattr(analysis_result, 'reason', ''),
                            'features': getattr(analysis_result, 'features', ''),
                            'tags': getattr(analysis_result, 'tags', []),
                            'expression_style': getattr(analysis_result, 'format_type', ''),
                            'mood_tone': getattr(analysis_result, 'mood', ''),
                            'target_audience': getattr(analysis_result, 'target_audience', ''),
                            'analyzed_scenes': [os.path.basename(scene.frame_path) for scene in video.scenes[:getattr(self.ai_analyzer, 'max_images', 10)]],
                            'token_usage': {},  # 기존 ai_analyzer는 토큰 정보를 반환하지 않음
                            'model_used': os.getenv('OPENAI_MODEL', 'gpt-4o')
                        }
                        self.db.save_analysis_result(video_id, analysis_data)
                        
                        logger.info(f"💾 DB 저장 완료 - 장르: {getattr(analysis_result, 'genre', 'Unknown')}")
                    else:
                        logger.warning("⚠️ AI 분석 결과가 None입니다")
                        
                except Exception as e:
                    logger.error(f"❌ AI 분석 중 오류 발생: {str(e)}")
                    logger.error(f"❌ 오류 상세: {type(e).__name__}: {e}")
                    import traceback
                    logger.error(f"❌ 스택 트레이스:\n{traceback.format_exc()}")
                    # AI 분석 실패해도 전체 프로세스는 계속 진행
            else:
                # 조건 미충족 이유 로깅
                if not self.ai_analyzer:
                    logger.info("ℹ️ AI 분석기가 초기화되지 않음 - OpenAI API 키를 확인하세요")
                elif not video.scenes:
                    logger.info("ℹ️ 추출된 씬이 없어 AI 분석을 건너뜁니다")
                else:
                    logger.info("ℹ️ AI 분석 조건을 만족하지 않음")
            
            # 9. 스토리지 업로드 (기존과 동일)
            if self.storage_manager.storage_type != StorageType.LOCAL:
                logger.info("스토리지 업로드 시작")
                self._upload_to_storage(video)
            
            # 10. 임시 파일 정리 (기존과 동일)
            if os.getenv("CLEANUP_TEMP_FILES", "false").lower() == "true":
                self._cleanup_temp_files(video)
            
            logger.info(f"영상 처리 완료: {video_id}")
            return video
            
        except Exception as e:
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
                local_path=None,  # 이미 다운로드된 파일 경로는 포함하지 않음
                metadata=VideoMetadata(
                    title=video_info.get('title', ''),
                    duration=video_info.get('duration', 0),
                    uploader=video_info.get('uploader', ''),
                    upload_date=video_info.get('upload_date', ''),
                    description=video_info.get('description', ''),
                    view_count=video_info.get('view_count', 0),
                    like_count=video_info.get('like_count', 0),
                    video_id=video_id,
                    ext='mp4',
                    thumbnail='',
                    webpage_url=video_info['url']
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
                # 파일명에서 특수문자 처리 (언더스코어는 유지)
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