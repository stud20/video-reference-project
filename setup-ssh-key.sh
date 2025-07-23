#!/bin/bash

# SSH 키 설정 도우미 스크립트

echo "🔐 SSH 키 기반 인증 설정"
echo "========================="
echo ""
echo "이 스크립트는 비밀번호 없이 SSH 접속을 위한 키를 설정합니다."
echo ""

# 1. SSH 키 생성 확인
if [ ! -f ~/.ssh/id_rsa ]; then
    echo "📝 SSH 키가 없습니다. 새로 생성합니다..."
    ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""
else
    echo "✅ 기존 SSH 키를 사용합니다."
fi

# 2. 원격 서버에 키 복사
echo ""
echo "🔑 원격 서버에 SSH 키를 복사합니다."
echo "비밀번호를 한 번만 입력하면 이후에는 비밀번호 없이 접속할 수 있습니다."
echo ""

ssh-copy-id ysk@192.168.50.50

echo ""
echo "✅ 설정 완료!"
echo ""
echo "이제 다음 명령으로 테스트해보세요:"
echo "ssh ysk@192.168.50.50 'echo SSH 접속 성공!'"