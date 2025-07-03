FROM python:3.11-slim

LABEL maintainer="greatminds <your-email@domain.com>"
LABEL description="AI Video Reference Analysis System - Optimized for 5 concurrent users"

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# Python 의존성 설치
COPY requirements_optimized.txt .
RUN pip install --no-cache-dir -r requirements_optimized.txt

# 애플리케이션 코드 복사
COPY . .

# 데이터 디렉토리 생성
RUN mkdir -p data/database data/temp data/cache data/workspaces logs

# 권한 설정
RUN chmod -R 755 data logs

# 포트 노출
EXPOSE 8501

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Streamlit 앱 시작
CMD ["streamlit", "run", "app_optimized.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true", "--server.fileWatcherType=none", "--browser.gatherUsageStats=false"]
