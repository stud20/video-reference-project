# web/components/settings/prompt.py
"""
AI 프롬프트 튜닝 설정 컴포넌트
"""

import streamlit as st
import os
import json
from typing import Dict, List
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)

# 기본 프롬프트 템플릿
DEFAULT_SYSTEM_PROMPT = "당신은 광고 영상 전문 분석가입니다. 주어진 이미지들과 메타데이터를 종합적으로 분석하여 영상의 장르, 특징, 타겟 등을 상세히 분석해주세요. 메타데이터는 참고용이며, 실제 이미지 내용을 우선시하여 분석해주세요."

DEFAULT_ANALYSIS_INSTRUCTION = """제공된 메타데이터(제목, 설명, 태그 등)를 참고하여 더 정확한 분석을 수행하되,
실제 이미지 내용이 메타데이터와 다를 경우 이미지 내용을 우선시해주세요."""

DEFAULT_ANALYSIS_ITEMS = [
    {
        "label": "A1",
        "title": "영상 장르",
        "instruction": "다음 중 하나만 선택",
        "description": "",
        "min_length": 0
    },
    {
        "label": "A2",
        "title": "장르 판단 이유",
        "instruction": "시각적 특징, 연출 스타일, 정보 전달 방식, 메타데이터 등을 종합하여 200자 이상 상세히 설명",
        "description": "",
        "min_length": 200
    },
    {
        "label": "A3",
        "title": "영상의 특징 및 특이사항",
        "instruction": "색감, 편집, 카메라워크, 분위기, 메시지 등을 200자 이상 상세히 설명",
        "description": "",
        "min_length": 200
    },
    {
        "label": "A4",
        "title": "관련 태그",
        "instruction": "10개 이상 (쉼표로 구분, # 기호 없이, YouTube 태그와 중복되지 않는 새로운 태그 위주로)",
        "description": "",
        "min_length": 10
    },
    {
        "label": "A5",
        "title": "표현형식",
        "instruction": "다음 중 하나만 선택",
        "description": "",
        "min_length": 0
    },
    {
        "label": "A6",
        "title": "전반적인 분위기와 톤",
        "instruction": "",
        "description": "",
        "min_length": 0
    },
    {
        "label": "A7",
        "title": "예상 타겟 고객층",
        "instruction": "",
        "description": "",
        "min_length": 0
    }
]

# 장르 및 표현형식 목록
GENRES = [
    "2D애니메이션", "3D애니메이션", "모션그래픽", "인터뷰", 
    "스팟광고", "VLOG", "유튜브콘텐츠", "다큐멘터리", 
    "브랜드필름", "TVC", "뮤직비디오", "교육콘텐츠",
    "제품소개", "이벤트영상", "웹드라마", "바이럴영상"
]

FORMAT_TYPES = ["2D", "3D", "실사", "혼합형", "스톱모션", "타이포그래피"]


def render_prompt_settings():
    """AI 프롬프트 설정 렌더링"""
    st.subheader("🤖 AI 프롬프트 튜닝")
    st.markdown("AI 모델에게 보낼 프롬프트를 커스터마이즈합니다.")
    
    # 프롬프트 설정 로드
    prompt_settings = load_prompt_settings()
    
    # 탭 구성
    tab1, tab2, tab3, tab4 = st.tabs([
        "📝 시스템 프롬프트",
        "📋 분석 항목",
        "🏷️ 선택 옵션",
        "👁️ 미리보기"
    ])
    
    # 시스템 프롬프트 설정
    with tab1:
        prompt_settings = render_system_prompt_settings(prompt_settings)
    
    # 분석 항목 설정
    with tab2:
        prompt_settings = render_analysis_items_settings(prompt_settings)
    
    # 선택 옵션 설정
    with tab3:
        prompt_settings = render_selection_options(prompt_settings)
    
    # 프롬프트 미리보기
    with tab4:
        render_prompt_preview(prompt_settings)
    
    # 저장 버튼
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 3])
    
    with col1:
        if st.button("💾 설정 저장", type="primary", use_container_width=True):
            save_prompt_settings(prompt_settings)
            st.success("✅ 프롬프트 설정이 저장되었습니다!")
            st.info("새로운 설정은 다음 분석부터 적용됩니다.")
    
    with col2:
        if st.button("🔄 기본값 복원", use_container_width=True):
            if st.checkbox("정말로 기본값으로 복원하시겠습니까?"):
                reset_prompt_settings()
                st.success("✅ 기본 프롬프트로 복원되었습니다!")
                st.rerun()


