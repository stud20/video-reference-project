#!/bin/bash

# Vimeo 수동 다운로드 테스트 스크립트
# 사용법: ./test_vimeo_download.sh

echo "🎬 Vimeo 다운로드 테스트 시작..."
echo "📹 URL: https://vimeo.com/662442279"
echo ""

# 다운로드 디렉토리 생성
mkdir -p vimeo_test
cd vimeo_test

echo "🔄 방법 1: 기본 yt-dlp 시도..."
yt-dlp "https://vimeo.com/662442279" \
    --output "%(id)s_%(title)s.%(ext)s" \
    --format "best[ext=mp4]" \
    --verbose

if [ $? -eq 0 ]; then
    echo "✅ 방법 1 성공!"
    exit 0
fi

echo ""
echo "🔄 방법 2: Player URL 사용..."
yt-dlp "https://player.vimeo.com/video/662442279" \
    --output "%(id)s_%(title)s.%(ext)s" \
    --format "best[ext=mp4]" \
    --referer "https://vimeo.com/662442279" \
    --user-agent "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
    --verbose

if [ $? -eq 0 ]; then
    echo "✅ 방법 2 성공!"
    exit 0
fi

echo ""
echo "🔄 방법 3: 최강 우회 모드..."
yt-dlp "https://player.vimeo.com/video/662442279" \
    --output "%(id)s_%(title)s.%(ext)s" \
    --format "best[ext=mp4]" \
    --referer "https://vimeo.com/662442279" \
    --user-agent "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
    --add-header "Accept:text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" \
    --add-header "Accept-Language:en-US,en;q=0.5" \
    --add-header "DNT:1" \
    --add-header "Connection:keep-alive" \
    --add-header "Upgrade-Insecure-Requests:1" \
    --geo-bypass \
    --geo-bypass-country US \
    --socket-timeout 120 \
    --retries 30 \
    --fragment-retries 30 \
    --sleep-interval 5 \
    --max-sleep-interval 15 \
    --no-check-certificate \
    --ignore-errors \
    --verbose

if [ $? -eq 0 ]; then
    echo "✅ 방법 3 성공!"
    exit 0
fi

echo ""
echo "🔄 방법 4: 정보만 추출 시도..."
yt-dlp "https://vimeo.com/662442279" \
    --dump-json \
    --no-download \
    --verbose

echo ""
echo "❌ 모든 방법 실패. 이 영상은 다운로드가 제한되어 있을 수 있습니다."
echo "🔒 Cloudflare 보호, 비공개 설정, 또는 지역 제한이 적용된 것으로 보입니다."