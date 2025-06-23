#!/bin/bash
# create_init_files.sh
# src 디렉토리 구조에 필요한 __init__.py 파일들을 생성합니다

echo "📁 Creating __init__.py files..."

# src 디렉토리
touch src/__init__.py
echo '"""Source root package"""' > src/__init__.py

# ui 디렉토리
touch src/ui/__init__.py
echo '"""UI components package"""' > src/ui/__init__.py

# ui/components 디렉토리
touch src/ui/components/__init__.py
echo '"""UI components modules"""' > src/ui/components/__init__.py

# utils 디렉토리
touch src/utils/__init__.py
echo '"""Utility modules"""' > src/utils/__init__.py

# handlers 디렉토리
touch src/handlers/__init__.py
echo '"""Handler modules"""' > src/handlers/__init__.py

# storage 디렉토리 (이미 있을 수도 있음)
if [ ! -f "src/storage/__init__.py" ]; then
    touch src/storage/__init__.py
    echo '"""Storage modules"""' > src/storage/__init__.py
fi

# services 디렉토리 (이미 있을 수도 있음)
if [ ! -f "src/services/__init__.py" ]; then
    touch src/services/__init__.py
    echo '"""Service modules"""' > src/services/__init__.py
fi

echo "✅ All __init__.py files created!"
echo ""
echo "📂 Directory structure:"
find src -name "__init__.py" | sort