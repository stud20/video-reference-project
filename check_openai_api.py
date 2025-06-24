# check_openai_api.py
"""OpenAI API 키 및 사용량 확인"""

import os
from openai import OpenAI
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

def check_api_key():
    """API 키 확인 및 간단한 테스트"""
    api_key = os.getenv("OPENAI_API_KEY")
    
    print("🔍 OpenAI API 확인")
    print("=" * 50)
    
    # 1. API 키 존재 확인
    if not api_key:
        print("❌ OPENAI_API_KEY가 .env 파일에 설정되지 않았습니다.")
        return
    
    print(f"✅ API 키 발견: {api_key[:8]}...{api_key[-4:]}")
    
    # 2. API 키 형식 확인
    if not api_key.startswith("sk-"):
        print("⚠️ API 키 형식이 올바르지 않습니다. 'sk-'로 시작해야 합니다.")
        return
    
    # 3. 간단한 API 테스트
    try:
        client = OpenAI(api_key=api_key)
        
        # 간단한 테스트 요청 (최소 토큰 사용)
        print("\n📝 간단한 테스트 요청 중...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # 저렴한 모델로 테스트
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5
        )
        
        print("✅ API 연결 성공!")
        print(f"응답: {response.choices[0].message.content}")
        
        # 4. 사용 가능한 모델 확인
        print("\n📋 GPT-4 Vision 테스트...")
        try:
            # GPT-4 Vision 테스트 (텍스트만)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5
            )
            print("✅ GPT-4 Vision (gpt-4o) 사용 가능!")
        except Exception as e:
            print(f"❌ GPT-4 Vision 사용 불가: {e}")
            print("💡 대안: gpt-4-vision-preview 또는 gpt-4-turbo-vision을 시도해보세요")
        
    except Exception as e:
        print(f"\n❌ API 오류: {e}")
        
        if "insufficient_quota" in str(e):
            print("\n💡 해결 방법:")
            print("1. https://platform.openai.com/usage 에서 사용량 확인")
            print("2. https://platform.openai.com/account/billing 에서 결제 정보 확인")
            print("3. 크레딧이 남아있는지 확인")
            print("4. API 키가 올바른 조직/프로젝트의 키인지 확인")
        elif "invalid_api_key" in str(e):
            print("\n💡 API 키가 유효하지 않습니다. 다시 확인해주세요.")

if __name__ == "__main__":
    check_api_key()