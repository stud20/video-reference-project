# web/components/analyze/reanalysis.py
"""
재추론 기능 - 멀티 모델 지원
"""

import streamlit as st
import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass

from utils.logger import get_logger
from core.analysis import VideoAnalyzer
from core.analysis.providers import OpenAIProvider, ClaudeProvider, GeminiProvider
from core.video.models import Video

logger = get_logger(__name__)


@dataclass
class ModelComparisonResult:
    """모델 비교 결과 데이터 클래스"""
    model_name: str
    display_name: str
    result: Optional[Dict[str, Any]]
    status: str  # 'success', 'failed', 'running'
    error_message: Optional[str] = None
    analysis_time: Optional[float] = None


class MultiModelAnalyzer:
    """멀티 모델 분석기"""
    
    # 지원 모델 정의
    SUPPORTED_MODELS = {
        "gpt-4o": {
            "display_name": "GPT-4o",
            "description": "OpenAI의 최신 멀티모달 모델 (균형잡힌 분석)",
            "color": "#10A37F",
            "icon": "🤖",
            "provider_class": OpenAIProvider,
            "config": {
                "model": "gpt-4o",
                "api_key": os.getenv("FACTCHAT_API_KEY", "NPpDGrF4ShhrecUsBJm1dIIW7DZab4qC"),
                "api_type": "factchat"
            }
        },
        "claude-sonnet-4-20250514": {
            "display_name": "Claude Sonnet 4",
            "description": "Anthropic의 Claude Sonnet (상세한 분석)",
            "color": "#D97706",
            "icon": "🧠",
            "provider_class": ClaudeProvider,
            "config": {
                "model": "claude-sonnet-4-20250514",
                "api_key": os.getenv("FACTCHAT_API_KEY", "NPpDGrF4ShhrecUsBJm1dIIW7DZab4qC"),
                "api_type": "factchat"
            }
        },
        "gemini-2.0-flash": {
            "display_name": "Gemini 2.0 Flash",
            "description": "Google의 Gemini Flash (창의적 분석)",
            "color": "#4285F4",
            "icon": "✨",
            "provider_class": GeminiProvider,
            "config": {
                "model": "gemini-2.0-flash",
                "api_key": os.getenv("FACTCHAT_API_KEY", "NPpDGrF4ShhrecUsBJm1dIIW7DZab4qC"),
                "api_type": "factchat"
            }
        }
    }
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """모델 정보 반환"""
        return self.SUPPORTED_MODELS.get(model_name, {})
    
    def analyze_with_single_model(self, video: Video, model_name: str) -> ModelComparisonResult:
        """단일 모델로 재분석"""
        start_time = datetime.now()
        model_info = self.get_model_info(model_name)
        
        result = ModelComparisonResult(
            model_name=model_name,
            display_name=model_info["display_name"],
            result=None,
            status="running"
        )
        
        try:
            self.logger.info(f"🤖 {model_info['display_name']} 분석 시작...")
            
            # Provider 인스턴스 생성
            provider_class = model_info["provider_class"]
            provider = provider_class(**model_info["config"])
            
            # VideoAnalyzer 생성 및 분석 실행
            analyzer = VideoAnalyzer(provider=provider)
            analysis_result = analyzer.analyze_video(video)
            
            if analysis_result:
                result.result = analysis_result
                result.status = "success"
                self.logger.info(f"✅ {model_info['display_name']} 분석 완료")
            else:
                result.status = "failed"
                result.error_message = "분석 결과 없음"
                self.logger.error(f"❌ {model_info['display_name']} 분석 실패: 결과 없음")
        
        except Exception as e:
            result.status = "failed"
            result.error_message = str(e)
            self.logger.error(f"❌ {model_info['display_name']} 분석 실패: {e}")
        
        # 분석 시간 계산
        end_time = datetime.now()
        result.analysis_time = (end_time - start_time).total_seconds()
        
        return result
    
    def analyze_with_multiple_models(self, video: Video, model_names: List[str]) -> Dict[str, ModelComparisonResult]:
        """여러 모델로 분석"""
        self.logger.info(f"🔬 {len(model_names)}개 모델로 분석 시작...")
        
        results = {}
        
        # 순차 실행 (Streamlit 환경에서 안전)
        for model_name in model_names:
            result = self.analyze_with_single_model(video, model_name)
            results[model_name] = result
        
        self.logger.info(f"✅ 모든 모델 분석 완료")
        return results
    
    def save_comparison_result(self, video: Video, comparison_results: Dict[str, ModelComparisonResult], 
                             selected_model: Optional[str] = None):
        """비교 결과 저장"""
        try:
            # 비교 결과 디렉토리 생성
            comparison_dir = os.path.join(video.session_dir, "model_comparison")
            os.makedirs(comparison_dir, exist_ok=True)
            
            # 비교 결과 저장
            comparison_data = {
                "timestamp": datetime.now().isoformat(),
                "models_analyzed": list(comparison_results.keys()),
                "selected_model": selected_model,
                "results": {}
            }
            
            for model_name, comp_result in comparison_results.items():
                comparison_data["results"][model_name] = {
                    "display_name": comp_result.display_name,
                    "status": comp_result.status,
                    "error_message": comp_result.error_message,
                    "analysis_time": comp_result.analysis_time,
                    "result": comp_result.result if comp_result.result else None
                }
            
            # JSON으로 저장
            comparison_file = os.path.join(comparison_dir, 
                                         f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            with open(comparison_file, 'w', encoding='utf-8') as f:
                json.dump(comparison_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"💾 비교 결과 저장: {comparison_file}")
            
            # 선택된 결과가 있으면 메인 결과로 업데이트
            if selected_model and selected_model in comparison_results:
                selected_result = comparison_results[selected_model].result
                if selected_result:
                    self._update_main_analysis_result(video, selected_result, selected_model)
            
        except Exception as e:
            self.logger.error(f"비교 결과 저장 실패: {e}")
    
    def _update_main_analysis_result(self, video: Video, result: Dict[str, Any], model_name: str):
        """메인 분석 결과 업데이트"""
        try:
            # 사용자가 선택했음을 표시
            result['user_selected'] = True
            result['selected_from_comparison'] = True
            result['model_used'] = f"factchat:{model_name}"
            
            # Video 객체에 결과 저장
            video.analysis_result = result
            
            # JSON 파일로 저장
            result_path = os.path.join(video.session_dir, "analysis_result.json")
            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"✅ 메인 분석 결과 업데이트: {model_name}")
            
        except Exception as e:
            self.logger.error(f"메인 분석 결과 업데이트 실패: {e}")


