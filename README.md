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

