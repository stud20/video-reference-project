"""프롬프트 향상 및 컨텍스트 통합 엔진"""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import re

class PromptEnhancer:
    """사용자 프롬프트를 비디오 메타데이터와 통합하여 향상시키는 클래스"""
    
    def __init__(self):
        self.base_analysis_framework = self._load_base_framework()
        self.video_context_keys = [
            'duration', 'resolution', 'fps', 'codec', 'bitrate',
            'audio_channels', 'file_size', 'creation_date'
        ]
    
    def _load_base_framework(self) -> Dict[str, Any]:
        """기본 분석 프레임워크 로드"""
        return {
            "analysis_structure": {
                "overview": "전체적인 영상 개요 및 주요 특징",
                "visual_analysis": "시각적 요소 분석 (색상, 구성, 조명, 앵글)",
                "content_analysis": "콘텐츠 내용 분석 (스토리, 메시지, 감정)",
                "technical_analysis": "기술적 품질 분석 (화질, 사운드, 편집)",
                "target_specific": "요청된 특정 분석 영역",
                "recommendations": "개선 사항 및 추천 사항"
            },
            "output_format": {
                "type": "structured_json",
                "include_scores": True,
                "include_timestamps": True,
                "include_confidence": True
            }
        }
    
    def enhance_prompt(
        self, 
        user_prompt: str, 
        video_metadata: Dict[str, Any] = None,
        analysis_type: str = "comprehensive"
    ) -> str:
        """사용자 프롬프트를 메타데이터와 결합하여 향상"""
        
        # 1. 사용자 프롬프트 분석 및 정제
        cleaned_prompt = self._clean_and_analyze_prompt(user_prompt)
        
        # 2. 비디오 컨텍스트 추가
        video_context = self._build_video_context(video_metadata)
        
        # 3. 분석 프레임워크 적용
        analysis_framework = self._build_analysis_framework(cleaned_prompt, analysis_type)
        
        # 4. 최종 프롬프트 구성
        enhanced_prompt = self._compose_final_prompt(
            cleaned_prompt, video_context, analysis_framework
        )
        
        return enhanced_prompt
    
    def _clean_and_analyze_prompt(self, user_prompt: str) -> Dict[str, Any]:
        """사용자 프롬프트 분석 및 정제"""
        
        # 키워드 추출
        keywords = self._extract_keywords(user_prompt)
        
        # 분석 의도 파악
        intent = self._detect_analysis_intent(user_prompt)
        
        # 우선순위 영역 식별
        priority_areas = self._identify_priority_areas(user_prompt, keywords)
        
        return {
            "original_text": user_prompt,
            "keywords": keywords,
            "intent": intent,
            "priority_areas": priority_areas,
            "complexity_level": self._assess_complexity(user_prompt)
        }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """텍스트에서 분석 관련 키워드 추출"""
        
        # 도메인별 키워드 사전
        domain_keywords = {
            "automotive": ["자동차", "차량", "주행", "운전", "도로", "속도", "안전", "디자인"],
            "fashion": ["패션", "스타일", "옷", "의상", "액세서리", "트렌드", "룩"],
            "beauty": ["뷰티", "메이크업", "화장", "헤어", "스킨케어", "네일"],
            "food": ["음식", "요리", "식당", "레시피", "맛", "플레이팅", "재료"],
            "tech": ["기술", "소프트웨어", "앱", "프로그램", "개발", "코딩", "시스템"],
            "lifestyle": ["라이프스타일", "일상", "인테리어", "홈", "취미", "여행"]
        }
        
        # 분석 타입 키워드
        analysis_keywords = [
            "분석", "평가", "검토", "측정", "비교", "조사", "연구", "진단",
            "색상", "구성", "움직임", "소리", "감정", "효과", "품질", "성능"
        ]
        
        found_keywords = []
        text_lower = text.lower()
        
        # 도메인 키워드 검색
        for domain, keywords in domain_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    found_keywords.append(f"{domain}:{keyword}")
        
        # 분석 키워드 검색
        for keyword in analysis_keywords:
            if keyword in text:
                found_keywords.append(f"analysis:{keyword}")
        
        return found_keywords
    
    def _detect_analysis_intent(self, text: str) -> Dict[str, Any]:
        """분석 의도 탐지"""
        
        intent_patterns = {
            "comparison": ["비교", "대비", "차이", "vs", "versus"],
            "evaluation": ["평가", "점수", "등급", "측정", "판단"],
            "improvement": ["개선", "향상", "최적화", "발전", "업그레이드"],
            "identification": ["찾기", "발견", "확인", "식별", "탐지"],
            "trend_analysis": ["트렌드", "유행", "변화", "패턴", "경향"],
            "quality_check": ["품질", "퀄리티", "완성도", "수준", "상태"]
        }
        
        detected_intents = []
        confidence_scores = {}
        
        for intent, patterns in intent_patterns.items():
            score = 0
            for pattern in patterns:
                if pattern in text:
                    score += 1
            
            if score > 0:
                detected_intents.append(intent)
                confidence_scores[intent] = score / len(patterns)
        
        return {
            "primary_intent": detected_intents[0] if detected_intents else "general_analysis",
            "all_intents": detected_intents,
            "confidence_scores": confidence_scores
        }
    
    def _identify_priority_areas(self, text: str, keywords: List[str]) -> List[str]:
        """우선순위 분석 영역 식별"""
        
        priority_areas = []
        
        # 키워드 기반 영역 매핑
        area_mapping = {
            "visual": ["색상", "조명", "구성", "앵글", "시각", "디자인"],
            "audio": ["소리", "음성", "음악", "오디오", "사운드"],
            "motion": ["움직임", "액션", "동작", "속도", "흐름"],
            "emotion": ["감정", "느낌", "분위기", "무드", "임팩트"],
            "technical": ["품질", "해상도", "편집", "효과", "기술"],
            "content": ["내용", "스토리", "메시지", "주제", "컨셉"]
        }
        
        for area, area_keywords in area_mapping.items():
            for keyword in area_keywords:
                if keyword in text:
                    priority_areas.append(area)
                    break
        
        # 기본 영역 추가 (우선순위가 없는 경우)
        if not priority_areas:
            priority_areas = ["visual", "content", "technical"]
        
        return list(set(priority_areas))  # 중복 제거
    
    def _assess_complexity(self, text: str) -> str:
        """프롬프트 복잡도 평가"""
        
        complexity_indicators = {
            "high": ["세부적으로", "정밀하게", "모든", "전체적으로", "종합적으로", "다각도로"],
            "medium": ["자세히", "구체적으로", "중점적으로", "특별히"],
            "low": ["간단히", "빠르게", "대략적으로", "개략적으로"]
        }
        
        scores = {"high": 0, "medium": 0, "low": 0}
        
        for level, indicators in complexity_indicators.items():
            for indicator in indicators:
                if indicator in text:
                    scores[level] += 1
        
        # 길이 기반 복잡도도 고려
        if len(text) > 200:
            scores["high"] += 1
        elif len(text) > 100:
            scores["medium"] += 1
        else:
            scores["low"] += 1
        
        return max(scores, key=scores.get)
    
    def _build_video_context(self, metadata: Dict[str, Any] = None) -> str:
        """비디오 메타데이터 기반 컨텍스트 구성"""
        
        if not metadata:
            return "비디오 메타데이터가 제공되지 않음. 업로드된 비디오를 기반으로 분석 진행."
        
        context_parts = ["=== 비디오 정보 ==="]
        
        # 기본 정보
        if 'duration' in metadata:
            context_parts.append(f"재생 시간: {metadata['duration']}")
        
        if 'resolution' in metadata:
            context_parts.append(f"해상도: {metadata['resolution']}")
        
        if 'fps' in metadata:
            context_parts.append(f"프레임레이트: {metadata['fps']} fps")
        
        # 품질 정보
        if 'file_size' in metadata:
            context_parts.append(f"파일 크기: {metadata['file_size']}")
        
        if 'bitrate' in metadata:
            context_parts.append(f"비트레이트: {metadata['bitrate']}")
        
        # 추가 정보
        if 'creation_date' in metadata:
            context_parts.append(f"생성일: {metadata['creation_date']}")
        
        return "\\n".join(context_parts)
    
    def _build_analysis_framework(self, prompt_data: Dict[str, Any], analysis_type: str) -> str:
        """분석 프레임워크 구성"""
        
        framework_parts = ["=== 분석 프레임워크 ==="]
        
        # 우선순위 영역별 분석 가이드
        priority_areas = prompt_data.get("priority_areas", [])
        
        if "visual" in priority_areas:
            framework_parts.append("""
시각적 분석:
- 색상 팔레트와 색조 분석
- 구성과 프레임 분할
- 조명과 그림자 효과
- 카메라 앵글과 움직임""")
        
        if "audio" in priority_areas:
            framework_parts.append("""
오디오 분석:
- 배경음악과 효과음
- 음성 품질과 명확성
- 사운드 디자인 효과
- 오디오-비주얼 동기화""")
        
        if "content" in priority_areas:
            framework_parts.append("""
콘텐츠 분석:
- 스토리텔링 구조
- 메시지 전달력
- 감정적 임팩트
- 타겟 오디언스 적합성""")
        
        if "technical" in priority_areas:
            framework_parts.append("""
기술적 분석:
- 화질과 선명도
- 편집 기법과 트랜지션
- 안정성과 흔들림
- 압축 품질과 아티팩트""")
        
        # 출력 형식 가이드
        framework_parts.append("""
=== 출력 형식 ===
분석 결과를 다음 JSON 구조로 제공:
{
    "overall_score": "전체 점수 (1-10)",
    "analysis_summary": "핵심 분석 요약",
    "detailed_analysis": {
        "강점": ["구체적인 강점들"],
        "개선점": ["구체적인 개선 제안들"],
        "특이사항": ["주목할 만한 특징들"]
    },
    "recommendations": ["실행 가능한 추천사항들"],
    "confidence_level": "분석 신뢰도 (high/medium/low)"
}""")
        
        return "\\n".join(framework_parts)
    
    def _compose_final_prompt(
        self, 
        prompt_data: Dict[str, Any], 
        video_context: str, 
        analysis_framework: str
    ) -> str:
        """최종 향상된 프롬프트 구성"""
        
        final_prompt_parts = [
            "=== 비디오 분석 요청 ===",
            f"사용자 요청: {prompt_data['original_text']}",
            "",
            video_context,
            "",
            analysis_framework,
            "",
            "=== 분석 지침 ===",
            f"복잡도 수준: {prompt_data['complexity_level']}",
            f"주요 키워드: {', '.join(prompt_data['keywords'][:10])}",  # 상위 10개만
            f"분석 의도: {prompt_data['intent']['primary_intent']}",
            "",
            "위 정보를 종합하여 요청된 분석을 수행하고, JSON 형식으로 구조화된 결과를 제공해주세요.",
            "분석은 객관적이고 구체적이며, 실용적인 인사이트를 포함해야 합니다."
        ]
        
        return "\\n".join(final_prompt_parts)
    
    def generate_follow_up_questions(self, analysis_result: str, original_prompt: str) -> List[str]:
        """분석 결과 기반 후속 질문 생성"""
        
        follow_up_questions = [
            "이 분석 결과에서 가장 중요한 개선점은 무엇인가요?",
            "특정 시간대나 장면에 대한 더 자세한 분석이 필요한가요?",
            "비슷한 영상들과 비교 분석을 원하시나요?",
            "이 영상의 타겟 오디언스 반응을 예측해볼까요?",
            "브랜드나 마케팅 관점에서 추가 분석이 필요한가요?"
        ]
        
        # 원본 프롬프트 기반 맞춤형 질문 추가
        if "자동차" in original_prompt:
            follow_up_questions.extend([
                "차량의 특정 기능이나 성능에 대한 더 깊은 분석이 필요한가요?",
                "안전성 측면에서의 추가 검토를 원하시나요?"
            ])
        
        if "패션" in original_prompt or "뷰티" in original_prompt:
            follow_up_questions.extend([
                "다른 시즌이나 트렌드와의 비교 분석이 필요한가요?",
                "특정 연령대나 타겟 그룹에 대한 어필도를 분석해볼까요?"
            ])
        
        return follow_up_questions[:5]  # 상위 5개만 반환
    
    def save_prompt_history(self, user_prompt: str, enhanced_prompt: str, result: str = None):
        """프롬프트 히스토리 저장 (향후 학습용)"""
        
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_prompt": user_prompt,
            "enhanced_prompt": enhanced_prompt,
            "result": result,
            "metadata": {
                "prompt_length": len(user_prompt),
                "enhancement_ratio": len(enhanced_prompt) / len(user_prompt) if user_prompt else 1
            }
        }
        
        # 실제 구현에서는 데이터베이스나 파일에 저장
        # 현재는 로그만 출력
        print(f"프롬프트 히스토리 저장: {history_entry['timestamp']}")
        
        return history_entry