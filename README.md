# Video Reference Analysis System 🎬

> AI 기반 영상 레퍼런스 분석 및 메타데이터 추론 시스템

## 📋 프로젝트 개요

### 시스템 정의
본 프로젝트는 광고, 브랜디드 콘텐츠, 다큐멘터리 영상의 레퍼런스를 AI를 활용해 자동으로 분석하고, 내용과 배경, 장르 및 표현 방식을 추론하는 통합 시스템입니다.

### 핵심 가치
- **자동화**: 수동 분석 작업을 AI로 대체하여 제작 시간 단축
- **체계화**: 비정형 영상 데이터를 구조화된 메타데이터로 변환
- **확장성**: 모듈화된 설계로 다양한 워크플로우에 통합 가능

### 타겟 사용자
- 영상 프로덕션 제작팀
- 크리에이티브 디렉터
- 콘텐츠 아카이빙 담당자
- 영상 레퍼런스 리서처

## 🎯 주요 기능

### 1. 영상 수집 및 다운로드
- **지원 플랫폼**: YouTube, Vimeo, 직접 업로드
- **메타데이터 추출**: 제목, 설명, 태그, 업로드 날짜, 조회수
- **자동 품질 선택**: 분석에 최적화된 해상도 자동 선택

### 2. 씬 분석 및 추출
- **정밀도 레벨 시스템**: 1-10단계 조절 가능
  - 레벨 1-3: 빠른 분석 (30초-3분)
  - 레벨 4-6: 균형잡힌 분석 (3-8분) ⭐ 권장
  - 레벨 7-10: 정밀 분석 (8-30분)
- **적응적 씬 추출**: 영상 길이와 복잡도에 따른 자동 조절
- **시각적 다양성 보장**: 중복 제거 및 시간적 분산

### 3. AI 기반 콘텐츠 추론
- **GPT-4 Vision API**: 시각적 내용 분석
- **다차원 분석**:
  - 장르 및 스타일 분류
  - 시각적 표현 기법 분석
  - 내러티브 구조 파악
  - 색상 및 톤 분석
  - 촬영 기법 추론

### 4. 데이터 저장 및 관리
- **다중 스토리지 지원**:
  - SFTP (Synology NAS)
  - WebDAV
  - Local Storage
- **메타데이터 DB**: TinyDB 기반 로컬 저장
- **자동 백업**: 일일 백업 시스템

### 5. 웹 인터페이스
- **Streamlit 기반**: 직관적 UI/UX
- **실시간 진행 상황**: 분석 프로세스 시각화
- **결과 대시보드**: 분석 결과 즉시 확인

## 🛠️ 기술 스택

### 백엔드
- **언어**: Python 3.8+
- **프레임워크**: Streamlit
- **영상 처리**: 
  - OpenCV (씬 감지)
  - ffmpeg (영상 변환)
  - yt-dlp (다운로드)
- **AI/ML**:
  - OpenAI GPT-4 Vision API
  - scikit-learn (클러스터링)
  - imagehash (중복 제거)

### 저장소
- **파일 시스템**: SFTP/WebDAV
- **데이터베이스**: TinyDB (JSON 기반)
- **캐시**: 로컬 임시 저장소

## 📁 프로젝트 구조

