# AI 기반 광고 영상 콘텐츠 추론 시스템

## 🎥 프로젝트 소개

YouTube와 Vimeo의 광고 영상을 자동으로 분석하여 장르, 특징, 타겟 고객층 등을 AI로 추론하는 시스템입니다. 영상 제작자와 마케터를 위한 레퍼런스 데이터베이스 구축을 목표로 합니다.

### 주요 특징
- 🤖 **GPT-4 Vision API**를 활용한 영상 콘텐츠 자동 분석
- 📊 **메타데이터 활용**: YouTube 태그, 조회수, 채널 정보를 분석에 반영
- 💾 **통합 데이터베이스**: TinyDB 기반 분석 결과 저장 및 검색
- 📝 **Notion 연동**: 분석 결과를 Notion 페이지에 자동 업로드
- 🎬 **macOS 최적화**: VP9 등 재생 불가 코덱 자동 H.264 변환

## 🚀 주요 기능

### 1. 영상 다운로드 및 분석
- YouTube, Vimeo URL 입력만으로 자동 다운로드
- 영상에서 대표 씬 자동 추출
- GPT-4 Vision으로 시각적 특징 분석

### 2. AI 분석 항목
- **장르 분류**: TVC, 브랜드필름, 바이럴영상 등 16개 카테고리
- **표현 형식**: 실사, 2D/3D 애니메이션, 모션그래픽 등
- **분위기 및 톤**: 영상의 전반적인 무드 분석
- **타겟 고객층**: 예상 시청 대상 분석
- **특징 추출**: 색감, 편집, 카메라워크 등 상세 분석
- **자동 태그 생성**: 검색 가능한 키워드 자동 생성

### 3. 데이터베이스 관리
- 분석된 영상 검색 및 필터링
- 장르별, 태그별 분류
- 일괄 내보내기/가져오기
- 분석 결과 수정 및 재분석

### 4. Notion 통합
- 분석 결과를 Notion 페이지에 자동 포맷팅
- 썸네일, 메타데이터, AI 분석 내용 구조화
- 일괄 업로드 지원

## 📋 시스템 요구사항

- Python 3.8 이상
- macOS, Linux, Windows
- FFmpeg (영상 처리용)
- 최소 4GB RAM
- OpenAI API 키 (GPT-4 Vision 접근 권한 필요)

a
# 프로젝트 디렉토리 구조 (현재 실제 구조)

