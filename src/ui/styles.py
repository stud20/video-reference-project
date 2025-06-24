# src/ui/styles.py
def get_app_styles() -> str:
    """
    앱의 모든 CSS 스타일 반환
    
    Returns:
        CSS 스타일 문자열
    """
    return """
    <style>
        /* 다크 테마 강제 적용 */
        :root {
            color-scheme: dark !important;
        }
        
        [data-testid="stAppViewContainer"] {
            background-color: #0e1117 !important;
        }
        
        /* 입력 필드 다크 테마 스타일 */
        .stTextInput > div > div > input {
            background-color: #262730 !important;
            color: #fafafa !important;
            border: 1px solid #4a4a52 !important;
        }
        
        .stTextArea > div > div > textarea {
            background-color: #262730 !important;
            color: #fafafa !important;
            border: 1px solid #4a4a52 !important;
        }
        
        .stSelectbox > div > div > div {
            background-color: #262730 !important;
            color: #fafafa !important;
        }
        
        /* 정밀도 관련 스타일 */
        .precision-info {
            background-color: #262730;
            color: #fafafa;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #1f4e79;
            margin: 1rem 0;
        }
        .precision-warning {
            background-color: #3d3d0d;
            color: #fafafa;
            padding: 0.8rem;
            border-radius: 6px;
            border-left: 4px solid #ffc107;
            margin: 0.5rem 0;
            font-size: 14px;
        }
        .precision-success {
            background-color: #1e3a1e;
            color: #fafafa;
            padding: 0.8rem;
            border-radius: 6px;
            border-left: 4px solid #28a745;
            margin: 0.5rem 0;
            font-size: 14px;
        }
        
        /* 프로그레스 바 */
        .stProgress > div > div > div > div {
            background-color: #1f4e79;
        }
        
        /* 모달 관련 스타일 */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.7);
            z-index: 1000;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .modal-content {
            background-color: #262730;
            color: #fafafa;
            border-radius: 10px;
            max-width: 90vw;
            max-height: 90vh;
            overflow-y: auto;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
        }
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
            background-color: #262730;
        }
        
        /* 비디오 카드 스타일 */
        .video-card {
            border: 1px solid #4a4a52;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
            background: #1e1e1e;
            color: #fafafa;
        }
        .video-card:hover {
            background: #262730;
            border-color: #1f4e79;
        }
        .video-card.selected {
            background: #1a3a52;
            border-color: #1976d2;
        }
        
        /* 태그 스타일 */
        .tag-container {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin: 0.5rem 0;
        }
        .tag {
            background-color: #007ACC;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
            display: inline-block;
        }
        
        /* 버튼 스타일 */
        .action-buttons {
            display: flex;
            gap: 0.5rem;
            margin-top: 1rem;
        }
        .btn-danger {
            background-color: #dc3545;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            cursor: pointer;
        }
        .btn-warning {
            background-color: #ffc107;
            color: black;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            cursor: pointer;
        }
        .btn-info {
            background-color: #17a2b8;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            cursor: pointer;
        }
        
        /* 페이지네이션 스타일 */
        .pagination {
            display: flex;
            justify-content: center;
            gap: 0.5rem;
            margin: 1rem 0;
        }
        .page-btn {
            padding: 0.5rem 1rem;
            border: 1px solid #4a4a52;
            background: #262730;
            color: #fafafa;
            cursor: pointer;
            border-radius: 3px;
        }
        .page-btn.active {
            background: #1f4e79;
            color: white;
        }
        
        /* 다크 테마 박스 스타일 */
        div[data-testid="stMarkdownContainer"] > div {
            color: #fafafa !important;
        }
        
        /* 코드 블록 다크 테마 */
        .stCodeBlock {
            background-color: #1e1e1e !important;
        }
    </style>
    """


