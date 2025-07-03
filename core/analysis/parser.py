# core/analysis/parser.py
"""AI 응답 파싱 모듈 - 간단하고 효과적인 버전"""

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
    
    def parse(self, response: str) -> Optional[ParsedAnalysis]:
        """AI 응답 파싱"""
        if not response or len(response) < 100:
            self.logger.error(f"응답이 너무 짧거나 비어있음: {len(response) if response else 0}자")
            return None
        
        self.logger.info("📝 응답 파싱 시작...")
        
        try:
            result = ParsedAnalysis(raw_response=response)
            
            # A1-A7 패턴으로 직접 파싱
            patterns = {
                'genre': r'A1[.\s]*[:：]?\s*(.+?)(?=\n\s*A2|$)',
                'reason': r'A2[.\s]*[:：]?\s*(.+?)(?=\n\s*A3|$)',
                'features': r'A3[.\s]*[:：]?\s*(.+?)(?=\n\s*A4|$)',
                'tags': r'A4[.\s]*[:：]?\s*(.+?)(?=\n\s*A5|$)',
                'format_type': r'A5[.\s]*[:：]?\s*(.+?)(?=\n\s*A6|$)',
                'mood': r'A6[.\s]*[:：]?\s*(.+?)(?=\n\s*A7|$)',
                'target_audience': r'A7[.\s]*[:：]?\s*(.+?)$'
            }
            
            # 각 패턴 매칭
            for field, pattern in patterns.items():
                match = re.search(pattern, response, re.MULTILINE | re.DOTALL)
                if match:
                    value = match.group(1).strip()
                    
                    if field == 'tags':
                        # 태그는 쉼표로 분리
                        tag_list = [tag.strip() for tag in value.split(',') if tag.strip()]
                        result.tags = tag_list[:20]  # 최대 20개
                        self.logger.debug(f"✅ 태그 {len(result.tags)}개 파싱됨")
                    else:
                        setattr(result, field, value)
                        self.logger.debug(f"✅ {field} 파싱됨: {value[:50]}...")
                else:
                    self.logger.warning(f"⚠️ {field} 매칭 실패")
            
            # 결과 유효성 검증
            if self._validate_result(result):
                self.logger.info("✅ 파싱 성공")
                return result
            else:
                # 섹션 기반 파싱 시도
                self.logger.info("🔄 섹션 기반 파싱 시도")
                return self._parse_section_format(response)
                
        except Exception as e:
            self.logger.error(f"파싱 오류: {str(e)}")
            return self._parse_minimal(response)
    
    def _parse_section_format(self, response: str) -> Optional[ParsedAnalysis]:
        """섹션 기반 파싱 (빈 줄로 구분)"""
        try:
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
            
            if len(sections) < 4:
                return None
            
            result = ParsedAnalysis(raw_response=response)
            
            # 섹션을 순서대로 매핑
            fields = ['genre', 'reason', 'features', 'tags', 'format_type', 'mood', 'target_audience']
            
            for i, section in enumerate(sections):
                if i < len(fields):
                    field = fields[i]
                    clean_section = self._clean_section(section)
                    
                    if field == 'tags':
                        tag_list = [tag.strip() for tag in clean_section.replace(',', ' ').split() if tag.strip()]
                        result.tags = tag_list[:20]
                    elif field in ['genre', 'format_type']:
                        # 첫 줄만 추출
                        result.__dict__[field] = clean_section.split('\n')[0].strip()
                    else:
                        result.__dict__[field] = clean_section
            
            return result if self._validate_result(result) else None
            
        except Exception as e:
            self.logger.error(f"섹션 파싱 오류: {str(e)}")
            return None
    
    def _parse_minimal(self, response: str) -> ParsedAnalysis:
        """최소한의 정보 추출"""
        result = ParsedAnalysis(raw_response=response)
        
        # 첫 줄을 장르로 추정
        lines = [line.strip() for line in response.split('\n') if line.strip()]
        if lines:
            result.genre = self._extract_genre_from_line(lines[0])
        
        # 전체 텍스트를 이유로 사용
        result.reason = response[:500] + "..." if len(response) > 500 else response
        
        # 간단한 태그 추출
        result.tags = self._extract_simple_tags(response)
        
        return result
    
    def _clean_section(self, section: str) -> str:
        """섹션 텍스트 정리"""
        # A1., A2. 등의 레이블 제거
        section = re.sub(r'^A\d+[.\s]*[:：]?\s*', '', section.strip())
        return section.strip()
    
    def _extract_genre_from_line(self, line: str) -> str:
        """줄에서 장르 추출"""
        line = self._clean_section(line)
        # 첫 50자만 반환
        return line[:50] if len(line) > 50 else line
    
    def _extract_simple_tags(self, text: str) -> List[str]:
        """간단한 태그 추출"""
        # 한글 단어만 추출 (2-10자)
        korean_words = re.findall(r'[가-힣]{2,10}', text)
        
        # 빈도수 계산 및 정리
        word_freq = {}
        exclude_words = {'영상', '분석', '이미지', '내용', '경우', '있습니다', '있으며', '활용하여', '특징을'}
        
        for word in korean_words:
            if word not in exclude_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # 빈도순 정렬하여 상위 10개 반환
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:10]]
    
    def _validate_result(self, result: ParsedAnalysis) -> bool:
        """파싱 결과 유효성 검사"""
        if result.genre == "Unknown" or not result.genre:
            self.logger.warning("⚠️ 장르 정보 부족")
            return False
        
        if result.reason == "분석 내용 없음" or len(result.reason) < 20:
            self.logger.warning("⚠️ 이유 설명 부족")
            return False
        
        self.logger.info(f"✅ 파싱 검증 통과: 장르={result.genre}, 이유={len(result.reason)}자")
        return True
