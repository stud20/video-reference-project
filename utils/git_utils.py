import subprocess
import os

def get_current_branch():
    """현재 Git 브랜치명을 반환합니다."""
    try:
        # Git 브랜치명 확인
        result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return None
    except Exception:
        return None

def is_beta_branch():
    """현재 브랜치가 베타(develop) 브랜치인지 확인합니다."""
    current_branch = get_current_branch()
    return current_branch == 'develop' if current_branch else False