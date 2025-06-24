# fix_imports.py
"""
src. 프리픽스를 제거하는 스크립트
프로젝트 루트에서 실행하세요.
"""

import os
import re

def fix_imports_in_file(filepath):
    """파일에서 src. import를 수정"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # import 패턴 수정
    patterns = [
        (r'from src\.ui\.', 'from ui.'),
        (r'from src\.utils\.', 'from utils.'),
        (r'from src\.handlers\.', 'from handlers.'),
        (r'from src\.storage\.', 'from storage.'),
        (r'from src\.services\.', 'from services.'),
        (r'import src\.', 'import '),
    ]
    
    modified = False
    for pattern, replacement in patterns:
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            modified = True
            content = new_content
    
    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ 수정됨: {filepath}")
    else:
        print(f"⏭️  변경 없음: {filepath}")

def main():
    """메인 함수"""
    # 수정할 파일들
    files_to_fix = [
        'app.py',
        'src/ui/styles.py',
        'src/ui/components/sidebar.py',
        'src/ui/components/database_modal.py',
        'src/ui/components/video_cards.py',
        'src/ui/components/analysis_display.py',
        'src/utils/constants.py',
        'src/utils/session_state.py',
        'src/handlers/db_handler.py',
        'src/handlers/video_handler.py',
    ]
    
    print("🔧 Import 경로 수정 시작...\n")
    
    for filepath in files_to_fix:
        if os.path.exists(filepath):
            fix_imports_in_file(filepath)
        else:
            print(f"❌ 파일 없음: {filepath}")
    
    print("\n✨ Import 경로 수정 완료!")
    print("\n다음 단계:")
    print("1. src/__init__.py 파일이 있는지 확인하세요")
    print("2. streamlit run app.py 로 실행하세요")

if __name__ == "__main__":
    main()