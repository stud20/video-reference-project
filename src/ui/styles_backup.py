# src/ui/styles.py
"""
AI 영상 분석 시스템 통합 스타일시트
"""

def get_enhanced_styles() -> str:
    """
    앱의 모든 CSS 스타일 반환 - 통합 버전
    
    Returns:
        CSS 스타일 문자열
    """
    return """
    <style>
    /* ===========================
       AI 영상 분석 시스템 통합 CSS
       =========================== */

    /* =============
       CSS 변수 정의
       ============= */
    :root {
        /* 색상 팔레트 */
        --primary-color: #1976d2;
        --primary-hover: #1565c0;
        --secondary-color: #28a745;
        --danger-color: #dc3545;
        --danger-hover: #c82333;
        --warning-color: #ffc107;
        --info-color: #17a2b8;
        
        /* 배경색 */
        --bg-primary: #0e1117;
        --bg-secondary: #262730;
        --bg-card: #1e1e1e;
        --bg-hover: #393a3f;
        
        /* 텍스트 색상 */
        --text-primary: #fafafa;
        --text-secondary: #b0b0b0;
        
        /* 테두리 */
        --border-color: #4a4a52;
        --border-radius: 8px;
        --border-radius-lg: 15px;
        
        /* 콘솔 스타일 */
        --console-bg: #000000;
        --console-text: #00ff00;
        --console-border: #333333;
        
        /* 그림자 */
        --shadow-sm: 0 2px 10px rgba(0, 0, 0, 0.2);
        --shadow-md: 0 4px 20px rgba(0, 0, 0, 0.3);
        --shadow-lg: 0 10px 40px rgba(0, 0, 0, 0.5);
        
        /* 애니메이션 */
        --transition-fast: 0.3s ease;
        --transition-normal: 0.5s ease-out;
    }

    /* ===================
       다크 테마 강제 적용
       =================== */
    :root {
        color-scheme: dark !important;
    }

    html, body, [data-testid="stAppViewContainer"], 
    [data-testid="stApp"], .main, .block-container {
        background-color: var(--bg-primary) !important;
        color: var(--text-primary) !important;
    }

    [data-testid="stSidebar"] {
        background-color: var(--bg-secondary) !important;
    }

    /* 라이트 모드 비활성화 */
    @media (prefers-color-scheme: light) {
        html, body, .stApp {
            background-color: var(--bg-primary) !important;
            color: var(--text-primary) !important;
        }
    }

    /* 모든 텍스트 요소 다크 모드 */
    p, h1, h2, h3, h4, h5, h6, span, div, label {
        color: var(--text-primary) !important;
    }

    /* ===================
       Streamlit 컴포넌트
       =================== */

    /* 입력 필드 */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: var(--border-radius);
        transition: var(--transition-fast);
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--primary-color) !important;
        box-shadow: 0 0 0 2px rgba(25, 118, 210, 0.2);
    }

    /* 셀렉트박스 */
    .stSelectbox > div > div > div {
        background-color: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
        border-radius: var(--border-radius);
    }

    /* 버튼 */
    .stButton > button {
        background-color: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: var(--border-radius);
        transition: var(--transition-fast);
        font-weight: 500;
    }

    .stButton > button:hover {
        background-color: var(--bg-hover) !important;
        border-color: var(--primary-color) !important;
        transform: translateY(-1px);
        box-shadow: var(--shadow-sm);
    }

    /* Primary 버튼 */
    .stButton > button[kind="primary"] {
        background-color: var(--primary-color) !important;
        color: white !important;
        border: none !important;
    }

    .stButton > button[kind="primary"]:hover {
        background-color: var(--primary-hover) !important;
    }

    /* 탭 스타일 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 15px;
        background: transparent;
        border: none;
        padding: 20px 0;
        margin: 1rem 0 2rem 0;
        box-shadow: none;
        display: flex;
        justify-content: center;
    }

    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 0 40px;
        border-radius: 25px;
        background: #e0e0e0;
        color: #666;
        font-size: 16px;
        font-weight: 600;
        transition: all 0.3s ease;
        border: none;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background: #d0d0d0;
        transform: none;
        box-shadow: none;
    }


    .stTabs [aria-selected="true"] {
        background: #ffffff;
        color: #333;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    }
    /* 프로그레스 바 */
    .stProgress > div > div > div > div {
        background-color: var(--primary-color);
    }

    /* 메트릭 */
    div[data-testid="metric-container"] {
        background-color: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: var(--border-radius);
        padding: 1rem;
    }

    /* Streamlit 헤더 투명하게 만들기 */
    header[data-testid="stHeader"] {
        background-color: transparent !important;
        backdrop-filter: none !important;
    }



    /* ===================
       애니메이션 정의
       =================== */
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }

    @keyframes slideUp {
        from { 
            transform: translateY(20px); 
            opacity: 0; 
        }
        to { 
            transform: translateY(0); 
            opacity: 1; 
        }
    }

    @keyframes slideDown {
        from { 
            transform: translateY(-20px); 
            opacity: 0; 
        }
        to { 
            transform: translateY(0); 
            opacity: 1; 
        }
    }

    @keyframes pulse {
        0%, 100% { opacity: 0.3; }
        50% { opacity: 1; }
    }

    @keyframes spin {
        to { transform: rotate(360deg); }
    }

    @keyframes blink {
        0%, 49% { opacity: 1; }
        50%, 100% { opacity: 0; }
    }

    @keyframes consoleFadeIn {
        from {
            opacity: 0;
            transform: translateX(-10px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }

    @keyframes modalSlideIn {
        from {
            opacity: 0;
            transform: scale(0.95) translateY(20px);
        }
        to {
            opacity: 1;
            transform: scale(1) translateY(0);
        }
    }

    @keyframes filmFrameFadeIn {
        from {
            opacity: 0;
            transform: scale(0.9) translateY(10px);
        }
        to {
            opacity: 1;
            transform: scale(1) translateY(0);
        }
    }

    @keyframes resultItemFadeIn {
        from {
            opacity: 0;
            transform: translateX(-20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }

    @keyframes tagFadeIn {
        from {
            opacity: 0;
            transform: scale(0.8);
        }
        to {
            opacity: 1;
            transform: scale(1);
        }
    }

    /* ===================
       컴포넌트 스타일
       =================== */

    /* 분석 입력 컨테이너 */
    .analyze-input-container {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 60vh;
        animation: fadeIn var(--transition-normal);
    }

    .analyze-input-wrapper {
        width: 75%;
        max-width: 600px;
        padding: 3rem;
        background: var(--bg-card);
        border-radius: var(--border-radius-lg);
        box-shadow: var(--shadow-lg);
        border: 1px solid var(--border-color);
        transition: var(--transition-fast);
        text-align: center;
    }

    .analyze-input-wrapper:hover {
        box-shadow: 0 15px 50px rgba(0, 0, 0, 0.4);
        transform: translateY(-2px);
    }

    .analyze-input-wrapper h3 {
        margin-bottom: 1rem;
    }

    /* 콘솔 창 */
    .console-window {
        background: var(--console-bg);
        color: var(--console-text);
        font-family: 'Courier New', 'Consolas', 'Monaco', monospace;
        padding: 15px;
        border-radius: var(--border-radius);
        height: 120px;
        overflow-y: auto;
        overflow-x: hidden;
        margin: 1rem 0;
        border: 1px solid var(--console-border);
        font-size: 14px;
        line-height: 1.6;
        animation: slideUp var(--transition-fast);
        box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.5);
        position: relative;
    }

    .console-window::-webkit-scrollbar {
        width: 8px;
    }

    .console-window::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.1);
    }

    .console-window::-webkit-scrollbar-thumb {
        background: var(--console-text);
        opacity: 0.5;
        border-radius: 4px;
    }

    .console-line {
        margin: 4px 0;
        opacity: 0;
        animation: consoleFadeIn 0.3s ease-out forwards;
        white-space: nowrap;
        overflow: hidden;
        position: relative;
    }

    .console-line::before {
        content: '> ';
        color: rgba(0, 255, 0, 0.7);
        margin-right: 5px;
    }

    .console-line:last-child::after {
        content: '_';
        animation: blink 1s infinite;
        color: var(--console-text);
        font-weight: bold;
    }

    /* 필름 스트립 */
    .film-strip-container {
        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
        border-radius: var(--border-radius-lg);
        padding: 2rem;
        margin: 2rem 0;
        animation: slideUp var(--transition-normal);
        box-shadow: var(--shadow-md);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .film-strip-container h4 {
        color: white;
        margin-bottom: 1rem;
        font-weight: 600;
    }

    .film-strip {
        display: flex;
        gap: 20px;
        overflow-x: auto;
        padding: 20px 5px;
        scroll-behavior: smooth;
        background: rgba(0, 0, 0, 0.3);
        border-radius: 10px;
        margin-top: 1rem;
    }

    .film-strip::-webkit-scrollbar {
        height: 10px;
    }

    .film-strip::-webkit-scrollbar-track {
        background: var(--bg-primary);
        border-radius: 5px;
    }

    .film-strip::-webkit-scrollbar-thumb {
        background: var(--primary-color);
        border-radius: 5px;
        transition: var(--transition-fast);
    }

    .film-strip::-webkit-scrollbar-thumb:hover {
        background: var(--primary-hover);
    }

    .film-frame {
        min-width: 200px;
        height: 150px;
        border-radius: 10px;
        overflow: hidden;
        border: 3px solid #333;
        transition: var(--transition-fast);
        cursor: pointer;
        position: relative;
        background: #000;
        opacity: 0;
        animation: filmFrameFadeIn 0.4s ease-out forwards;
        box-shadow: var(--shadow-sm);
    }

    .film-frame::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(
            to bottom,
            transparent 0%,
            transparent 70%,
            rgba(0, 0, 0, 0.7) 100%
        );
        z-index: 1;
        transition: opacity var(--transition-fast);
    }

    .film-frame:hover::before {
        opacity: 0;
    }

    .film-frame:hover {
        border-color: var(--primary-color);
        transform: scale(1.08) translateY(-8px);
        box-shadow: 0 12px 40px rgba(25, 118, 210, 0.5);
        z-index: 10;
    }

    .film-frame img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        transition: transform var(--transition-fast);
    }

    .film-frame:hover img {
        transform: scale(1.1);
    }

    /* 비디오 임베드 */
    .video-embed-container {
        position: relative;
        padding-bottom: 56.25%;
        height: 0;
        overflow: hidden;
        border-radius: 10px;
        box-shadow: var(--shadow-md);
        margin: 1rem 0;
    }

    .video-embed-container iframe {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        border: none;
        border-radius: 10px;
    }

    /* 결과 섹션 */
    .result-section {
        background: var(--bg-card);
        border-radius: 10px;
        padding: 2rem;
        margin: 1rem 0;
        animation: slideUp var(--transition-normal);
        box-shadow: var(--shadow-md);
        border: 1px solid var(--border-color);
    }

    .result-item {
        display: flex;
        align-items: flex-start;
        margin-bottom: 1.5rem;
        padding-bottom: 1.5rem;
        border-bottom: 1px solid var(--border-color);
        opacity: 0;
        animation: resultItemFadeIn 0.5s ease-out forwards;
    }

    .result-item:last-child {
        border-bottom: none;
        margin-bottom: 0;
        padding-bottom: 0;
    }

    .result-label {
        font-weight: 600;
        color: var(--primary-color);
        min-width: 140px;
        margin-right: 1.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .result-value {
        flex: 1;
        color: var(--text-primary);
        line-height: 1.8;
    }

    /* 태그 */
    .tag-container {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin: 0.5rem 0;
    }

    .tag {
        background-color: #007ACC;
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 14px;
        display: inline-block;
        font-weight: 500;
        transition: var(--transition-fast);
        cursor: pointer;
        opacity: 0;
        animation: tagFadeIn 0.3s ease-out forwards;
    }

    .tag:hover {
        background: var(--primary-hover);
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(25, 118, 210, 0.4);
    }

    /* 다운로드 버튼 (Streamlit 버튼 완전 모방) */
    .download-link {
        display: block;
        width: 100%;
        text-decoration: none !important;
    }
    
    .download-button {
        width: 100%;
        min-height: 38px;
        padding: 0.25rem 0.75rem;
        background-color: #262730;
        color: #fafafa;
        border: 1px solid rgba(250, 250, 250, 0.2);
        border-radius: 0.5rem;
        font-size: 14px;
        font-weight: 400;
        cursor: pointer;
        transition: all 0.3s;
        text-align: center;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        font-family: "Source Sans Pro", sans-serif;
        line-height: 1.6;
        box-sizing: border-box;
        margin: 0;
    }
    
    .download-button:hover {
        background-color: #464646;
        border-color: rgba(250, 250, 250, 0.2);
        color: #fafafa;
    }

    /* 액션 버튼 */
    .action-button {
        background: var(--primary-color);
        color: white;
        border: none;
        padding: 0.8rem 1.5rem;
        border-radius: var(--border-radius);
        font-weight: 500;
        cursor: pointer;
        transition: var(--transition-fast);
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        box-shadow: 0 2px 10px rgba(25, 118, 210, 0.3);
    }

    .action-button:hover {
        background: var(--primary-hover);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(25, 118, 210, 0.5);
    }

    .action-button:active {
        transform: translateY(0);
    }

    .action-button.secondary {
        background: var(--bg-secondary);
        color: var(--text-primary);
        box-shadow: var(--shadow-sm);
    }

    .action-button.secondary:hover {
        background: #363640;
    }

    .action-button.danger {
        background: var(--danger-color);
        box-shadow: 0 2px 10px rgba(220, 53, 69, 0.3);
    }

    .action-button.danger:hover {
        background: var(--danger-hover);
        box-shadow: 0 6px 20px rgba(220, 53, 69, 0.5);
    }

    /* 정밀도 관련 */
    .precision-info {
        background-color: var(--bg-secondary);
        color: var(--text-primary);
        padding: 1rem;
        border-radius: var(--border-radius);
        border-left: 4px solid #1f4e79;
        margin: 1rem 0;
    }

    .precision-warning {
        background-color: #3d3d0d;
        color: var(--text-primary);
        padding: 0.8rem;
        border-radius: 6px;
        border-left: 4px solid var(--warning-color);
        margin: 0.5rem 0;
        font-size: 14px;
    }

    .precision-success {
        background-color: #1e3a1e;
        color: var(--text-primary);
        padding: 0.8rem;
        border-radius: 6px;
        border-left: 4px solid var(--secondary-color);
        margin: 0.5rem 0;
        font-size: 14px;
    }

    /* 모달 */
    .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.85);
        backdrop-filter: blur(5px);
        z-index: 1000;
        display: flex;
        justify-content: center;
        align-items: center;
        animation: fadeIn var(--transition-fast);
    }

    .modal-content {
        background: var(--bg-secondary);
        color: var(--text-primary);
        border-radius: var(--border-radius-lg);
        width: 90%;
        max-width: 1200px;
        max-height: 90vh;
        overflow-y: auto;
        padding: 2rem;
        animation: modalSlideIn var(--transition-fast);
        box-shadow: var(--shadow-lg);
    }

    /* 데이터베이스 관련 */
    .db-header {
        background: linear-gradient(90deg, #1f4e79, #2e8b57);
        color: white;
        padding: 1rem 2rem;
        border-radius: 10px 10px 0 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .db-content {
        padding: 2rem;
        background-color: var(--bg-secondary);
    }

    .video-card {
        border: 1px solid var(--border-color);
        border-radius: var(--border-radius);
        padding: 1rem;
        margin: 1rem 0;
        background: var(--bg-card);
        color: var(--text-primary);
        transition: var(--transition-fast);
    }

    .video-card:hover {
        background: var(--bg-secondary);
        border-color: var(--primary-color);
        transform: translateY(-2px);
        box-shadow: var(--shadow-sm);
    }

    .video-card.selected {
        background: #1a3a52;
        border-color: var(--primary-color);
    }

    /* 페이지네이션 */
    .pagination {
        display: flex;
        justify-content: center;
        gap: 0.5rem;
        margin: 1rem 0;
    }

    .page-btn {
        padding: 0.5rem 1rem;
        border: 1px solid var(--border-color);
        background: var(--bg-secondary);
        color: var(--text-primary);
        cursor: pointer;
        border-radius: 3px;
        transition: var(--transition-fast);
    }

    .page-btn:hover {
        background: var(--bg-hover);
        border-color: var(--primary-color);
    }

    .page-btn.active {
        background: var(--primary-color);
        color: white;
        border-color: var(--primary-color);
    }

    /* 로딩 스피너 */
    .loading-spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid rgba(255, 255, 255, 0.3);
        border-radius: 50%;
        border-top-color: white;
        animation: spin 1s ease-in-out infinite;
    }

    /* 프로그레스 인디케이터 */
    .progress-indicator {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px;
        background: rgba(25, 118, 210, 0.1);
        border-radius: var(--border-radius);
        margin: 10px 0;
    }

    .progress-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--primary-color);
        opacity: 0.3;
        animation: pulse 1.5s ease-in-out infinite;
    }

    .progress-dot.active {
        opacity: 1;
    }

    .progress-dot:nth-child(1) { animation-delay: 0s; }
    .progress-dot:nth-child(2) { animation-delay: 0.3s; }
    .progress-dot:nth-child(3) { animation-delay: 0.6s; }

    /* 이미지 그리드 */
    .image-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 15px;
        padding: 1rem 0;
    }

    .grid-image {
        position: relative;
        aspect-ratio: 16/9;
        border-radius: var(--border-radius);
        overflow: hidden;
        cursor: pointer;
        transition: var(--transition-fast);
    }

    .grid-image:hover {
        transform: scale(1.05);
        box-shadow: var(--shadow-md);
    }

    .grid-image.selected {
        border: 3px solid var(--primary-color);
    }

    .grid-image img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }

    /* 무드보드 관련 */
    .moodboard-title {
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
        color: white;
    }

    .stats-card {
        background: rgba(38, 39, 48, 0.8);
        border-radius: var(--border-radius);
        padding: 1rem;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* 코드 블록 */
    .stCodeBlock {
        background-color: var(--bg-card) !important;
    }

    /* 스크롤바 전역 설정 */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }

    ::-webkit-scrollbar-track {
        background: var(--bg-primary);
    }

    ::-webkit-scrollbar-thumb {
        background: var(--border-color);
        border-radius: 5px;
        transition: background var(--transition-fast);
    }

    ::-webkit-scrollbar-thumb:hover {
        background: var(--primary-color);
    }

    /* ===================
       반응형 디자인
       =================== */
    @media (max-width: 768px) {
        .film-frame {
            min-width: 120px;
            height: 80px;
        }
        
        .result-item {
            flex-direction: column;
        }
        
        .result-label {
            margin-bottom: 0.5rem;
        }
        
        .modal-content {
            padding: 1rem;
            width: 95%;
        }
        
        .analyze-input-wrapper {
            padding: 2rem 1rem;
        }
        
        .film-strip-container {
            padding: 1rem;
        }
    }

    /* ===================
       유틸리티 클래스
       =================== */
    .text-center { text-align: center; }
    .text-left { text-align: left; }
    .text-right { text-align: right; }

    .mt-1 { margin-top: 0.5rem; }
    .mt-2 { margin-top: 1rem; }
    .mt-3 { margin-top: 1.5rem; }
    .mb-1 { margin-bottom: 0.5rem; }
    .mb-2 { margin-bottom: 1rem; }
    .mb-3 { margin-bottom: 1.5rem; }

    .p-1 { padding: 0.5rem; }
    .p-2 { padding: 1rem; }
    .p-3 { padding: 1.5rem; }

    .rounded { border-radius: var(--border-radius); }
    .rounded-lg { border-radius: var(--border-radius-lg); }

    .shadow-sm { box-shadow: var(--shadow-sm); }
    .shadow-md { box-shadow: var(--shadow-md); }
    .shadow-lg { box-shadow: var(--shadow-lg); }

    .opacity-0 { opacity: 0; }
    .opacity-50 { opacity: 0.5; }
    .opacity-100 { opacity: 1; }

    .transition-fast { transition: all var(--transition-fast); }
    .transition-normal { transition: all var(--transition-normal); }

    /* styles.py에 추가할 CSS */

    /* 히어로 섹션 */
    .hero-section {
        text-align: center;
        padding: 4rem 0;
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        border-radius: 20px;
        margin-bottom: 3rem;
        position: relative;
        overflow: hidden;
    }

    .hero-section::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        animation: pulse 4s ease-in-out infinite;
    }

    .hero-title {
        font-size: 3.5rem;
        margin-bottom: 1rem;
        font-weight: 700;
        position: relative;
        z-index: 1;
    }

    .gradient-text {
        background: linear-gradient(45deg, #fff, #64b5f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .hero-subtitle {
        display: block;
        font-size: 2rem;
        margin-top: 0.5rem;
        color: rgba(255,255,255,0.9);
    }

    .hero-description {
        font-size: 1.2rem;
        color: rgba(255,255,255,0.8);
        max-width: 600px;
        margin: 0 auto;
        line-height: 1.8;
    }

    /* 입력 섹션 스타일 */
    .input-section {
        text-align: center;
        margin: 3rem 0;
    }

    .input-label {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 1rem;
    }

        
    /* 분석하기 버튼 스타일 */
    .stButton > button[kind="primary"] {
        background-color: #4dd0e1 !important;
        color: white !important;
        border: none !important;
        border-radius: 10px;
        padding: 15px 30px;
        font-size: 16px;
        font-weight: 600;
    }

    .stButton > button[kind="primary"]:hover {
        background-color: #3dbfd0 !important;
    }

    /* 배경 곡선 추가 */
    .stApp::after {
        content: '';
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        height: 50vh;
        background: radial-gradient(ellipse at center bottom, #3a4a5c 0%, #2a3a4c 100%);
        border-radius: 50% 50% 0 0 / 100px 100px 0 0;
        z-index: -1;
    }

    /* 전체 배경을 밝게 */
    .stApp {
        background-color: #f8f9fa !important;
    }

    /* 상단 여백 조정 */
    .block-container {
        padding-top: 1rem !important;
    }

    /* URL 입력창 스타일 */
    .stTextInput > div > div > input {
        background-color: #f5f5f5 !important;
        border: 1px solid #ddd !important;
        border-radius: 10px;
        padding: 15px;
        font-size: 16px;
        color: #333 !important;
    }


    .input-card {
        background: var(--bg-card);
        border: 2px solid var(--border-color);
        border-radius: 20px;
        padding: 2rem;
        text-align: center;
        transition: all 0.3s ease;
        position: relative;
    }

    .input-card:hover {
        border-color: var(--primary-color);
        transform: translateY(-2px);
        box-shadow: 0 10px 30px rgba(25, 118, 210, 0.3);
    }

    .input-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        animation: float 3s ease-in-out infinite;
    }

    .input-hint {
        color: var(--text-secondary);
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }

    /* 기능 카드 */
    .features-section {
        margin: 4rem 0;
    }

    .section-title {
        text-align: center;
        font-size: 2rem;
        margin-bottom: 2rem;
        color: var(--text-primary);
    }

    .features-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 2rem;
        margin-top: 2rem;
    }

    .feature-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 15px;
        padding: 2rem;
        text-align: center;
        transition: all 0.3s ease;
        cursor: default;
    }

    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        border-color: var(--primary-color);
    }

    .feature-icon {
        font-size: 2.5rem;
        margin-bottom: 1rem;
        display: inline-block;
        animation: bounce 2s ease-in-out infinite;
    }

    .feature-card h4 {
        font-size: 1.2rem;
        margin-bottom: 0.5rem;
        color: var(--primary-color);
    }

    .feature-card p {
        font-size: 0.9rem;
        color: var(--text-secondary);
        line-height: 1.6;
    }

    /* 예시 섹션 */
    .examples-section {
        margin-top: 4rem;
    }

    /* 애니메이션 */
    @keyframes float {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-10px); }
    }

    @keyframes bounce {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.1); }
    }

    /* 탭 스타일 개선 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 20px;
        padding: 10px;
        margin: 1rem 0 2rem 0;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
    }

    .stTabs [data-baseweb="tab"] {
        height: 80px;
        padding: 0 30px;
        border-radius: 15px;
        color: rgba(255, 255, 255, 0.7);
        font-size: 34px;
        font-weight: 600;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
        background: transparent;
        border: 2px solid transparent;
    }

    /* 탭 호버 효과 */
    .stTabs [data-baseweb="tab"]:hover {
        color: white;
        background: rgba(255, 255, 255, 0.1);
        border-color: rgba(255, 255, 255, 0.2);
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(25, 118, 210, 0.3);
    }

    /* 활성 탭 */
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%);
        color: white;
        border-color: transparent;
        box-shadow: 0 5px 25px rgba(25, 118, 210, 0.5);
        transform: translateY(-2px);
    }

    /* 탭 아이콘 애니메이션 */
    .stTabs [data-baseweb="tab"] span {
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 34px;
    }

    /* 탭 내용에 애니메이션 효과 추가 */
    .stTabs [aria-selected="true"]::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        animation: shimmer 2s infinite;
    }

    @keyframes shimmer {
        to {
            left: 100%;
        }
    }

    /* 탭 컨테이너 위 헤더 추가 */
    .main-header {
        text-align: center;
        padding: 1rem 0 1rem 0;
        position: relative;
    }

    .main-title {
        font-size: 4rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }

    .title-blue {
        color: #1976d2;
    }

    .title-mint {
        color: #4dd0e1;
    }

    .powered-by {
        font-size: 1rem;
        color: #666;
        margin-top: -0.5rem;
    }

    .main-subtitle {
        font-size: 1.1rem;
        color: var(--text-secondary);
        font-weight: 400;
    }

    .block-container {
        padding-top: 1rem !important;  /* 기본값은 보통 3-5rem */
    }

    /* 메인 앱 뷰 컨테이너 여백 조정 */
    .stApp > div > div > div > div {
        padding-top: 0 !important;
    }

    /* 탭 패널 트랜지션 */
    .stTabs [data-baseweb="tab-panel"] {
        animation: fadeInUp 0.5s ease-out;
    }

    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }



    @keyframes expandWidth {
        from {
            left: 50%;
            right: 50%;
        }
        to {
            left: 10%;
            right: 10%;
        }
    }

    /* 탭 뱃지 (선택사항) */
    .tab-badge {
        position: absolute;
        top: 5px;
        right: 5px;
        background: #ff4757;
        color: white;
        font-size: 10px;
        padding: 2px 6px;
        border-radius: 10px;
        font-weight: bold;
    }
    </style>
    """