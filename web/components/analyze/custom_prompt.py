"""맞춤형 분석 프롬프트 UI 컴포넌트"""

import streamlit as st
from typing import Optional, Dict, Any
import json
from config.analysis_prompts import AnalysisPromptTemplates

def render_custom_analysis_prompt() -> Optional[str]:
    """맞춤형 분석 요청 UI 렌더링"""
    st.subheader("🎯 맞춤형 분석 요청")
    
    # 템플릿 선택
    templates = AnalysisPromptTemplates()
    template_categories = templates.get_categories()
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        selected_category = st.selectbox(
            "분석 카테고리 선택",
            options=list(template_categories.keys()),
            help="목적에 맞는 분석 카테고리를 선택하세요"
        )
    
    with col2:
        if selected_category:
            category_templates = template_categories[selected_category]
            selected_template = st.selectbox(
                "템플릿 선택",
                options=list(category_templates.keys()),
                help="구체적인 분석 템플릿을 선택하세요"
            )
        else:
            selected_template = None
    
    # 사용자 맞춤 요청사항
    st.markdown("### 📝 상세 분석 요청사항")
    
    # 템플릿 기반 초기값 설정
    template_content = ""
    if selected_category and selected_template:
        template_content = templates.get_template(selected_category, selected_template)
    
    custom_prompt = st.text_area(
        "구체적인 분석 요청사항을 입력하세요",
        value=template_content,
        height=150,
        help="예: '자동차 광고용 주행감 분석 - 도로 환경, 차량 움직임, 운전자 반응에 집중'"
    )
    
    # 키워드 추출 및 태그
    if custom_prompt:
        st.markdown("### 🏷️ 분석 키워드")
        keywords = extract_keywords(custom_prompt)
        
        if keywords:
            # 키워드를 태그 형태로 표시
            keyword_html = " ".join([f"<span style='background-color: #e1f5fe; padding: 2px 8px; border-radius: 12px; margin: 2px;'>{kw}</span>" for kw in keywords])
            st.markdown(keyword_html, unsafe_allow_html=True)
    
    # 프롬프트 미리보기
    if custom_prompt:
        with st.expander("🔍 최종 프롬프트 미리보기", expanded=False):
            preview_prompt = generate_preview_prompt(custom_prompt)
            st.code(preview_prompt, language="text")
    
    # 저장 및 적용
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("💾 프롬프트 저장", type="secondary"):
            save_custom_prompt(custom_prompt, selected_category, selected_template)
            st.success("프롬프트가 저장되었습니다!")
    
    with col2:
        if st.button("🔄 초기화", type="secondary"):
            st.rerun()
    
    with col3:
        if st.button("✅ 분석 시작", type="primary", disabled=not custom_prompt):
            return custom_prompt
    
    return None

def extract_keywords(text: str) -> list:
    """텍스트에서 분석 키워드 추출"""
    # 간단한 키워드 추출 로직
    keywords = []
    
    # 산업/도메인 키워드
    industry_keywords = ['자동차', '패션', '뷰티', '식음료', '기술', 'IT', '라이프스타일', '여행', '건강']
    for keyword in industry_keywords:
        if keyword in text:
            keywords.append(keyword)
    
    # 분석 타입 키워드
    analysis_keywords = ['주행감', '스타일링', '트렌드', '브랜딩', '감정', '색상', '구성', '움직임', '소리']
    for keyword in analysis_keywords:
        if keyword in text:
            keywords.append(keyword)
    
    # 기술적 키워드
    tech_keywords = ['프레임', '장면', '컷', '앵글', '조명', '색보정', '편집', '트랜지션']
    for keyword in tech_keywords:
        if keyword in text:
            keywords.append(keyword)
    
    return list(set(keywords))  # 중복 제거

def generate_preview_prompt(custom_prompt: str) -> str:
    """최종 분석 프롬프트 미리보기 생성"""
    base_prompt = """비디오 분석 요청:

사용자 요청사항:
{custom_request}

분석 시 고려사항:
- 영상의 전체적인 구성과 흐름
- 주요 시각적 요소들의 특징
- 색상, 조명, 앵글 등의 기술적 요소
- 감정적/심리적 임팩트
- 타겟 목적에 맞는 효과성

분석 결과는 구체적이고 실용적인 인사이트로 제공해주세요."""
    
    return base_prompt.format(custom_request=custom_prompt)

def save_custom_prompt(prompt: str, category: str = None, template: str = None):
    """사용자 맞춤 프롬프트 저장"""
    try:
        # 간단한 로컬 저장 (실제로는 데이터베이스나 파일에 저장)
        prompt_data = {
            "prompt": prompt,
            "category": category,
            "template": template,
            "timestamp": st.session_state.get("current_time", "")
        }
        
        # 세션 상태에 저장
        if "saved_prompts" not in st.session_state:
            st.session_state.saved_prompts = []
        
        st.session_state.saved_prompts.append(prompt_data)
        
    except Exception as e:
        st.error(f"프롬프트 저장 중 오류 발생: {str(e)}")

def load_saved_prompts() -> list:
    """저장된 프롬프트 목록 불러오기"""
    return st.session_state.get("saved_prompts", [])

def render_saved_prompts_sidebar():
    """사이드바에 저장된 프롬프트 목록 표시"""
    saved_prompts = load_saved_prompts()
    
    if saved_prompts:
        st.sidebar.markdown("### 💾 저장된 프롬프트")
        
        for i, prompt_data in enumerate(saved_prompts[-5:]):  # 최근 5개만 표시
            with st.sidebar.expander(f"프롬프트 {i+1}"):
                st.text(prompt_data["prompt"][:100] + "..." if len(prompt_data["prompt"]) > 100 else prompt_data["prompt"])
                if st.button(f"사용하기", key=f"use_prompt_{i}"):
                    return prompt_data["prompt"]
    
    return None