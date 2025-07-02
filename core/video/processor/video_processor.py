# core/video/processor/video_processor.py
"""비디오 코덱 확인 및 재인코딩 처리"""

import subprocess
import os
from utils.logger import get_logger

class VideoProcessor:
    """비디오 후처리 - macOS 호환성 확인 및 재인코딩"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.ffmpeg_path = self._find_ffmpeg()
        self.non_playable_codecs = {"vp9", "vp8", "av1", "vp09", "vp08", "vp10"}
    
    def _find_ffmpeg(self) -> str:
        """FFmpeg 경로 찾기"""
        # 가능한 FFmpeg 경로들
        possible_paths = [
            "/opt/homebrew/bin/ffmpeg",  # M1 Mac homebrew
            "/usr/local/bin/ffmpeg",      # Intel Mac homebrew
            "ffmpeg"                      # PATH에 있는 경우
        ]
        
        for path in possible_paths:
            try:
                subprocess.run([path, "-version"], 
                             capture_output=True, 
                             check=True)
                self.logger.info(f"✅ FFmpeg 찾음: {path}")
                return path
            except:
                continue
        
        self.logger.warning("⚠️ FFmpeg를 찾을 수 없습니다. 재인코딩 기능 비활성화")
        return None
    
    def get_video_codec(self, file_path: str) -> str:
        """비디오 코덱 확인"""
        if not self.ffmpeg_path or not os.path.exists(file_path):
            return None
        
        try:
            result = subprocess.run(
                [self.ffmpeg_path, '-i', file_path],
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True
            )
            
            for line in result.stderr.splitlines():
                if 'Video:' in line:
                    codec = line.split('Video:')[1].split(',')[0].strip()
                    self.logger.info(f"🎥 비디오 코덱: {codec}")
                    return codec
                    
        except Exception as e:
            self.logger.error(f"코덱 확인 중 오류: {e}")
        
        return None
    
    def needs_reencode(self, file_path: str) -> bool:
        """재인코딩이 필요한지 확인"""
        codec = self.get_video_codec(file_path)
        if not codec:
            return False
        
        needs_reencode = codec.lower() in self.non_playable_codecs
        if needs_reencode:
            self.logger.warning(f"⚠️ macOS 미지원 코덱({codec}) 감지")
        
        return needs_reencode
    
    def reencode_to_h264(self, input_file: str, delete_original: bool = True) -> str:
        """H.264로 재인코딩"""
        if not self.ffmpeg_path:
            self.logger.error("FFmpeg가 없어 재인코딩할 수 없습니다")
            return input_file
        
        # 출력 파일명 생성
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}-h264.mp4"
        
        self.logger.info("🎞 H.264로 재인코딩 시작...")
        
        cmd = [
            self.ffmpeg_path, 
            '-y',  # 덮어쓰기
            '-i', input_file,
            '-c:v', 'libx264',         # H.264 비디오 코덱
            '-c:a', 'aac',             # AAC 오디오 코덱
            '-preset', 'fast',         # 인코딩 속도
            '-crf', '23',             # 품질 (18-28, 낮을수록 좋음)
            '-movflags', '+faststart', # 웹 스트리밍 최적화
            output_file
        ]
        
        try:
            # 진행률 표시를 위한 설정
            process = subprocess.Popen(
                cmd, 
                stderr=subprocess.PIPE, 
                universal_newlines=True
            )
            
            # 진행 상황 모니터링
            for line in process.stderr:
                if 'time=' in line:
                    # 시간 정보 추출 (선택사항)
                    pass
            
            process.wait()
            
            if process.returncode == 0 and os.path.exists(output_file):
                self.logger.info(f"✅ 재인코딩 완료: {output_file}")
                
                # 파일 크기 비교
                original_size = os.path.getsize(input_file) / (1024 * 1024)  # MB
                new_size = os.path.getsize(output_file) / (1024 * 1024)  # MB
                self.logger.info(f"📊 크기: {original_size:.1f}MB → {new_size:.1f}MB")
                
                # 원본 삭제 (옵션)
                if delete_original:
                    os.remove(input_file)
                    self.logger.info(f"🗑 원본 삭제 완료")
                
                return output_file
            else:
                self.logger.error("재인코딩 실패")
                return input_file
                
        except Exception as e:
            self.logger.error(f"재인코딩 중 오류: {e}")
            return input_file
    
    def process_video(self, file_path: str) -> str:
        """비디오 처리 - 필요시 재인코딩"""
        if not os.path.exists(file_path):
            return file_path
        
        # 코덱 확인
        if self.needs_reencode(file_path):
            return self.reencode_to_h264(file_path)
        else:
            codec = self.get_video_codec(file_path)
            self.logger.info(f"✅ macOS 호환 코덱({codec}) - 재인코딩 불필요")
            return file_path