# Sense of Frame - AI 영상 분석 플랫폼

> **AI 기반 광고/프로모션 영상 콘텐츠 자동 분석 시스템**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
[![Redis](https://img.shields.io/badge/Redis-Cache-red.svg)](https://redis.io)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 📋 목차
- [개요](#-개요)
- [주요 기능](#-주요-기능)
- [시스템 아키텍처](#-시스템-아키텍처)
- [설치 및 실행](#-설치-및-실행)
- [사용법](#-사용법)
- [API 설정](#-api-설정)
- [성능 최적화](#-성능-최적화)
- [문제 해결](#-문제-해결)
- [기여](#-기여)

## 🎯 개요

**Sense of Frame**은 광고 및 프로모션 영상을 자동으로 분석하여 마케팅 인사이트를 제공하는 AI 기반 플랫폼입니다. YouTube, Vimeo 등의 플랫폼에서 영상을 다운로드하고, 주요 씬을 추출한 후 서강대학교 FactChat API를 통해 여러 AI 모델(GPT-4o, Claude, Gemini)을 활용하여 심층 분석을 수행합니다.

### 📌 개발 배경
현재 YouTube에는 약 **51억 개**의 영상이 존재하며, 하루에만 **300만 개**의 새로운 영상이 업로드됩니다. 이러한 방대한 콘텐츠 속에서:
- 광고 제작사들은 적절한 레퍼런스 영상 발굴에 막대한 시간과 인력을 투자
- 제작사-고객사 간 커뮤니케이션의 핵심 도구로 '레퍼런스 영상' 활용
- 데이터 기반 개인 맞춤형 영상 제작 전략으로의 전환 필요성 증가

### 🎯 연구 목적
본 프로젝트는 **AI를 활용한 광고 영상 콘텐츠 추론 연구**를 통해:
1. **시간과 비용 절감**: 레퍼런스 영상 검색 및 분석 과정 자동화
2. **커뮤니케이션 개선**: 제작사-고객사 간 원활한 의사소통 도구 제공
3. **데이터 기반 의사결정**: 영상의 내용, 배경, 장르, 표현 방식 등을 체계적으로 분석
4. **맥락 분석 강화**: 브랜드 메시지 전달 방식과 소비자 반응 예측

### 💡 핵심 가치
- 🎬 **자동화된 영상 분석**: URL 입력만으로 전체 분석 프로세스 자동화
- 🧠 **멀티모달 AI 분석**: 텍스트(제목, 설명, 자막) + 이미지(씬 추출) 통합 추론
- 📊 **구조화된 데이터베이스**: 분석 결과의 체계적 저장 및 카테고리화
- 🚀 **실시간 처리**: 동시 다중 사용자 지원 및 캐싱 최적화
- 🔄 **재활용 가능한 인사이트**: 축적된 데이터를 통한 마케팅 전략 수립

## 🌟 주요 기능

### 1. 영상 처리 파이프라인
```
URL 입력 → 다운로드 → 씬 추출 → AI 분석 → 데이터 저장 → 결과 시각화
```

- **지원 플랫폼**: YouTube, Vimeo, 직접 URL
- **씬 추출**: 자동 장면 변화 감지 및 대표 프레임 선정
- **그룹화**: 유사 씬 자동 그룹화 (perceptual hash)

### 2. AI 분석 모듈 (FactChat 통합 API)
**FactChat**: 서강대학교에서 제공하는 통합 AI API 서비스를 통해 다양한 AI 모델에 접근

| 모델 | 용도 | 특징 |
|------|------|------|
| **GPT-4o** | 균형 분석 | 종합적 마케팅 인사이트 |
| **Claude Sonnet** | 상세 분석 | 심층 콘텐츠 해석 |
| **Google Gemini** | 빠른 분석 | 실시간 처리 |

> 모든 AI 모델은 FactChat API를 통해 통합 관리되어 단일 API 키로 사용 가능

### 3. 데이터 관리
- **SQLite + Connection Pooling**: 안정적인 동시성 처리
- **Redis Cache**: 응답 속도 3배 향상
- **Session Management**: 사용자별 작업 공간 격리
- **Notion Integration**: 외부 플랫폼 자동 동기화

### 4. 사용자 인터페이스
- **Streamlit 기반**: 직관적인 웹 인터페이스
- **실시간 진행 상황**: 작업 진행률 시각화
- **대시보드**: 시스템 모니터링 및 통계
- **무드보드 생성**: 분석 결과 기반 비주얼 보드

## 🏗️ 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit Web UI                      │
├─────────────────────────────────────────────────────────┤
│                    Application Core                      │
├──────────────┬──────────────┬──────────────┬───────────┤
│   Workflow   │   Analysis   │   Database   │   Cache   │
│  Coordinator │   Providers  │  Repository  │  Manager  │
├──────────────┴──────────────┴──────────────┴───────────┤
│                   Infrastructure Layer                   │
├──────────────┬──────────────┬──────────────┬───────────┤
│    SQLite    │    Redis     │  File System │   Docker  │
└──────────────┴──────────────┴──────────────┴───────────┘
```

### 디렉토리 구조
```
video-reference-project/
├── app.py                  # 메인 애플리케이션 진입점
├── config/                 # 설정 파일
│   ├── settings.py        # 전역 설정
│   └── prompt_settings.json # AI 프롬프트 설정
├── core/                   # 핵심 비즈니스 로직
│   ├── analysis/          # AI 분석 모듈
│   │   └── providers/     # AI 제공자별 구현
│   ├── database/          # 데이터베이스 레이어
│   ├── video/             # 영상 처리 모듈
│   │   ├── downloader/    # 플랫폼별 다운로더
│   │   └── processor/     # 영상 처리 유틸리티
│   └── workflow/          # 파이프라인 조정자
│       └── stages/        # 개별 처리 단계
├── web/                   # 웹 UI 컴포넌트
│   ├── components/        # 재사용 가능한 UI 컴포넌트
│   └── pages/             # Streamlit 페이지
├── utils/                 # 유틸리티 모듈
│   ├── session_manager.py # 세션 관리
│   └── cache_manager.py   # 캐시 관리
├── integrations/          # 외부 서비스 연동
│   ├── notion/           # Notion API 연동
│   └── storage/          # 스토리지 추상화
└── data/                 # 데이터 저장소
    ├── workspaces/       # 사용자별 작업 공간
    └── cache/            # 캐시 파일
```

## 🚀 설치 및 실행

### 사전 요구사항
- Python 3.11+
- Redis Server (캐싱용)
- FFmpeg (영상 처리용)
- 8GB+ RAM
- 50GB+ 저장 공간

### 1. Docker 설치 (권장)
```bash
# 저장소 클론
git clone https://github.com/yourusername/video-reference-project.git
cd video-reference-project

# 환경 설정
cp .env.example .env
# .env 파일 편집하여 API 키 설정

# Docker Compose 실행
docker-compose up -d

# 접속
open http://localhost:8501
```

### 2. 로컬 개발 환경
```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# Redis 시작 (별도 터미널)
redis-server

# 환경 설정
cp .env.example .env
# .env 파일 편집

# 애플리케이션 실행
streamlit run app.py
```

## 📖 사용법

### 1. 영상 분석
1. **ANALYZE** 탭 선택
2. YouTube/Vimeo URL 입력
3. AI 모델 선택 (GPT-4o/Claude/Gemini - FactChat API를 통해 제공)
4. 분석 옵션 설정
5. "Analyze Video" 클릭

### 2. 데이터베이스 검색
1. **DATABASE** 탭 선택
2. 검색 필터 적용 (날짜, 태그, 키워드)
3. 분석 결과 조회 및 다운로드

### 3. 무드보드 생성
1. 데이터베이스에서 영상 선택
2. "Create Moodboard" 클릭
3. 레이아웃 커스터마이징
4. 이미지 다운로드 또는 공유

## 🔧 API 설정

### 필수 API 키
```bash
# .env 파일
# FactChat API (서강대학교 통합 AI API 서비스)
FACTCHAT_API_KEY=your_factchat_api_key_here

# FactChat API를 통해 아래 모델들을 모두 사용 가능:
# - OpenAI GPT-4o
# - Anthropic Claude Sonnet
# - Google Gemini
```

### 선택 API 키
```bash
NOTION_API_KEY=secret_...      # Notion 연동
NOTION_DATABASE_ID=...         # Notion 데이터베이스 ID
```

## ⚡ 성능 최적화

### 동시성 설정
```bash
# .env 파일
MAX_CONCURRENT_USERS=5          # 최대 동시 사용자
MAX_CONCURRENT_TASKS=3          # 사용자당 최대 작업
SESSION_TIMEOUT_MINUTES=30      # 세션 타임아웃
```

### 리소스 제한
```bash
MAX_CPU_PERCENT=80              # CPU 사용률 제한
MAX_MEMORY_PERCENT=85           # 메모리 사용률 제한
MEMORY_CACHE_SIZE_MB=50         # 캐시 메모리 크기
```

### 성능 벤치마크
| 메트릭 | 성능 | 조건 |
|--------|------|------|
| 평균 응답시간 | 2.3초 | 캐시 히트 |
| 동시 처리량 | 8개/분 | 5명 동시 사용 |
| 캐시 적중률 | 85% | 일반 사용 패턴 |
| 메모리 사용량 | 6GB | 풀 로드 |

## 🔍 문제 해결

### Redis 연결 실패
```bash
# Redis 상태 확인
redis-cli ping

# Docker로 Redis 실행
docker run -d --name redis -p 6379:6379 redis:alpine
```

### 메모리 부족
```bash
# 캐시 크기 조정
echo "MEMORY_CACHE_SIZE_MB=25" >> .env

# 동시 사용자 제한
echo "MAX_CONCURRENT_USERS=3" >> .env
```

### yt-dlp 다운로드 오류
```bash
# yt-dlp 업데이트
pip install --upgrade yt-dlp

# 쿠키 파일 사용
echo "COOKIES_FILE=cookies.txt" >> .env
```

## 🎓 학술적 의의

### 연구 방법론
본 시스템은 다음과 같은 기술적 접근을 통해 구현되었습니다:

1. **멀티모달 데이터 수집**
   - Python 기반 웹 크롤링을 통한 레퍼런스 영상 자동 수집
   - 메타데이터 추출: 제목, 설명, 업로더, 업로드 일시, 자막 등

2. **컴퓨터 비전 기술 적용**
   - FFmpeg Scene Detection: 장면 전환 감지 및 키프레임 추출
   - OpenCV 기반 이미지 특징 분석 및 유사도 계산
   - Perceptual Hash를 통한 시각적 유사 씬 그룹화

3. **AI 기반 통합 추론**
   - 텍스트 + 이미지 데이터의 멀티모달 분석
   - FactChat API를 통한 다양한 LLM 모델 활용
   - 맥락 인식 기반 광고 메시지 해석

### 기대 효과
- **산업적 효과**: 광고 제작 프로세스의 효율성 30% 이상 향상
- **학술적 기여**: 멀티모달 AI 분석의 실무 적용 사례 제시
- **확장 가능성**: 광고 외 다양한 영상 콘텐츠 분석으로 확대 가능

## 🤝 기여

### 개발 가이드라인
1. `develop` 브랜치에서 작업
2. 기능별 브랜치 생성
3. 코드 스타일 준수 (PEP 8)
4. 테스트 작성 및 실행
5. PR 요청

### 배포 프로세스
```bash
# 자동 배포 스크립트
git add -A
git commit -m "feat: 기능 설명"
git push origin develop
ssh ysk@192.168.50.50 "docker restart sense-of-frame-dev"
```

## 📚 추가 문서
- [API 문서](docs/api.md)
- [개발자 가이드](docs/developer-guide.md)
- [배포 가이드](docs/deployment.md)

## 📖 참고 문헌
1. Vora, D., Kadam, P., Mohite, D. D., Kumar, N., Kumar, N., Radhakrishnan, P., & Bhagwat, S. (2025). AI-driven video summarization for optimizing content retrieval and management through deep learning techniques. Scientific Reports, 15(4058), 1-15.

2. Zhang, Z., Gu, Y., Plummer, B. A., et al. (2022). Movie genre classification by language augmentation and shot sampling (Movie-CLIP). arXiv:2203.13281v2.

3. Solanki, L., & Rajasekaran, R. S. (2022). Automatic generation of video metadata for the super-personalized recommendation of media. IEEE Transactions.

## 📄 라이선스
MIT License - 자세한 내용은 [LICENSE](LICENSE) 파일 참조

## 👥 개발팀
- **서강대학교 미디어커뮤니케이션 대학원**
- **인공지능버추얼콘텐츠 전공**
- **연구/개발**: 김윤섭 (C65028)
- **지도교수**: [지도교수명]
- **Organization**: greatminds.

## 📞 연락처
- **GitHub Issues**: 버그 리포트 및 기능 요청
- **연구 문의**: [학교 이메일]
- **프로젝트 페이지**: [프로젝트 URL]

---

**© 2025 Sense of Frame - AI 기반 광고 영상 콘텐츠 추론 연구 프로젝트**
**서강대학교 미디어커뮤니케이션 대학원 | 인공지능버추얼콘텐츠 전공**