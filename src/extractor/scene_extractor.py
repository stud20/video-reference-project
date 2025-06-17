# src/extractor/scene_extractor.py
"""영상에서 주요 씬 이미지 추출"""

import os
import subprocess
import json
from typing import List, Dict, Tuple
from dataclasses import dataclass
import cv2
from utils.logger import get_logger
from src.models.video import Scene

@dataclass
class SceneInfo:
    """씬 정보"""
    timestamp: float
    scene_score: float
    frame_path: str = ""

class SceneExtractor:
    """영상 씬 추출기"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.ffmpeg_path = self._find_ffmpeg()
        self.min_scenes = 5
        self.max_scenes = 10
        self.min_scene_duration = 1.0  # 최소 1초 간격
    
    def _find_ffmpeg(self) -> str:
        """FFmpeg 경로 찾기"""
        possible_paths = [
            "/opt/homebrew/bin/ffmpeg",  # M1 Mac
            "/usr/local/bin/ffmpeg",      # Intel Mac
            "ffmpeg"                      # PATH
        ]
        
        for path in possible_paths:
            try:
                subprocess.run([path, "-version"], 
                             capture_output=True, 
                             check=True)
                return path
            except:
                continue
        
        self.logger.warning("FFmpeg를 찾을 수 없습니다")
        return "ffmpeg"
    
    def get_video_duration(self, video_path: str) -> float:
        """영상 길이 확인 (초)"""
        try:
            cmd = [
                self.ffmpeg_path, '-i', video_path,
                '-show_entries', 'format=duration',
                '-v', 'quiet',
                '-of', 'csv=p=0'
            ]
            
            # ffprobe 사용
            ffprobe_path = self.ffmpeg_path.replace('ffmpeg', 'ffprobe')
            cmd[0] = ffprobe_path
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            duration = float(result.stdout.strip())
            
            self.logger.info(f"📹 영상 길이: {duration:.1f}초 ({duration/60:.1f}분)")
            return duration
            
        except Exception as e:
            self.logger.error(f"영상 길이 확인 실패: {e}")
            # OpenCV로 재시도
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            cap.release()
            return frame_count / fps if fps > 0 else 0
    
    def get_scene_threshold(self, duration: float) -> float:
        """영상 길이에 따른 scene threshold 자동 설정"""
        if duration <= 60:  # 1분 이하
            return 0.6
        elif duration <= 900:  # 15분 이하
            return 0.4
        else:  # 15분 초과
            return 0.3
    
    def detect_scenes(self, video_path: str, threshold: float) -> List[SceneInfo]:
        """FFmpeg를 사용한 씬 전환 검출"""
        self.logger.info(f"🎬 씬 검출 시작 (threshold: {threshold})")
        
        # 임시 로그 파일
        log_file = video_path + "_scene.log"
        
        try:
            # FFmpeg scene detection 명령
            cmd = [
                self.ffmpeg_path,
                '-i', video_path,
                '-filter:v', f'select=gt(scene\\,{threshold}),showinfo',
                '-f', 'null',
                '-'
            ]
            
            # 실행
            result = subprocess.run(
                cmd, 
                stderr=subprocess.PIPE, 
                text=True,
                encoding='utf-8'
            )
            
            # 로그에서 타임스탬프 추출
            scenes = []
            for line in result.stderr.split('\n'):
                if 'pts_time:' in line:
                    # pts_time 추출
                    try:
                        pts_time = float(line.split('pts_time:')[1].split()[0])
                        scenes.append(SceneInfo(timestamp=pts_time, scene_score=threshold))
                    except:
                        continue
            
            self.logger.info(f"📊 검출된 씬 수: {len(scenes)}")
            return scenes
            
        except Exception as e:
            self.logger.error(f"씬 검출 실패: {e}")
            return []
    
    def filter_scenes(self, scenes: List[SceneInfo], min_interval: float = 1.0) -> List[SceneInfo]:
        """씬 필터링 - 너무 가까운 씬 제거"""
        if not scenes:
            return []
        
        filtered = [scenes[0]]
        
        for scene in scenes[1:]:
            if scene.timestamp - filtered[-1].timestamp >= min_interval:
                filtered.append(scene)
        
        self.logger.info(f"🔍 필터링 후 씬 수: {len(filtered)}")
        return filtered
    
    def extract_frame(self, video_path: str, timestamp: float, output_path: str) -> bool:
        """특정 시간의 프레임 추출"""
        try:
            cmd = [
                self.ffmpeg_path,
                '-ss', str(timestamp),
                '-i', video_path,
                '-frames:v', '1',
                '-q:v', '2',  # JPEG 품질 (1-31, 낮을수록 좋음)
                '-y',
                output_path
            ]
            
            subprocess.run(cmd, capture_output=True, check=True)
            return os.path.exists(output_path)
            
        except Exception as e:
            self.logger.error(f"프레임 추출 실패 ({timestamp}s): {e}")
            return False
    
    def extract_scenes(self, video_path: str, output_dir: str) -> List[Scene]:
        """영상에서 주요 씬 추출"""
        if not os.path.exists(video_path):
            self.logger.error(f"영상 파일이 없습니다: {video_path}")
            return []
        
        # 출력 디렉토리 생성
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. 영상 길이 확인
        duration = self.get_video_duration(video_path)
        if duration <= 0:
            self.logger.error("영상 길이를 확인할 수 없습니다")
            return []
        
        # 2. 초기 threshold 설정
        threshold = self.get_scene_threshold(duration)
        
        # 3. 씬 검출 (최소 씬 수 확보를 위해 threshold 조정)
        scenes = []
        attempts = 0
        max_attempts = 3
        
        while len(scenes) < self.min_scenes and attempts < max_attempts:
            detected_scenes = self.detect_scenes(video_path, threshold)
            scenes = self.filter_scenes(detected_scenes, self.min_scene_duration)
            
            if len(scenes) < self.min_scenes:
                threshold *= 0.7  # threshold 낮춰서 더 많은 씬 검출
                attempts += 1
                self.logger.warning(f"씬 수 부족, threshold 조정: {threshold:.2f}")
        
        # 4. 백업 전략: 등간격 샘플링
        if len(scenes) < self.min_scenes:
            self.logger.warning("씬 검출 부족, 등간격 샘플링 사용")
            interval = duration / (self.min_scenes + 1)
            scenes = [SceneInfo(timestamp=interval * (i + 1), scene_score=0) 
                     for i in range(self.min_scenes)]
        
        # 5. 최대 씬 수 제한
        if len(scenes) > self.max_scenes:
            # scene_score가 높은 순으로 정렬하여 상위 10개 선택
            scenes = sorted(scenes, key=lambda x: x.scene_score, reverse=True)[:self.max_scenes]
            scenes = sorted(scenes, key=lambda x: x.timestamp)  # 시간순 재정렬
        
        # 6. 프레임 추출
        extracted_scenes = []
        for i, scene in enumerate(scenes):
            frame_filename = f"scene_{i+1:02d}_{scene.timestamp:.1f}s.jpg"
            frame_path = os.path.join(output_dir, frame_filename)
            
            if self.extract_frame(video_path, scene.timestamp, frame_path):
                extracted_scene = Scene(
                    timestamp=scene.timestamp,
                    frame_path=frame_path
                )
                extracted_scenes.append(extracted_scene)
                self.logger.info(f"✅ 씬 {i+1} 추출: {scene.timestamp:.1f}초")
        
        # 7. 메타데이터 저장
        metadata = {
            "video_path": video_path,
            "duration": duration,
            "threshold": threshold,
            "scenes": [
                {
                    "index": i + 1,
                    "timestamp": scene.timestamp,
                    "frame_path": scene.frame_path
                }
                for i, scene in enumerate(extracted_scenes)
            ]
        }
        
        metadata_path = os.path.join(output_dir, "scenes.json")
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"📸 총 {len(extracted_scenes)}개 씬 추출 완료")
        return extracted_scenes