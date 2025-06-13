# config/settings.py
import os
from dotenv import load_dotenv
from dataclasses import dataclass

# .env 파일 로드
load_dotenv()

@dataclass
class WebDAVConfig:
    """WebDAV 설정"""
    hostname: str = os.getenv("WEBDAV_HOSTNAME", "https://nas.greatminds.kr:5006")
    login: str = os.getenv("WEBDAV_LOGIN", "dav")
    password: str = os.getenv("WEBDAV_PASSWORD", "dav123")
    root: str = os.getenv("WEBDAV_ROOT", "/dav/videoRef/")
    remote_folder: str = "2025-session/"

@dataclass
class VideoConfig:
    """비디오 처리 설정"""
    max_duration: int = 600  # 10분
    output_format: str = "mp4"
    quality: str = "bestvideo+bestaudio/best"
    subtitle_languages: list = None
    
    def __post_init__(self):
        if self.subtitle_languages is None:
            self.subtitle_languages = ['ko', 'en']

@dataclass
class PathConfig:
    """경로 설정"""
    data_dir: str = "data"
    temp_dir: str = "data/temp"
    cache_dir: str = "data/cache"
    results_dir: str = "results"
    reports_dir: str = "results/reports"
    database_dir: str = "results/database"

class Settings:
    """전체 설정 관리 클래스"""
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Configurations
    webdav = WebDAVConfig()
    video = VideoConfig()
    paths = PathConfig()
    
    # Debug Mode
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    @classmethod
    def create_directories(cls):
        """필요한 디렉토리들을 생성"""
        import os
        for path in [cls.paths.temp_dir, cls.paths.cache_dir, 
                    cls.paths.reports_dir, cls.paths.database_dir]:
            os.makedirs(path, exist_ok=True)

# 프로젝트 시작 시 디렉토리 생성
Settings.create_directories()
