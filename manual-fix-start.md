# start.sh 수동 수정 방법

## 1. SSH 접속
```bash
ssh gm@192.168.50.50
```

## 2. 컨테이너 내부로 진입
```bash
docker exec -it sense-of-frame-dev bash
```

## 3. start.sh 수정 (vi가 없으므로 sed 사용)
```bash
# 기존 main을 develop으로 변경
sed -i 's/BRANCH=${GIT_BRANCH:-main}/BRANCH=${GIT_BRANCH:-develop}/' /app/start.sh

# 또는 전체 파일을 다시 작성
cat > /app/start.sh << 'EOF'
#!/bin/bash
BRANCH=${GIT_BRANCH:-develop}

# 이미 clone 되어 있다면 pull, 없으면 clone
if [ -d "/app/video-reference-project" ]; then
    echo "📥 Git Pull from branch: $BRANCH"
    cd /app/video-reference-project
    git fetch origin
    git checkout $BRANCH
    git pull origin $BRANCH
else
    echo "📥 Git Clone..."
    git clone https://github.com/stud20/video-reference-project.git        
    cd /app/video-reference-project
    git checkout $BRANCH
fi

# Streamlit 실행
echo "🚀 Starting Streamlit on branch: $BRANCH"
streamlit run app.py --server.port=8501 --server.address=0.0.0.0
EOF

# 실행 권한 부여
chmod +x /app/start.sh
```

## 4. 확인
```bash
# 변경사항 확인
cat /app/start.sh | grep BRANCH

# 컨테이너 나가기
exit
```

## 5. 컨테이너 재시작 (SSH 세션에서)
```bash
docker restart sense-of-frame-dev
```

## 6. 로그 확인
```bash
docker logs -f sense-of-frame-dev
```

이제 컨테이너가 재시작될 때마다 자동으로 develop 브랜치에서 코드를 가져옵니다.