def get_enhanced_styles() -> str:
    """향상된 UI 스타일"""
    return """
    <style>
        /* 다크 테마 기본 설정 */
        :root {
            --primary-color: #1976d2;
            --secondary-color: #28a745;
            --danger-color: #dc3545;
            --bg-primary: #0e1117;
            --bg-secondary: #262730;
            --bg-card: #1e1e1e;
            --text-primary: #fafafa;
            --text-secondary: #b0b0b0;
            --border-color: #4a4a52;
        }
        
        /* 메인 헤더 스타일 */
        .main-header {
            text-align: center;
            padding: 2rem 0;
            margin-bottom: 2rem;
            background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%);
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(25, 118, 210, 0.3);
        }
        
        .main-header h1 {
            color: white;
            margin: 0;
            font-size: 2.5rem;
            font-weight: 700;
        }
        
        .main-header p {
            color: rgba(255, 255, 255, 0.9);
            margin: 0.5rem 0 0 0;
            font-size: 1.1rem;
        }
        
        /* 탭 스타일 개선 */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: var(--bg-secondary);
            border-radius: 10px;
            padding: 4px;
        }
        
        .stTabs [data-baseweb="tab"] {
            border-radius: 6px;
            color: var(--text-secondary);
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: var(--primary-color);
            color: white;
        }
        
        /* 애니메이션 효과 */
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
        
        /* 분석 입력 필드 스타일 */
        .analyze-input-container {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 400px;
            animation: fadeIn 0.5s ease-out;
        }
        
        .analyze-input-wrapper {
            width: 100%;
            max-width: 600px;
            padding: 3rem;
            background: var(--bg-card);
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border-color);
        }
        
        /* 콘솔 창 스타일 */
        .console-window {
            background: #000;
            color: #0f0;
            font-family: 'Courier New', monospace;
            padding: 1rem;
            border-radius: 8px;
            height: 120px;
            overflow-y: auto;
            margin: 1rem 0;
            border: 1px solid #333;
            font-size: 0.9rem;
            line-height: 1.4;
            animation: slideUp 0.3s ease-out;
        }
        
        .console-line {
            margin: 2px 0;
            opacity: 0;
            animation: fadeIn 0.3s ease-out forwards;
        }
        
        /* 필름 스트립 스타일 */
        .film-strip-container {
            background: var(--bg-secondary);
            border-radius: 10px;
            padding: 1rem;
            margin: 1rem 0;
            animation: slideUp 0.5s ease-out;
        }
        
        .film-strip {
            display: flex;
            gap: 10px;
            overflow-x: auto;
            padding: 10px 0;
        }
        
        .film-strip::-webkit-scrollbar {
            height: 8px;
        }
        
        .film-strip::-webkit-scrollbar-track {
            background: var(--bg-primary);
            border-radius: 4px;
        }
        
        .film-strip::-webkit-scrollbar-thumb {
            background: var(--primary-color);
            border-radius: 4px;
        }
        
        .film-frame {
            min-width: 150px;
            height: 100px;
            border-radius: 8px;
            overflow: hidden;
            border: 2px solid var(--border-color);
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .film-frame:hover {
            border-color: var(--primary-color);
            transform: scale(1.05);
            box-shadow: 0 4px 20px rgba(25, 118, 210, 0.4);
        }
        
        .film-frame img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        
        /* 비디오 카드 스타일 */
        .video-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            transition: all 0.3s ease;
            animation: slideUp 0.3s ease-out;
        }
        
        .video-card:hover {
            border-color: var(--primary-color);
            box-shadow: 0 4px 20px rgba(25, 118, 210, 0.2);
        }
        
        .video-card.selected {
            background: rgba(25, 118, 210, 0.1);
            border-color: var(--primary-color);
        }
        
        /* 버튼 스타일 */
        .action-button {
            background: var(--primary-color);
            color: white;
            border: none;
            padding: 0.5rem 1.5rem;
            border-radius: 6px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .action-button:hover {
            background: #1565c0;
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(25, 118, 210, 0.4);
        }
        
        .action-button.secondary {
            background: var(--bg-secondary);
            color: var(--text-primary);
        }
        
        .action-button.danger {
            background: var(--danger-color);
        }
        
        /* 무드보드 모달 */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            z-index: 1000;
            display: flex;
            justify-content: center;
            align-items: center;
            animation: fadeIn 0.3s ease-out;
        }
        
        .modal-content {
            background: var(--bg-secondary);
            border-radius: 15px;
            width: 90%;
            max-width: 1200px;
            max-height: 90vh;
            overflow-y: auto;
            padding: 2rem;
            animation: slideUp 0.3s ease-out;
        }
        
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
            border-radius: 8px;
            overflow: hidden;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .grid-image:hover {
            transform: scale(1.05);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        }
        
        .grid-image.selected {
            border: 3px solid var(--primary-color);
        }
        
        .grid-image img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        
        /* 체크박스 스타일 */
        .image-checkbox {
            position: absolute;
            top: 10px;
            right: 10px;
            width: 24px;
            height: 24px;
            background: rgba(255, 255, 255, 0.9);
            border-radius: 4px;
            display: none;
        }
        
        .grid-image.selected .image-checkbox {
            display: block;
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
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* 결과 섹션 */
        .result-section {
            background: var(--bg-card);
            border-radius: 10px;
            padding: 1.5rem;
            margin: 1rem 0;
            animation: slideUp 0.5s ease-out;
        }
        
        .result-item {
            display: flex;
            align-items: flex-start;
            margin-bottom: 1rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid var(--border-color);
        }
        
        .result-item:last-child {
            border-bottom: none;
            margin-bottom: 0;
            padding-bottom: 0;
        }
        
        .result-label {
            font-weight: 600;
            color: var(--primary-color);
            min-width: 120px;
            margin-right: 1rem;
        }
        
        .result-value {
            flex: 1;
            color: var(--text-primary);
            line-height: 1.6;
        }
        
        /* 태그 스타일 */
        .tag-container {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }
        
        .tag {
            background: var(--primary-color);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 500;
        }
        
        /* 스크롤바 커스터마이징 */
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
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--primary-color);
        }
    </style>
    """