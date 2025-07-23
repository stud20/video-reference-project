#!/bin/bash

# 원격 서버의 sense-of-frame-dev를 빠르게 업데이트하는 스크립트
# SSH를 통해 실행

REMOTE_HOST="192.168.50.50"
REMOTE_USER="gm"  # 사용자명을 gm으로 설정
CONTAINER_NAME="sense-of-frame-dev"

echo "🔄 Quick update for $CONTAINER_NAME on $REMOTE_HOST..."

# SSH를 통해 원격 명령 실행
ssh $REMOTE_USER@$REMOTE_HOST << ENDSSH
    echo "📍 Connected to remote server"
    
    # 컨테이너가 실행 중인지 확인
    if ! docker ps | grep -q $CONTAINER_NAME; then
        echo "❌ Container $CONTAINER_NAME is not running"
        exit 1
    fi
    
    echo "🔄 Updating code in container..."
    
    # 컨테이너 내부에서 git pull 실행
    docker exec $CONTAINER_NAME bash -c '
        cd /app/video-reference-project
        echo "📍 Current branch: $(git branch --show-current)"
        echo "🔽 Fetching latest changes..."
        git fetch origin
        git checkout develop
        git pull origin develop
        echo "✅ Code updated to latest develop branch"
    '
    
    # Streamlit 프로세스 재시작 (선택사항)
    echo "🔄 Restarting Streamlit process..."
    docker exec $CONTAINER_NAME bash -c '
        pkill -f streamlit
        sleep 2
        cd /app/video-reference-project
        nohup streamlit run app.py --server.port=8501 --server.address=0.0.0.0 > /dev/null 2>&1 &
        echo "✅ Streamlit restarted"
    '
    
    echo "✅ Update completed!"
    echo "🌐 Access the app at: http://192.168.50.50:8501"
ENDSSH