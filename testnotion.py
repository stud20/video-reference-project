from dotenv import load_dotenv
load_dotenv()

import os
from notion_client import Client

# Notion 클라이언트 초기화
client = Client(auth=os.getenv("NOTION_API_KEY"))
database_id = os.getenv("NOTION_DATABASE_ID")

# 데이터베이스 정보 가져오기
try:
    db = client.databases.retrieve(database_id)
    
    print("📊 Notion 데이터베이스 속성 목록:")
    print("=" * 50)
    
    for prop_name, prop_info in db['properties'].items():
        prop_type = prop_info['type']
        print(f"- {prop_name}: {prop_type}")
        
        # select/multi_select의 경우 옵션도 표시
        if prop_type in ['select', 'multi_select']:
            options = prop_info.get(prop_type, {}).get('options', [])
            if options:
                print(f"  옵션: {[opt['name'] for opt in options[:5]]}...")
    
    print("=" * 50)
    print(f"총 {len(db['properties'])}개의 속성")
    
except Exception as e:
    print(f"❌ 오류: {e}")