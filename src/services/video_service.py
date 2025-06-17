# src/services/video_service.py
import os
from typing import Optional, List
from src.models.video import Video
from src.fetcher.youtube import YouTubeFetcher
from src.fetcher.vimeo import VimeoFetcher
from src.storage.storage_manager import StorageManager, StorageType
from utils.logger import get_logger

class VideoService:
    """비디오 처리 서비스 - 다운로드, 분석, 저장을 통합 관리"""
    
    def __init__(self, storage_type: StorageType = StorageType.LOCAL):
        self.logger = get_logger(__name__)
        self.fetchers = [YouTubeFetcher(), VimeoFetcher()]
        
        # 스토리지 매니저 초기화
        self.storage_manager = StorageManager(storage_type)
        self.logger.info(f"VideoService 초기화 - 스토리지 타입: {storage_type.value}")
    
    def get_fetcher(self, url: str):
        """URL에 맞는 다운로더 선택"""
        for fetcher in self.fetchers:
            if fetcher.is_supported(url):
                return fetcher
        raise ValueError(f"지원하지 않는 URL입니다: {url}")
    
    def process_video(self, url: str) -> Video:
        """비디오 처리 전체 워크플로우"""
        # 1. Video 객체 생성
        video = Video(session_id="", url=url)
        self.logger.info(f"🎬 비디오 처리 시작: {url}")
        
        try:
            # 2. 적절한 다운로더 선택
            fetcher = self.get_fetcher(url)
            self.logger.info(f"📥 다운로더 선택: {fetcher.__class__.__name__}")
            
            # 3. 비디오 다운로드
            video_path, metadata = fetcher.download(video)
            self.logger.info(f"✅ 다운로드 완료: {video_path}")
            
            # 4. 메타데이터 저장
            metadata_path = fetcher.save_metadata(video)
            
            # 5. 씬 추출
            self.logger.info("🎬 씬 추출 시작...")
            from src.extractor.scene_extractor import SceneExtractor
            
            scene_extractor = SceneExtractor()
            scenes_dir = os.path.join(video.session_dir, "scenes")
            video.scenes = scene_extractor.extract_scenes(video_path, scenes_dir)
            
            # 6. AI 분석 (OpenAI API 키가 있는 경우)
            if os.getenv("OPENAI_API_KEY"):
                self.logger.info("🤖 AI 분석 시작...")
                from src.analyzer.ai_analyzer import AIAnalyzer
                
                analyzer = AIAnalyzer()
                analysis_result = analyzer.analyze_video(video)
                
                if analysis_result:
                    self.logger.info(f"✅ AI 분석 완료: {analysis_result.genre}")
                else:
                    self.logger.warning("⚠️ AI 분석 실패 또는 스킵")
            
            # 7. 스토리지에 저장 (비디오, 메타데이터, 씬 이미지, 분석 결과 모두)
            files_to_upload = [video_path, metadata_path]
            
            # 씬 이미지 파일들 추가
            if video.scenes:
                for scene in video.scenes:
                    if os.path.exists(scene.frame_path):
                        files_to_upload.append(scene.frame_path)
                
                # scenes.json 파일도 추가
                scenes_json = os.path.join(scenes_dir, "scenes.json")
                if os.path.exists(scenes_json):
                    files_to_upload.append(scenes_json)
            
            self._save_to_storage(video, files_to_upload)
            
            return video
            
        except Exception as e:
            self.logger.error(f"❌ 비디오 처리 실패: {e}")
            raise
    
    def _save_to_storage(self, video: Video, files: List[str]):
        """스토리지에 파일 저장"""
        remote_folder = f"2025-session/{video.session_id}"
        
        for file_path in files:
            try:
                uploaded_path = self.storage_manager.upload_file(file_path, remote_folder)
                self.logger.info(f"✅ 저장 완료: {uploaded_path}")
            except Exception as e:
                self.logger.error(f"저장 실패: {file_path}, 오류: {e}")
                raise
    
    def test_storage_connection(self) -> bool:
        """스토리지 연결 테스트"""
        return self.storage_manager.test_connection()