# src/ui/tabs/analyze_function_recom.py
"""
재추론 기능 - 멀티 모델 지원
"""

import streamlit as st
import os
from typing import Dict, Any, Optional
from datetime import datetime

from src.analyzer.multi_model_analyzer import multi_model_analyzer, ModelComparisonResult
from src.models.video import Video
from utils.logger import get_logger

logger = get_logger(__name__)

def render_reanalysis_section(video: Video):
    """재추론 섹션 렌더링"""
    if not video:
        st.error("❌ 분석 결과가 없습니다.")
        return
    
    st.markdown("### 🔄 AI 모델 재추론")
    st.markdown("다른 AI 모델로 재분석하여 다양한 관점의 결과를 비교해보세요.")
    
    # 모델 선택 탭
    tab1, tab2 = st.tabs(["🎯 개별 모델", "🔬 전체 비교"])
    
    with tab1:
        render_individual_model_section(video)
    
    with tab2:
        render_comparison_section(video)

def render_individual_model_section(video: Video):
    """개별 모델 재추론 섹션"""
    st.markdown("#### 특정 모델로 재분석")
    
    # 모델 선택 그리드
    col1, col2 = st.columns(2)
    
    with col1:
        # Claude 버튼
        model_info = multi_model_analyzer.get_model_info("claude-sonnet-4-20250514")
        if st.button(
            f"{model_info['icon']} {model_info['display_name']}\n{model_info['description']}",
            key="reanalyze_claude",
            help="Claude Sonnet 4로 상세한 재분석을 수행합니다",
            use_container_width=True
        ):
            run_individual_analysis(video, "claude-sonnet-4-20250514")
        
        # GPT-4.1 Nano 버튼
        model_info = multi_model_analyzer.get_model_info("gpt-4.1-nano")
        if st.button(
            f"{model_info['icon']} {model_info['display_name']}\n{model_info['description']}",
            key="reanalyze_nano",
            help="GPT-4.1 Nano로 빠른 재분석을 수행합니다",
            use_container_width=True
        ):
            run_individual_analysis(video, "gpt-4.1-nano")
    
    with col2:
        # Gemini 버튼
        model_info = multi_model_analyzer.get_model_info("gemini-2.0-flash")
        if st.button(
            f"{model_info['icon']} {model_info['display_name']}\n{model_info['description']}",
            key="reanalyze_gemini",
            help="Gemini 2.0 Flash로 창의적인 재분석을 수행합니다",
            use_container_width=True
        ):
            run_individual_analysis(video, "gemini-2.0-flash")
        
        # GPT-4o 버튼
        model_info = multi_model_analyzer.get_model_info("gpt-4o")
        if st.button(
            f"{model_info['icon']} {model_info['display_name']}\n{model_info['description']}",
            key="reanalyze_gpt4o",
            help="GPT-4o로 균형잡힌 재분석을 수행합니다",
            use_container_width=True
        ):
            run_individual_analysis(video, "gpt-4o")

def render_comparison_section(video: Video):
    """전체 모델 비교 섹션"""
    st.markdown("#### 모든 모델 동시 비교")
    
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col2:
        if st.button(
            "🚀 모든 모델로 분석",
            key="analyze_all_models",
            type="primary",
            help="4개 모델로 동시에 분석하고 결과를 비교합니다 (2-3분 소요)",
            use_container_width=True
        ):
            run_all_models_analysis(video)
    
    st.markdown("---")
    
    # 예상 소요 시간 안내
    st.info("""
    📊 **전체 모델 비교 분석**
    - 🤖 GPT-4o, 🧠 Claude Sonnet 4, ✨ Gemini 2.0 Flash, ⚡ GPT-4.1 Nano
    - ⏱️ 예상 소요 시간: 2-3분
    - 📋 결과를 3컬럼으로 비교하여 최적의 분석을 선택할 수 있습니다
    """)

