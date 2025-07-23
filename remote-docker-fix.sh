#!/bin/bash

# 원격 서버의 Docker 설정을 수정하는 스크립트
# 192.168.50.50 서버에서 실행

echo "🔧 Fixing sense-of-frame-dev Docker configuration..."

# 1. 현재 실행 중인 컨테이너 확인
CONTAINER_NAME="sense-of-frame-dev"
if ! docker ps | grep -q $CONTAINER_NAME; then
    echo "❌ Container $CONTAINER_NAME is not running"
    exit 1
fi

# 2. docker-compose.yml 찾기
echo "📍 Looking for docker-compose.yml..."
COMPOSE_FILE=$(find /home /opt /var -name "docker-compose*.yml" -type f 2>/dev/null | grep -i "sense-of-frame" | head -1)

if [ -z "$COMPOSE_FILE" ]; then
    echo "❌ docker-compose.yml not found"
    echo "Please specify the path to your docker-compose.yml file"
    exit 1
fi

echo "📄 Found compose file: $COMPOSE_FILE"

# 3. 환경변수 추가를 위한 수정된 compose 파일 생성
cp $COMPOSE_FILE ${COMPOSE_FILE}.backup
echo "📋 Created backup: ${COMPOSE_FILE}.backup"

# 4. GIT_BRANCH 환경변수 추가
echo ""
echo "🔧 Adding GIT_BRANCH=develop to environment..."
echo ""
echo "Please edit $COMPOSE_FILE and add this line under 'environment:' section:"
echo "      - GIT_BRANCH=develop"
echo ""
echo "Or run this command to update automatically:"
echo "docker-compose down && docker-compose up -d"

# 5. 임시 해결책 제공
echo ""
echo "🚀 Quick fix (run inside container):"
echo "docker exec -it $CONTAINER_NAME bash -c 'cd /app/video-reference-project && git checkout develop && git pull origin develop'"

# 6. 영구 해결을 위한 docker-compose 예시
cat > docker-compose.sense-of-frame.yml << 'EOF'
version: '3.8'

services:
  sense-of-frame-dev:
    image: sense-of-frame:latest
    container_name: sense-of-frame-dev
    ports:
      - "8501:8501"
    environment:
      - GIT_BRANCH=develop  # ← 이 줄을 추가하세요
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
EOF

echo ""
echo "✅ Example docker-compose.yml created: docker-compose.sense-of-frame.yml"
echo ""
echo "To apply changes:"
echo "1. Update your docker-compose.yml with GIT_BRANCH=develop"
echo "2. Run: docker-compose down && docker-compose up -d"