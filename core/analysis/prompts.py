# src/analyzer/prompts/prompt_builder.py
"""프롬프트 빌더 - 동적 프롬프트 생성"""

import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
from utils.logger import get_logger


class PromptBuilder:
    """동적 프롬프트 생성기"""
    
    # 기본 장르 목록
    DEFAULT_GENRES = [
        "2D애니메이션", "3D애니메이션", "모션그래픽", "인터뷰", 
        "스팟광고", "VLOG", "유튜브콘텐츠", "다큐멘터리", 
        "브랜드필름", "TVC", "뮤직비디오", "교육콘텐츠",
        "제품소개", "이벤트영상", "웹드라마", "바이럴영상"
    ]
    
    # 기본 표현 형식
    DEFAULT_FORMAT_TYPES = ["2D", "3D", "실사", "혼합형", "스톱모션", "타이포그래피"]
    
    # 기본 시스템 프롬프트
    DEFAULT_SYSTEM_PROMPT = """당신은 광고 영상 전문 분석가입니다. 주어진 이미지들과 메타데이터를 종합적으로 분석하여 영상의 장르, 특징, 타겟 등을 상세히 분석해주세요. 메타데이터는 참고용이며, 실제 이미지 내용을 우선시하여 분석해주세요."""
    
    # 기본 분석 지침
    DEFAULT_ANALYSIS_INSTRUCTION = """제공된 메타데이터(제목, 설명, 태그 등)를 참고하여 더 정확한 분석을 수행하되,
실제 이미지 내용이 메타데이터와 다를 경우 이미지 내용을 우선시해주세요."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.logger = get_logger(__name__)
        self.config_path = config_path or "config/prompt_settings.json"
        
        # 설정 로드
        self._load_config()
    
    def _load_config(self):
        """프롬프트 설정 로드"""
        # 기본값 설정
        self.system_prompt = self.DEFAULT_SYSTEM_PROMPT
        self.analysis_instruction = self.DEFAULT_ANALYSIS_INSTRUCTION
        self.genres = self.DEFAULT_GENRES.copy()
        self.format_types = self.DEFAULT_FORMAT_TYPES.copy()
        self.analysis_items = self._get_default_analysis_items()
        self.require_labels = True
        self.strict_format = True
        
        # 설정 파일이 있으면 로드
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                # 설정 적용
                self.system_prompt = settings.get('system_prompt', self.system_prompt)
                self.analysis_instruction = settings.get('analysis_instruction', self.analysis_instruction)
                self.genres = settings.get('genres', self.genres)
                self.format_types = settings.get('format_types', self.format_types)
                self.analysis_items = settings.get('analysis_items', self.analysis_items)
                self.require_labels = settings.get('require_labels', True)
                self.strict_format = settings.get('strict_format', True)
                
                self.logger.info("✅ 프롬프트 설정 로드 완료")
                
            except Exception as e:
                self.logger.error(f"프롬프트 설정 로드 실패: {str(e)}")
                self.logger.info("기본 설정을 사용합니다")
    
    def _get_default_analysis_items(self) -> List[Dict[str, Any]]:
        """기본 분석 항목"""
        return [
            {
                "label": "A1",
                "title": "영상 장르",
                "instruction": "다음 중 하나만 선택"
            },
            {
                "label": "A2",
                "title": "장르 판단 이유",
                "instruction": "시각적 특징, 연출 스타일, 정보 전달 방식, 메타데이터 등을 종합하여 200자 이상 상세히 설명"
            },
            {
                "label": "A3",
                "title": "영상의 특징 및 특이사항",
                "instruction": "색감, 편집, 카메라워크, 분위기, 메시지 등을 200자 이상 상세히 설명"
            },
            {
                "label": "A4",
                "title": "관련 태그 10개 이상",
                "instruction": "쉼표로 구분, # 기호 없이, YouTube 태그와 중복되지 않는 새로운 태그 위주로"
            },
            {
                "label": "A5",
                "title": "표현형식",
                "instruction": "다음 중 하나만 선택"
            },
            {
                "label": "A6",
                "title": "전반적인 분위기와 톤",
                "instruction": ""
            },
            {
                "label": "A7",
                "title": "예상 타겟 고객층",
                "instruction": ""
            }
        ]
    
    def build_analysis_prompt(self, 
                            context: Dict[str, Any], 
                            image_count: int) -> str:
        """분석 프롬프트 생성
        
        Args:
            context: 영상 메타데이터 컨텍스트
            image_count: 분석할 이미지 개수
            
        Returns:
            생성된 프롬프트 문자열
        """
        # 메타데이터 정보 구성
        metadata_lines = self._build_metadata_section(context)
        
        # 설명 텍스트 추가
        description_text = self._build_description_section(context)
        
        # 분석 항목 텍스트 생성
        analysis_items_text, num_items = self._build_analysis_items()
        
        # 추가 지침 구성
        instructions_text = self._build_instructions()
        
        # 전체 프롬프트 조합
        prompt = f"""영상 메타데이터:
{metadata_lines}{description_text}