def run_individual_analysis(video: Video, model_name: str):
    """개별 모델 분석 실행"""
    model_info = multi_model_analyzer.get_model_info(model_name)
    
    with st.spinner(f"🤖 {model_info['display_name']} 분석 중..."):
        try:
            # 단일 모델 분석
            result = multi_model_analyzer.analyze_with_single_model(video, model_name)
            
            if result.status == "success" and result.result:
                # 성공 시 결과 비교 표시
                st.success(f"✅ {model_info['display_name']} 분석 완료!")
                
                # 기존 결과와 비교 표시
                display_comparison_results({
                    "기본 분석": get_current_analysis_result(video),
                    model_info['display_name']: result
                }, video, allow_selection=True)
                
            else:
                st.error(f"❌ {model_info['display_name']} 분석 실패: {result.error_message}")
        
        except Exception as e:
            st.error(f"❌ 분석 중 오류 발생: {str(e)}")
            logger.error(f"Individual analysis failed for {model_name}: {e}")

def run_all_models_analysis(video: Video):
    """모든 모델 분석 실행"""
    with st.status("🔬 모든 모델로 분석 중...", expanded=True) as status:
        try:
            # 진행률 표시
            progress_placeholder = st.empty()
            models = list(multi_model_analyzer.SUPPORTED_MODELS.keys())
            
            results = {}
            
            for i, model_name in enumerate(models):
                model_info = multi_model_analyzer.get_model_info(model_name)
                
                # 진행 상황 업데이트
                progress = (i + 1) / len(models)
                progress_placeholder.progress(progress, f"🤖 {model_info['display_name']} 분석 중... ({i+1}/{len(models)})")
                
                # 분석 실행
                result = multi_model_analyzer.analyze_with_single_model(video, model_name)
                results[model_name] = result
                
                # 결과 로깅
                if result.status == "success":
                    st.write(f"✅ {model_info['display_name']} 완료")
                else:
                    st.write(f"❌ {model_info['display_name']} 실패: {result.error_message}")
            
            progress_placeholder.empty()
            status.update(label="✅ 모든 모델 분석 완료!", state="complete")
            
            # 결과 저장
            multi_model_analyzer.save_comparison_result(video, results)
            
        except Exception as e:
            st.error(f"❌ 분석 중 오류 발생: {str(e)}")
            status.update(label="❌ 분석 실패", state="error")
            logger.error(f"All models analysis failed: {e}")
            return
    
    # 결과 표시
    display_all_models_comparison(results, video)

def display_comparison_results(results: Dict[str, Any], video: Video, allow_selection: bool = False):
    """비교 결과 표시 (2개 결과용) - 컬럼 중첩 방지"""
    st.markdown("### 📊 분석 결과 비교")
    
    # 각 결과를 순차적으로 표시 (컬럼 사용하지 않음)
    for i, (name, result) in enumerate(results.items()):
        with st.container():
            display_single_result_card(name, result, f"compare_{i}", allow_selection, video)
            
            # 결과 간 구분선 (마지막 결과 제외)
            if i < len(results) - 1:
                st.markdown("---")

def display_all_models_comparison(results: Dict[str, ModelComparisonResult], video: Video):
    """전체 모델 비교 결과 표시 - 컬럼 중첩 문제 해결"""
    st.markdown("### 🔬 3개 모델 분석 결과 비교")
    st.markdown("각 모델의 독특한 관점으로 분석한 결과를 비교하고 최적의 결과를 선택하세요.")
    
    # 성공한 모델만 필터링
    successful_results = {
        name: result for name, result in results.items() 
        if result.status == "success" and result.result
    }
    
    if not successful_results:
        st.warning("⚠️ 성공한 분석 결과가 없습니다.")
        return
    
    # 통계 정보 (컬럼 중첩 방지)
    display_analysis_summary(results)
    
    st.markdown("---")
    
    # 각 모델 결과를 순차적으로 표시 (컬럼 사용하지 않음)
    for i, (model_name, result) in enumerate(successful_results.items()):
        model_info = multi_model_analyzer.get_model_info(model_name)
        
        # 각 모델마다 컨테이너로 분리
        with st.container():
            display_single_result_card(
                model_info['display_name'], 
                result, 
                f"select_{model_name}", 
                True, 
                video,
                model_name=model_name
            )
            
            # 모델 간 구분선 (마지막 모델 제외)
            if i < len(successful_results) - 1:
                st.markdown("---")

