"""분석 프롬프트 템플릿 관리"""

from typing import Dict, Any

class AnalysisPromptTemplates:
    """산업별 분석 프롬프트 템플릿 관리 클래스"""
    
    def __init__(self):
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, Dict[str, str]]:
        """산업별 템플릿 로드"""
        return {
            "자동차/모빌리티": {
                "주행감 분석": """자동차 광고용 주행감 분석을 요청합니다.

다음 요소들을 중심으로 분석해주세요:
- 차량의 움직임과 역동성 (가속, 코너링, 브레이킹)
- 도로 환경과 주행 상황 (도심, 고속도로, 산길, 날씨)
- 카메라 앵글과 시점 변화 (내부, 외부, 추적샷, 드론샷)
- 운전자와 승객의 반응 및 표정
- 차량 외관의 디자인 강조 포인트
- 주행 중 발생하는 사운드와 진동감

광고 효과성 관점에서 어떤 감정과 욕구를 자극하는지 분석해주세요.""",

                "안전성 강조": """자동차 안전 기능 분석을 요청합니다.

다음 안전 요소들을 확인해주세요:
- 능동 안전 시스템 (자동 브레이킹, 차선 유지, 사각지대 감지)
- 수동 안전 시스템 (에어백, 차체 구조, 안전벨트)
- 위험 상황 대응 능력 (급제동, 회피 기동)
- 운전자 주의 집중 상태
- 탑승자 보호 기능
- 야간 및 악천후 대응 능력

안전성이 어떻게 시각적으로 전달되는지 분석해주세요.""",

                "디자인 리뷰": """자동차 디자인 중심 분석을 요청합니다.

다음 디자인 요소들을 평가해주세요:
- 외관 디자인 (라인, 비율, 컬러)
- 내부 인테리어 (시트, 대시보드, 조작계)
- 조명 디자인 (헤드라이트, 테일라이트, 실내등)
- 재질감과 마감 품질
- 브랜드 아이덴티티 표현
- 타겟 고객층에 맞는 디자인 어필

디자인의 감성적 메시지와 차별화 포인트를 분석해주세요."""
            },
            
            "패션/뷰티": {
                "스타일링 분석": """패션 스타일링 분석을 요청합니다.

다음 요소들을 분석해주세요:
- 의상 조합과 색상 매칭
- 액세서리와 소품 활용
- 헤어스타일과 메이크업
- 전체적인 룩의 컨셉과 테마
- 계절감과 TPO 적합성
- 체형 보완과 스타일링 효과
- 트렌드 반영도와 개성 표현

패션 브랜드나 뷰티 제품의 어필 포인트를 중심으로 분석해주세요.""",

                "뷰티 룩 분석": """뷰티 메이크업 및 헤어 분석을 요청합니다.

다음 뷰티 요소들을 평가해주세요:
- 베이스 메이크업 (파운데이션, 컨실러, 파우더)
- 포인트 메이크업 (아이, 립, 치크)
- 헤어스타일과 컬러
- 네일아트와 손 관리
- 스킨케어 상태와 피부 톤
- 조명과 각도에 따른 메이크업 효과
- 전체적인 이미지와 분위기

뷰티 제품의 효과와 브랜드 메시지 전달력을 분석해주세요.""",

                "트렌드 분석": """패션/뷰티 트렌드 분석을 요청합니다.

현재 트렌드 관점에서 분석해주세요:
- 색상 트렌드와 시즌 컬러
- 실루엣과 핏의 유행
- 소재와 텍스처 트렌드
- 액세서리 및 소품 트렌드
- 헤어/메이크업 트렌드
- 세대별/지역별 트렌드 차이
- SNS 인플루언서 스타일 반영도

트렌드 선도성과 대중성의 균형을 평가해주세요."""
            },
            
            "식음료": {
                "푸드 스타일링": """식음료 비주얼 분석을 요청합니다.

다음 요소들을 중심으로 분석해주세요:
- 음식의 색감과 질감 표현
- 플레이팅과 데코레이션
- 식기와 테이블 세팅
- 조명과 각도 설정
- 신선함과 맛있어 보이는 정도
- 브랜드/레스토랑 컨셉 반영
- 타겟 고객의 식욕 자극 정도

F&B 마케팅 관점에서 효과성을 분석해주세요.""",

                "레시피/조리법": """요리 과정 분석을 요청합니다.

다음 조리 과정을 분석해주세요:
- 재료 준비와 손질 과정
- 조리 순서와 테크닉
- 조리 도구와 기기 사용법
- 시간 관리와 타이밍
- 완성도와 재현 가능성
- 안전성과 위생 관리
- 초보자 이해도와 난이도

요리 교육 콘텐츠로서의 가치를 평가해주세요.""",

                "브랜드 분석": """식음료 브랜드 분석을 요청합니다.

브랜드 메시지 전달 관점에서 분석해주세요:
- 브랜드 아이덴티티 표현
- 제품의 품질과 프리미엄감
- 타겟 고객층 설정의 적절성
- 감성적 어필과 스토리텔링
- 경쟁사 대비 차별화 포인트
- 브랜드 일관성과 통일성
- 구매 욕구 자극 효과

마케팅 전략 관점에서 개선점을 제안해주세요."""
            },
            
            "기술/IT": {
                "제품 시연": """IT 제품 시연 분석을 요청합니다.

다음 기술적 요소들을 분석해주세요:
- 사용자 인터페이스(UI) 디자인
- 사용자 경험(UX) 플로우
- 기능 시연의 명확성
- 성능과 속도 표현
- 기술적 혁신성 어필
- 사용법의 직관성
- 문제 해결 능력 시연

기술 제품의 경쟁력과 사용자 편의성을 평가해주세요.""",

                "서비스 소개": """IT 서비스 소개 분석을 요청합니다.

서비스 가치 전달 관점에서 분석해주세요:
- 서비스 컨셉과 핵심 가치
- 사용자 페인 포인트 해결
- 서비스 플로우와 사용 시나리오
- 차별화된 기능과 장점
- 타겟 사용자층 설정
- 비즈니스 모델 명확성
- 확장성과 미래 가능성

시장에서의 포지셔닝과 성공 가능성을 분석해주세요.""",

                "개발자 튜토리얼": """개발 튜토리얼 분석을 요청합니다.

교육 콘텐츠 관점에서 분석해주세요:
- 설명의 논리성과 단계별 구성
- 코드 예제의 명확성
- 실습 환경 설정의 용이성
- 오류 처리와 디버깅 가이드
- 초보자 이해도와 난이도 조절
- 실무 활용 가능성
- 최신 기술 트렌드 반영

개발자 교육 효과성을 평가해주세요."""
            },
            
            "라이프스타일": {
                "일상 브이로그": """일상 라이프스타일 분석을 요청합니다.

다음 라이프스타일 요소들을 분석해주세요:
- 일상 루틴과 시간 관리
- 인테리어와 공간 활용
- 라이프스타일 제품 사용
- 취미와 여가 활동
- 인간관계와 소통 방식
- 건강 관리와 웰빙
- 개인적 가치관과 철학

시청자의 공감과 동기부여 효과를 분석해주세요.""",

                "홈 인테리어": """홈 인테리어 분석을 요청합니다.

공간 디자인 관점에서 분석해주세요:
- 공간 구성과 동선 계획
- 색상 조합과 컬러 스킴
- 가구 배치와 비율
- 조명 계획과 분위기 연출
- 수납과 정리 솔루션
- 브랜드/스타일 일관성
- 기능성과 실용성

인테리어 브랜드나 제품의 어필 효과를 평가해주세요.""",

                "건강/피트니스": """건강 및 피트니스 분석을 요청합니다.

웰빙 라이프스타일 관점에서 분석해주세요:
- 운동 자세와 테크닉
- 운동 강도와 난이도
- 안전성과 부상 위험도
- 운동 장비와 공간 활용
- 동기부여와 지속 가능성
- 건강한 식습관과 영양
- 정신 건강과 스트레스 관리

피트니스/헬스케어 브랜드 메시지 전달력을 분석해주세요."""
            }
        }
    
    def get_categories(self) -> Dict[str, Dict[str, str]]:
        """모든 카테고리와 템플릿 반환"""
        return self.templates
    
    def get_category_templates(self, category: str) -> Dict[str, str]:
        """특정 카테고리의 템플릿들 반환"""
        return self.templates.get(category, {})
    
    def get_template(self, category: str, template_name: str) -> str:
        """특정 템플릿 내용 반환"""
        return self.templates.get(category, {}).get(template_name, "")
    
    def add_custom_template(self, category: str, template_name: str, content: str):
        """사용자 정의 템플릿 추가"""
        if category not in self.templates:
            self.templates[category] = {}
        self.templates[category][template_name] = content
    
    def search_templates(self, keyword: str) -> Dict[str, Dict[str, str]]:
        """키워드로 템플릿 검색"""
        results = {}
        
        for category, templates in self.templates.items():
            matching_templates = {}
            for template_name, content in templates.items():
                if (keyword.lower() in template_name.lower() or 
                    keyword.lower() in content.lower()):
                    matching_templates[template_name] = content
            
            if matching_templates:
                results[category] = matching_templates
        
        return results
    
    def get_template_keywords(self, category: str, template_name: str) -> list:
        """템플릿에서 키워드 추출"""
        content = self.get_template(category, template_name)
        
        # 간단한 키워드 추출 로직
        keywords = []
        
        # 분석 관련 키워드
        analysis_keywords = [
            '분석', '평가', '검토', '측정', '비교', '진단', '조사', '연구',
            '색상', '디자인', '구성', '스타일', '트렌드', '품질', '효과',
            '브랜드', '마케팅', '고객', '타겟', '시장', '경쟁', '차별화'
        ]
        
        for keyword in analysis_keywords:
            if keyword in content:
                keywords.append(keyword)
        
        return list(set(keywords))  # 중복 제거
    
    def export_templates(self) -> dict:
        """템플릿 데이터 내보내기"""
        return {
            "templates": self.templates,
            "metadata": {
                "total_categories": len(self.templates),
                "total_templates": sum(len(templates) for templates in self.templates.values())
            }
        }
    
    def import_templates(self, template_data: dict):
        """템플릿 데이터 가져오기"""
        if "templates" in template_data:
            self.templates.update(template_data["templates"])