# src/ui/styles/modern_theme.py
"""
Veon AI 스타일의 모던 다크 테마 - 통합 스타일 관리
"""

def apply_modern_theme():
    """모던 다크 테마 적용 - 모든 스타일 통합 관리"""
    css = """
    <style>
        /* ===== 전체 배경 및 기본 색상 ===== */
        .stApp {
            background-color: #0A0A0B;
            color: #FAFAFA;
        }
        
        /* 메인 컨테이너 스타일 */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 5rem;
            max-width: 1200px;
            margin: 0 auto;
        }
        
        /* ===== 탭 스타일 ===== */
        .stTabs {
            background-color: #0A0A0B;
        }
        
        .stTabs [data-baseweb="tab-list"] {
            gap: 2rem;
            background-color: transparent;
            padding: 1rem 0;
            border-bottom: 1px solid #27272A;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 3rem;
            background-color: transparent;
            border: none;
            color: #71717A;
            font-size: 1rem;
            font-weight: 500;
            padding: 0 1rem;
            transition: all 0.3s ease;
        }
        
        .stTabs [data-baseweb="tab"]:hover {
            color: #E4E4E7;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: transparent !important;
            color: #A78BFA !important;
        }
        
        .stTabs [data-baseweb="tab-highlight"] {
            background-color: #A78BFA;
            height: 2px;
        }
        
        .stTabs [data-baseweb="tab-panel"] {
            padding-top: 2rem;
        }
        
        /* ===== 헤더 스타일 ===== */
        .main-header {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, #FAFAFA 0%, #A78BFA 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-align: center;
        }
        
        .sub-header {
            color: #A3A3A3;
            font-size: 1.125rem;
            text-align: center;
            margin-bottom: 3rem;
        }
        
        /* ===== 입력 필드 스타일 ===== */
        .stTextInput > div > div > input {
            background-color: #18181B;
            border: 1px solid #27272A;
            color: #FAFAFA;
            border-radius: 12px;
            padding: 1rem;
            font-size: 1rem;
            transition: all 0.3s ease;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #8B5CF6;
            box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.2);
        }
        
        .stTextInput > div > div > input::placeholder {
            color: #71717A;
        }
        
        /* ===== 버튼 스타일 ===== */
        .stButton > button {
            background: linear-gradient(135deg, #8B5CF6 0%, #A78BFA 100%);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 0.75rem 2rem;
            font-weight: 600;
            font-size: 1rem;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3);
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(139, 92, 246, 0.4);
        }
        
        /* Secondary 버튼 */
        .stButton > button[kind="secondary"] {
            background: #27272A;
            color: #FAFAFA;
            box-shadow: none;
        }
        
        .stButton > button[kind="secondary"]:hover {
            background: #3F3F46;
            transform: translateY(-2px);
        }
        
        /* ===== 슬라이더 스타일 ===== */
        .stSlider > div > div > div {
            background-color: #27272A;
        }
        
        .stSlider > div > div > div > div {
            background-color: #8B5CF6;
        }
        
        /* ===== 메트릭 카드 스타일 ===== */
        [data-testid="metric-container"] {
            background-color: #18181B;
            border: 1px solid #27272A;
            padding: 1rem;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        [data-testid="metric-container"] [data-testid="metric-label"] {
            color: #A3A3A3;
        }
        
        [data-testid="metric-container"] [data-testid="metric-value"] {
            color: #FAFAFA;
        }
        
        /* ===== 비디오 컨테이너 ===== */
        .video-container {
            margin: 2rem 0;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        
        .video-container iframe {
            width: 100%;
            height: 400px;
            border: none;
        }
        
        /* ===== 필름스트립 스타일 ===== */
        .filmstrip-container {
            display: flex;
            gap: 1rem;
            overflow-x: auto;
            padding: 1rem 0;
            margin: 2rem 0;
            scrollbar-width: thin;
            scrollbar-color: #3F3F46 #18181B;
        }
        
        .filmstrip-container::-webkit-scrollbar {
            height: 8px;
        }
        
        .filmstrip-container::-webkit-scrollbar-track {
            background: #18181B;
            border-radius: 4px;
        }
        
        .filmstrip-container::-webkit-scrollbar-thumb {
            background: #3F3F46;
            border-radius: 4px;
        }
        
        .filmstrip-item {
            flex: 0 0 auto;
            position: relative;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
            transition: transform 0.3s ease;
        }
        
        .filmstrip-item:hover {
            transform: scale(1.05);
        }
        
        .filmstrip-item img {
            height: 120px;
            width: auto;
            display: block;
        }
        
        .filmstrip-label {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            background: linear-gradient(to top, rgba(0, 0, 0, 0.8), transparent);
            color: white;
            padding: 0.5rem;
            font-size: 0.875rem;
            text-align: center;
        }
        
        /* ===== 분석 결과 카드 ===== */
        .analysis-card {
            background-color: #18181B;
            border: 1px solid #27272A;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            transition: all 0.3s ease;
        }
        
        .analysis-card:hover {
            border-color: #3F3F46;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
        }
        
        .analysis-header {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1rem;
        }
        
        .analysis-icon {
            font-size: 1.5rem;
        }
        
        .analysis-title {
            font-size: 1.25rem;
            font-weight: 600;
            color: #FAFAFA;
        }
        
        .analysis-content {
            color: #D4D4D8;
            line-height: 1.6;
            white-space: pre-wrap;
        }
        
        /* ===== 태그 컨테이너 ===== */
        .tag-container {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 1rem;
        }
        
        .tag {
            background-color: #8B5CF6;
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.875rem;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        .tag:hover {
            background-color: #A78BFA;
            transform: translateY(-2px);
        }
        
        /* ===== 구분선 ===== */
        hr {
            border: none;
            border-top: 1px solid #27272A;
            margin: 2rem 0;
        }
        
        /* ===== 스크롤바 전역 스타일 ===== */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: #18181B;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #3F3F46;
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #52525B;
        }
        
        /* ===== Streamlit 기본 요소 숨기기 ===== */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* ===== 반응형 디자인 ===== */
        @media (max-width: 768px) {
            .main-header {
                font-size: 2rem;
            }
            
            .sub-header {
                font-size: 1rem;
            }
            
            .video-container iframe {
                height: 250px;
            }
            
            .filmstrip-item img {
                height: 80px;
            }
        }
        
        /* ===== 로딩 애니메이션 ===== */
        @keyframes pulse {
            0% { opacity: 0.6; }
            50% { opacity: 1; }
            100% { opacity: 0.6; }
        }
        
        .stSpinner > div {
            border-color: #8B5CF6 !important;
        }
        
        /* ===== 에러 및 성공 메시지 ===== */
        .stAlert {
            background-color: #18181B;
            border: 1px solid #27272A;
            border-radius: 12px;
            padding: 1rem;
        }
        
        .stAlert[data-baseweb="notification"][aria-label*="error"] {
            border-color: #DC2626;
            background-color: rgba(220, 38, 38, 0.1);
        }
        
        .stAlert[data-baseweb="notification"][aria-label*="success"] {
            border-color: #16A34A;
            background-color: rgba(22, 163, 74, 0.1);
        }
        
        /* ===== 추가 섹션 스타일 ===== */
        .input-section {
            background-color: #111111;
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 2rem;
            border: 1px solid #27272A;
        }
        
        .main-container {
            animation: fadeIn 0.5s ease-out;
        }
        
        @keyframes fadeIn {
            from { 
                opacity: 0; 
                transform: translateY(20px); 
            }
            to { 
                opacity: 1; 
                transform: translateY(0); 
            }
        }
    </style>
    """
    
    import streamlit as st
    st.markdown(css, unsafe_allow_html=True)