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
