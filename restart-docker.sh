#!/bin/bash

# Docker 재시작 스크립트 - Git pull 포함
# sense-of-frame-dev 환경을 위한 자동 업데이트 스크립트

echo "🔄 Starting Docker restart process..."

# 1. 현재 브랜치 확인
CURRENT_BRANCH=$(git branch --show-current)
echo "📍 Current branch: $CURRENT_BRANCH"

# 2. develop 브랜치로 체크아웃
if [ "$CURRENT_BRANCH" != "develop" ]; then
    echo "📝 Switching to develop branch..."
    git checkout develop
fi

# 3. 최신 코드 가져오기
echo "🔽 Pulling latest code from develop branch..."
git pull origin develop

# 4. Docker 컨테이너 중지
echo "🛑 Stopping existing containers..."
docker-compose down

# 5. Docker 이미지 재빌드 (캐시 무시)
echo "🔨 Rebuilding Docker images..."
docker-compose build --no-cache

# 6. Docker 컨테이너 시작
echo "🚀 Starting containers..."
docker-compose up -d

# 7. 로그 확인 (선택적)
echo "📋 Container status:"
docker-compose ps

echo "✅ Docker restart completed!"
echo "💡 To view logs, run: docker-compose logs -f"