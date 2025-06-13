# 🎥 AI 기반 광고 영상 콘텐츠 추론 시스템

## 📋 프로젝트 개요

본 프로젝트는 광고 영상의 레퍼런스를 AI를 활용해 분석하고, 내용과 배경, 장르 및 표현 방식을 추론하는 시스템입니다.

### 주요 기능
- YouTube/Vimeo 영상 다운로드 및 메타데이터 추출
- 영상 장면 분석 및 텍스트 추출
- AI 기반 콘텐츠 추론
- WebDAV를 통한 NAS 저장
- Streamlit 기반 웹 인터페이스

## 🚀 시작하기

### 1. 환경 설정

```bash
# 레포지토리 클론
git clone https://github.com/your-username/video-reference-project.git
cd video-reference-project

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env
# .env 파일을 열어 필요한 값 설정
```

### 2. 프로젝트 구조

```
video-reference-project/
├── app.py                  # Streamlit 메인 앱
├── src/                    # 핵심 소스 코드
│   ├── fetcher/           # 영상 다운로드
│   ├── extractor/         # 영상 분석
│   ├── analyzer/          # AI 추론
│   ├── models/            # 데이터 모델
│   └── storage/           # 스토리지 관리
├── utils/                 # 유틸리티
├── config/                # 설정 관리
└── tests/                 # 테스트 코드
```

### 3. 실행 방법

```bash
# Streamlit 앱 실행
streamlit run app.py
```

## 🔧 개발 가이드

### Git 브랜치 전략

```bash
main                    # 안정적인 릴리즈 버전
├── develop            # 개발 통합 브랜치
    ├── feature/xxx    # 기능 개발
    ├── bugfix/xxx     # 버그 수정
    └── hotfix/xxx     # 긴급 수정
```

### 커밋 메시지 규칙

```
feat: 새로운 기능 추가
fix: 버그 수정
docs: 문서 수정
style: 코드 포맷팅
refactor: 코드 리팩토링
test: 테스트 코드
chore: 빌드 업무 수정
```

### 개발 워크플로우

1. 새 기능 개발 시
```bash
git checkout develop
git pull origin develop
git checkout -b feature/새기능명
# 개발 진행
git add .
git commit -m "feat: 새기능 설명"
git push origin feature/새기능명
# GitHub에서 Pull Request 생성
```

2. 테스트 실행
```bash
pytest tests/
```

## 🤝 기여 방법

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'feat: Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 라이센스

This project is licensed under the MIT License.

## 👥 개발자

- 김윤섭 (C65028) - 인공지능버추얼콘텐츠전공

## 📚 참고 문헌

1. Vora, D., et al. (2025). AI-driven video summarization for optimizing content retrieval...
2. Zhang, Z., et al. (2022). Movie genre classification by language augmentation...
3. Solanki, L., & Rajasekaran, R. S. (2022). Automatic generation of video metadata...