def render_system_prompt_settings(settings: Dict) -> Dict:
    """시스템 프롬프트 설정"""
    st.markdown("### 📝 시스템 프롬프트")
    st.info("AI의 역할과 기본 지침을 설정합니다.")
    
    # 시스템 프롬프트
    settings['system_prompt'] = st.text_area(
        "시스템 프롬프트",
        value=settings.get('system_prompt', DEFAULT_SYSTEM_PROMPT),
        height=150,
        help="AI의 역할과 전반적인 분석 방향을 설정합니다"
    )
    
    st.markdown("### 📌 분석 지침")
    
    # 분석 지침
    settings['analysis_instruction'] = st.text_area(
        "메타데이터 활용 지침",
        value=settings.get('analysis_instruction', DEFAULT_ANALYSIS_INSTRUCTION),
        height=100,
        help="메타데이터와 이미지 내용의 우선순위를 설정합니다"
    )
    
    # 추가 지침
    st.markdown("### ➕ 추가 지침")
    
    col1, col2 = st.columns(2)
    
    with col1:
        settings['require_labels'] = st.checkbox(
            "항목 레이블 제거 요구",
            value=settings.get('require_labels', True),
            help="'A1.', '장르:' 같은 레이블 없이 내용만 작성하도록 요구"
        )
    
    with col2:
        settings['strict_format'] = st.checkbox(
            "엄격한 형식 요구",
            value=settings.get('strict_format', True),
            help="각 항목을 정확히 구분하여 작성하도록 요구"
        )
    
    # Temperature와 Max Tokens 설정
    st.markdown("### ⚙️ 모델 파라미터")
    
    col3, col4 = st.columns(2)
    
    with col3:
        settings['temperature'] = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=settings.get('temperature', 0.7),
            step=0.1,
            help="높을수록 더 창의적이고 다양한 응답을 생성합니다."
        )
    
    with col4:
        settings['max_tokens'] = st.number_input(
            "최대 토큰 수",
            min_value=500,
            max_value=4000,
            value=settings.get('max_tokens', 2000),
            step=100,
            help="AI 응답의 최대 길이를 제한합니다."
        )
    
    return settings


def render_analysis_items_settings(settings: Dict) -> Dict:
    """분석 항목 설정"""
    st.markdown("### 📋 분석 항목 설정")
    st.info("각 분석 항목의 제목과 설명을 커스터마이즈할 수 있습니다.")
    
    # 분석 항목 리스트 가져오기
    analysis_items = settings.get('analysis_items', DEFAULT_ANALYSIS_ITEMS.copy())
    
    # 각 항목 편집
    for i, item in enumerate(analysis_items):
        with st.expander(f"{item['label']}. {item['title']}", expanded=False):
            col1, col2 = st.columns([1, 3])
            
            with col1:
                item['label'] = st.text_input(
                    "레이블",
                    value=item['label'],
                    key=f"label_{i}",
                    help="A1, A2 같은 항목 번호"
                )
            
            with col2:
                item['title'] = st.text_input(
                    "항목 제목",
                    value=item['title'],
                    key=f"title_{i}",
                    help="분석 항목의 이름"
                )
            
            item['instruction'] = st.text_area(
                "설명/지침",
                value=item['instruction'],
                key=f"instruction_{i}",
                height=80,
                help="이 항목에 대한 구체적인 지침"
            )
            
            if item.get('min_length', 0) > 0:
                col3, col4 = st.columns(2)
                with col3:
                    if item['label'] == 'A4':  # 태그
                        item['min_length'] = st.number_input(
                            "최소 태그 개수",
                            min_value=1,
                            max_value=30,
                            value=item.get('min_length', 10),
                            key=f"min_length_{i}"
                        )
                    else:
                        item['min_length'] = st.number_input(
                            "최소 글자 수",
                            min_value=0,
                            max_value=500,
                            value=item.get('min_length', 200),
                            key=f"min_length_{i}"
                        )
    
    settings['analysis_items'] = analysis_items
    return settings


