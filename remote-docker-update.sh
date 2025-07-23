#!/bin/bash

# 원격 서버에 복사해서 실행할 스크립트
# 이 파일을 원격 서버의 프로젝트 디렉토리에 복사하고 실행

echo "🔄 Starting Docker update process on sense-of-frame-dev..."

# 현재 디렉토리가 프로젝트 루트인지 확인
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found in current directory"
    echo "Please run this script from the project root directory"
    exit 1
fi

# 1. 현재 브랜치 확인
CURRENT_BRANCH=$(git branch --show-current)
echo "📍 Current branch: $CURRENT_BRANCH"

# 2. develop 브랜치로 전환
if [ "$CURRENT_BRANCH" != "develop" ]; then
    echo "📝 Switching to develop branch..."
    git checkout develop
fi

# 3. 최신 코드 가져오기
echo "🔽 Pulling latest changes from develop..."
git pull origin develop

if [ $? -ne 0 ]; then
    echo "❌ Git pull failed. Please check your git configuration."
    exit 1
fi

# 4. Docker 재시작 옵션 선택
echo ""
echo "Select restart option:"
echo "1) Quick restart (container only)"
echo "2) Full rebuild (recommended for major updates)"
echo -n "Enter choice [1-2]: "
read -r choice

case $choice in
    1)
        echo "🔄 Quick restarting containers..."
        docker-compose restart
        ;;
    2)
        echo "🛑 Stopping containers..."
        docker-compose down
        
        echo "🔨 Rebuilding images..."
        docker-compose build --no-cache
        
        echo "🚀 Starting containers..."
        docker-compose up -d
        ;;
    *)
        echo "❌ Invalid choice. Exiting."
        exit 1
        ;;
esac

# 5. 상태 확인
echo ""
echo "📋 Container status:"
docker-compose ps

echo ""
echo "✅ Update completed!"
echo "💡 To view logs: docker-compose logs -f"
echo "🌐 Access the app at: http://192.168.50.50:8501"