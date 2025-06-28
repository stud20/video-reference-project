# src/ui/styles.py
"""
AI 영상 분석 시스템 스타일시트 - Streamlit 호환 버전
"""

def get_enhanced_styles() -> str:
    """
    Streamlit과 충돌하지 않는 CSS 스타일
    
    Returns:
        CSS 스타일 문자열
    """
    return """
    <style>
    /* =============
       폰트 임포트
       ============= */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800;900&display=swap');

    /* Streamlit 헤더 숨기기 */
    header[data-testid="stHeader"] {
        display: none !important;
    }

    /* 헤더 옆 링크 아이콘 숨기기 */
    .stMarkdown a.headingLink {
        display: none !important;
    }

    /* 헤더 앵커 링크 숨기기 */
    a[href^="#"] svg {
        display: none !important;
    }

    /* 헤더 호버 시 나타나는 링크도 숨기기 */
    .stMarkdown h1:hover a,
    .stMarkdown h2:hover a,
    .stMarkdown h3:hover a,
    .stMarkdown h4:hover a,
    .stMarkdown h5:hover a,
    .stMarkdown h6:hover a {
        display: none !important;
    }

    /* ===================
       스크롤바 숨기기
       =================== */
    /* 전체 스크롤바 숨기기 */
    ::-webkit-scrollbar {
        display: none !important;
    }

    /* Firefox용 */
    * {
        scrollbar-width: none !important;
    }

    /* IE/Edge용 */
    * {
        -ms-overflow-style: none !important;
    }

    /* Streamlit 메인 컨테이너 스크롤바도 숨기기 */
    .main, section.main, [data-testid="stAppViewContainer"] {
        overflow-y: auto !important;
        scrollbar-width: none !important;
        -ms-overflow-style: none !important;
    }

    .main::-webkit-scrollbar,
    section.main::-webkit-scrollbar,
    [data-testid="stAppViewContainer"]::-webkit-scrollbar {
        display: none !important;
    }


    /* =============
       CSS 변수 정의
       ============= */
    :root {
        --gradient-primary: linear-gradient(90deg, #0062cb 0%, #5aff96 100%);
        --gradient-button: linear-gradient(90deg, #49e0a0 0%, #066cc7 100%);
        --gradient-button-c: linear-gradient(90deg, #A949E0 0%, #C7064D 100%);
        --color-white: #ffffff;
        --color-dark: #1a1a1a;
    }

    /* ===================
       배경 추가 (Streamlit 구조 유지)
       =================== */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(to bottom, #000000 0%, #0a1929 50%, #001122 100%);
    }

    /* 배경 효과 오버레이 */
    [data-testid="stAppViewContainer"]::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: 
            radial-gradient(circle at 30% 20%, rgba(0, 98, 203, 0.15) 0%, transparent 50%),
            radial-gradient(circle at 70% 60%, rgba(90, 255, 150, 0.1) 0%, transparent 40%),
            radial-gradient(ellipse at center bottom, rgba(0, 56, 116, 0.4) 0%, transparent 70%);
        pointer-events: none;
        z-index: 1;
    }

    /* 콘텐츠를 배경 위로 */
    .block-container {
        position: relative;
        z-index: 2;
        padding-top: 2rem;
    }

    /* ===================
       메인 헤더
       =================== */
    .main-header {
        text-align: center;
        margin: 1rem 0 1rem 0;
    }

    .main-title {
        font-family: 'Poppins', sans-serif;
        font-size: 120px;
        font-weight: 700;
        letter-spacing: -2px;
        line-height: 1;
        background: var(--gradient-primary);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0;
        filter: drop-shadow(0 0 20px rgba(0, 98, 203, 0.5));
    }

    .powered-by {
        color: rgba(255, 255, 255, 0.7);
        font-family: 'Poppins', sans-serif;
        font-size: 12px;
        font-weight: 400;
        margin-top: 0rem;
    }

    /* ===================
       탭 스타일
       =================== */
    .stTabs [data-baseweb="tab-list"] {
        background: transparent;
        gap: 3rem;
        justify-content: center;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* 빨간색 인디케이터 제거 */
    .stTabs [data-baseweb="tab-highlight"] {
        display: none !important;
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: rgba(255, 255, 255, 0.5);
        font-family: 'Poppins', sans-serif;
        font-size: 28px;
        font-weight: 800;
        padding: 0.5rem 0;
        border: none;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: rgba(255, 255, 255, 0.8);
    }

    .stTabs [aria-selected="true"] {
        color: #ffffff;
        background: transparent;
        position: relative;
    }

    .stTabs [aria-selected="true"]::after {
        content: '';
        position: absolute;
        bottom: -1px;
        left: 0;
        right: 0;
        height: 3px;
        background: var(--gradient-primary);
        border-radius: 2px;
    }


    /* ===================
       사용방법 가이드
       =================== */
    .usage-guide {
        max-width: 900px;
        margin: 2rem auto 2rem auto;
        padding: 1rem 2rem 2rem 2rem;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
    }

    .usage-title {
        text-align: center;
        color: #ffffff;
        font-size: 24px;
        font-weight: 600;
        padding: 2rem;
        margin-bottom: 2rem;
        font-family: 'Poppins', sans-serif;
    }

    .usage-steps {
        display: flex;
        justify-content: space-around;
        gap: 2rem;
        flex-wrap: wrap;
    }

    .usage-step {
        flex: 1;
        min-width: 200px;
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 1rem;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        transition: all 0.3s ease;
    }

    .usage-step:hover {
        background: rgba(255, 255, 255, 0.08);
        transform: translateY(-5px);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    }

    .step-number {
        width: 50px;
        height: 50px;
        background: var(--gradient-primary);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        font-weight: bold;
        color: white;
        flex-shrink: 0;
    }

    .step-content h4 {
        color: #ffffff;
        font-size: 18px;
        margin: 0 0 0.5rem 0;
        font-weight: 600;
    }

    .step-content p {
        color: rgba(255, 255, 255, 0.7);
        font-size: 14px;
        margin: 0;
        line-height: 1.5;
    }

    /* 모바일 대응 */
    @media (max-width: 768px) {
        .usage-steps {
            flex-direction: column;
        }
        
        .usage-guide {
            padding: 1.5rem;
            margin: 2rem 1rem;
        }
        
        .usage-title {
            font-size: 20px;
        }
    }

    .stTextInput > div > div > input::placeholder {
        color: rgba(255, 255, 255, 0.5);
    }

    .stTextInput > div > div > input:focus {
        outline: none;
        border-color: #00a8ff;
        box-shadow: 
            inset 0 0 20px rgba(0, 0, 0, 0.5),
            0 0 40px rgba(0, 168, 255, 0.3);
    }


    /* ===================
       Analyze 탭 전용 입력 필드 (key 기반)
       =================== */

    div.st-key-analyze_url_input > div > div > div > input {
        background: linear-gradient(180deg, #001022 0%, #001c3a 100%) !important;
        border-radius: 16px !important;
        color: #ffffff !important;
        font-family: 'Poppins', sans-serif !important;
        font-size: 18px !important;
        height: 54px !important;
        padding: 0 24px !important;
        text-align: center !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        transition: all 0.3s ease !important;
    }

    /* 포커스 상태 */
    div.st-key-analyze_url_input > div > div > div > input:focus {
        outline: none !important;
        border: 1px solid #4a9eff !important;
        box-shadow: 0 0 20px rgba(74, 158, 255, 0.3) !important;
    }

    /* database_tab_search */
    div.st-key-db_search_input > div > div > div > input {
        background: linear-gradient(180deg, #001022 0%, #001c3a 100%) !important;
        border-radius: 1px !important;
        color: #ffffff !important;
        font-family: 'Poppins', sans-serif !important;
        font-size: 16px !important;
        height: 38px !important;
        padding: 0 12px !important;
        text-align: left !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        transition: all 0.3s ease !important;
    }

    /* 포커스 상태 */
    div.st-key-db_search_input > div > div > div > input:focus {
        outline: none !important;
        border: 1px solid #4a9eff !important;
        box-shadow: 0 0 20px rgba(74, 158, 255, 0.3) !important;
    }



    
    /* analyze_url_input의 컨테이너들 */
    div:has(> input[id="text_input_1"]) {
        height: 56px !important;
    }
    
    div:has(> div > input[id="text_input_1"]) {
        height: 56px !important;
    }
    
    /* placeholder 스타일 */
    input[id="text_input_1"]::placeholder {
        color: rgba(255, 255, 255, 0.5) !important;
    }
    
    /* focus 상태 */
    input[id="st-key-analyze_url_input"]:focus {
        outline: none !important;
        border-color: #00a8ff !important;
        box-shadow: 
            inset 0 0 20px rgba(0, 0, 0, 0.5),
            0 0 40px rgba(0, 168, 255, 0.3) !important;
    }
    
    /* 입력창과 버튼이 같은 줄에 정렬되도록 - 제거 (analyze-input-container로 이동) */

    .stTextInput > div > div > input::placeholder {
        color: rgba(255, 255, 255, 0.5);
    }

    .stTextInput > div > div > input:focus {
        outline: none;
        border-color: #00a8ff;
        box-shadow: 
            inset 0 0 20px rgba(0, 0, 0, 0.5),
            0 0 40px rgba(0, 168, 255, 0.3);
    }

    /* ===================
       버튼
       =================== */

    div.st-key-analyze_start_button div button::before {
        content: '' !important;
        position: absolute !important;
        top: 0 !important;
        left: -100% !important;
        width: 100% !important;
        height: 100% !important;
        background: linear-gradient(
            90deg, 
            transparent, 
            rgba(255, 255, 255, 0.3), 
            transparent
        ) !important;
        transition: left 0.5s !important;
    }

    div.st-key-analyze_start_button div button {
        position: relative !important;
        background: var(--gradient-button) !important;
        border: none !important;
        border-radius: 16px !important;
        box-shadow: 
            inset 0 0 0 1px rgba(0, 0, 0, 0.2),
            0 0 30px rgba(255, 255, 255, 0.3) !important;
        color: #ffffff !important;
        font-family: 'Poppins', sans-serif !important;
        font-size: 20px !important;
        font-weight: 900 !important;
        height: 56px !important;
        min-width: 120px !important;
        padding: 0 30px !important;
        cursor: pointer !important;
        overflow: hidden !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        transform: perspective(1px) translateZ(0) !important;
    }

    /* 호버 효과 - 부드러운 상승과 그림자 */
    div.st-key-analyze_start_button div button:hover {
        background: var(--gradient-button-c) !important;
        transform: translateY(-4px) scale(1.02) !important;
        box-shadow: 
            inset 0 0 0 1px rgba(0, 0, 0, 0.2),
            0 10px 40px rgba(200, 200, 200, 0.4),
            0 15px 60px rgba(200, 200, 200, 0.2) !important;
    }

    /* 클릭(활성) 상태 - 눌림 효과 */
    div.st-key-analyze_start_button div button:active {
        transform: translateY(-1px) scale(0.98) !important;
        box-shadow: 
            inset 0 0 0 1px rgba(0, 0, 0, 0.3),
            0 2px 15px rgba(73, 224, 160, 0.3) !important;
        transition: all 0.1s ease !important;
    }

    div[class*="st-key-vc_"] > div > button {
        /* 정사각형 버튼 */
        padding: 0 !important;
        
        /* 기본 스타일 */
        border: 1px solid #404040 !important;
        background: rgba(0, 0, 0, 0.1) !important;
        border-radius: 12px !important;
        
        /* 버튼 기본 설정 */
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
    }

    /* 버튼 내부 텍스트/아이콘 스타일 */
    div[class*="st-key-vc_"] > div > button > div p {
        color: rgba(255, 255, 255, 0.8) !important;
        font-size: 12px !important;
    }

    /* 호버 효과 - 절제된 스타일 */
    div[class*="st-key-vc_"] > div > button:hover {
        background: rgba(255, 255, 255, 0.05) !important;
        border-color: #606060 !important;
    }


    div[class*="st-key"] > div > div > div > div > button {
        /* 정사각형 버튼 */
        padding: 0 !important;
        
        /* 기본 스타일 */
        border: 1px solid #404040 !important;
        background: rgba(0, 0, 0, 0.1) !important;
        border-radius: 12px !important;
        
        /* 버튼 기본 설정 */
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
    }

    /* 호버 효과 - 절제된 스타일 */
    div[class*="st-key"] > div > div > div > div > button:hover {
        background: rgba(255, 255, 255, 0.05) !important;
        border-color: #606060 !important;
    }



    /* 포커스 효과 - 접근성 */
    div[class*="st-key"] > div > div > div > div > button:focus {
        outline: none !important;
        border-color: #666666 !important;
        box-shadow: 
            0px 4px 4px 0px rgba(0, 0, 0, 0.25),
            0 0 0 2px rgba(255, 255, 255, 0.1) !important;
    }

    /* 버튼 내부 텍스트/아이콘 스타일 */
    div[class*="st-key"] > div > div > div > div > button * {
        color: rgba(255, 255, 255, 0.8) !important;
        font-size: 12px !important;
    }

    /* 호버 시 내부 요소 */
    div[class*="st-key"] > div > div > div > div > button:hover * {
        color: rgba(255, 255, 255, 0.95) !important;
    }

    div[class*="st-key"] > div > div > div[data-baseweb="base-input"] {
        border: 1px solid #404040 !important;
        background: rgba(0, 0, 0, 0.1) !important;
        border-radius: 12px !important;

    }

    div[class*="st-key"] > div > div[data-baseweb="textarea"] {
    border: 1px solid #404040 !important;
    background: rgba(0, 0, 0, 0.1) !important;
    border-radius: 12px !important;
    min-height: 120px !important;  /* 최소 높이 설정 */
    height: auto !important;        /* 내용에 따라 자동 확장 */
    }

    /* 실제 textarea 요소 스타일 */
    div[class*="st-key"] > div > div[data-baseweb="textarea"] > div[data-baseweb="base-input"] textarea {
    color: #b0b0b0 !important;     /* 옅은 회색 텍스트 */
    background: transparent !important;
    border: none !important;
    padding: 12px 16px !important;
    font-size: 16px !important;
    line-height: 1.6 !important;
    min-height: 100px !important;   /* textarea 자체의 최소 높이 */
    resize: vertical !important;
}





    /* ===================
       기본 입력/버튼 스타일 (다른 탭용)
       =================== */
    /* 기본 텍스트 색상 */
    .stMarkdown {
        color: #ffffff;
    }

    /* 에러 메시지 */
    .stAlert {
        background: rgba(255, 0, 0, 0.1);
        border: 1px solid rgba(255, 0, 0, 0.3);
        color: #ff6b6b;
    }

    /* 콘솔 창 */
    .console-window {
        background: #000000;
        border: 1px solid #333;
        border-radius: 8px;
        color: #00ff00;
        font-family: monospace;
        padding: 1rem;
    }

    /* 결과 섹션 */
    .result-section {
        background: rgba(0, 16, 34, 0.6);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 2rem;
        color: #ffffff;
    }
    
    /* ===================
       Footer
       =================== */
    .footer {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: rgba(0, 0, 0, 0.8);
        backdrop-filter: blur(10px);
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        padding: 8px 0;
        text-align: center;
        z-index: 100;
    }
    
    .footer p {
        font-size: 11px !important;
        color: rgba(255, 255, 255, 0.5) !important;
        margin: 2px 0 !important;
        font-family: 'Poppins', sans-serif !important;
        letter-spacing: 0.5px;
    }
    
    /* 메인 컨텐츠에 하단 여백 추가 */
    .block-container {
        padding-bottom: 80px !important;
    }

    /* ===================
       Database 카드 스타일
       =================== */
    /* 텍스트 영역 패딩 줄이기 */
    .db-card-container .stTextArea > div > div > textarea {
        padding: 0.5rem;
    }
    
    .db-card-container .stTextInput > div > div > input {
        padding: 0.5rem;
    }
    
    /* 비디오 카드 기본 스타일 */
    .video-card {
        border: 1px solid #303842;
        border-radius: 10px;
        padding: 1.5rem 1rem 3rem 1rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    
    .video-card:hover {
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-color: #c0c0c0;
    }
    
    /* 썸네일 플레이스홀더 */
    .thumbnail-placeholder {
        width: 100%;
        height: 80px;
        background: #444;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #888;
        font-size: 24px;
    }
    
    /* 태그 컨테이너 */
    .tags-container {
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
        max-height: 120px;
        overflow-y: auto;
    }
    
    /* YouTube 태그 */
    .tag-youtube {
        background-color: #007ACC;
        color: white;
        padding: 2px 6px;
        border-radius: 10px;
        font-size: 11px;
        white-space: nowrap;
    }
    
    /* AI 태그 */
    .tag-ai {
        background-color: #28a745;
        color: white;
        padding: 2px 6px;
        border-radius: 10px;
        font-size: 11px;
        white-space: nowrap;
    }

    /* 비디오 카드 - stylable_container용 */
    [data-testid*="video_card_"] > div:first-child {
        border: 1px solid #303842 !important;
        border-radius: 10px !important;
        padding: 1.5rem 1rem 3rem 1rem !important;
        margin-bottom: 1rem !important;
        transition: all 0.3s ease !important;
    }
    
    [data-testid*="video_card_"] > div:first-child:hover {
        box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
        border-color: #c0c0c0 !important;
    }

    </style>
    """