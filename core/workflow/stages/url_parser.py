# src/pipeline/stages/url_parse_stage.py
"""URL 파싱 스테이지"""

import re
from typing import Tuple

from ..pipeline import PipelineStage, PipelineContext


class URLParseStage(PipelineStage):
    """URL 파싱 및 플랫폼 식별"""
    
    def __init__(self):
        super().__init__("url_parse")
    
    def execute(self, context: PipelineContext) -> PipelineContext:
        """URL 파싱 실행"""
        self.update_progress(5, "🔍 영상 URL 분석 중...", context)
        
        platform, video_id = self._parse_video_url(context.url)
        
        context.platform = platform
        context.video_id = video_id
        
        self.update_progress(10, f"✅ 플랫폼 확인: {platform} - {video_id}", context)
        
        return context
    
    def _parse_video_url(self, url: str) -> Tuple[str, str]:
        """URL에서 플랫폼과 비디오 ID 추출"""
        if 'youtube.com' in url or 'youtu.be' in url:
            # YouTube ID 추출
            patterns = [
                r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
                r'youtu\.be\/([0-9A-Za-z_-]{11})',
                r'youtube\.com\/embed\/([0-9A-Za-z_-]{11})',
                r'youtube\.com\/v\/([0-9A-Za-z_-]{11})'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return 'youtube', match.group(1)
                    
        elif 'vimeo.com' in url:
            # Vimeo ID 추출
            patterns = [
                r'vimeo\.com\/(\d+)',
                r'player\.vimeo\.com\/video\/(\d+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return 'vimeo', match.group(1)
        
        raise ValueError(f"지원하지 않는 비디오 URL 형식입니다: {url}")
