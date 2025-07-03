# src/pipeline/stages/storage_stage.py
"""스토리지 업로드 스테이지 - 배치 업로드 지원"""

import os
from integrations.storage.interface import StorageType, StorageManager

from ..pipeline import PipelineStage, PipelineContext


class StorageUploadStage(PipelineStage):
    """스토리지 업로드"""
    
    def __init__(self, storage_type: StorageType = None):
        super().__init__("storage_upload")
        
        # 스토리지 타입 결정
        if storage_type is None:
            storage_type_str = os.getenv("STORAGE_TYPE", "local").lower()
            storage_type = StorageType.SFTP if storage_type_str == "sftp" else StorageType.LOCAL
        
        self.storage_manager = StorageManager(storage_type)
        self.storage_type = storage_type
    
    def can_skip(self, context: PipelineContext) -> bool:
        """로컬 스토리지이거나 캐시 히트 시 스킵"""
        # 환경변수로 로컬 스토리지 스킵 여부 결정
        skip_local_storage = os.getenv("SKIP_LOCAL_STORAGE", "true").lower() == "true"
        
        return ((self.storage_type == StorageType.LOCAL and skip_local_storage) or 
                context.stage_results.get("cache_hit", False))
    
    def execute(self, context: PipelineContext) -> PipelineContext:
        """스토리지 업로드 실행"""
        self.update_progress(85, "📤 스토리지 업로드 시작...", context)
        
        video = context.video_object
        remote_base_path = f"video_analysis/{video.session_id}"
        
        # 세션 디렉토리 확인
        self.logger.info(f"📁 세션 디렉토리: {video.session_dir}")
        
        # 모든 업로드할 파일을 수집
        file_pairs = []
        
        # 1. 비디오 파일
        if video.local_path and os.path.exists(video.local_path):
            video_filename = os.path.basename(video.local_path)
            remote_video_path = os.path.join(remote_base_path, video_filename)
            file_pairs.append((video.local_path, remote_video_path))
            self.logger.info(f"📹 비디오 파일 추가: {video_filename}")
        
        # 2. 썸네일
        thumbnail_path = os.path.join(video.session_dir, f"{video.session_id}_Thumbnail.jpg")
        if os.path.exists(thumbnail_path):
            remote_thumb_path = os.path.join(remote_base_path, f"{video.session_id}_Thumbnail.jpg")
            file_pairs.append((thumbnail_path, remote_thumb_path))
            self.logger.info(f"🖼️ 썸네일 파일 추가")
        
        # 3. 씬 이미지 (scenes 디렉토리)
        scenes_dir = os.path.join(video.session_dir, "scenes")
        if os.path.exists(scenes_dir):
            scene_files = sorted([f for f in os.listdir(scenes_dir) if f.endswith('.jpg')])
            self.logger.info(f"🎬 씬 이미지 추가: {len(scene_files)}개")
            
            for scene_file in scene_files:
                scene_path = os.path.join(scenes_dir, scene_file)
                remote_scene_path = os.path.join(remote_base_path, scene_file)
                file_pairs.append((scene_path, remote_scene_path))
        
        # 4. 그룹화된 이미지 (grouped 디렉토리)
        grouped_dir = os.path.join(video.session_dir, "grouped")
        if os.path.exists(grouped_dir):
            grouped_files = sorted([f for f in os.listdir(grouped_dir) if f.endswith('.jpg')])
            self.logger.info(f"🎨 그룹 이미지 추가: {len(grouped_files)}개")
            
            for grouped_file in grouped_files:
                grouped_path = os.path.join(grouped_dir, grouped_file)
                remote_grouped_path = os.path.join(remote_base_path, grouped_file)
                file_pairs.append((grouped_path, remote_grouped_path))
        
        # 5. 분석 결과
        if video.analysis_result:
            analysis_path = os.path.join(video.session_dir, "analysis_result.json")
            
            if not os.path.exists(analysis_path):
                import json
                os.makedirs(os.path.dirname(analysis_path), exist_ok=True)
                with open(analysis_path, 'w', encoding='utf-8') as f:
                    json.dump(video.analysis_result, f, ensure_ascii=False, indent=2)
            
            remote_analysis_path = os.path.join(remote_base_path, "analysis_result.json")
            file_pairs.append((analysis_path, remote_analysis_path))
            self.logger.info(f"📄 분석 결과 파일 추가")
        
        # 파일 개수 통계
        self.logger.info(f"📊 업로드할 파일 총 {len(file_pairs)}개:")
        self.logger.info(f"  - 비디오: {sum(1 for p in file_pairs if 'mp4' in p[0] or 'webm' in p[0])}개")
        self.logger.info(f"  - 이미지: {sum(1 for p in file_pairs if '.jpg' in p[0])}개")
        self.logger.info(f"  - JSON: {sum(1 for p in file_pairs if '.json' in p[0])}개")
        
        # 배치 업로드 실행
        if self.storage_type == StorageType.SFTP and len(file_pairs) > 1:
            # SFTP의 경우 배치 업로드 사용
            self.logger.info(f"🚀 SFTP 배치 업로드 시작 (동시 {os.getenv('SFTP_MAX_CONCURRENT', '5')}개 연결)")
            # 진행률 콜백 없이 실행 (현재 버그가 있음)
            results = self.storage_manager.upload_files_batch(file_pairs)
            
            # 결과 분석
            uploaded = sum(1 for r in results if r["success"])
            failed = [r for r in results if not r["success"]]
            
            self.logger.info(f"📊 업로드 완료: {uploaded}/{len(file_pairs)}개 파일")
            
            if failed:
                self.logger.warning(f"⚠️ 실패한 파일 {len(failed)}개:")
                for f in failed:
                    self.logger.error(f"  ❌ {f['local_path']}: {f['error']}")
        else:
            # 로컬 스토리지나 파일이 1개인 경우 순차 처리
            self.logger.info(f"📤 순차 업로드 시작")
            uploaded = 0
            
            for i, (local_path, remote_path) in enumerate(file_pairs):
                filename = os.path.basename(local_path)
                self.logger.info(f"📤 업로드 [{i+1}/{len(file_pairs)}]: {filename}")
                
                if self.storage_manager.upload_file(local_path, remote_path):
                    uploaded += 1
                    self.logger.info(f"✅ {filename} 업로드 성공")
                else:
                    self.logger.error(f"❌ {filename} 업로드 실패")
                
                # 진행률 업데이트
                progress = 85 + int(((i+1) / len(file_pairs)) * 10)
                self.update_progress(progress, f"📤 업로드 중: {filename}", context)
            
            self.logger.info(f"📊 업로드 완료: {uploaded}/{len(file_pairs)}개 파일")
        
        self.update_progress(95, "✅ 스토리지 업로드 완료", context)
        
        return context