```
video-reference-project/
├── app.py                    # Streamlit 메인 애플리케이션
├── src/                      # 핵심 소스 코드
│   ├── fetcher/             # 영상 다운로드 모듈
│   │   ├── youtube.py       # YouTube 다운로더
│   │   ├── vimeo.py         # Vimeo 다운로더
│   │   └── base.py          # 기본 인터페이스
│   ├── extractor/           # 영상 분석 모듈
│   │   ├── scene_detector.py    # 씬 감지
│   │   ├── frame_extractor.py   # 프레임 추출
│   │   └── feature_extractor.py # 특징 추출
│   ├── analyzer/            # AI 추론 모듈
│   │   ├── gpt_analyzer.py      # GPT-4 Vision 분석
│   │   ├── prompt_builder.py    # 프롬프트 생성└── video-reference-project
    ├── __pycache__
    │   └── uploader.cpython-311.pyc
    ├── app.py
    ├── check_openai_api.py
    ├── config
    │   ├── __init__.py
    │   ├── __pycache__
    │   │   ├── __init__.cpython-311.pyc
    │   │   └── settings.cpython-311.pyc
    │   └── settings.py
    ├── create_init_files.sh
    ├── data
    ├── debug_synology_detailed.py
    ├── debug_webdav.py
    ├── enhanced_synology_debug.py
    ├── fix_imports.py
    ├── fix_synology_error_119.py
    ├── logs
    ├── README.md
    ├── requirements.txt
    ├── results
    ├── src
    │   ├── __init__.py
    │   ├── __pycache__
    │   │   └── __init__.cpython-311.pyc
    │   ├── analyzer
    │   │   ├── __init__.py
    │   │   ├── __pycache__
    │   │   │   ├── __init__.cpython-311.pyc
    │   │   │   └── ai_analyzer.cpython-311.pyc
    │   │   └── ai_analyzer.py
    │   ├── database
    │   │   └── tiny_db.py
    │   ├── extractor
    │   │   ├── __init__.py
    │   │   ├── __pycache__
    │   │   │   ├── __init__.cpython-311.pyc
    │   │   │   └── scene_extractor.cpython-311.pyc
    │   │   └── scene_extractor.py
    │   ├── fetcher
    │   │   ├── __init__.py
    │   │   ├── __pycache__
    │   │   │   ├── __init__.cpython-311.pyc
    │   │   │   ├── base.cpython-311.pyc
    │   │   │   ├── download_options.cpython-311.pyc
    │   │   │   ├── video_processor.cpython-311.pyc
    │   │   │   ├── vimeo.cpython-311.pyc
    │   │   │   └── youtube.cpython-311.pyc
    │   │   ├── base.py
    │   │   ├── download_options.py
    │   │   ├── video_processor.py
    │   │   ├── vimeo.py
    │   │   └── youtube.py
    │   ├── handlers
    │   │   ├── __init__.py
    │   │   ├── db_handler.py
    │   │   └── video_handler.py
    │   ├── models
    │   │   ├── __init__.py
    │   │   ├── __pycache__
    │   │   │   ├── __init__.cpython-311.pyc
    │   │   │   └── video.cpython-311.pyc
    │   │   └── video.py
    │   ├── services
    │   │   ├── __init__.py
    │   │   ├── __pycache__
    │   │   │   ├── __init__.cpython-311.pyc
    │   │   │   └── video_service.cpython-311.pyc
    │   │   ├── notion_service.py
    │   │   └── video_service.py
    │   ├── storage
    │   │   ├── __init__.py
    │   │   ├── __pycache__
    │   │   │   ├── __init__.cpython-311.pyc
    │   │   │   ├── db_manager.cpython-311.pyc
    │   │   │   ├── local_storage.cpython-311.pyc
    │   │   │   ├── sftp_client.cpython-311.pyc
    │   │   │   ├── storage_manager.cpython-311.pyc
    │   │   │   └── synology_api_client.cpython-311.pyc
    │   │   ├── db_manager.py
    │   │   ├── local_storage.py
    │   │   ├── sftp_client.py
    │   │   ├── storage_manager.py
    │   │   ├── synology_api_client.py
    │   │   └── webdav_client.py
    │   └── ui
    │       ├── __init__.py
    │       ├── components
    │       │   ├── __init__.py
    │       │   ├── analysis_display.py
    │       │   ├── database_modal.py
    │       │   ├── sidebar.py
    │       │   └── video_cards.py
    │       └── styles.py
    ├── temp_tree.txt
    ├── test_webdav.py
    ├── tests
    │   └── __init__.py
    └── utils
        ├── __init__.py
        ├── __pycache__
        │   ├── __init__.cpython-311.pyc
        │   └── logger.cpython-311.pyc
        ├── constants.py
        ├── logger.py
        └── session_state.py

│   │   └── result_parser.py     # 결과 파싱
│   ├── models/              # 데이터 모델
│   │   ├── video.py             # 영상 데이터 모델
│   │   ├── scene.py             # 씬 데이터 모델
│   │   └── analysis.py          # 분석 결과 모델
│   └── storage/             # 스토리지 관리
│       ├── sftp_storage.py      # SFTP 구현
│       ├── webdav_storage.py    # WebDAV 구현
│       └── base_storage.py      # 스토리지 인터페이스
├── utils/                   # 유틸리티
│   ├── logger.py           # 로깅 설정
│   ├── validators.py       # 입력 검증
│   └── helpers.py          # 헬퍼 함수
├── config/                  # 설정 관리
│   ├── settings.py         # 애플리케이션 설정
│   └── constants.py        # 상수 정의
├── tests/                   # 테스트 코드
│   ├── test_fetcher.py
│   ├── test_extractor.py
│   └── test_analyzer.py
├── data/                    # 로컬 데이터
│   ├── video_analysis.json  # 분석 결과 DB
│   └── cache/              # 임시 캐시
├── requirements.txt         # 의존성 목록
├── .env.example            # 환경 변수 예시
├── docker-compose.yml      # Docker 설정
└── README.md               # 프로젝트 문서

```

## 🚀 설치 및 실행

### 사전 요구사항
- Python 3.8 이상
- ffmpeg 설치
- Synology NAS (선택사항)
- OpenAI API 키

### 빠른 시작

```bash
# 1. 저장소 클론
git clone https://github.com/stud20/video-reference-project.git
cd video-reference-project

# 2. 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 환경변수 설정
cp .env.example .env
# .env 파일을 열어 필요한 값 설정

# 5. 애플리케이션 실행
streamlit run app.py
```

### Docker 사용 (권장)

```bash
# Docker Compose로 실행
docker-compose up -d

# 브라우저에서 http://localhost:8501 접속
```

## 🔧 설정 가이드

### 환경 변수 (.env)