위 영상에서 추출한 {image_count}개의 이미지를 분석해주세요. 
첫 번째 이미지는 썸네일이며, 나머지는 영상의 대표 장면들입니다.

{self.analysis_instruction}

다음 {num_items}개 항목을 모두 작성해주세요.{instructions_text}

분석 항목:
{analysis_items_text}"""
        
        return prompt
    
    def _build_metadata_section(self, context: Dict[str, Any]) -> str:
        """메타데이터 섹션 구성"""
        metadata_info = []
        
        if context.get("title"):
            metadata_info.append(f"제목: {context['title']}")
        
        if context.get("uploader"):
            metadata_info.append(f"업로더/채널: {context['uploader']}")
        
        if context.get("duration"):
            metadata_info.append(f"영상 길이: {context['duration']}")
        
        if context.get("view_count", 0) > 0:
            metadata_info.append(f"조회수: {context['view_count']:,}회")
        
        if context.get("tags"):
            tags = context['tags'][:10]  # 최대 10개
            metadata_info.append(f"YouTube 태그: {', '.join(tags)}")
        
        return "\n".join(metadata_info)
    
    def _build_description_section(self, context: Dict[str, Any]) -> str:
        """설명 섹션 구성"""
        if context.get("description"):
            # 설명이 너무 길면 500자로 제한
            desc = context["description"][:500]
            if len(context["description"]) > 500:
                desc += "..."
            return f"\n\n영상 설명:\n{desc}"
        return ""
    
    def _build_analysis_items(self) -> tuple[str, int]:
        """분석 항목 텍스트 생성"""
        analysis_items_text = []
        
        for item in self.analysis_items:
            item_text = f"{item['label']}. {item['title']}"
            
            # 장르와 표현형식은 선택 목록 추가
            if item['label'] == 'A1':
                item_text += f" (다음 중 하나만 선택): {', '.join(self.genres)}"
            elif item['label'] == 'A5':
                item_text += f" (다음 중 하나만 선택): {', '.join(self.format_types)}"
            
            # 설명/지침 추가
            if item.get('instruction'):
                item_text += f" ({item['instruction']})"
            
            analysis_items_text.append(item_text)
        
        return '\n'.join(analysis_items_text), len(analysis_items_text)
    
    def _build_instructions(self) -> str:
        """추가 지침 구성"""
        instructions = []
        
        if self.require_labels:
            instructions.append(
                '각 항목의 답변에는 "장르 판단 이유:", "영상의 특징:" 같은 '
                '레이블을 포함하지 말고 내용만 작성하세요.'
            )
        
        if self.strict_format:
            instructions.append("각 항목은 빈 줄로 구분하여 명확히 구분해주세요.")
        
        return ' ' + ' '.join(instructions) if instructions else ''
    
    def save_config(self, config: Dict[str, Any]):
        """설정 저장"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"✅ 프롬프트 설정 저장 완료: {self.config_path}")
            
            # 저장 후 다시 로드
            self._load_config()
            
        except Exception as e:
            self.logger.error(f"❌ 프롬프트 설정 저장 실패: {str(e)}")
            raise