def display_single_result_card(name: str, result: Any, key_prefix: str, allow_selection: bool, video: Video, model_name: Optional[str] = None):
    """단일 결과 카드 표시 - 컬럼 중첩 제거"""
    
    # 모델 정보 가져오기
    if model_name:
        model_info = multi_model_analyzer.get_model_info(model_name)
        color = model_info.get('color', '#6B7280')
        icon = model_info.get('icon', '🤖')
    else:
        color = '#6B7280'
        icon = '📊'
    
    # 카드 헤더
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {color}20, {color}10);
        border: 1px solid {color}40;
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 16px;
        text-align: center;
    ">
        <div style="font-size: 24px; margin-bottom: 8px;">{icon}</div>
        <div style="font-weight: bold; color: {color}; font-size: 16px;">{name}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 결과 내용
    if hasattr(result, 'result') and result.result:
        # ModelComparisonResult 객체
        analysis_result = result.result
        
        # 주요 정보 - 컬럼 대신 단순 표시
        st.markdown("**🎬 장르**")
        st.info(analysis_result.genre)
        
        st.markdown("**🎨 표현형식**") 
        st.info(analysis_result.format_type)
        
        # 특징 미리보기
        st.markdown("**✨ 주요 특징**")
        features_preview = analysis_result.features[:120] + "..." if len(analysis_result.features) > 120 else analysis_result.features
        st.write(features_preview)
        
        # 상위 태그
        if analysis_result.tags:
            st.markdown("**🏷️ 주요 태그**")
            tags_display = " • ".join(analysis_result.tags[:6])
            st.caption(tags_display)
        
        # 분석 시간 표시
        if hasattr(result, 'analysis_time') and result.analysis_time:
            st.caption(f"⏱️ 분석 시간: {result.analysis_time:.1f}초")
        
        # 전체 결과 보기
        with st.expander("📄 상세 결과"):
            st.markdown(f"**판단 이유:**\n{analysis_result.reason}")
            st.markdown(f"**전체 특징:**\n{analysis_result.features}")
            if analysis_result.mood:
                st.markdown(f"**분위기:** {analysis_result.mood}")
            if analysis_result.target_audience:
                st.markdown(f"**타겟:** {analysis_result.target_audience}")
            if len(analysis_result.tags) > 6:
                remaining_tags = analysis_result.tags[6:]
                st.markdown(f"**추가 태그:** {', '.join(remaining_tags)}")
        
        # 선택 버튼
        if allow_selection and model_name:
            if st.button(
                f"✅ 이 결과 선택",
                key=f"{key_prefix}_select",
                help=f"{name}의 분석 결과를 최종 결과로 선택합니다",
                use_container_width=True
            ):
                handle_result_selection(video, result, model_name, name)
    
    else:
        # 기본 분석 결과 (현재 결과)
        if hasattr(video, 'analysis_result') and video.analysis_result:
            ar = video.analysis_result
            
            # 장르와 형식 - 컬럼 대신 단순 표시
            st.markdown("**🎬 장르**")
            st.info(ar.get('genre', 'Unknown'))
            
            st.markdown("**🎨 표현형식**")
            st.info(ar.get('expression_style', 'Unknown'))
            
            features = ar.get('features', '')
            features_preview = features[:120] + "..." if len(features) > 120 else features
            st.markdown("**✨ 주요 특징**")
            st.write(features_preview)
            
            tags = ar.get('tags', [])
            if tags:
                st.markdown("**🏷️ 주요 태그**")
                tags_display = " • ".join(tags[:6])
                st.caption(tags_display)
        else:
            st.warning("분석 결과가 없습니다.")

