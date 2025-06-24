# create_directories.py
"""
새로운 UI 구조를 위한 디렉토리 생성 스크립트
"""

import os

# 프로젝트 루트 디렉토리
root_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(root_dir, 'src')

# 생성할 디렉토리 구조
directories = [
    'src/ui',
    'src/ui/pages',
    'src/ui/components',
    'src/ui/styles'
]

# 디렉토리 생성
for directory in directories:
    dir_path = os.path.join(root_dir, directory)
    os.makedirs(dir_path, exist_ok=True)
    
    # __init__.py 파일 생성
    init_file = os.path.join(dir_path, '__init__.py')
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            f.write('"""UI modules"""')
        print(f"Created: {init_file}")

print("✅ 디렉토리 구조 생성 완료!")

# 파일 이동 안내
print("\n📁 다음 파일들을 생성해주세요:")
print("- src/ui/pages/analyze_page.py")
print("- src/ui/pages/database_page.py") 
print("- src/ui/pages/settings_page.py")
print("- src/ui/components/footer_stats.py")
print("- src/ui/styles/modern_theme.py")