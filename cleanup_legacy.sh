#!/bin/bash
# 레거시 코드 정리 스크립트

echo "🧹 레거시 코드 정리를 시작합니다..."

# 삭제할 디렉토리 및 파일 목록
ITEMS_TO_DELETE=(
    "legacy/"
    "old/"
    "src/"
    "app.py"
    "test_factchat_api.py"
    "core/analysis/providers/openai_gpt4_debug.py"  # 디버깅용 임시 파일
)

# 각 항목 삭제
for item in "${ITEMS_TO_DELETE[@]}"; do
    if [ -e "$item" ]; then
        echo "삭제: $item"
        rm -rf "$item"
    else
        echo "존재하지 않음: $item"
    fi
done

# Python 캐시 파일 정리
echo "🗑️ Python 캐시 파일 정리 중..."
find . -type f -name "*.pyc" -delete
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name ".DS_Store" -delete

echo "✅ 레거시 코드 정리 완료!"
echo ""
echo "📁 현재 프로젝트 구조:"
ls -la
