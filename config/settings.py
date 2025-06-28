# config/settings.py
import os
from dotenv import load_dotenv
from dataclasses import dataclass

# .env 파일 로드
load_dotenv()

@dataclass
class VideoConfig:
    """비디오 처리 설정"""
    max_duration: int = 600  # 10분
    output_format: str = "mp4"
    quality: str = "bestvideo+bestaudio/best"
    # subtitle_languages: list = None  # 자막 비활성화
    
    def __post_init__(self):
        pass
        # if self.subtitle_languages is None:
        #     self.subtitle_languages = ['ko', 'en']

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