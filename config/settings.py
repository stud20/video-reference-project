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
    data_dir: str = os.getenv("DATA_DIR", "data")
    temp_dir: str = os.getenv("TEMP_DIR", "data/temp")
    cache_dir: str = os.getenv("CACHE_DIR", "data/cache")
    results_dir: str = os.getenv("RESULTS_DIR", "results")
    reports_dir: str = os.getenv("REPORTS_DIR", "results/reports")
    database_dir: str = os.getenv("DATABASE_DIR", "results/database")
    workspaces_dir: str = os.getenv("WORKSPACES_DIR", "data/workspaces")
    
    def __post_init__(self):
        # 상대 경로를 절대 경로로 변환
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.abspath(os.path.join(base_dir, self.data_dir))
        self.temp_dir = os.path.abspath(os.path.join(base_dir, self.temp_dir))
        self.cache_dir = os.path.abspath(os.path.join(base_dir, self.cache_dir))
        self.results_dir = os.path.abspath(os.path.join(base_dir, self.results_dir))
        self.reports_dir = os.path.abspath(os.path.join(base_dir, self.reports_dir))
        self.database_dir = os.path.abspath(os.path.join(base_dir, self.database_dir))
        self.workspaces_dir = os.path.abspath(os.path.join(base_dir, self.workspaces_dir))

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
        for path in [cls.paths.data_dir, cls.paths.temp_dir, cls.paths.cache_dir, 
                    cls.paths.results_dir, cls.paths.reports_dir, cls.paths.database_dir,
                    cls.paths.workspaces_dir]:
            os.makedirs(path, exist_ok=True)

# 프로젝트 시작 시 디렉토리 생성
Settings.create_directories()