```env
# OpenAI 설정
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4-vision-preview

# 스토리지 설정 (택 1)
STORAGE_TYPE=sftp  # sftp, webdav, local

# SFTP 설정 (Synology NAS)
SFTP_HOST=nas.example.com
SFTP_PORT=22
SFTP_USER=username
SFTP_PASS=password
SFTP_BASE_PATH=/dav/videoRef

# 분석 설정
SCENE_PRECISION_LEVEL=5  # 1-10
ANALYSIS_IMAGE_QUALITY=high  # low, high
MAX_ANALYSIS_IMAGES=10

# 데이터베이스
DB_PATH=data/video_analysis.json
DB_BACKUP_ENABLED=true
```

### 정밀도 레벨 설정

| 레벨 | 설명 | 예상 시간 | 출력 이미지 | 사용 시나리오 |
|------|------|-----------|-------------|---------------|
| 1-2 | 초고속 | 30초-2분 | 4개 | 빠른 프리뷰 |
| 3-4 | 빠름 | 2-4분 | 5개 | 일반 분석 |
| 5-6 | 균형 ⭐ | 4-8분 | 6-7개 | 프로덕션 |
| 7-8 | 정밀 | 8-15분 | 8-10개 | 상세 분석 |
| 9-10 | 최고 | 15-30분 | 10개 | 아카이빙 |

## 📊 사용 방법

### 웹 인터페이스 사용

1. **애플리케이션 실행**
   ```bash
   streamlit run app.py
   ```

2. **영상 분석 단계**
   - 영상 URL 입력 (YouTube/Vimeo) 또는 파일 업로드
   - 정밀도 레벨 선택 (1-10, 권장: 5-6)
   - "분석 시작" 버튼 클릭
   - 실시간 진행 상황 확인
   - 분석 결과 확인 및 다운로드

3. **결과 확인**
   - 추출된 주요 씬 이미지
   - AI 분석 내용 (장르, 스타일, 기법)
   - 메타데이터 정보
   - JSON 형식 결과 다운로드

## 🔄 분석 프로세스

```
1. 영상 입력 → 2. 다운로드 및 메타데이터 추출
                          ↓
5. AI 분석 완료 ← 4. GPT-4 Vision 분석 ← 3. 씬 감지 및 추출
       ↓
6. 결과 저장 (SFTP + TinyDB)
```

### 주요 처리 단계
- **씬 감지**: OpenCV 기반 장면 전환 감지
- **중복 제거**: 이미지 해시를 통한 유사 프레임 제거
- **클러스터링**: 시각적 다양성을 위한 씬 그룹화
- **AI 분석**: 선택된 대표 씬들을 GPT-4 Vision으로 분석

## 🤝 개발 참여

이 프로젝트는 개인 연구 프로젝트입니다. 
피드백이나 제안사항은 Issues를 통해 남겨주세요.

### 코드 스타일
- Python PEP 8 준수
- 함수와 클래스에 docstring 작성
- 타입 힌트 사용 권장

## 📈 개발 현황 및 계획

### 현재 구현된 기능
- ✅ YouTube/Vimeo 영상 다운로드
- ✅ 씬 감지 및 추출 (정밀도 레벨 1-10)
- ✅ GPT-4 Vision API 통합
- ✅ Streamlit 웹 인터페이스
- ✅ SFTP 스토리지 연동
- ✅ TinyDB 메타데이터 저장

### 진행 중
- 🔄 Notion 데이터베이스 연동
- 🔄 배치 처리 최적화
- 🔄 에러 핸들링 개선

### 향후 계획
- 🔲 분석 결과 시각화 대시보드
- 🔲 영상 유사도 검색 기능
- 🔲 태그 기반 필터링
- 🔲 분석 템플릿 시스템

## 🐛 문제 해결

### 일반적인 문제

1. **ModuleNotFoundError**
   ```bash
   # 모든 의존성 재설치
   pip install -r requirements.txt
   ```

2. **OpenAI API 오류**
   - API 키가 올바른지 확인
   - 이미지 크기가 너무 크면 `ANALYSIS_IMAGE_QUALITY=low` 설정
   - Rate limit 도달 시 잠시 대기 후 재시도

3. **Synology 연결 실패**
   - SFTP 포트(22) 개방 확인
   - 사용자 권한 확인
   - `/dav/videoRef` 폴더 존재 여부 확인

4. **메모리 부족**
   - 정밀도 레벨 낮추기 (1-3)
   - 동시 처리 영상 수 제한

## 📚 기술 스택 상세

### 핵심 라이브러리
- **yt-dlp**: YouTube/Vimeo 다운로드
- **OpenCV**: 씬 감지 및 영상 처리
- **Streamlit**: 웹 인터페이스
- **OpenAI**: GPT-4 Vision API
- **Paramiko**: SFTP 연결
- **TinyDB**: 로컬 데이터베이스

## 📄 라이선스

This project is licensed under the MIT License.

## 👤 개발자

**Stud20 (슷터드)**
- 서강대학교 미디어커뮤니케이션대학원 AI·버추얼콘텐츠전공
- greatminds 대표/감독
- GitHub: [@stud20](https://github.com/stud20)

---

<p align="center">
  광고·브랜디드 콘텐츠·다큐멘터리 제작을 위한 AI 기반 레퍼런스 분석 시스템
</p>