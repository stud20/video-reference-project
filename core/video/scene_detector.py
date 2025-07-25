# src/extractor/scene_extractor.py
"""정밀도 레벨 기반 개선된 씬 추출 및 그룹화 모듈"""

import os
import cv2
import numpy as np
from typing import List, Dict, Any, Tuple, Optional, Callable
from pathlib import Path
import subprocess
import json
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from scipy.spatial.distance import cdist
import imagehash
from PIL import Image
from collections import defaultdict
from utils.logger import get_logger
from core.video.models import Scene

logger = get_logger(__name__)



class SceneExtractor:
    """영상에서 주요 씬을 추출하고 정밀도 레벨에 따라 정교하게 그룹화"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.temp_dir = "data/temp"
        
        # 기본값 설정 (load_settings 전에 초기화)
        self.precision_level = 5
        self.target_scene_count = 6  # 기본값 설정
        
        # 초기 설정 로드
        self.load_settings()
        
        # 정밀도 레벨별 특징 가중치 및 목표 씬 개수 설정
        self._setup_precision_weights()
        
        self.logger.info(f"🎯 SceneExtractor 초기화 - 정밀도 레벨: {self.precision_level}")
    
    def load_settings(self):
        """환경변수에서 설정 로드"""
        # 정밀도 레벨 (1-10) - 따옴표 처리 추가
        precision_str = os.getenv("SCENE_PRECISION_LEVEL")
        # 따옴표 제거
        precision_str = precision_str.strip("'\"")
        
        try:
            self.precision_level = int(precision_str)
        except ValueError:
            self.logger.warning(f"잘못된 SCENE_PRECISION_LEVEL 값: {precision_str}, 기본값 5 사용")
            self.precision_level = 5
        
        # 씬 추출 설정
        self.scene_threshold = float(os.getenv("SCENE_THRESHOLD", "0.3"))
        self.min_scene_duration = float(os.getenv("MIN_SCENE_DURATION", "0.5"))
        
        # 그룹화 설정
        self.min_scenes_for_grouping = int(os.getenv("MIN_SCENES_FOR_GROUPING", "10"))
        self.similarity_threshold = float(os.getenv("SCENE_SIMILARITY_THRESHOLD", "0.92"))
        self.hash_threshold = int(os.getenv("SCENE_HASH_THRESHOLD", "5"))
        self.max_output_scenes = int(os.getenv("MAX_ANALYSIS_IMAGES", "10"))
        
        # 로그 추가하여 실제 로드된 값 확인
        self.logger.info(f"📋 설정 로드 완료:")
        self.logger.info(f"  - SCENE_PRECISION_LEVEL: {self.precision_level}")
        # target_scene_count는 _setup_precision_weights 이후에 설정되므로 여기서는 로그하지 않음
        
    def update_settings(self):
        """환경변수에서 최신 설정을 다시 읽어옴"""
        # 이전 설정 저장
        old_precision_level = self.precision_level
        old_scene_threshold = self.scene_threshold
        old_similarity_threshold = self.similarity_threshold
        
        # 새로운 설정 로드
        self.load_settings()
        
        # 변경사항 로깅
        settings_changed = False
        
        if old_precision_level != self.precision_level:
            self.logger.info(f"🔄 정밀도 레벨 변경: {old_precision_level} → {self.precision_level}")
            settings_changed = True
        
        if abs(old_scene_threshold - self.scene_threshold) > 0.001:
            self.logger.info(f"🔄 씬 전환 임계값 변경: {old_scene_threshold:.3f} → {self.scene_threshold:.3f}")
            settings_changed = True
        
        if abs(old_similarity_threshold - self.similarity_threshold) > 0.001:
            self.logger.info(f"🔄 씬 유사도 임계값 변경: {old_similarity_threshold:.3f} → {self.similarity_threshold:.3f}")
            settings_changed = True
        
        # 정밀도 레벨이 변경되었으면 가중치 재설정
        if old_precision_level != self.precision_level:
            self._setup_precision_weights()
            self.logger.info(f"✅ 정밀도 레벨 {self.precision_level} 설정 적용 완료")
        
        if not settings_changed:
            self.logger.debug("설정 변경사항 없음")
        
        return settings_changed
    
    def _setup_precision_weights(self):
        """정밀도 레벨에 따른 특징 가중치 및 출력 설정"""
        
        # 기본 가중치 (레벨 10)
        base_weights = {
            'color_hist': 0.25,      # 색상 히스토그램
            'edge_density': 0.20,    # 엣지 밀도
            'texture': 0.20,         # 텍스처 특징
            'spatial_color': 0.15,   # 공간별 색상 분포
            'perceptual_hash': 0.10, # 지각적 해시
            'brightness': 0.05,      # 밝기
            'contrast': 0.03,        # 대비
            'color_diversity': 0.02  # 색상 다양성
        }
        
        # 정밀도 레벨별 설정
        if self.precision_level == 1:
            # 초고속: 색상 히스토그램만
            self.feature_weights = {'color_hist': 1.0}
            self.active_features = ['color_hist']
            self.target_scene_count = 4  # 최소한의 다양성
            
        elif self.precision_level == 2:
            # 고속: 색상 + 기본 엣지
            self.feature_weights = {'color_hist': 0.7, 'edge_density': 0.3}
            self.active_features = ['color_hist', 'edge_density']
            self.target_scene_count = 4
            
        elif self.precision_level == 3:
            # 빠름: 색상 + 엣지 + 밝기
            self.feature_weights = {'color_hist': 0.6, 'edge_density': 0.25, 'brightness': 0.15}
            self.active_features = ['color_hist', 'edge_density', 'brightness']
            self.target_scene_count = 5
            
        elif self.precision_level == 4:
            # 보통-빠름: 기본 특징들
            self.feature_weights = {
                'color_hist': 0.4, 'edge_density': 0.3, 
                'brightness': 0.2, 'contrast': 0.1
            }
            self.active_features = ['color_hist', 'edge_density', 'brightness', 'contrast']
            self.target_scene_count = 5
            
        elif self.precision_level == 5:
            # 균형: 권장 설정 - 6개 목표
            self.feature_weights = {
                'color_hist': 0.35, 'edge_density': 0.25, 
                'brightness': 0.15, 'contrast': 0.15, 'color_diversity': 0.1
            }
            self.active_features = ['color_hist', 'edge_density', 'brightness', 'contrast', 'color_diversity']
            self.target_scene_count = 6  # 6개 목표
            
        elif self.precision_level == 6:
            # 정밀: 기본 + 텍스처 - 7개 목표
            self.feature_weights = {
                'color_hist': 0.3, 'edge_density': 0.2, 'texture': 0.2,
                'brightness': 0.1, 'contrast': 0.1, 'color_diversity': 0.1
            }
            self.active_features = ['color_hist', 'edge_density', 'texture', 'brightness', 'contrast', 'color_diversity']
            self.target_scene_count = 7
            
        elif self.precision_level == 7:
            # 고정밀: 기본 + 텍스처 + 공간색상 - 8개 목표
            self.feature_weights = {
                'color_hist': 0.25, 'edge_density': 0.2, 'texture': 0.2,
                'spatial_color': 0.15, 'brightness': 0.08, 'contrast': 0.07, 'color_diversity': 0.05
            }
            self.active_features = ['color_hist', 'edge_density', 'texture', 'spatial_color', 'brightness', 'contrast', 'color_diversity']
            self.target_scene_count = 8
            
        elif self.precision_level == 8:
            # 매우정밀: 대부분 특징 활성화 - 10개 목표
            self.feature_weights = {
                'color_hist': 0.25, 'edge_density': 0.2, 'texture': 0.2,
                'spatial_color': 0.15, 'perceptual_hash': 0.08,
                'brightness': 0.05, 'contrast': 0.04, 'color_diversity': 0.03
            }
            self.active_features = ['color_hist', 'edge_density', 'texture', 'spatial_color', 'perceptual_hash', 'brightness', 'contrast', 'color_diversity']
            self.target_scene_count = 10
            
        elif self.precision_level == 9:
            # 초정밀: 거의 모든 특징 - 10개 목표
            self.feature_weights = base_weights.copy()
            self.active_features = list(base_weights.keys())
            self.target_scene_count = 10
            
        else:  # 레벨 10
            # 최고정밀: 모든 특징 + 고해상도 - 10개 목표
            self.feature_weights = base_weights.copy()
            self.active_features = list(base_weights.keys())
            self.target_scene_count = 10
            # 고해상도 처리를 위한 추가 설정
            self.high_resolution_mode = True
        
        # 가중치 정규화
        total_weight = sum(self.feature_weights.values())
        if total_weight > 0:
            self.feature_weights = {k: v/total_weight for k, v in self.feature_weights.items()}
        
        self.logger.info(f"🔧 정밀도 레벨 {self.precision_level} 설정 완료")
        self.logger.info(f"📋 활성화된 특징: {', '.join(self.active_features)}")
        self.logger.info(f"🎯 목표 씬 개수: {self.target_scene_count}개")
    
        
    def extract_scenes(self, video_path: str, session_id: str, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """비디오에서 모든 씬 추출 후 정밀도에 따라 그룹화"""
        # 시작하기 전에 최신 설정 로드
        settings_changed = self.update_settings()
        if settings_changed:
            self.logger.info("🔄 변경된 설정으로 씬 추출을 시작합니다")
        
        try:
            output_dir = os.path.join(self.temp_dir, session_id, "scenes")
            os.makedirs(output_dir, exist_ok=True)
            
            self.logger.info(f"🎬 씬 추출 시작")
            
            # 1. FFmpeg로 모든 씬 전환점 검출 (정밀도와 무관)
            self.logger.info("🔍 씬 전환점 검출 중...")
            scene_changes = self._detect_scene_changes(video_path)
            
            if not scene_changes:
                self.logger.warning("씬 전환점을 찾을 수 없습니다")
                return {'all_scenes': [], 'grouped_scenes': []}
            
            # 2. 비디오 정보 가져오기
            video_info = self._get_video_info(video_path)
            duration = float(video_info.get('duration', 0))
            width = int(video_info.get('width', 0))
            height = int(video_info.get('height', 0))
            
            # Shorts/Reels 감지
            is_short_form = duration <= 60 or (height > width and height/width > 1.5)
            if is_short_form:
                self.logger.info(f"📱 짧은 형식 동영상 감지! (길이: {duration:.1f}초, 비율: {width}x{height})")
                # 짧은 동영상용 설정 조정
                self.min_scene_duration = 0.2  # 더 짧은 씬도 포함
                self.scene_threshold = 0.15  # 더 민감한 씬 감지
            
            self.logger.info(f"📹 영상 길이: {duration:.1f}초")
            
            # 3. 모든 씬 중간점에서 프레임 추출
            all_scenes = self._extract_frames_at_midpoints(
                video_path, scene_changes, output_dir, duration, progress_callback
            )
            
            self.logger.info(f"📸 총 {len(all_scenes)}개 씬 추출 완료")
            
            # 4. 정밀도 레벨에 따른 그룹화 수행
            grouped_scenes = []
            if len(all_scenes) > 0:
                self.logger.info(f"🔬 정밀도 레벨 {self.precision_level}로 씬 그룹화 시작...")
                grouped_scenes = self._group_similar_scenes_precision(all_scenes.copy(), output_dir, progress_callback)
                
                # 그룹화된 씬들을 별도 디렉토리에 저장
                grouped_scenes = self._save_grouped_scenes(grouped_scenes, session_id)
            
            self.logger.info(
                f"✅ 씬 추출 완료 - 전체: {len(all_scenes)}개, "
                f"그룹화: {len(grouped_scenes)}개 (정밀도 레벨: {self.precision_level})"
            )
            
            # 5. 결과 반환 (전체 씬과 그룹화된 씬 모두 포함)
            return {
                'all_scenes': all_scenes,
                'grouped_scenes': grouped_scenes,
                'precision_level': self.precision_level,
                'target_count': self.target_scene_count
            }
            
        except Exception as e:
            self.logger.error(f"씬 추출 중 오류: {str(e)}")
            return {'all_scenes': [], 'grouped_scenes': []}
        
    def _detect_scene_changes(self, video_path: str) -> List[float]:
        """FFmpeg를 사용한 모든 씬 전환점 검출 (정밀도와 무관)"""
        # 정밀도 레벨 조정 제거 - 항상 동일한 임계값 사용
        threshold = self.scene_threshold
        
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-filter:v', f"select='gt(scene,{threshold})',showinfo",
            '-f', 'null',
            '-'
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            # showinfo 출력에서 타임스탬프 추출
            timestamps = []
            for line in result.stderr.split('\n'):
                if 'pts_time:' in line:
                    try:
                        pts_time = float(line.split('pts_time:')[1].split()[0])
                        timestamps.append(pts_time)
                    except:
                        continue
            
            # 시작점 추가
            if timestamps and timestamps[0] > 1.0:
                timestamps.insert(0, 0.0)
            elif not timestamps:
                timestamps = [0.0]
            
            self.logger.info(f"🎞️ {len(timestamps)}개 씬 전환점 검출 (임계값: {threshold:.3f})")
            
            return timestamps
            
        except Exception as e:
            self.logger.error(f"씬 검출 실패: {str(e)}")
            return []
    
    def _extract_frames_at_midpoints(
        self, 
        video_path: str, 
        scene_changes: List[float], 
        output_dir: str,
        duration: float,
        progress_callback: Optional[Callable] = None
    ) -> List[Scene]:
        """씬 중간점에서 프레임 추출"""
        scenes = []
        
        # 마지막 타임스탬프 추가
        if scene_changes[-1] < duration - 1:
            scene_changes.append(duration)
        
        # 정밀도 레벨에 따른 품질 설정
        quality = '2'  # 기본 고품질
        if self.precision_level <= 3:
            quality = '5'  # 빠른 처리를 위해 낮은 품질
        elif self.precision_level >= 8:
            quality = '1'  # 최고 품질
        
        # 각 씬의 중간점 계산
        total_scenes = len(scene_changes) - 1
        
        for i in range(len(scene_changes) - 1):
            start_time = scene_changes[i]
            end_time = scene_changes[i + 1]
            
            # 너무 짧은 씬 제외
            if end_time - start_time < self.min_scene_duration:
                continue
            
            # 진행률 업데이트
            if progress_callback and total_scenes > 0:
                progress = int(40 + (i / total_scenes) * 30)  # 40-70% 범위
                progress_callback(progress, f"📸 프레임 추출 중... {i+1}/{total_scenes}")
            
            # 중간점 계산
            mid_time = (start_time + end_time) / 2
            
            # 프레임 추출
            output_path = os.path.join(output_dir, f"scene_{i:04d}.jpg")
            
            cmd = [
                'ffmpeg',
                '-ss', str(mid_time),
                '-i', video_path,
                '-frames:v', '1',
                '-q:v', quality,
                output_path,
                '-y'
            ]
            
            try:
                subprocess.run(cmd, capture_output=True, check=True)
                
                if os.path.exists(output_path):
                    scene = Scene(
                        timestamp=mid_time,
                        frame_path=output_path,
                        scene_type='mid'
                    )
                    scenes.append(scene)
                    
            except Exception as e:
                self.logger.error(f"프레임 추출 실패 ({mid_time:.1f}초): {str(e)}")
        
        return scenes
    
    def _group_similar_scenes_precision(self, scenes: List[Scene], output_dir: str, progress_callback: Optional[Callable] = None) -> List[Scene]:
        """정밀도 레벨 기반 씬 그룹화 알고리즘 (개선된 버전)"""
        if len(scenes) <= self.min_scenes_for_grouping:
            # 씬이 적은 경우 목표 개수에 맞춰 조정
            if len(scenes) < self.target_scene_count:
                return scenes  # 모든 씬 반환
            else:
                return self._select_diverse_scenes(scenes)[:self.target_scene_count]
        
        # 1. 정밀도 레벨에 따른 특징 추출
        self.logger.info(f"🔬 정밀도 레벨 {self.precision_level} 특징 추출 중...")
        features = []
        valid_scenes = []
        
        for i, scene in enumerate(scenes):
            try:
                if self.precision_level <= 5:
                    # 빠른 처리를 위해 진행률 로깅 생략
                    pass
                else:
                    # 상세한 진행률 표시
                    if i % 10 == 0:
                        self.logger.info(f"📊 특징 추출 진행률: {i+1}/{len(scenes)}")
                
                feature_vector = self._extract_precision_features(scene.frame_path)
                if feature_vector is not None:
                    features.append(feature_vector)
                    valid_scenes.append(scene)
            except Exception as e:
                self.logger.warning(f"특징 추출 실패: {scene.frame_path} - {str(e)}")
        
        if not features:
            return scenes[:self.target_scene_count]
        
        # 2. 특징 정규화
        features_array = np.array(features)
        scaler = StandardScaler()
        features_normalized = scaler.fit_transform(features_array)
        
        # 3. 정밀도 레벨에 따른 거리 계산
        distance_matrix = self._calculate_precision_distance(features_normalized)
        
        # 4. 적응적 클러스터링 파라미터
        eps = self._get_adaptive_clustering_eps(len(valid_scenes))
        min_samples = max(2, min(4, len(valid_scenes) // 15))  # 더 작은 클러스터 허용
        
        clustering = DBSCAN(
            eps=eps,
            min_samples=min_samples,
            metric='precomputed'
        ).fit(distance_matrix)
        
        # 5. 클러스터 대표 씬 선택
        cluster_representatives = self._select_cluster_representatives(
            valid_scenes, features_normalized, clustering.labels_
        )
        
        # 6. 노이즈 포인트 처리
        noise_scenes = [
            scene for i, scene in enumerate(valid_scenes) 
            if clustering.labels_[i] == -1
        ]
        
        # 7. 목표 개수에 맞춘 씬 선택 전략
        final_scenes = self._balance_scene_selection(
            cluster_representatives, noise_scenes, valid_scenes
        )
        
        # 8. 최종 씬 리스트 (시간순 정렬)
        final_scenes.sort(key=lambda s: s.timestamp)
        
        self.logger.info(
            f"📊 정밀도 레벨 {self.precision_level} 그룹화 완료: "
            f"{len(scenes)}개 → {len(final_scenes)}개 "
            f"(목표: {self.target_scene_count}개, 클러스터: {len(cluster_representatives)}, 독립: {len(noise_scenes)})"
        )
        
        return final_scenes

    def _save_grouped_scenes(self, grouped_scenes: List[Scene], session_id: str) -> List[Scene]:
        """그룹화된 씬들을 별도 디렉토리에 저장"""
        grouped_dir = os.path.join(self.temp_dir, session_id, "grouped")
        os.makedirs(grouped_dir, exist_ok=True)
        
        updated_scenes = []
        for i, scene in enumerate(grouped_scenes):
            # 원본 씬 이미지 경로
            original_path = scene.frame_path
            
            # 그룹화된 씬 이미지 경로
            grouped_filename = f"grouped_{i:04d}.jpg"
            grouped_path = os.path.join(grouped_dir, grouped_filename)
            
            # 이미지 복사
            try:
                import shutil
                shutil.copy2(original_path, grouped_path)
                
                # Scene 객체 업데이트 (grouped 경로 추가)
                scene.grouped_path = grouped_path
                updated_scenes.append(scene)
                
                self.logger.debug(f"그룹화된 씬 저장: {grouped_filename}")
            except Exception as e:
                self.logger.error(f"그룹화된 씬 복사 실패: {str(e)}")
                updated_scenes.append(scene)
        
        return updated_scenes
        
    def _balance_scene_selection(self, cluster_reps: List[Scene], noise_scenes: List[Scene], all_scenes: List[Scene]) -> List[Scene]:
        """목표 개수에 맞춘 균형잡힌 씬 선택"""
        current_count = len(cluster_reps) + len(noise_scenes)
        
        # 목표 개수보다 적은 경우
        if current_count < self.target_scene_count:
            needed = self.target_scene_count - current_count
            
            # 사용되지 않은 씬들에서 추가 선택
            used_scenes = set(cluster_reps + noise_scenes)
            unused_scenes = [s for s in all_scenes if s not in used_scenes]
            
            if unused_scenes:
                # 시간적으로 균등하게 분산된 씬 추가
                additional_scenes = self._select_time_distributed_scenes(unused_scenes, needed)
                result = cluster_reps + noise_scenes + additional_scenes
            else:
                result = cluster_reps + noise_scenes
                
        # 목표 개수보다 많은 경우
        elif current_count > self.target_scene_count:
            # 클러스터 대표 씬을 우선적으로 선택
            if len(cluster_reps) >= self.target_scene_count:
                # 클러스터 대표 씬만으로 목표 달성
                result = self._select_diverse_scenes(cluster_reps)[:self.target_scene_count]
            else:
                # 클러스터 대표 + 일부 노이즈 씬
                remaining_slots = self.target_scene_count - len(cluster_reps)
                selected_noise = self._select_diverse_scenes(noise_scenes)[:remaining_slots]
                result = cluster_reps + selected_noise
        else:
            # 정확히 목표 개수
            result = cluster_reps + noise_scenes
        
        return result
    
    def _select_time_distributed_scenes(self, scenes: List[Scene], count: int) -> List[Scene]:
        """시간적으로 균등하게 분산된 씬 선택"""
        if len(scenes) <= count:
            return scenes
        
        # 시간순으로 정렬
        sorted_scenes = sorted(scenes, key=lambda s: s.timestamp)
        
        # 균등 간격으로 선택
        interval = len(sorted_scenes) / count
        selected_indices = [int(i * interval) for i in range(count)]
        
        return [sorted_scenes[i] for i in selected_indices]
    
    def _get_adaptive_clustering_eps(self, scene_count: int) -> float:
        """씬 개수와 정밀도 레벨에 따른 적응적 eps 값"""
        base_eps = 1.0 - self.similarity_threshold
        
        # 씬 개수에 따른 조정
        if scene_count > 30:
            count_factor = 0.8  # 많은 씬: 더 엄격하게
        elif scene_count < 15:
            count_factor = 1.3  # 적은 씬: 더 관대하게
        else:
            count_factor = 1.0
        
        # 정밀도 레벨에 따른 조정
        if self.precision_level <= 3:
            precision_factor = 1.5  # 빠른 처리: 더 관대한 그룹화
        elif self.precision_level >= 8:
            precision_factor = 0.7  # 고정밀: 더 엄격한 그룹화
        else:
            precision_factor = 1.0
        
        return base_eps * count_factor * precision_factor
    
    def _extract_precision_features(self, image_path: str) -> Optional[np.ndarray]:
        """정밀도 레벨에 따른 특징 추출"""
        try:
            # OpenCV로 이미지 읽기
            img_bgr = cv2.imread(image_path)
            if img_bgr is None:
                return None
            
            # 정밀도 레벨에 따른 이미지 크기 조정
            if self.precision_level <= 3:
                # 빠른 처리를 위해 크기 축소
                img_bgr = cv2.resize(img_bgr, (160, 120))
            elif self.precision_level >= 8:
                # 고정밀을 위해 큰 크기 유지
                img_bgr = cv2.resize(img_bgr, (320, 240))
            else:
                # 기본 크기
                img_bgr = cv2.resize(img_bgr, (240, 180))
            
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
            img_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
            
            features = []
            
            # 활성화된 특징만 추출
            if 'color_hist' in self.active_features:
                features.extend(self._extract_color_histogram(img_hsv))
            
            if 'edge_density' in self.active_features:
                features.append(self._extract_edge_density(img_gray))
            
            if 'texture' in self.active_features:
                features.extend(self._extract_lbp_features(img_gray))
            
            if 'spatial_color' in self.active_features:
                features.extend(self._extract_spatial_color(img_hsv))
            
            if 'perceptual_hash' in self.active_features:
                features.extend(self._extract_perceptual_hash(img_rgb))
            
            if 'brightness' in self.active_features:
                features.extend(self._extract_brightness_stats(img_hsv))
            
            if 'contrast' in self.active_features:
                features.append(self._extract_contrast(img_gray))
            
            if 'color_diversity' in self.active_features:
                features.append(self._extract_color_diversity(img_rgb))
            
            return np.array(features) if features else None
            
        except Exception as e:
            self.logger.error(f"정밀도 특징 추출 오류: {str(e)}")
            return None
    
    def _extract_color_histogram(self, img_hsv: np.ndarray) -> List[float]:
        """색상 히스토그램 추출"""
        # 정밀도 레벨에 따른 히스토그램 빈 수 조정
        bins = 16 if self.precision_level <= 3 else 32 if self.precision_level <= 7 else 64
        
        hist_h = cv2.calcHist([img_hsv], [0], None, [bins], [0, 180])
        hist_s = cv2.calcHist([img_hsv], [1], None, [bins], [0, 256])
        hist_v = cv2.calcHist([img_hsv], [2], None, [bins], [0, 256])
        
        color_hist = np.concatenate([hist_h, hist_s, hist_v]).flatten()
        color_hist = color_hist / (color_hist.sum() + 1e-7)
        
        return color_hist.tolist()
    
    def _extract_edge_density(self, img_gray: np.ndarray) -> float:
        """엣지 밀도 추출"""
        # 정밀도 레벨에 따른 Canny 임계값 조정
        if self.precision_level <= 3:
            edges = cv2.Canny(img_gray, 100, 200)
        elif self.precision_level >= 8:
            edges = cv2.Canny(img_gray, 30, 100)
        else:
            edges = cv2.Canny(img_gray, 50, 150)
        
        return float(np.sum(edges > 0) / edges.size)
    
    def _extract_lbp_features(self, gray_img: np.ndarray, num_points: int = 8, radius: int = 1) -> List[float]:
        """Local Binary Patterns 특징 추출"""
        h, w = gray_img.shape
        lbp = np.zeros_like(gray_img)
        
        # 정밀도 레벨에 따른 LBP 파라미터 조정
        if self.precision_level <= 3:
            num_points = 6  # 빠른 처리
        elif self.precision_level >= 8:
            num_points = 12  # 정밀한 처리
        
        for i in range(radius, h - radius):
            for j in range(radius, w - radius):
                center = gray_img[i, j]
                binary_code = 0
                
                for k in range(num_points):
                    angle = 2 * np.pi * k / num_points
                    x = int(round(i + radius * np.cos(angle)))
                    y = int(round(j + radius * np.sin(angle)))
                    
                    if 0 <= x < h and 0 <= y < w and gray_img[x, y] >= center:
                        binary_code |= (1 << k)
                
                lbp[i, j] = binary_code
        
        # LBP 히스토그램
        bins = 16 if self.precision_level <= 5 else 32
        hist, _ = np.histogram(lbp, bins=bins, range=(0, 256))
        hist = hist.astype(float) / (hist.sum() + 1e-7)
        
        return hist.tolist()
    
    def _extract_spatial_color(self, img_hsv: np.ndarray) -> List[float]:
        """공간별 색상 분포 추출"""
        h, w = img_hsv.shape[:2]
        
        # 정밀도 레벨에 따른 그리드 크기 조정
        if self.precision_level <= 3:
            grid_size = 2
        elif self.precision_level <= 6:
            grid_size = 3
        else:
            grid_size = 4
        
        spatial_features = []
        
        for i in range(grid_size):
            for j in range(grid_size):
                y1 = i * h // grid_size
                y2 = (i + 1) * h // grid_size
                x1 = j * w // grid_size
                x2 = (j + 1) * w // grid_size
                
                region = img_hsv[y1:y2, x1:x2]
                bins = 8 if self.precision_level <= 5 else 16
                region_hist = cv2.calcHist([region], [0], None, [bins], [0, 180])
                region_hist = region_hist.flatten() / (region_hist.sum() + 1e-7)
                spatial_features.extend(region_hist)
        
        return spatial_features
    
    def _extract_perceptual_hash(self, img_rgb: np.ndarray) -> List[float]:
        """지각적 해시 추출"""
        pil_img = Image.fromarray(img_rgb)
        
        # 정밀도 레벨에 따른 해시 크기 조정
        hash_size = 4 if self.precision_level <= 3 else 8 if self.precision_level <= 7 else 16
        
        phash = imagehash.phash(pil_img, hash_size=hash_size)
        dhash = imagehash.dhash(pil_img, hash_size=hash_size)
        
        # 해시를 바이너리 배열로 변환
        hash_features = []
        
        for hash_obj in [phash, dhash]:
            for char in str(hash_obj):
                if char in '0123456789abcdef':
                    binary = format(int(char, 16), '04b')
                    hash_features.extend([float(b) for b in binary])
        
        return hash_features
    
    def _extract_brightness_stats(self, img_hsv: np.ndarray) -> List[float]:
        """밝기 통계 추출"""
        brightness = img_hsv[:, :, 2]
        mean_brightness = np.mean(brightness) / 255.0
        std_brightness = np.std(brightness) / 255.0
        
        if self.precision_level >= 7:
            # 고정밀도에서는 추가 통계 포함
            min_brightness = np.min(brightness) / 255.0
            max_brightness = np.max(brightness) / 255.0
            return [mean_brightness, std_brightness, min_brightness, max_brightness]
        
        return [mean_brightness, std_brightness]
    
    def _extract_contrast(self, img_gray: np.ndarray) -> float:
        """대비 추출"""
        return float(img_gray.std() / 255.0)
    
    def _extract_color_diversity(self, img_rgb: np.ndarray) -> float:
        """색상 다양성 추출"""
        h, w = img_rgb.shape[:2]
        
        # 정밀도 레벨에 따른 샘플링 조정
        if self.precision_level <= 3:
            # 빠른 처리를 위해 샘플링
            sample_rate = 4
            sampled = img_rgb[::sample_rate, ::sample_rate].reshape(-1, 3)
        else:
            sampled = img_rgb.reshape(-1, 3)
        
        unique_colors = len(np.unique(sampled, axis=0))
        total_pixels = len(sampled)
        
        return float(unique_colors / total_pixels)
    
    def _calculate_precision_distance(self, features: np.ndarray) -> np.ndarray:
        """정밀도 레벨에 따른 가중치 기반 거리 행렬 계산"""
        n_samples = features.shape[0]
        distance_matrix = np.zeros((n_samples, n_samples))
        
        # 특징별 인덱스 범위 동적 계산
        idx = 0
        feature_ranges = {}
        
        for feat_name in self.active_features:
            if feat_name == 'color_hist':
                size = self._get_color_hist_size()
                feature_ranges[feat_name] = (idx, idx + size)
                idx += size
            elif feat_name == 'edge_density':
                feature_ranges[feat_name] = (idx, idx + 1)
                idx += 1
            elif feat_name == 'texture':
                size = 16 if self.precision_level <= 5 else 32
                feature_ranges[feat_name] = (idx, idx + size)
                idx += size
            elif feat_name == 'spatial_color':
                grid_size = 2 if self.precision_level <= 3 else 3 if self.precision_level <= 6 else 4
                bins = 8 if self.precision_level <= 5 else 16
                size = grid_size * grid_size * bins
                feature_ranges[feat_name] = (idx, idx + size)
                idx += size
            elif feat_name == 'perceptual_hash':
                hash_size = 4 if self.precision_level <= 3 else 8 if self.precision_level <= 7 else 16
                size = hash_size * hash_size * 2 * 4  # phash + dhash, 4비트 per hex char
                feature_ranges[feat_name] = (idx, idx + size)
                idx += size
            elif feat_name == 'brightness':
                size = 4 if self.precision_level >= 7 else 2
                feature_ranges[feat_name] = (idx, idx + size)
                idx += size
            elif feat_name == 'contrast':
                feature_ranges[feat_name] = (idx, idx + 1)
                idx += 1
            elif feat_name == 'color_diversity':
                feature_ranges[feat_name] = (idx, idx + 1)
                idx += 1
        
        # 각 특징별로 거리 계산 후 가중치 적용
        for feat_name, (start, end) in feature_ranges.items():
            if start < features.shape[1] and feat_name in self.feature_weights:
                weight = self.feature_weights[feat_name]
                actual_end = min(end, features.shape[1])
                
                if start < actual_end:
                    feat_distances = cdist(
                        features[:, start:actual_end], 
                        features[:, start:actual_end], 
                        metric='euclidean'
                    )
                    # 정규화
                    if feat_distances.max() > 0:
                        feat_distances = feat_distances / feat_distances.max()
                    distance_matrix += weight * feat_distances
        
        return distance_matrix
    
    def _get_color_hist_size(self) -> int:
        """정밀도 레벨에 따른 색상 히스토그램 크기 반환"""
        bins = 16 if self.precision_level <= 3 else 32 if self.precision_level <= 7 else 64
        return bins * 3  # H, S, V
    
    def _select_cluster_representatives(
        self, 
        scenes: List[Scene], 
        features: np.ndarray, 
        labels: np.ndarray
    ) -> List[Scene]:
        """각 클러스터에서 가장 대표적인 씬 선택"""
        representatives = []
        unique_labels = set(labels)
        unique_labels.discard(-1)  # 노이즈 제외
        
        for label in unique_labels:
            # 클러스터에 속한 씬들의 인덱스
            cluster_indices = np.where(labels == label)[0]
            
            if len(cluster_indices) == 1:
                representatives.append(scenes[cluster_indices[0]])
            else:
                # 정밀도 레벨에 따른 대표 씬 선택 방식
                if self.precision_level <= 3:
                    # 빠른 처리: 첫 번째 씬 선택
                    representatives.append(scenes[cluster_indices[0]])
                else:
                    # 클러스터 중심과 가장 가까운 씬 선택
                    cluster_features = features[cluster_indices]
                    center = np.mean(cluster_features, axis=0)
                    distances = np.sum((cluster_features - center) ** 2, axis=1)
                    closest_idx = cluster_indices[np.argmin(distances)]
                    representatives.append(scenes[closest_idx])
        
        return representatives
    
    def _select_diverse_scenes(self, scenes: List[Scene]) -> List[Scene]:
        """다양성을 고려한 씬 선택"""
        if len(scenes) <= self.target_scene_count:
            return scenes
        
        # 정밀도 레벨에 따른 선택 방식
        if self.precision_level <= 3:
            # 빠른 처리: 균등 간격 샘플링
            interval = len(scenes) / self.target_scene_count
            selected_indices = [int(i * interval) for i in range(self.target_scene_count)]
            return [scenes[i] for i in selected_indices]
        else:
            # 정밀한 처리: 시간적 분산을 고려한 선택
            if len(scenes) == 0:
                return []
            
            selected = [scenes[0]]  # 첫 번째 씬 포함
            remaining = scenes[1:]
            
            while len(selected) < self.target_scene_count and remaining:
                # 선택된 씬들과 시간적으로 가장 멀리 떨어진 씬 선택
                max_min_distance = -1
                best_scene = None
                best_idx = -1
                
                for i, candidate in enumerate(remaining):
                    min_distance = min(
                        abs(candidate.timestamp - selected_scene.timestamp)
                        for selected_scene in selected
                    )
                    
                    if min_distance > max_min_distance:
                        max_min_distance = min_distance
                        best_scene = candidate
                        best_idx = i
                
                if best_scene:
                    selected.append(best_scene)
                    remaining.pop(best_idx)
                else:
                    break
            
            return sorted(selected, key=lambda s: s.timestamp)
    
    def _get_video_info(self, video_path: str) -> Dict[str, Any]:
        """비디오 정보 추출"""
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            video_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            info = json.loads(result.stdout)
            
            # 비디오 스트림 찾기
            video_stream = None
            for stream in info.get('streams', []):
                if stream.get('codec_type') == 'video':
                    video_stream = stream
                    break
            
            return {
                'duration': float(info.get('format', {}).get('duration', 0)),
                'width': int(video_stream.get('width', 0)) if video_stream else 0,
                'height': int(video_stream.get('height', 0)) if video_stream else 0,
                'fps': eval(video_stream.get('r_frame_rate', '0/1')) if video_stream else 0
            }
            
        except Exception as e:
            self.logger.error(f"비디오 정보 추출 실패: {str(e)}")
            return {}