def render_selection_options(settings: Dict) -> Dict:
    """선택 옵션 설정"""
    st.markdown("### 🏷️ 선택 옵션 관리")
    
    # 장르 목록
    st.markdown("#### 🎬 장르 목록")
    genres = settings.get('genres', GENRES.copy())
    
    # 장르 편집
    genres_text = st.text_area(
        "장르 목록 (한 줄에 하나씩)",
        value="\n".join(genres),
        height=200,
        help="AI가 선택할 수 있는 장르 목록"
    )
    settings['genres'] = [g.strip() for g in genres_text.split('\n') if g.strip()]
    
    # 신규 장르 추가
    col1, col2 = st.columns([3, 1])
    with col1:
        new_genre = st.text_input("새 장르 추가", key="new_genre")
    with col2:
        if st.button("➕ 추가", key="add_genre", use_container_width=True):
            if new_genre and new_genre not in settings['genres']:
                settings['genres'].append(new_genre)
                st.success(f"✅ '{new_genre}' 추가됨")
                st.rerun()
    
    st.markdown("---")
    
    # 표현형식 목록
    st.markdown("#### 🎨 표현형식 목록")
    format_types = settings.get('format_types', FORMAT_TYPES.copy())
    
    # 표현형식 편집
    format_types_text = st.text_area(
        "표현형식 목록 (한 줄에 하나씩)",
        value="\n".join(format_types),
        height=150,
        help="AI가 선택할 수 있는 표현형식 목록"
    )
    settings['format_types'] = [f.strip() for f in format_types_text.split('\n') if f.strip()]
    
    # 신규 표현형식 추가
    col3, col4 = st.columns([3, 1])
    with col3:
        new_format = st.text_input("새 표현형식 추가", key="new_format")
    with col4:
        if st.button("➕ 추가", key="add_format", use_container_width=True):
            if new_format and new_format not in settings['format_types']:
                settings['format_types'].append(new_format)
                st.success(f"✅ '{new_format}' 추가됨")
                st.rerun()
    
    return settings


def render_prompt_preview(settings: Dict):
    """프롬프트 미리보기"""
    st.markdown("### 👁️ 프롬프트 미리보기")
    st.info("실제로 AI에게 전송될 프롬프트를 확인할 수 있습니다.")
    
    # 예제 컨텍스트
    example_context = {
        "title": "Nike Air Max 2024 - 'Run Your Way' 캠페인",
        "uploader": "Nike Korea",
        "duration": "30초",
        "view_count": 1500000,
        "tags": ["나이키", "에어맥스", "운동화", "스포츠", "광고"],
        "description": "당신만의 방식으로 달리세요. 새로운 Nike Air Max 2024와 함께하는 자유로운 러닝의 시작."
    }
    
    # 프롬프트 생성
    prompt = generate_prompt_from_settings(settings, example_context, 6)
    
    # 시스템 프롬프트
    st.markdown("#### 시스템 메시지")
    st.code(settings.get('system_prompt', DEFAULT_SYSTEM_PROMPT), language=None)
    
    # 사용자 프롬프트
    st.markdown("#### 사용자 메시지")
    st.code(prompt, language=None)
    
    # 예상 토큰 수 계산
    estimated_tokens = len(prompt.split()) + len(settings.get('system_prompt', '').split())
    st.caption(f"예상 토큰 수: 약 {estimated_tokens * 1.3:.0f}개 (한글 특성상 실제로는 더 많을 수 있음)")


