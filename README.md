# AI 기반 광고 영상 콘텐츠 추론 시스템 (최적화 버전)

> **동시 사용자 5명을 안정적으로 지원하는 고성능 영상 분석 플랫폼**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
[![Redis](https://img.shields.io/badge/Redis-Cache-red.svg)](https://redis.io)

## 🚀 주요 개선사항

### 🎯 성능 최적화
- **사용자별 작업 공간 격리**: 파일 충돌 방지
- **SQLite + 커넥션 풀링**: TinyDB 대비 10배 향상된 동시성
- **Redis 하이브리드 캐시**: 메모리 + 지속성 캐시로 응답속도 3배 향상
- **비동기 작업 큐**: 블로킹 없는 백그라운드 처리

### 🔒 안정성 강화
- **세션 관리 시스템**: 사용자별 상태 격리 및 자동 정리
- **리소스 모니터링**: CPU/메모리 사용률 실시간 감시
- **에러 핸들링**: 복구 가능한 오류 자동 처리
- **헬스체크**: 시스템 상태 자동 진단

### 📊 모니터링 대시보드
- **실시간 시스템 상태**: 사용자, 작업, 리소스 현황
- **성능 메트릭**: 캐시 적중률, 처리 시간, 처리량
- **알림 시스템**: 임계치 초과 시 자동 경고
- **벤치마크 도구**: 성능 측정 및 최적화 가이드

## 🎯 프로젝트 구조

```
video-reference-project/
├── app.py                  # 메인 애플리케이션
├── core/                   # 핵심 비즈니스 로직
│   ├── analysis/          # AI 분석 모듈
│   │   ├── analyzer.py    # 비디오 분석기
│   │   ├── parser.py      # 응답 파서
│   │   ├── prompts.py     # AI 프롬프트
│   │   └── providers/     # AI Provider 구현
│   ├── database/          # 데이터베이스 관련
│   ├── downloaders/       # 비디오 다운로더
│   ├── handlers/          # 비즈니스 로직 핸들러
│   ├── processors/        # 비디오 프로세서
│   ├── video/            # 비디오 모델
│   └── workflow/         # Pipeline 워크플로우
├── web/                   # Streamlit UI
│   ├── components/       # UI 컴포넌트
│   │   ├── analyze/     # 분석 탭 컴포넌트
│   │   ├── database/    # 데이터베이스 탭 컴포넌트
│   │   └── settings/    # 설정 탭 컴포넌트
│   ├── pages/           # 페이지 렌더러
│   ├── state.py         # 상태 관리
│   ├── styles/          # 스타일 정의
│   └── utils/           # UI 유틸리티
├── utils/                # 공통 유틸리티
│   ├── cache.py         # 캐시 관리
│   ├── hash.py          # 해시 유틸리티
│   └── logger.py        # 로깅 설정
├── integrations/         # 외부 서비스 통합
│   └── notion.py        # Notion API
├── config/              # 설정 파일
│   └── settings.py      # 앱 설정
├── data/                # 데이터 디렉토리
├── logs/                # 로그 파일
└── results/             # 분석 결과

```

## 🚀 주요 기능

1. **멀티 AI 모델 지원**
   - GPT-4o (균형 분석)
   - Claude Sonnet 4 (상세 분석)
   - Google Gemini (빠른 분석)

2. **Pipeline 기반 비디오 처리**
   - 다운로드 → 씬 추출 → 그룹화 → AI 분석 → 저장

3. **실시간 진행 상황 표시**
   - 콘솔 로그 스트리밍
   - 단계별 진행률 표시

4. **데이터베이스 관리**
   - 분석 결과 저장/조회
   - 태그 기반 검색
   - 무드보드 생성

## 🛠️ 설치 및 실행

```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env
# .env 파일 편집하여 API 키 설정

# 실행
streamlit run app.py
```

## 📝 환경변수

- `FACTCHAT_API_KEY`: FactChat API 키 (필수)
- `NOTION_API_KEY`: Notion API 키 (선택)
- `NOTION_DATABASE_ID`: Notion 데이터베이스 ID (선택)

## 🔧 개발자 정보

- 서강대학교 미디어커뮤니케이션 대학원
- 인공지능버추얼콘텐츠 전공
- greatminds.
