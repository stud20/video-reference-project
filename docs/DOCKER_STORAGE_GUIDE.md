# Docker 스토리지 설정 가이드

## Windows에서 C:\Users\ysk\Documents\SOF-video 폴더 사용하기

### 1. 원격 서버에 접속
```bash
ssh ysk@192.168.50.50
# 비밀번호: 1212
```

### 2. docker-compose.yml 파일 찾기
```bash
# Docker 컨테이너 정보 확인
docker ps -a | grep sense-of-frame-dev

# docker-compose.yml 위치 찾기
find ~ -name "docker-compose.yml" -type f 2>/dev/null | grep sense-of-frame
```

### 3. docker-compose.yml 수정
```yaml
version: '3.8'

services:
  sense-of-frame-dev:
    # ... 기존 설정 ...
    
    environment:
      # 컨테이너 내부 경로 설정
      - DATA_DIR=/app/data
      - TEMP_DIR=/app/data/temp
      - CACHE_DIR=/app/data/cache
      - WORKSPACES_DIR=/app/data/workspaces
      
    volumes:
      # Windows 경로를 Docker 볼륨으로 마운트
      # 형식: 호스트경로:컨테이너경로
      - /mnt/c/Users/ysk/Documents/SOF-video:/app/data
      
      # 또는 네트워크 드라이브 사용 시
      # - //192.168.x.x/SOF-video:/app/data
```

### 4. Windows 폴더 공유 설정 (필요한 경우)

#### 방법 1: WSL2 사용 시
- Windows 경로는 자동으로 `/mnt/c/`로 마운트됨
- 예: `C:\Users\ysk\Documents\SOF-video` → `/mnt/c/Users/ysk/Documents/SOF-video`

#### 방법 2: 네트워크 공유 사용 시
1. Windows에서 폴더 우클릭 → 속성 → 공유
2. 고급 공유 → 이 폴더 공유 체크
3. 권한 설정에서 읽기/쓰기 권한 부여
4. docker-compose.yml에서 SMB/CIFS 마운트 사용

### 5. .env 파일 설정
```bash
# 원격 서버의 .env 파일 수정
vi .env

# 다음 내용 추가
DATA_DIR=/app/data
TEMP_DIR=/app/data/temp
CACHE_DIR=/app/data/cache
WORKSPACES_DIR=/app/data/workspaces
```

### 6. Docker 컨테이너 재시작
```bash
docker-compose down
docker-compose up -d
```

### 7. 권한 문제 해결 (필요한 경우)
```bash
# 컨테이너 내부에서 권한 확인
docker exec -it sense-of-frame-dev bash
ls -la /app/data

# 필요시 권한 조정
chmod -R 755 /app/data
```

## 주의사항

1. **경로 형식**: Windows 경로를 Linux Docker에서 사용할 때는 적절한 형식으로 변환 필요
   - Windows: `C:\Users\ysk\Documents\SOF-video`
   - WSL2: `/mnt/c/Users/ysk/Documents/SOF-video`
   - 네트워크: `//192.168.x.x/SOF-video`

2. **성능**: 네트워크 마운트는 로컬 디스크보다 느릴 수 있음

3. **백업**: 중요한 데이터는 정기적으로 백업 권장

4. **용량**: Windows 디스크 용량 확인 필요

## 테스트 방법

1. 웹 브라우저에서 애플리케이션 접속
2. 비디오 분석 실행
3. Windows 폴더 확인:
   - `C:\Users\ysk\Documents\SOF-video\temp` - 다운로드된 비디오
   - `C:\Users\ysk\Documents\SOF-video\workspaces` - 사용자별 작업 파일
   - `C:\Users\ysk\Documents\SOF-video\database` - 데이터베이스 파일