```
video-reference-project/
│
├── app.py                          # 메인 Streamlit 애플리케이션 (Sense of Frame)
├── requirements.txt                # Python 의존성 패키지
├── README.md                       # 프로젝트 문서
├── .gitignore                      # Git 제외 파일 목록
├── .env                           # 환경변수 파일 (git ignore)
├── .env.example                   # 환경변수 템플릿 (작성 예정)
│
├── config/                        # 설정 관련
│   ├── __init__.py
│   ├── settings.py               # 전역 설정 관리
│   └── prompt_settings.json      # AI 프롬프트 설정 (런타임 생성)
│
├── src/                          # 소스 코드
│   ├── __init__.py
│   │
│   ├── analyzer/                 # AI 분석 모듈
│   │   ├── __init__.py
│   │   └── ai_analyzer.py       # GPT-4 Vision 분석기
│   │
│   ├── database/                 # 데이터베이스 관련
│   │   ├── __init__.py
│   │   └── tiny_db.py           # TinyDB 래퍼
│   │
│   ├── extractor/               # 씬 추출 모듈
│   │   ├── __init__.py
│   │   └── scene_extractor.py   # 씬 추출 및 그룹화
│   │
│   ├── fetcher/                 # 영상 다운로드 모듈
│   │   ├── __init__.py
│   │   ├── base.py             # 추상 기본 클래스
│   │   ├── download_options.py  # yt-dlp 옵션 설정
│   │   ├── video_processor.py   # 코덱 변환 처리
│   │   ├── vimeo.py            # Vimeo 다운로더
│   │   └── youtube.py          # YouTube 다운로더
│   │
│   ├── handlers/                # 비즈니스 로직 핸들러
│   │   ├── __init__.py
│   │   ├── db_handler.py        # DB 작업 핸들러
│   │   └── enhanced_video_handler.py  # 향상된 영상 처리
│   │
│   ├── models/                  # 데이터 모델
│   │   ├── __init__.py
│   │   └── video.py            # Video, Scene, VideoMetadata 클래스
│   │
│   ├── services/               # 외부 서비스 연동
│   │   ├── __init__.py
│   │   ├── notion_service.py   # Notion API 서비스
│   │   └── video_service.py    # 메인 비디오 서비스
│   │
│   ├── storage/                # 스토리지 관련
│   │   ├── __init__.py
│   │   ├── db_manager.py       # TinyDB 관리자
│   │   ├── local_storage.py    # 로컬 스토리지
│   │   ├── sftp_client.py      # SFTP 클라이언트
│   │   └── storage_manager.py  # 통합 스토리지 관리자
│   │
│   └── ui/                     # UI 컴포넌트
│       ├── __init__.py
│       ├── styles.py           # 향상된 CSS 스타일
│       ├── components/         # 재사용 가능한 UI 컴포넌트
│       │   ├── __init__.py
│       │   ├── analysis_display.py  # 분석 결과 표시
│       │   ├── database_modal.py    # DB 관리 모달
│       │   ├── sidebar.py           # 사이드바
│       │   └── video_cards.py       # 영상 카드 UI
│       └── tabs/               # 메인 탭 컴포넌트들
│           ├── __init__.py
│           ├── analyze_tab.py       # ANALYZE 탭 메인
│           ├── analyze_result.py    # 분석 결과 표시
│           ├── analyze_function.py  # 분석 기능 (모달 등)
│           ├── analyze_function_sens.py  # 정밀도 설정
│           ├── database_tab.py      # DATABASE 탭 메인
│           ├── database_video_card.py    # DB 영상 카드
│           ├── database_edit.py     # DB 편집 기능
│           ├── database_delete.py   # DB 삭제 기능
│           ├── settings_tab.py      # SETTINGS 탭 메인
│           ├── settings_cache.py    # 캐시 관리 설정
│           ├── settings_prompt.py   # AI 프롬프트 설정
│           ├── settings_precision.py # 정밀도 설정
│           └── settings_notion.py   # Notion 연동 설정
│
├── tests/                      # 테스트 코드
│   └── __init__.py
│
└── utils/                      # 유틸리티
    ├── __init__.py
    ├── constants.py            # 상수 정의 (장르, 표현형식 등)
    ├── logger.py              # 로깅 설정
    └── session_state.py       # Streamlit 세션 관리


 
```


### FFmpeg 설치
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt update
sudo apt install ffmpeg

# Windows
# https://ffmpeg.org/download.html 에서 다운로드
```

## 🛠️ 설치 및 실행

### 1. 저장소 클론
```bash
git clone https://github.com/yourusername/video-content-analyzer.git
cd video-content-analyzer
```

### 2. 가상환경 생성 및 활성화
```bash
# 가상환경 생성
python -m venv venv

# 활성화 (macOS/Linux)
source venv/bin/activate

# 활성화 (Windows)
venv\Scripts\activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 환경변수 설정
```bash
# .env.example을 복사하여 .env 생성
cp .env.example .env

# .env 파일을 편집하여 API 키 입력
# 필수: OPENAI_API_KEY
# 선택: NOTION_API_KEY, NOTION_PARENT_PAGE_ID
```