# 전역 인스턴스
multi_model_analyzer = MultiModelAnalyzer()


def render_reanalysis_section(video: Video):
    """재추론 섹션 렌더링"""
    if not video:
        st.error("❌ 분석 결과가 없습니다.")
        return
    
    st.markdown("### 🔄 AI 모델 재추론")
    st.markdown("다른 AI 모델로 재분석하여 다양한 관점의 결과를 비교해보세요.")
    
    # 재추론 옵션 선택
    with st.expander("🎯 재추론 옵션", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            # 모델 선택
            available_models = list(multi_model_analyzer.SUPPORTED_MODELS.keys())
            selected_models = st.multiselect(
                "분석할 모델 선택",
                options=available_models,
                default=available_models[:2],  # 기본적으로 처음 2개 선택
                help="여러 모델을 선택하여 결과를 비교할 수 있습니다."
            )
        
        with col2:
            # 분석 모드
            analysis_mode = st.radio(
                "분석 모드",
                options=["빠른 분석", "상세 분석"],
                index=0,
                help="상세 분석은 더 많은 이미지를 사용합니다."
            )
    
    # 모델 정보 표시
    if selected_models:
        st.markdown("#### 선택된 모델")
        cols = st.columns(len(selected_models))
        
        for idx, model_name in enumerate(selected_models):
            model_info = multi_model_analyzer.get_model_info(model_name)
            with cols[idx]:
                st.markdown(f"""
                <div style="text-align: center; padding: 10px; border-radius: 10px; 
                           background-color: {model_info['color']}20; border: 1px solid {model_info['color']};">
                    <h4>{model_info['icon']} {model_info['display_name']}</h4>
                    <p style="font-size: 0.9em; color: gray;">{model_info['description']}</p>
                </div>
                """, unsafe_allow_html=True)
    
    # 재분석 버튼
    if st.button("🔄 재분석 시작", use_container_width=True, type="primary", 
                disabled=not selected_models):
        if not selected_models:
            st.warning("⚠️ 분석할 모델을 선택해주세요.")
            return
        
        # 분석 진행
        with st.spinner(f"🔄 {len(selected_models)}개 모델로 재분석 중..."):
            # 진행 상황 표시용 placeholder
            progress_container = st.container()
            
            # 각 모델별로 분석 실행
            comparison_results = {}
            
            for idx, model_name in enumerate(selected_models):
                model_info = multi_model_analyzer.get_model_info(model_name)
                
                # 진행 상황 업데이트
                with progress_container:
                    progress = (idx + 1) / len(selected_models)
                    st.progress(progress, text=f"{model_info['icon']} {model_info['display_name']} 분석 중...")
                
                # 모델 분석 실행
                result = multi_model_analyzer.analyze_with_single_model(video, model_name)
                comparison_results[model_name] = result
        
        # 결과 표시
        st.success(f"✅ {len(selected_models)}개 모델 분석 완료!")
        
        # 결과 비교 표시
        _display_comparison_results(video, comparison_results)


def _display_comparison_results(video: Video, comparison_results: Dict[str, ModelComparisonResult]):
    """비교 결과 표시"""
    st.markdown("### 📊 분석 결과 비교")
    
    # 성공한 결과만 필터링
    successful_results = {k: v for k, v in comparison_results.items() if v.status == "success"}
    
    if not successful_results:
        st.error("❌ 모든 모델 분석이 실패했습니다.")
        return
    
    # 탭으로 각 모델 결과 표시
    tabs = st.tabs([
        f"{multi_model_analyzer.get_model_info(model)['icon']} {result.display_name}" 
        for model, result in successful_results.items()
    ])
    
    for idx, (model_name, result) in enumerate(successful_results.items()):
        with tabs[idx]:
            if result.result:
                _display_single_result(model_name, result)
    
    # 결과 선택 및 저장
    st.markdown("---")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        selected_model = st.selectbox(
            "📌 메인 결과로 사용할 모델 선택",
            options=list(successful_results.keys()),
            format_func=lambda x: f"{multi_model_analyzer.get_model_info(x)['icon']} {successful_results[x].display_name}"
        )
    
    with col2:
        if st.button("💾 선택된 결과 저장", use_container_width=True):
            multi_model_analyzer.save_comparison_result(video, comparison_results, selected_model)
            st.success("✅ 결과가 저장되었습니다!")
            st.rerun()
    
    with col3:
        if st.button("📊 비교 결과 저장", use_container_width=True):
            multi_model_analyzer.save_comparison_result(video, comparison_results)
            st.success("✅ 비교 결과가 저장되었습니다!")


def _display_single_result(model_name: str, result: ModelComparisonResult):
    """단일 모델 결과 표시"""
    model_info = multi_model_analyzer.get_model_info(model_name)
    
    # 분석 시간 표시
    if result.analysis_time:
        st.info(f"⏱️ 분석 시간: {result.analysis_time:.1f}초")
    
    if result.status == "failed":
        st.error(f"❌ 분석 실패: {result.error_message}")
        return
    
    if not result.result:
        st.warning("⚠️ 분석 결과가 없습니다.")
        return
    
    # 결과 표시
    res = result.result
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🎬 장르")
        st.info(res.get('genre', 'Unknown'))
        
        st.markdown("#### 🎨 표현 형식")
        st.info(res.get('expression_style', '실사'))
    
    with col2:
        st.markdown("#### 🎯 타겟 오디언스")
        st.info(res.get('target_audience', '일반'))
        
        st.markdown("#### 🌈 무드/톤")
        st.info(res.get('mood_tone', '중립적'))
    
    # 추론 근거
    st.markdown("#### 💭 분석 근거")
    st.text_area("", value=res.get('reasoning', ''), height=150, disabled=True)
    
    # 주요 특징
    st.markdown("#### ✨ 주요 특징")
    st.text_area("", value=res.get('features', ''), height=100, disabled=True)
    
    # 태그
    if res.get('tags'):
        st.markdown("#### 🏷️ 태그")
        tag_html = " ".join([f"<span style='background-color: {model_info['color']}30; "
                            f"padding: 5px 10px; margin: 2px; border-radius: 15px; "
                            f"display: inline-block;'>#{tag}</span>" 
                            for tag in res['tags']])
        st.markdown(tag_html, unsafe_allow_html=True)
