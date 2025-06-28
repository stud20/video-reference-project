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
        # logger를 먼저 초기화
        self.logger = get_logger(__name__)
        self.downloader = YouTubeDownloader()
        # scene_extractor는 process_video에서 필요할 때 생성
        
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
                    subtitle_files=download_result.get('subtitle_files', {})
                )
            )
            
            # session_dir 속성 추가
            video.session_dir = os.path.dirname(download_result['filepath'])
            
            # 5. DB에 영상 정보 저장
            update_progress("database", 45, "💾 데이터베이스에 정보 저장 중...")
            video_data = {
                'video_id': video_id,
                'url': url,
                'title': video.metadata.title,
                'duration': video.metadata.duration,
                'platform': platform,
                'download_date': datetime.now().isoformat(),
                'uploader': video.metadata.uploader,
                'description': video.metadata.description,
                'view_count': video.metadata.view_count,
                'tags': video.metadata.tags,
                'channel_id': video.metadata.channel_id,
                'categories': video.metadata.categories,
                'language': video.metadata.language,
                'like_count': video.metadata.like_count,
                'comment_count': video.metadata.comment_count
            }
            self.db.save_video_info(video_data)
            
            
            # 6. 씬 추출 - SceneExtractor 인스턴스 생성
            update_progress("extract", 50, "🎬 주요 씬 추출 시작...")

            # SceneExtractor를 여기서 생성하여 최신 설정 반영


            # SceneExtractor를 여기서 생성하여 최신 설정 반영

            scene_extractor = SceneExtractor()
            scenes_result = scene_extractor.extract_scenes(
                video.local_path, 
                video.session_id
            )

            # 전체 씬과 그룹화된 씬 처리
            all_scenes = scenes_result.get('all_scenes', [])
            grouped_scenes = scenes_result.get('grouped_scenes', [])

            self.logger.info(f"📸 전체 {len(all_scenes)}개 씬 추출, {len(grouped_scenes)}개로 그룹화")

            # Video 객체에 모든 씬 저장
            video.scenes = all_scenes
            video.grouped_scenes = grouped_scenes  # 그룹화된 씬 별도 저장

            update_progress("extract", 60, f"✅ {len(all_scenes)}개 씬 추출 완료 (그룹화: {len(grouped_scenes)}개)")

            # 7. AI 분석 - 그룹화된 씬만 사용
            if self.ai_analyzer and grouped_scenes:
                try:
                    update_progress("analyze", 65, "🤖 AI 영상 분석 시작...")
                    update_progress("analyze", 70, f"🤖 {len(grouped_scenes)}개 대표 이미지로 분석 중...")
                    
                    # AI 분석을 위한 임시 video 객체 생성 (그룹화된 씬만 포함)
                    analysis_video = Video(
                        session_id=video.session_id,
                        url=video.url,
                        local_path=video.local_path,
                        metadata=video.metadata,
                        scenes=grouped_scenes  # 그룹화된 씬만 전달
                    )
                    analysis_video.session_dir = video.session_dir
                    
                    # AI 분석 실행
                    analysis_result = self.ai_analyzer.analyze_video(analysis_video)
                    
                    if analysis_result:
                        update_progress("analyze", 75, f"✅ AI 분석 성공: {getattr(analysis_result, 'genre', 'Unknown')}")
                        
                        # 분석 결과를 원본 video 객체에 저장
                        video.analysis_result = {
                            'genre': getattr(analysis_result, 'genre', ''),
                            'reasoning': getattr(analysis_result, 'reason', ''),
                            'features': getattr(analysis_result, 'features', ''),
                            'tags': getattr(analysis_result, 'tags', []),
                            'expression_style': getattr(analysis_result, 'format_type', ''),
                            'mood_tone': getattr(analysis_result, 'mood', ''),
                            'target_audience': getattr(analysis_result, 'target_audience', ''),
                            'analyzed_scenes_count': len(grouped_scenes),  # 분석에 사용된 씬 개수
                            'total_scenes_count': len(all_scenes)  # 전체 씬 개수
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
                            'analyzed_scenes': [os.path.basename(scene.frame_path) for scene in grouped_scenes],
                            'total_scenes': len(all_scenes),
                            'grouped_scenes': len(grouped_scenes),
                            'precision_level': scenes_result.get('precision_level', 5),
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
            
            # 8. 스토리지 업로드 - 나머지 코드는 동일
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
            
            # 9. 임시 파일 정리
            if os.getenv("CLEANUP_TEMP_FILES", "false").lower() == "true":
                update_progress("cleanup", 98, "🗑️ 임시 파일 정리 중...")
                self._cleanup_temp_files(video)
            
            update_progress("complete", 100, f"✅ 영상 처리 완료: {video_id}")
            return video
            
        except Exception as e:
            if progress_callback:
                progress_callback("error", 0, f"❌ 오류 발생: {str(e)}")
            logger.error(f"영상 처리 중 오류 발생: {str(e)}")
            raise
    
    # 나머지 메서드들은 그대로 유지
    def _create_video_from_db(self, video_id: str, analysis_data: Dict[str, Any]) -> Optional[Video]:
        """DB 데이터로부터 Video 객체 생성 - 씬 정보 복원 포함"""
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
            
            # 씬 정보 복원
            video.scenes = []
            video.grouped_scenes = []
            
            # 전체 씬 수와 그룹화된 씬 수 정보 활용
            total_scenes = analysis_data.get('total_scenes', 0)
            grouped_scenes_count = analysis_data.get('grouped_scenes', 0)
            precision_level = analysis_data.get('precision_level', 5)
            
            # analyzed_scenes에서 그룹화된 씬 정보 복원
            if 'analyzed_scenes' in analysis_data:
                analyzed_scenes = analysis_data['analyzed_scenes']
                for i, scene_filename in enumerate(analyzed_scenes):
                    scene = Scene(
                        timestamp=i * 10.0,  # 추정값
                        frame_path=scene_filename,
                        scene_type='mid',
                        grouped_path=scene_filename  # 그룹화된 씬으로 표시
                    )
                    video.grouped_scenes.append(scene)
            
            self.logger.info(
                f"DB에서 씬 정보 복원 - 전체: {total_scenes}개, "
                f"그룹화: {grouped_scenes_count}개, 정밀도: {precision_level}"
            )
            
            # 분석 결과에 씬 정보 추가
            video.analysis_result = {
                'genre': analysis_data.get('genre', ''),
                'reasoning': analysis_data.get('reasoning', ''),
                'features': analysis_data.get('features', ''),
                'tags': analysis_data.get('tags', []),
                'expression_style': analysis_data.get('expression_style', ''),
                'mood_tone': analysis_data.get('mood_tone', ''),
                'target_audience': analysis_data.get('target_audience', ''),
                'analyzed_at': analysis_data.get('analysis_date', ''),
                'total_scenes': total_scenes,  # 추가
                'grouped_scenes': grouped_scenes_count,  # 추가
                'precision_level': precision_level  # 추가
            }
            
            return video
            
        except Exception as e:
            logger.error(f"DB에서 Video 객체 생성 실패: {str(e)}")
            return None
    
    # src/services/video_service.py - _upload_to_storage 메서드 수정

    def _upload_to_storage(self, video: Video) -> None:
        """영상 및 씬 이미지를 스토리지에 업로드"""
        try:
            # 원격 기본 경로 설정 - video_id 폴더에 바로 저장
            remote_base_path = f"video_analysis/{video.session_id}"
            
            # 1. 비디오 파일 업로드
            if video.local_path and os.path.exists(video.local_path):
                video_filename = os.path.basename(video.local_path)
                remote_video_path = f"{remote_base_path}/{video_filename}"
                
                success = self.storage_manager.upload_file(video.local_path, remote_video_path)
                if success:
                    self.logger.info(f"✅ 비디오 업로드 완료: {video_filename}")
            
            # 2. 썸네일 업로드
            thumbnail_path = None
            if video.metadata and video.metadata.thumbnail:
                session_dir = os.path.dirname(video.local_path) if video.local_path else f"data/temp/{video.session_id}"
                possible_thumbnail = os.path.join(session_dir, f"{video.session_id}_Thumbnail.jpg")
                
                if os.path.exists(possible_thumbnail):
                    thumbnail_path = possible_thumbnail
                else:
                    for ext in ['.jpg', '.jpeg', '.png', '.webp']:
                        test_path = os.path.join(session_dir, f"thumbnail{ext}")
                        if os.path.exists(test_path):
                            thumbnail_path = test_path
                            break
            
            if thumbnail_path:
                thumbnail_filename = f"{video.session_id}_Thumbnail.jpg"
                remote_thumbnail_path = f"{remote_base_path}/{thumbnail_filename}"
                
                success = self.storage_manager.upload_file(thumbnail_path, remote_thumbnail_path)
                if success:
                    self.logger.info(f"✅ 썸네일 업로드 완료: {thumbnail_filename}")
            
            # 3. 모든 씬 이미지 업로드 (scene_XXXX.jpg)
            scenes_dir = os.path.join(os.path.dirname(video.local_path), "scenes")
            if os.path.exists(scenes_dir):
                scene_files = sorted([f for f in os.listdir(scenes_dir) if f.startswith('scene_') and f.endswith('.jpg')])
                
                for scene_file in scene_files:
                    scene_path = os.path.join(scenes_dir, scene_file)
                    remote_scene_path = f"{remote_base_path}/{scene_file}"
                    
                    success = self.storage_manager.upload_file(scene_path, remote_scene_path)
                    if success:
                        self.logger.debug(f"✅ 씬 업로드: {scene_file}")
                
                self.logger.info(f"📸 총 {len(scene_files)}개 씬 이미지 업로드 완료")
            
            # 4. 그룹화된 씬 이미지 업로드 (grouped_XXXX.jpg)
            grouped_dir = os.path.join(os.path.dirname(video.local_path), "grouped")
            if os.path.exists(grouped_dir):
                grouped_files = sorted([f for f in os.listdir(grouped_dir) if f.startswith('grouped_') and f.endswith('.jpg')])
                
                for grouped_file in grouped_files:
                    grouped_path = os.path.join(grouped_dir, grouped_file)
                    remote_grouped_path = f"{remote_base_path}/{grouped_file}"
                    
                    success = self.storage_manager.upload_file(grouped_path, remote_grouped_path)
                    if success:
                        self.logger.debug(f"✅ 그룹화된 씬 업로드: {grouped_file}")
                
                self.logger.info(f"🔍 총 {len(grouped_files)}개 그룹화된 씬 업로드 완료")
            
            # 5. 분석 결과 JSON 업로드
            if video.analysis_result:
                analysis_path = os.path.join(video.session_dir, "analysis_result.json")
                
                if not os.path.exists(analysis_path):
                    os.makedirs(os.path.dirname(analysis_path), exist_ok=True)
                    
                    import json
                    with open(analysis_path, 'w', encoding='utf-8') as f:
                        json.dump(video.analysis_result, f, ensure_ascii=False, indent=2)
                
                remote_analysis_path = f"{remote_base_path}/analysis_result.json"
                
                success = self.storage_manager.upload_file(analysis_path, remote_analysis_path)
                if success:
                    self.logger.info(f"✅ 분석 결과 업로드 완료")
                    
        except Exception as e:
            self.logger.error(f"스토리지 업로드 중 오류: {str(e)}")
    
    def _cleanup_temp_files(self, video: Video) -> None:
        """임시 파일 정리"""
        # 기존 코드 그대로 유지
        try:
            import shutil
            temp_dir = f"data/temp/{video.session_id}"
            
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                logger.info(f"임시 파일 정리 완료: {temp_dir}")
                
        except Exception as e:
            logger.error(f"임시 파일 정리 실패: {str(e)}")
    
    def test_storage_connection(self) -> bool:
        """스토리지 연결 테스트"""
        return self.storage_manager.test_connection()
    
    def get_analysis_history(self, video_id: str) -> List[Dict[str, Any]]:
        """특정 영상의 분석 히스토리 조회"""
        return self.db.get_all_analyses(video_id)
    
    def search_by_genre(self, genre: str) -> List[Dict[str, Any]]:
        """장르로 영상 검색"""
        return self.db.search_by_genre(genre)
    
    def search_by_tags(self, tags: List[str]) -> List[Dict[str, Any]]:
        """태그로 영상 검색"""
        return self.db.search_by_tags(tags)
    
    def get_statistics(self) -> Dict[str, Any]:
        """전체 통계 정보 조회"""
        return self.db.get_statistics()
    
    def __del__(self):
        """소멸자: DB 연결 종료"""
        if hasattr(self, 'db'):
            self.db.close()