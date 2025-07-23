#!/bin/bash

# 원격 서버(192.168.50.50) Docker 업데이트 스크립트
# SSH를 통해 원격 서버에서 git pull 및 Docker 재시작 실행

REMOTE_HOST="192.168.50.50"
REMOTE_USER="your_username"  # 실제 사용자명으로 변경하세요
REMOTE_PATH="/path/to/video-reference-project"  # 실제 프로젝트 경로로 변경하세요

echo "🔄 Updating sense-of-frame-dev on $REMOTE_HOST..."

# SSH를 통해 원격 명령 실행
ssh $REMOTE_USER@$REMOTE_HOST << 'ENDSSH'
    echo "📍 Connected to remote server"
    
    # 프로젝트 디렉토리로 이동
    cd $REMOTE_PATH || exit 1
    
    echo "🔽 Pulling latest code from develop branch..."
    git checkout develop
    git pull origin develop
    
    echo "🛑 Stopping Docker containers..."
    docker-compose down
    
    echo "🔨 Rebuilding Docker images..."
    docker-compose build --no-cache
    
    echo "🚀 Starting Docker containers..."
    docker-compose up -d
    
    echo "📋 Container status:"
    docker-compose ps
    
    echo "✅ Update completed on remote server!"
ENDSSH

echo "✅ Remote update script finished!"