def generate_prompt_from_settings(settings: Dict, context: Dict, image_count: int) -> str:
    """설정에서 프롬프트 생성"""
    # 메타데이터 정보 구성
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
        metadata_info.append(f"YouTube 태그: {', '.join(context['tags'])}")
    
    metadata_text = "\n".join(metadata_info)
    
    # 설명 텍스트
    description_text = ""
    if context.get("description"):
        description_text = f"\n\n영상 설명:\n{context['description']}"
    
    # 분석 지침
    analysis_instruction = settings.get('analysis_instruction', DEFAULT_ANALYSIS_INSTRUCTION)
    
    # 분석 항목 구성
    analysis_items_text = []
    for item in settings.get('analysis_items', DEFAULT_ANALYSIS_ITEMS):
        item_text = f"{item['label']}. {item['title']}"
        
        # A1 (장르)와 A5 (표현형식)는 선택 목록 추가
        if item['label'] == 'A1':
            genres = settings.get('genres', GENRES)
            item_text += f" (다음 중 하나만 선택): {', '.join(genres)}"
        elif item['label'] == 'A5':
            format_types = settings.get('format_types', FORMAT_TYPES)
            item_text += f" (다음 중 하나만 선택): {', '.join(format_types)}"
        
        # 설명/지침 추가
        if item['instruction']:
            item_text += f" ({item['instruction']})"
        
        analysis_items_text.append(item_text)
    
    # 추가 지침
    additional_instructions = []
    if settings.get('require_labels', True):
        additional_instructions.append('각 항목의 답변에는 "장르 판단 이유:", "영상의 특징:" 같은 레이블을 포함하지 말고 내용만 작성하세요.')
    
    if settings.get('strict_format', True):
        additional_instructions.append("각 항목은 빈 줄로 구분하여 명확히 구분해주세요.")
    
    # 전체 프롬프트 조합
    prompt = f"""영상 메타데이터:
{metadata_text}{description_text}

위 영상에서 추출한 {image_count}개의 이미지를 분석해주세요. 
첫 번째 이미지는 썸네일이며, 나머지는 영상의 대표 장면들입니다.

{analysis_instruction}

다음 {len(analysis_items_text)}개 항목을 모두 작성해주세요.{' ' + ' '.join(additional_instructions) if additional_instructions else ''}

분석 항목:
{chr(10).join(analysis_items_text)}"""
    
    return prompt


def load_prompt_settings() -> Dict:
    """프롬프트 설정 로드"""
    settings_file = "config/prompt_settings.json"
    
    if os.path.exists(settings_file):
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"프롬프트 설정 로드 실패: {str(e)}")
    
    # 기본 설정 반환
    return {
        'system_prompt': DEFAULT_SYSTEM_PROMPT,
        'analysis_instruction': DEFAULT_ANALYSIS_INSTRUCTION,
        'analysis_items': DEFAULT_ANALYSIS_ITEMS.copy(),
        'genres': GENRES.copy(),
        'format_types': FORMAT_TYPES.copy(),
        'require_labels': True,
        'strict_format': True,
        'temperature': 0.7,
        'max_tokens': 2000
    }


def save_prompt_settings(settings: Dict):
    """프롬프트 설정 저장"""
    settings_file = "config/prompt_settings.json"
    os.makedirs(os.path.dirname(settings_file), exist_ok=True)
    
    try:
        settings['updated_at'] = datetime.now().isoformat()
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        logger.info("프롬프트 설정 저장 완료")
    except Exception as e:
        logger.error(f"프롬프트 설정 저장 실패: {str(e)}")
        raise


def reset_prompt_settings():
    """프롬프트 설정 초기화"""
    settings_file = "config/prompt_settings.json"
    
    if os.path.exists(settings_file):
        try:
            os.remove(settings_file)
            logger.info("프롬프트 설정 초기화 완료")
        except Exception as e:
            logger.error(f"프롬프트 설정 초기화 실패: {str(e)}")
            raise


# 외부에서 사용할 함수들
def get_custom_prompt_settings() -> Dict:
    """커스텀 프롬프트 설정 가져오기 (AI 분석기에서 사용)"""
    return load_prompt_settings()


def get_custom_system_prompt() -> str:
    """커스텀 시스템 프롬프트 가져오기"""
    settings = load_prompt_settings()
    return settings.get('system_prompt', DEFAULT_SYSTEM_PROMPT)


def get_custom_user_prompt(context: Dict, image_count: int) -> str:
    """커스텀 사용자 프롬프트 생성"""
    settings = load_prompt_settings()
    return generate_prompt_from_settings(settings, context, image_count)


def get_model_parameters() -> Dict:
    """모델 파라미터 가져오기"""
    settings = load_prompt_settings()
    return {
        'temperature': settings.get('temperature', 0.7),
        'max_tokens': settings.get('max_tokens', 2000)
    }
