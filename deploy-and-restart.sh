#!/bin/bash

# Git push 후 원격 서버 Docker 재시작 스크립트
# 보안을 위해 SSH 키 인증 사용을 권장합니다

REMOTE_HOST="192.168.50.50"
REMOTE_USER="ysk"
CONTAINER_NAME="sense-of-frame-dev"

echo "🚀 Starting deployment process..."

# 1. Git 변경사항 확인
if [ -z "$(git status --porcelain)" ]; then
    echo "✅ No changes to commit"
else
    # Git add, commit, push
    echo "📝 Committing changes..."
    git add -A
    
    # 커밋 메시지 입력받기
    read -p "Enter commit message: " commit_message
    git commit -m "$commit_message"
    
    echo "📤 Pushing to remote..."
    git push origin develop
fi

# 2. SSH를 통한 Docker 재시작
echo "🔄 Restarting Docker container on $REMOTE_HOST..."

# SSH 키 기반 인증 사용 시
ssh $REMOTE_USER@$REMOTE_HOST "docker restart $CONTAINER_NAME"

# 또는 sshpass 사용 시 (보안상 권장하지 않음)
# sshpass -p '1212' ssh $REMOTE_USER@$REMOTE_HOST "docker restart $CONTAINER_NAME"

if [ $? -eq 0 ]; then
    echo "✅ Docker container restarted successfully!"
    echo "🌐 Application should be available at http://$REMOTE_HOST:8501"
else
    echo "❌ Failed to restart Docker container"
    exit 1
fi