### 5. 실행
```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 접속



## 🤖 AI 분석 프롬프트 구조

### 📋 시스템 프롬프트

```plaintext
당신은 광고 영상 전문 분석가입니다. 주어진 이미지들과 메타데이터를 종합적으로 분석하여 
영상의 장르, 특징, 타겟 등을 상세히 분석해주세요. 메타데이터는 참고용이며, 
실제 이미지 내용을 우선시하여 분석해주세요.
```

### 📝 7가지 분석 항목


| **영상 장르** | 16개 장르 중 1개 선택
| **장르 판단 이유** | 시각적 특징, 연출 스타일 등 종합 분석
| **특징 및 특이사항** | 색감, 편집, 카메라워크, 메시지 등
| **관련 태그** | 검색 가능한 키워드
| **표현형식** | 2D/3D/실사/혼합형 등
| **분위기와 톤** | 전반적인 무드 설명
| **타겟 고객층** | 예상 시청 대상

### 🎯 장르 분류 체계


애니메이션, 광고/마케팅, 콘텐츠, 기타
2D애니메이션, 스팟광고, VLOG, 인터뷰
3D애니메이션, TVC, 유튜브콘텐츠, 다큐멘터리
모션그래픽, 브랜드필름, 웹드라마, 이벤트영상
바이럴영상, 뮤직비디오, 교육콘텐츠
제품소개


### ⚙️ 프롬프트 커스터마이징

#### 🎨 SETTINGS > AI 프롬프트에서 설정 가능

🔧 커스터마이징 가능 항목

##### 1. **시스템 프롬프트**
- AI의 역할 정의
- 분석 관점 설정
- 전문 분야 지정

##### 2. **분석 지침**
- 메타데이터 가중치
- 우선순위 설정
- 출력 상세도

##### 3. **장르 목록**
- 기본 16개 장르 수정
- 새로운 장르 추가
- 산업별 특화 장르

##### 4. **표현형식**
- 2D, 3D, 실사, 혼합형
- 스톱모션, 타이포그래피
- 커스텀 형식 추가

##### 5. **분석 항목**
- 항목 순서 변경
- 제목/설명 수정
- 새 항목 추가/제거

### 💡 프롬프트 예시

```yaml
영상 메타데이터:
제목: [NIKE] Just Do It - 2024 Campaign
업로더/채널: Nike Korea
영상 길이: 1분 30초
조회수: 1,234,567회
YouTube 태그: 나이키, 운동화, 스포츠, 광고, 캠페인

영상 설명:
나이키의 2024년 글로벌 캠페인 'Just Do It'의 한국 버전입니다...

위 영상에서 추출한 10개의 이미지를 분석해주세요.
첫 번째 이미지는 썸네일이며, 나머지는 영상의 대표 장면들입니다.

제공된 메타데이터(제목, 설명, 태그 등)를 참고하여 더 정확한 분석을 수행하되,
실제 이미지 내용이 메타데이터와 다를 경우 이미지 내용을 우선시해주세요.

다음 7개 항목을 모두 작성해주세요. 각 항목은 빈 줄로 구분하여 명확히 구분해주세요.

분석 항목:
A1. 영상 장르 (다음 중 하나만 선택): 2D애니메이션, 3D애니메이션, ...
A2. 장르 판단 이유 (시각적 특징, 연출 스타일, 정보 전달 방식, 메타데이터 등을 종합하여 200자 이상 상세히 설명)
...
```



## 📖 사용 가이드

### 기본 워크플로우
1. **영상 URL 입력**: YouTube 또는 Vimeo 링크 입력
2. **분석 시작**: 자동으로 다운로드 → 씬 추출 → AI 분석 진행
3. **결과 확인**: 장르, 특징, 태그 등 분석 결과 확인
4. **데이터베이스 저장**: 자동으로 로컬 DB에 저장
5. **Notion 업로드** (선택): 분석 결과를 Notion에 업로드

### 데이터베이스 관리
- 사이드바의 "🗂️ 데이터베이스 관리자" 버튼 클릭
- 필터링: 장르별, 분석 상태별, 최근 7일 등
- 검색: 제목, 업로더, 태그로 검색
- 일괄 작업: 선택한 영상들 내보내기, 재분석, Notion 업로드

### 품질 설정
`.env` 파일에서 조절 가능:
- `VIDEO_QUALITY`: 다운로드 품질 (best/balanced/fast)
- `MAX_ANALYSIS_IMAGES`: AI 분석에 사용할 이미지 수
- `ANALYSIS_IMAGE_QUALITY`: 분석 이미지 품질 (low/high)

## 🗺️ 로드맵

### 계획 중
- [ ] 🎚️ **정밀도 레벨 시스템**: 1-10 레벨로 씬 추출 정밀도 조절
- [ ] 🎵 **오디오 분석**: 웨이브폼 분석을 통한 추가 추론
- [ ] 📝 **OCR 텍스트 검출**: 영상 내 텍스트 추출 및 분석
- [ ] 🖥️ **로컬 AI 모델**: API 없이 로컬에서 실행 가능한 모델 지원
- [ ] 🌐 **다국어 지원**: 분석 결과 다국어 번역

## 👨‍💻 개발자

- 서강대학교 미디어커뮤니케이션대학원 인공지능버추얼콘텐츠전공 김윤섭

