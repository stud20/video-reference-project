#!/bin/bash

# 원격 서버의 상태를 확인하는 스크립트

echo "🔍 Checking sense-of-frame-dev status on 192.168.50.50..."

ssh gm@192.168.50.50 << 'ENDSSH'
    echo "📋 Container status:"
    docker ps | grep sense-of-frame-dev
    
    echo -e "\n📍 Current branch in container:"
    docker exec sense-of-frame-dev bash -c "cd /app/video-reference-project && git branch --show-current"
    
    echo -e "\n📝 Latest commit:"
    docker exec sense-of-frame-dev bash -c "cd /app/video-reference-project && git log --oneline -1"
    
    echo -e "\n✅ Version check in app.py:"
    docker exec sense-of-frame-dev bash -c "cd /app/video-reference-project && grep -A 5 'Version History' app.py || echo 'Version history not found'"
    
    echo -e "\n🌐 Application URL: http://192.168.50.50:8501"
ENDSSH