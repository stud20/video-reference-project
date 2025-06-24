# src/ui/styles.py

def get_enhanced_styles() -> str:
    """향상된 UI 스타일 - 콘솔 애니메이션 포함"""
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
            --console-bg: #000000;
            --console-text: #00ff00;
            --console-border: #333333;
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
        
        @keyframes typewriter {
            from { width: 0; }
            to { width: 100%; }
        }
        
        @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0; }
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
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
            transition: all 0.3s ease;
        }
        
        .analyze-input-wrapper:hover {
            box-shadow: 0 15px 50px rgba(0, 0, 0, 0.4);
            transform: translateY(-2px);
        }
        
        /* 콘솔 창 스타일 - 실제 터미널처럼 */
        .console-window {
            background: var(--console-bg);
            color: var(--console-text);
            font-family: 'Courier New', 'Consolas', 'Monaco', monospace;
            padding: 15px;
            border-radius: 8px;
            height: 120px;
            overflow-y: auto;
            overflow-x: hidden;
            margin: 1rem 0;
            border: 1px solid var(--console-border);
            font-size: 14px;
            line-height: 1.6;
            animation: slideUp 0.3s ease-out;
            box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.5);
            position: relative;
        }
        
        /* 콘솔 스크롤바 스타일 */
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
        
        /* 콘솔 라인 스타일 */
        .console-line {
            margin: 4px 0;
            opacity: 0;
            animation: consoleFadeIn 0.3s ease-out forwards;
            white-space: nowrap;
            overflow: hidden;
            position: relative;
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
        
        /* 콘솔 커서 효과 */
        .console-line:last-child::after {
            content: '_';
            animation: blink 1s infinite;
            color: var(--console-text);
            font-weight: bold;
        }
        
        /* 콘솔 프롬프트 스타일 */
        .console-line::before {
            content: '> ';
            color: rgba(0, 255, 0, 0.7);
            margin-right: 5px;
        }
        
        /* 필름 스트립 스타일 */
        .film-strip-container {
            background: var(--bg-secondary);
            border-radius: 10px;
            padding: 1.5rem;
            margin: 1rem 0;
            animation: slideUp 0.5s ease-out;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        }
        
        .film-strip {
            display: flex;
            gap: 15px;
            overflow-x: auto;
            padding: 15px 5px;
            scroll-behavior: smooth;
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
            transition: all 0.3s ease;
        }
        
        .film-strip::-webkit-scrollbar-thumb:hover {
            background: #1565c0;
        }
        
        .film-frame {
            min-width: 180px;
            height: 120px;
            border-radius: 8px;
            overflow: hidden;
            border: 2px solid var(--border-color);
            transition: all 0.3s ease;
            cursor: pointer;
            position: relative;
            background: var(--bg-card);
            opacity: 0;
            animation: filmFrameFadeIn 0.4s ease-out forwards;
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
        
        .film-frame:hover {
            border-color: var(--primary-color);
            transform: scale(1.05) translateY(-5px);
            box-shadow: 0 8px 30px rgba(25, 118, 210, 0.4);
            z-index: 10;
        }
        
        .film-frame img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.3s ease;
        }
        
        .film-frame:hover img {
            transform: scale(1.1);
        }
        
        /* 비디오 임베드 컨테이너 */
        .video-embed-container {
            position: relative;
            padding-bottom: 56.25%;
            height: 0;
            overflow: hidden;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
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
            animation: slideUp 0.5s ease-out;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
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
        
        /* 태그 스타일 */
        .tag-container {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }
        
        .tag {
            background: var(--primary-color);
            color: white;
            padding: 6px 15px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 500;
            transition: all 0.3s ease;
            cursor: pointer;
            opacity: 0;
            animation: tagFadeIn 0.3s ease-out forwards;
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
        
        .tag:hover {
            background: #1565c0;
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(25, 118, 210, 0.4);
        }
        
        /* 액션 버튼 스타일 */
        .action-button {
            background: var(--primary-color);
            color: white;
            border: none;
            padding: 0.8rem 1.5rem;
            border-radius: 8px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            box-shadow: 0 2px 10px rgba(25, 118, 210, 0.3);
        }
        
        .action-button:hover {
            background: #1565c0;
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(25, 118, 210, 0.5);
        }
        
        .action-button:active {
            transform: translateY(0);
        }
        
        .action-button.secondary {
            background: var(--bg-secondary);
            color: var(--text-primary);
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
        }
        
        .action-button.secondary:hover {
            background: #363640;
        }
        
        .action-button.danger {
            background: var(--danger-color);
            box-shadow: 0 2px 10px rgba(220, 53, 69, 0.3);
        }
        
        .action-button.danger:hover {
            background: #c82333;
            box-shadow: 0 6px 20px rgba(220, 53, 69, 0.5);
        }
        
        /* 모달 스타일 */
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
            animation: modalSlideIn 0.3s ease-out;
            box-shadow: 0 10px 50px rgba(0, 0, 0, 0.5);
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
        
        /* 프로그레스 인디케이터 */
        .progress-indicator {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px;
            background: rgba(25, 118, 210, 0.1);
            border-radius: 8px;
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
            transition: background 0.3s ease;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--primary-color);
        }
        
        /* 반응형 디자인 */
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
        }
    </style>
    """