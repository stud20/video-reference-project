# core/analysis/parser.py
"""AI 응답 파싱 모듈"""

import re
import json
import os
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from utils.logger import get_logger


@dataclass
class ParsedAnalysis:
    """파싱된 분석 결과"""
    genre: str = "Unknown"
    reason: str = "분석 내용 없음"
    features: str = "분석 내용 없음"
    tags: List[str] = None
    format_type: str = "실사"
    mood: str = ""
    target_audience: str = ""
    raw_response: str = ""
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'genre': self.genre,
            'reasoning': self.reason,
            'features': self.features,
            'tags': self.tags,
            'expression_style': self.format_type,
            'mood_tone': self.mood,
            'target_audience': self.target_audience
        }


class ResponseParser:
    """AI 응답 파서"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # 커스텀 프롬프트 설정 로드
        self._load_custom_settings()
        
        # 파싱 패턴들
        self.patterns = self._build_patterns()
    
    def _load_custom_settings(self):
        """커스텀 프롬프트 설정 로드"""
        settings_file = "config/prompt_settings.json"
        
        # 기본 분석 항목
        self.analysis_items = [
            {"label": "A1", "field": "genre"},
            {"label": "A2", "field": "reason"},
            {"label": "A3", "field": "features"},
            {"label": "A4", "field": "tags"},
            {"label": "A5", "field": "format_type"},
            {"label": "A6", "field": "mood"},
            {"label": "A7", "field": "target_audience"}
        ]
        
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                # 분석 항목이 있으면 매핑 업데이트
                if 'analysis_items' in settings:
                    custom_items = settings['analysis_items']
                    
                    # 레이블과 필드 매핑 업데이트
                    for i, item in enumerate(custom_items[:7]):  # 최대 7개 항목
                        if i < len(self.analysis_items):
                            self.analysis_items[i]["label"] = item.get("label", f"A{i+1}")
                            # 제목에서 필드 타입 추정 (선택사항)
                            title = item.get("title", "").lower()
                            if "장르" in title:
                                self.analysis_items[i]["field"] = "genre"
                            elif "이유" in title or "판단" in title:
                                self.analysis_items[i]["field"] = "reason"
                            elif "특징" in title or "특이" in title:
                                self.analysis_items[i]["field"] = "features"
                            elif "태그" in title or "키워드" in title:
                                self.analysis_items[i]["field"] = "tags"
                            elif "표현" in title or "형식" in title:
                                self.analysis_items[i]["field"] = "format_type"
                            elif "분위기" in title or "톤" in title:
                                self.analysis_items[i]["field"] = "mood"
                            elif "타겟" in title or "고객" in title:
                                self.analysis_items[i]["field"] = "target_audience"
                
                self.logger.info("✅ 커스텀 파싱 설정 로드 완료")
                
            except Exception as e:
                self.logger.error(f"커스텀 설정 로드 실패: {str(e)}")
    
    def _build_patterns(self) -> Dict[str, Dict[str, str]]:
        """동적 파싱 패턴 생성"""
        labeled_patterns = {}
        
        # 커스텀 레이블 기반 패턴 생성
        for i, item in enumerate(self.analysis_items):
            label = item["label"]
            field = item["field"]
            
            # 다음 레이블까지 또는 끝까지 매칭
            if i < len(self.analysis_items) - 1:
                next_label = self.analysis_items[i + 1]["label"]
                pattern = rf'{label}[.\s]*[:：]?\s*(.+?)(?={next_label}|$)'
            else:
                pattern = rf'{label}[.\s]*[:：]?\s*(.+?)(?=$)'
            
            labeled_patterns[field] = pattern
        
        return {
            'labeled': labeled_patterns,
            'section': {
                'sections': r'(?:^|\n\n)(.+?)(?=\n\n|$)'
            }
        }
    
    def parse(self, response: str) -> Optional[ParsedAnalysis]:
        """AI 응답 파싱
        
        Args:
            response: AI의 원본 응답 텍스트
            
        Returns:
            파싱된 분석 결과 또는 None
        """
        if not response or len(response) < 100:
            self.logger.error(f"응답이 너무 짧거나 비어있음: {len(response) if response else 0}자")
            return None
        
        # 파싱 전에 최신 설정 다시 로드
        self._load_custom_settings()
        self.patterns = self._build_patterns()
        
        self.logger.info("📝 응답 파싱 시작...")
        self.logger.debug(f"📊 로드된 분석 항목 개수: {len(self.analysis_items)}")
        self.logger.debug(f"📊 첫 번째 항목: {self.analysis_items[0] if self.analysis_items else 'None'}")
        self.logger.debug(f"📊 응답 길이: {len(response)}자")
        
        # 여러 파싱 전략 시도
        result = None
        
        # 1. 레이블 기반 파싱 시도 (커스텀 레이블 사용)
        result = self._parse_labeled_format(response)
        if result and self._validate_result(result):
            self.logger.info("✅ 레이블 형식 파싱 성공")
            return result
        
        # 2. 섹션 기반 파싱 시도 (빈 줄로 구분)
        result = self._parse_section_format(response)
        if result and self._validate_result(result):
            self.logger.info("✅ 섹션 형식 파싱 성공")
            return result
        
        # 3. 자유 형식 파싱 시도 (키워드 기반)
        result = self._parse_free_format(response)
        if result and self._validate_result(result):
            self.logger.info("✅ 자유 형식 파싱 성공")
            return result
        
        # 4. 최소한의 정보라도 추출
        self.logger.warning("⚠️ 정교한 파싱 실패, 기본 파싱 시도")
        return self._parse_minimal(response)
    
    def _parse_labeled_format(self, response: str) -> Optional[ParsedAnalysis]:
        """레이블 형식 파싱 (커스텀 레이블 지원)"""
        try:
            result = ParsedAnalysis(raw_response=response)
            
            # 각 필드 추출
            for field, pattern in self.patterns['labeled'].items():
                match = re.search(pattern, response, re.MULTILINE | re.DOTALL)
                if match:
                    value = match.group(1).strip()
                    
                    if field == 'tags':
                        # 태그는 리스트로 변환
                        result.tags = self._parse_tags(value)
                    else:
                        setattr(result, field, self._clean_text(value))
            
            return result
            
        except Exception as e:
            self.logger.error(f"레이블 형식 파싱 오류: {str(e)}")
            return None
    
    def _parse_section_format(self, response: str) -> Optional[ParsedAnalysis]:
        """섹션 형식 파싱 (빈 줄로 구분)"""
        try:
            # 빈 줄로 섹션 분리
            sections = []
            current_section = []
            
            for line in response.strip().split('\n'):
                if line.strip():
                    current_section.append(line)
                else:
                    if current_section:
                        sections.append('\n'.join(current_section))
                        current_section = []
            
            if current_section:
                sections.append('\n'.join(current_section))
            
            if len(sections) < 4:  # 최소 4개 섹션 필요
                return None
            
            # 섹션을 순서대로 매핑
            result = ParsedAnalysis(raw_response=response)
            
            # 커스텀 항목 순서에 따라 매핑
            for i, section in enumerate(sections):
                if i < len(self.analysis_items):
                    field = self.analysis_items[i]["field"]
                    
                    if field == "tags":
                        result.tags = self._parse_tags(section)
                    elif field in ["genre", "format_type"]:
                        setattr(result, field, self._extract_first_line(section))
                    else:
                        setattr(result, field, self._clean_text(section))
            
            return result
            
        except Exception as e:
            self.logger.error(f"섹션 형식 파싱 오류: {str(e)}")
            return None
    
    def _parse_free_format(self, response: str) -> Optional[ParsedAnalysis]:
        """자유 형식 파싱 (키워드 기반)"""
        try:
            result = ParsedAnalysis(raw_response=response)
            
            # 장르 찾기
            genre_keywords = ["장르", "분류", "카테고리", "타입", "유형"]
            for keyword in genre_keywords:
                pattern = rf'{keyword}[:\s]*([^\n]+)'
                match = re.search(pattern, response, re.IGNORECASE)
                if match:
                    result.genre = self._extract_first_line(match.group(1))
                    break
            
            # 태그 찾기
            tag_keywords = ["태그", "키워드", "관련어", "연관어"]
            for keyword in tag_keywords:
                pattern = rf'{keyword}[:\s]*([^\n]+(?:\n[^\n]+)*)'
                match = re.search(pattern, response, re.IGNORECASE)
                if match:
                    result.tags = self._parse_tags(match.group(1))
                    break
            
            # 나머지 필드는 텍스트의 순서와 길이로 추정
            lines = [line.strip() for line in response.split('\n') if line.strip()]
            
            # 긴 텍스트를 이유와 특징으로 분류
            long_texts = [line for line in lines if len(line) > 100]
            if len(long_texts) >= 2:
                result.reason = long_texts[0]
                result.features = long_texts[1]
            elif len(long_texts) == 1:
                result.reason = long_texts[0]
                result.features = "분석 내용 없음"
            
            return result
            
        except Exception as e:
            self.logger.error(f"자유 형식 파싱 오류: {str(e)}")
            return None
    
    def _parse_minimal(self, response: str) -> ParsedAnalysis:
        """최소한의 정보 추출"""
        result = ParsedAnalysis(raw_response=response)
        
        # 첫 줄을 장르로 가정
        lines = [line.strip() for line in response.split('\n') if line.strip()]
        if lines:
            result.genre = self._extract_first_line(lines[0])
        
        # 전체 텍스트를 이유로 사용
        result.reason = response[:500] + "..." if len(response) > 500 else response
        
        # 태그 추출 시도
        result.tags = self._extract_potential_tags(response)
        
        return result
    
    def _parse_tags(self, text: str) -> List[str]:
        """태그 텍스트를 리스트로 변환"""
        # 여러 구분자 처리
        delimiters = [',', '/', '#', '·', '|', '\n']
        
        # 가장 많이 사용된 구분자 찾기
        delimiter_counts = {d: text.count(d) for d in delimiters}
        main_delimiter = max(delimiter_counts, key=delimiter_counts.get)
        
        if delimiter_counts[main_delimiter] == 0:
            # 구분자가 없으면 공백으로 분리
            tags = text.split()
        else:
            tags = text.split(main_delimiter)
        
        # 정리
        cleaned_tags = []
        for tag in tags:
            tag = tag.strip()
            # 특수문자 제거
            tag = re.sub(r'^[#\-\*\·\s]+', '', tag)
            tag = re.sub(r'[#\-\*\·\s]+$', '', tag)
            
            if tag and len(tag) > 1 and len(tag) < 50:
                cleaned_tags.append(tag)
        
        return cleaned_tags[:20]  # 최대 20개
    
    def _extract_potential_tags(self, text: str) -> List[str]:
        """텍스트에서 잠재적인 태그 추출"""
        # 한글 단어 추출 (2-10자)
        korean_words = re.findall(r'[가-힣]{2,10}', text)
        
        # 빈도수 계산
        word_freq = {}
        for word in korean_words:
            if word not in ['영상', '분석', '이미지', '내용', '경우']:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # 빈도순 정렬
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        return [word for word, freq in sorted_words[:10]]
    
    def _clean_text(self, text: str) -> str:
        """텍스트 정리"""
        # 커스텀 레이블 패턴 제거
        for item in self.analysis_items:
            label = item["label"]
            text = re.sub(rf'^{label}[.\s]*[:：]?\s*', '', text.strip())
        
        # 앞뒤 특수문자 제거
        text = re.sub(r'^[-\*\·\s]+', '', text)
        text = re.sub(r'[-\*\·\s]+$', '', text)
        
        return text.strip()
    
    def _extract_first_line(self, text: str) -> str:
        """첫 줄 또는 짧은 텍스트 추출"""
        text = self._clean_text(text)
        
        # 첫 줄만 추출 (장르나 형식 같은 짧은 답변용)
        first_line = text.split('\n')[0].strip()
        
        # 너무 길면 첫 50자만
        return first_line[:50] if len(first_line) > 50 else first_line
    
    def _validate_result(self, result: ParsedAnalysis) -> bool:
        """파싱 결과 유효성 검사"""
        # 필수 필드 확인
        if result.genre == "Unknown" or not result.genre:
            self.logger.warning(f"⚠️ 장르 정보 부족: '{result.genre}'")
            return False
        
        if result.reason == "분석 내용 없음" or len(result.reason) < 20:
            self.logger.warning(f"⚠️ 이유 설명 부족: {len(result.reason)}자")
            return False
        
        self.logger.info(f"✅ 파싱 결과 유효성 검사 통과: 장르={result.genre}, 이유={len(result.reason)}자")
        return True
