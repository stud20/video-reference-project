# config/migration_config.py
"""마이그레이션 설정 - 점진적 전환을 위한 설정"""

import os

# 새로운 AI Analyzer 사용 여부
USE_NEW_AI_ANALYZER = os.getenv("USE_NEW_AI_ANALYZER", "false").lower() == "true"

# 디버그 모드
DEBUG_MODE = os.getenv("DEBUG_MODE", "true").lower() == "true"

# 마이그레이션 플래그들
MIGRATION_FLAGS = {
    "use_new_analyzer": USE_NEW_AI_ANALYZER,
    "use_new_prompt_builder": True,  # 프롬프트 빌더는 바로 적용 가능
    "use_new_parser": True,  # 파서도 바로 적용 가능
    "enable_debug_logging": DEBUG_MODE
}
