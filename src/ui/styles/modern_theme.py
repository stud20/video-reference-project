# src/ui/styles/modern_theme.py
"""
Veon AI 스타일의 모던 다크 테마
"""

def apply_modern_theme():
    """모던 다크 테마 적용"""
    css = """
    <style>
        /* 전체 배경 및 기본 색상 */
        .stApp {
            background-color: #0A0A0B;
            color: #FAFAFA;
        }
        
        /* 메인 컨테이너 패딩 제거 */
        .main .block-container {
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            max-width: 1200px;
        }
        
        /* 상단 여백 제거 */
        .appview-container .main .block-container {
            padding-top: 0 !important;
        }
        
        /* 탭 컨테이너를 상단에 붙이기 */
        div[data-testid="stTabs"] {
            position: sticky;
            top: 0;
            z-index: 999;
            background-color: #0A0A0B;
            padding-top: 1rem;
        }
        
        /* 탭 스타일 */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2rem;
            background-color: transparent;
            padding: 1rem 0;
            border-bottom: 1px solid #27272A !important;
        }
        
        /* 탭 하단 선 숨기기 */
        .stTabs [data-baseweb="tab-border"] {
            display: none !important;
        }
        
        /* 탭 highlight 바 스타일 */
        .stTabs [data-baseweb="tab-highlight"] {
            background-color: #A78BFA !important;
            height: 2px !important;
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
            border-bottom: 2px solid #A78BFA;
        }
        
        /* 입력 필드 스타일 */
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
            box-shadow: 0 0 0 1px #8B5CF6;
        }
        
        .stTextInput > div > div > input::placeholder {
            color: #71717A;
        }
        
        /* 버튼 스타일 */
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
        
        /* 카드 스타일 */
        .custom-card {
            background-color: #18181B;
            border: 1px solid #27272A;
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            transition: all 0.3s ease;
        }
        
        .custom-card:hover {
            border-color: #3F3F46;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
        }
        
        /* 페이드 애니메이션 */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes fadeOut {
            from { opacity: 1; transform: translateY(0); }
            to { opacity: 0; transform: translateY(-10px); }
        }
        
        .fade-in {
            animation: fadeIn 0.5s ease-out forwards;
        }
        
        .fade-out {
            animation: fadeOut 0.3s ease-out forwards;
        }
        
        /* 중앙 정렬 컨테이너 */
        .center-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: calc(100vh - 150px);
            text-align: center;
        }
        
        /* 타이틀 스타일 */
        .main-title {
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 3rem;
            background: linear-gradient(135deg, #FAFAFA 0%, #A78BFA 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        /* 진행 상황 텍스트 */
        .progress-text {
            color: #A78BFA;
            font-size: 1.125rem;
            font-weight: 500;
        }
        
        /* 하단 통계 호버 영역 */
        .footer-stats {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            height: 3rem;
            background-color: #0A0A0B;
            border-top: 1px solid #27272A;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .footer-stats:hover {
            height: auto;
            padding: 1rem;
            background-color: #111111;
        }
        
        .footer-arrow {
            color: #71717A;
            transition: transform 0.3s ease;
        }
        
        .footer-stats:hover .footer-arrow {
            transform: rotate(180deg);
        }
        
        /* 스크롤바 스타일 */
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
        
        /* Streamlit 기본 요소 숨기기 */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* 메인 컨텐츠 패딩 조정 */
        .main .block-container {
            padding-top: 0;
            padding-bottom: 5rem;
            max-width: 1200px;
        }
        
        /* 탭을 상단에 고정 */
        .stTabs {
            position: sticky;
            top: 0;
            z-index: 999;
            background-color: #0A0A0B;
        }
        
        /* 탭 하단 구분선 제거 */
        .stTabs [data-baseweb="tab-list"] {
            border-bottom: none !important;
        }
        
        /* 탭 패널 패딩 제거 */
        .stTabs [data-baseweb="tab-panel"] {
            padding-top: 0;
        }
        
        /* 탭 선택 표시를 더 깔끔하게 */
        .stTabs [aria-selected="true"] {
            border-bottom: 2px solid #A78BFA !important;
        }
    </style>
    """
    
    import streamlit as st
    st.markdown(css, unsafe_allow_html=True)