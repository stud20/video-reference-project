# core/video/downloader/vimeo.py
import yt_dlp
import os
import re
import subprocess
from typing import Dict, Any, Optional, List, Tuple
from core.video.downloader.base import VideoFetcher
from core.video.models import Video, VideoMetadata
from utils.logger import get_logger
from core.video.processor.download_options import DownloadOptions
from core.video.processor.video_processor import VideoProcessor

logger = get_logger(__name__)


class VimeoDownloader(VideoFetcher):
    """Vimeo 비디오 다운로더 - 확장된 메타데이터 추출 + macOS 호환성"""
    
    def __init__(self):
        super().__init__()
        self.logger = logger
        self.temp_dir = "data/temp"
        os.makedirs(self.temp_dir, exist_ok=True)
        self.video_processor = VideoProcessor()
        self.download_options = DownloadOptions()
    
    def is_supported(self, url: str) -> bool:
        """Vimeo URL인지 확인"""
        vimeo_patterns = [
            r'(https?://)?(www\.)?vimeo\.com/\d+',
            r'(https?://)?(www\.)?vimeo\.com/[^/]+/\d+',  # 채널/비디오ID 형식
            r'(https?://)?player\.vimeo\.com/video/\d+',
            r'(https?://)?(www\.)?vimeo\.com/showcase/\d+/video/\d+'  # showcase 형식
        ]
        return any(re.match(pattern, url) for pattern in vimeo_patterns)
    
    def _sanitize_filename(self, title: str, max_length: int = 100) -> str:
        """파일명으로 사용할 수 있도록 제목 정리"""
        # 특수문자를 언더스코어로 치환
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
        # 연속된 언더스코어를 하나로
        safe_title = re.sub(r'_+', '_', safe_title)
        # 앞뒤 공백 및 언더스코어 제거
        safe_title = safe_title.strip('_ ')
        # 최대 길이 제한
        return safe_title[:max_length]
    
    def download(self, video: Video) -> Tuple[str, VideoMetadata]:
        """
        Vimeo 비디오 다운로드 - 확장된 메타데이터 추출 및 macOS 호환성 보장
        
        Args:
            video: Video 객체
            
        Returns:
            (파일경로, 메타데이터) 튜플
        """
        try:
            # 1. 먼저 정보만 추출
            self.logger.info(f"📊 메타데이터 추출 중: {video.url}")
            with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                info = ydl.extract_info(video.url, download=False)
                video_id = info.get('id', '')
                video_title = info.get('title', 'untitled')
            
            if not video_id:
                raise ValueError("비디오 ID를 추출할 수 없습니다.")
            
            # 2. 세션 디렉토리 준비
            output_dir = self.prepare_session_directory(video)
            
            # 3. 파일명 생성
            safe_title = self._sanitize_filename(video_title)
            output_template = os.path.join(output_dir, f'{safe_title}.%(ext)s')
            
            # 4. 다운로드 옵션 설정 (macOS 호환 H.264 우선)
            quality_option = os.getenv("VIDEO_QUALITY", "best")
            
            if quality_option == "fast":
                ydl_opts = self.download_options.get_fast_mp4_options(output_template)
            elif quality_option == "balanced":
                ydl_opts = self.download_options.get_balanced_mp4_options(output_template)
            else:  # best
                ydl_opts = self.download_options.get_best_mp4_options(output_template)
            
            self.logger.info(f"📥 다운로드 시작: {video.url} (품질: {quality_option})")
            self.logger.info(f"📁 저장 위치: {output_dir}")
            
            # 5. 다운로드 실행
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video.url, download=True)
                
                # 실제 다운로드된 파일 경로 찾기
                downloaded_file = ydl.prepare_filename(info)
                
                # 확장자가 변경되었을 수 있으므로 확인
                if not os.path.exists(downloaded_file):
                    base_name = os.path.splitext(downloaded_file)[0]
                    for ext in ['.mp4', '.webm', '.mkv', '.mov']:
                        test_file = base_name + ext
                        if os.path.exists(test_file):
                            downloaded_file = test_file
                            break
            
            if not os.path.exists(downloaded_file):
                raise FileNotFoundError(f"다운로드된 파일을 찾을 수 없습니다: {downloaded_file}")
            
            # 6. macOS 호환성 확인 및 필요시 재인코딩
            self.logger.info("🎥 macOS 호환성 확인 중...")
            processed_file = self.video_processor.process_video(downloaded_file)
            
            # 7. 파일 크기 확인
            file_size = os.path.getsize(processed_file) / (1024 * 1024)  # MB
            self.logger.info(f"📊 최종 파일 크기: {file_size:.1f} MB")
            
            # 8. 자막 파일 찾기
            subtitle_files = self._find_subtitle_files(output_dir)
            
            # 9. 썸네일 파일 찾기
            thumbnail_file = self._find_thumbnail_file(output_dir)
            
            # 10. Vimeo 특유의 메타데이터 추가 추출
            vimeo_metadata = self._extract_vimeo_specific_metadata(info)
            
            # 11. 메타데이터 생성 (확장된 버전)
            metadata = VideoMetadata(
                video_id=video_id,
                title=info.get('title', ''),
                url=video.url,
                duration=info.get('duration', 0),
                uploader=info.get('uploader', info.get('creator', '')),  # Vimeo는 creator 필드도 사용
                channel_id=info.get('uploader_id', ''),
                upload_date=info.get('upload_date', ''),
                description=info.get('description', ''),
                view_count=info.get('view_count', 0),
                like_count=info.get('like_count', 0),
                comment_count=info.get('comment_count', 0),
                tags=self._extract_vimeo_tags(info),  # Vimeo 태그 추출
                categories=info.get('categories', []),
                language=info.get('language', ''),
                age_limit=info.get('age_limit', 0),
                ext=os.path.splitext(processed_file)[1][1:],
                thumbnail=info.get('thumbnail', ''),
                webpage_url=info.get('webpage_url', video.url),
                subtitle_files=subtitle_files,
                platform='vimeo'
            )
            
            # Video 객체 업데이트
            video.local_path = processed_file
            video.metadata = metadata
            
            # 12. 메타데이터 파일 저장
            self.save_metadata(video)
            
            self.logger.info(f"✅ 다운로드 및 처리 완료: {safe_title}")
            self.logger.info(f"🎬 업로더: {metadata.uploader}")
            self.logger.info(f"👁 조회수: {metadata.view_count:,}")
            self.logger.info(f"🏷 태그: {', '.join(metadata.tags[:5])}")
            
            # Vimeo 특유 정보 로깅
            if vimeo_metadata:
                if vimeo_metadata.get('privacy'):
                    self.logger.info(f"🔒 프라이버시: {vimeo_metadata['privacy']}")
                if vimeo_metadata.get('is_staff_pick'):
                    self.logger.info(f"⭐ Staff Pick 여부: {vimeo_metadata['is_staff_pick']}")
            
            return processed_file, metadata
            
        except Exception as e:
            self.logger.error(f"다운로드 실패: {str(e)}")
            raise
    
    def _find_subtitle_files(self, directory: str) -> Dict[str, str]:
        """자막 파일 찾기"""
        subtitle_files = {}
        for file in os.listdir(directory):
            if file.endswith(('.vtt', '.srt')):
                if '.ko.' in file or 'Korean' in file:
                    subtitle_files['ko'] = os.path.join(directory, file)
                elif '.en.' in file or 'English' in file:
                    subtitle_files['en'] = os.path.join(directory, file)
                else:
                    # 언어 코드 추출 시도
                    lang_match = re.search(r'\.([a-z]{2})\.(vtt|srt)$', file)
                    if lang_match:
                        lang_code = lang_match.group(1)
                        subtitle_files[lang_code] = os.path.join(directory, file)
        return subtitle_files
    
    def _find_thumbnail_file(self, directory: str) -> Optional[str]:
        """썸네일 파일 찾기"""
        for file in os.listdir(directory):
            if file.endswith(('.jpg', '.jpeg', '.png', '.webp')):
                # 썸네일 파일명 패턴 확인
                if 'thumbnail' in file.lower() or 'thumb' in file.lower():
                    return os.path.join(directory, file)
        
        # 썸네일 키워드가 없으면 첫 번째 이미지 파일 반환
        for file in os.listdir(directory):
            if file.endswith(('.jpg', '.jpeg', '.png', '.webp')):
                return os.path.join(directory, file)
        return None
    
    def _extract_vimeo_tags(self, info: Dict[str, Any]) -> List[str]:
        """Vimeo 태그 추출"""
        tags = []
        
        # 기본 tags 필드
        if info.get('tags'):
            tags.extend(info['tags'])
        
        # Vimeo는 categories를 태그처럼 사용하기도 함
        if info.get('categories'):
            for category in info['categories']:
                if isinstance(category, str):
                    tags.append(category)
                elif isinstance(category, dict) and 'name' in category:
                    tags.append(category['name'])
        
        # 중복 제거 및 정리
        unique_tags = []
        seen = set()
        for tag in tags:
            tag_clean = tag.strip()
            if tag_clean and tag_clean.lower() not in seen:
                seen.add(tag_clean.lower())
                unique_tags.append(tag_clean)
        
        return unique_tags
    
    def _extract_vimeo_specific_metadata(self, info: Dict[str, Any]) -> Dict[str, Any]:
        """Vimeo 특유의 메타데이터 추출"""
        vimeo_metadata = {}
        
        # 프라이버시 설정
        if 'privacy' in info:
            vimeo_metadata['privacy'] = info['privacy']
        
        # Staff Pick 여부
        if 'is_staff_pick' in info:
            vimeo_metadata['is_staff_pick'] = info['is_staff_pick']
        
        # 라이선스 정보
        if 'license' in info:
            vimeo_metadata['license'] = info['license']
        
        # 다운로드 가능 여부
        if 'is_downloadable' in info:
            vimeo_metadata['is_downloadable'] = info['is_downloadable']
        
        return vimeo_metadata
    
    def get_video_info(self, url: str) -> Dict[str, Any]:
        """
        다운로드 없이 비디오 정보만 추출 (확장된 버전)
        
        Args:
            url: Vimeo 비디오 URL
            
        Returns:
            확장된 비디오 정보 딕셔너리
        """
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'dump_single_json': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # 사용 가능한 자막 언어 확인
                subtitle_langs = []
                if info.get('subtitles'):
                    subtitle_langs = list(info['subtitles'].keys())
                if info.get('automatic_captions'):
                    subtitle_langs.extend([f"{lang} (자동)" for lang in info['automatic_captions'].keys()])
                
                # Vimeo 특유 메타데이터
                vimeo_metadata = self._extract_vimeo_specific_metadata(info)
                
                result = {
                    'video_id': info.get('id', ''),
                    'title': info.get('title', ''),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', info.get('creator', '')),
                    'channel_id': info.get('uploader_id', ''),
                    'upload_date': info.get('upload_date', ''),
                    'description': info.get('description', ''),
                    'view_count': info.get('view_count', 0),
                    'like_count': info.get('like_count', 0),
                    'comment_count': info.get('comment_count', 0),
                    'tags': self._extract_vimeo_tags(info),
                    'categories': info.get('categories', []),
                    'language': info.get('language', ''),
                    'age_limit': info.get('age_limit', 0),
                    'thumbnail': info.get('thumbnail', ''),
                    'webpage_url': info.get('webpage_url', url),
                    'available_subtitles': subtitle_langs,
                    'platform': 'vimeo',
                    'vimeo_specific': vimeo_metadata  # Vimeo 특유 정보
                }
                
                return result
                
        except Exception as e:
            self.logger.error(f"정보 추출 실패: {str(e)}")
            raise