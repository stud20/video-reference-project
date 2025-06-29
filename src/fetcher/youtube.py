import yt_dlp
import os
import re
import subprocess
from typing import Dict, Any, Optional, List
from utils.logger import get_logger
from src.fetcher.download_options import DownloadOptions
from src.fetcher.video_processor import VideoProcessor

logger = get_logger(__name__)


class YouTubeDownloader:
    """YouTube/Vimeo 비디오 다운로더 - 메타데이터 추출 + macOS 호환성"""
    
    def __init__(self):
        self.logger = logger
        self.temp_dir = "data/temp"
        os.makedirs(self.temp_dir, exist_ok=True)
        self.video_processor = VideoProcessor()
        self.download_options = DownloadOptions()
    
    def is_supported(self, url: str) -> bool:
        """지원하는 URL인지 확인"""
        patterns = [
            # YouTube
            r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/',
            r'(https?://)?(www\.)?youtube\.com/watch\?v=',
            r'(https?://)?(www\.)?youtu\.be/',
            # Vimeo
            r'(https?://)?(www\.)?vimeo\.com/\d+',
            r'(https?://)?player\.vimeo\.com/video/\d+'
        ]
        return any(re.match(pattern, url) for pattern in patterns)
    
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

    def _normalize_url(self, url: str) -> str:
        """
        YouTube URL을 표준 형식으로 정규화
        
        지원하는 형식:
        - https://www.youtube.com/watch?v=VIDEO_ID&param=value
        - https://youtu.be/VIDEO_ID?param=value
        - https://youtube.com/watch?v=VIDEO_ID
        - https://m.youtube.com/watch?v=VIDEO_ID
        
        Returns:
            표준 형식 URL: https://www.youtube.com/watch?v=VIDEO_ID
        """
        try:
            # 비디오 ID 추출을 위한 패턴들
            patterns = [
                # 표준 YouTube URL
                r'(?:https?://)?(?:www\.)?(?:m\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
                # 단축 URL
                r'(?:https?://)?youtu\.be/([a-zA-Z0-9_-]{11})',
                # embed URL
                r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
                # mobile URL
                r'(?:https?://)?m\.youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})'
            ]
            
            video_id = None
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    video_id = match.group(1)
                    break
            
            if not video_id:
                # URL이 유효하지 않은 경우 원본 반환
                self.logger.warning(f"YouTube 비디오 ID를 추출할 수 없습니다: {url}")
                return url
            
            # 표준 형식으로 변환
            normalized_url = f"https://www.youtube.com/watch?v={video_id}"
            self.logger.info(f"URL 정규화: {url} -> {normalized_url}")
            
            return normalized_url
            
        except Exception as e:
            self.logger.error(f"URL 정규화 중 오류: {str(e)}")
            return url



    def download(self, url: str) -> Dict[str, Any]:
        """
        비디오 다운로드 - 메타데이터 추출 및 macOS 호환성 보장
        
        Args:
            url: 다운로드할 비디오 URL
            
        Returns:
            다운로드 결과 딕셔너리 (확장된 메타데이터 포함)
        """
        try:
        # URL 정규화
            url = self._normalize_url(url)
            # 1. 먼저 정보만 추출
            self.logger.info(f"📊 메타데이터 추출 중: {url}")
            with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                video_id = info.get('id', '')
                video_title = info.get('title', 'untitled')
            
            if not video_id:
                raise ValueError("비디오 ID를 추출할 수 없습니다.")
            
            # 2. 다운로드 디렉토리 생성
            output_dir = os.path.join(self.temp_dir, video_id)
            os.makedirs(output_dir, exist_ok=True)
            
            # 3. 파일명 생성
            safe_title = self._sanitize_filename(video_title)
            # 비디오 파일명을 {video_id}_제목.mp4 형식으로 변경
            output_template = os.path.join(output_dir, f'{video_id}_{safe_title}.%(ext)s')
            
            # 4. 다운로드 옵션 설정 (macOS 호환 H.264 우선)
            quality_option = os.getenv("VIDEO_QUALITY", "best")
            
            if quality_option == "fast":
                ydl_opts = self.download_options.get_fast_mp4_options(output_template)
            elif quality_option == "balanced":
                ydl_opts = self.download_options.get_balanced_mp4_options(output_template)
            else:  # best
                ydl_opts = self.download_options.get_best_mp4_options(output_template)
            
            self.logger.info(f"📥 다운로드 시작: {url} (품질: {quality_option})")
            self.logger.info(f"📁 저장 위치: {output_dir}")
            
            # 5. 다운로드 실행
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
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
            
            # 9. 썸네일 파일 처리
            thumbnail_file = self._download_and_save_thumbnail(info, output_dir, video_id)
            
            # 10. 결과 반환 (확장된 메타데이터)
            result = {
                'filepath': processed_file,
                'video_id': video_id,
                'title': info.get('title', ''),
                'duration': info.get('duration', 0),
                'uploader': info.get('uploader', info.get('channel', '')),  # 채널명
                'channel_id': info.get('channel_id', ''),
                'upload_date': info.get('upload_date', ''),
                'description': info.get('description', ''),
                'view_count': info.get('view_count', 0),
                'like_count': info.get('like_count', 0),
                'comment_count': info.get('comment_count', 0),
                'tags': info.get('tags', []),
                'categories': info.get('categories', []),
                'language': info.get('language', ''),
                'age_limit': info.get('age_limit', 0),
                'ext': os.path.splitext(processed_file)[1][1:],
                'thumbnail': info.get('thumbnail', ''),  # 원본 URL
                'thumbnail_file': thumbnail_file,  # 로컬 파일 경로
                'webpage_url': info.get('webpage_url', url),
                'subtitle_files': subtitle_files,
                'platform': self._detect_platform(url),
                'original_codec': self.video_processor.get_video_codec(downloaded_file),
                'processed_codec': self.video_processor.get_video_codec(processed_file) if processed_file != downloaded_file else None,
            }
            
            self.logger.info(f"✅ 다운로드 및 처리 완료: {safe_title}")
            self.logger.info(f"📺 채널: {result['uploader']}")
            if result.get('view_count') is not None:
                self.logger.info(f"👁 조회수: {result['view_count']:,}")
            else:
                self.logger.info(f"👁 조회수: 정보 없음")
            if result.get('tags'):
                self.logger.info(f"🏷 태그: {', '.join(result['tags'][:5])}")
            else:
                self.logger.info(f"🏷 태그: 없음")
            
            return result
            
        except Exception as e:
            self.logger.error(f"다운로드 실패: {str(e)}")
            raise
    
    def _download_and_save_thumbnail(self, info: Dict[str, Any], output_dir: str, video_id: str) -> Optional[str]:
        """썸네일 다운로드 및 저장"""
        thumbnail_url = info.get('thumbnail', '')
        if not thumbnail_url:
            return None
            
        try:
            # 썸네일 파일 경로 설정
            thumbnail_path = os.path.join(output_dir, f'{video_id}_Thumbnail.jpg')
            
            # yt-dlp를 사용하여 썸네일 다운로드
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'outtmpl': thumbnail_path,
                'writethumbnail': True,
                'skip_download': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # 썸네일만 다운로드
                import urllib.request
                urllib.request.urlretrieve(thumbnail_url, thumbnail_path)
                
            if os.path.exists(thumbnail_path):
                self.logger.info(f"✅ 썸네일 저장: {thumbnail_path}")
                return thumbnail_path
            else:
                self.logger.warning("썸네일 다운로드 실패")
                return None
                
        except Exception as e:
            self.logger.error(f"썸네일 다운로드 중 오류: {str(e)}")
            return None
    
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
        """썸네일 파일 찾기 (레거시 지원용)"""
        for file in os.listdir(directory):
            if file.endswith(('.jpg', '.jpeg', '.png', '.webp')) and 'Thumbnail' in file:
                return os.path.join(directory, file)
        return None
    
    def _detect_platform(self, url: str) -> str:
        """URL에서 플랫폼 감지"""
        if 'youtube.com' in url or 'youtu.be' in url:
            return 'youtube'
        elif 'vimeo.com' in url:
            return 'vimeo'
        else:
            return 'unknown'
    
    def get_video_info(self, url: str) -> Dict[str, Any]:
        """
        다운로드 없이 비디오 정보만 추출 (확장된 버전)
        
        Args:
            url: 비디오 URL
            
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
                
                return {
                    'video_id': info.get('id', ''),
                    'title': info.get('title', ''),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', info.get('channel', '')),
                    'channel_id': info.get('channel_id', ''),
                    'upload_date': info.get('upload_date', ''),
                    'description': info.get('description', ''),
                    'view_count': info.get('view_count', 0),
                    'like_count': info.get('like_count', 0),
                    'comment_count': info.get('comment_count', 0),
                    'tags': info.get('tags', []),
                    'categories': info.get('categories', []),
                    'language': info.get('language', ''),
                    'age_limit': info.get('age_limit', 0),
                    'thumbnail': info.get('thumbnail', ''),
                    'webpage_url': info.get('webpage_url', url),
                    'available_subtitles': subtitle_langs,
                    'platform': self._detect_platform(url),
                }
                
        except Exception as e:
            self.logger.error(f"정보 추출 실패: {str(e)}")
            raise