def display_analysis_summary(results: Dict[str, ModelComparisonResult]):
    """분석 요약 정보 표시 - 컬럼 중첩 방지"""
    st.markdown("#### 📊 분석 요약")
    
    # 성공/실패 통계
    successful = len([r for r in results.values() if r.status == "success"])
    failed = len([r for r in results.values() if r.status == "failed"])
    
    # 평균 분석 시간
    times = [r.analysis_time for r in results.values() if r.analysis_time]
    avg_time = sum(times) / len(times) if times else 0
    
    # 고유 장르 수
    genres = set()
    for result in results.values():
        if result.status == "success" and result.result:
            genres.add(result.result.genre)
    
    # 단순한 메트릭 표시 (컬럼 사용하지 않음)
    st.markdown(f"""
    📈 **분석 통계**
    - ✅ 성공: {successful}개
    - ❌ 실패: {failed}개  
    - ⏱️ 평균 시간: {avg_time:.1f}초
    - 🎬 장르 다양성: {len(genres)}개
    """)

def handle_result_selection(video: Video, result: ModelComparisonResult, model_name: str, display_name: str):
    """결과 선택 처리"""
    try:
        st.balloons()
        st.success(f"🎯 **{display_name}** 분석 결과가 선택되었습니다!")
        
        # 메인 분석 결과 업데이트
        multi_model_analyzer._update_main_analysis_result(video, result.result, model_name)
        
        # 데이터베이스 저장
        save_to_database(video, result.result, model_name)
        
        # 세션 상태 업데이트
        st.session_state.analysis_result = result.result
        st.session_state.selected_model = model_name
        
        st.info("💾 결과가 저장되었습니다. Notion에도 저장하시겠습니까?")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("📝 Notion에 저장", key="save_to_notion", use_container_width=True):
                save_to_notion(video)
        
    except Exception as e:
        st.error(f"결과 선택 중 오류 발생: {str(e)}")
        logger.error(f"Result selection failed: {e}")

def save_to_database(video: Video, result, model_name: str):
    """데이터베이스에 저장"""
    try:
        from src.database.video_db import VideoDatabase
        
        db = VideoDatabase()
        
        if db.video_exists(video.video_id):
            db.update_analysis_result(video.video_id, video.analysis_result)
        else:
            db.save_video_with_analysis(video)
        
        logger.info(f"✅ 데이터베이스 저장 완료: {model_name}")
        
    except Exception as e:
        st.warning(f"데이터베이스 저장 실패: {str(e)}")
        logger.error(f"Database save failed: {e}")

def save_to_notion(video: Video):
    """Notion에 저장"""
    try:
        from src.services.notion_service import NotionService
        
        notion = NotionService()
        
        with st.spinner("Notion에 저장 중..."):
            if notion.test_connection():
                success = notion.upload_video_analysis(video)
                if success:
                    st.success("✅ Notion에 저장되었습니다!")
                else:
                    st.error("❌ Notion 저장에 실패했습니다.")
            else:
                st.error("❌ Notion 연결에 실패했습니다.")
        
    except Exception as e:
        st.error(f"Notion 저장 실패: {str(e)}")
        logger.error(f"Notion save failed: {e}")

def get_current_analysis_result(video: Video):
    """현재 분석 결과를 ModelComparisonResult 형태로 반환"""
    from src.analyzer.ai_analyzer import AnalysisResult
    
    if hasattr(video, 'analysis_result') and video.analysis_result:
        ar = video.analysis_result
        
        # AnalysisResult 객체 생성
        current_result = AnalysisResult(
            genre=ar.get('genre', 'Unknown'),
            reason=ar.get('reasoning', ''),
            features=ar.get('features', ''),
            tags=ar.get('tags', []),
            format_type=ar.get('expression_style', 'Unknown'),
            mood=ar.get('mood_tone', ''),
            target_audience=ar.get('target_audience', '')
        )
        
        # ModelComparisonResult로 래핑
        return type('MockResult', (), {
            'result': current_result,
            'status': 'success'
        })()
    
    return None