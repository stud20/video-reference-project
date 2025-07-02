# src/pipeline/stages/storage_stage.py
"""스토리지 업로드 스테이지"""

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
        
        # 파일 수 계산
        file_count = 1  # 비디오
        
        # 이미지 파일 수 계산
        scenes_dir = os.path.join(video.session_dir, "scenes")
        grouped_dir = os.path.join(video.session_dir, "grouped")
        
        self.logger.info(f"🔍 디렉토리 확인:")
        self.logger.info(f"  - scenes: {scenes_dir} (존재: {os.path.exists(scenes_dir)})")
        self.logger.info(f"  - grouped: {grouped_dir} (존재: {os.path.exists(grouped_dir)})")
        
        if os.path.exists(scenes_dir):
            scene_count = len([f for f in os.listdir(scenes_dir) if f.endswith('.jpg')])
            file_count += scene_count
            self.logger.info(f"  - scenes 이미지: {scene_count}개")
        if os.path.exists(grouped_dir):
            grouped_count = len([f for f in os.listdir(grouped_dir) if f.endswith('.jpg')])
            file_count += grouped_count
            self.logger.info(f"  - grouped 이미지: {grouped_count}개")
        
        # 썸네일
        file_count += 1
        
        if video.analysis_result:
            file_count += 1  # 분석 결과
        
        self.logger.info(f"📊 총 업로드할 파일: {file_count}개")
        
        uploaded = 0
        
        # 1. 비디오 파일 업로드
        if video.local_path and os.path.exists(video.local_path):
            video_filename = os.path.basename(video.local_path)
            remote_video_path = os.path.join(remote_base_path, video_filename)
            
            self.logger.info(f"📹 비디오 업로드: {video.local_path} -> {remote_video_path}")
            if self.storage_manager.upload_file(video.local_path, remote_video_path):
                uploaded += 1
                self.logger.info(f"✅ 비디오 업로드 완료: {video_filename}")
            else:
                self.logger.error(f"❌ 비디오 업로드 실패: {video_filename}")
        
        # 2. 썸네일 업로드
        thumbnail_path = os.path.join(video.session_dir, f"{video.session_id}_Thumbnail.jpg")
        if os.path.exists(thumbnail_path):
            remote_thumb_path = os.path.join(remote_base_path, f"{video.session_id}_Thumbnail.jpg")
            self.logger.info(f"🖼️ 썸네일 업로드: {thumbnail_path} -> {remote_thumb_path}")
            if self.storage_manager.upload_file(thumbnail_path, remote_thumb_path):
                uploaded += 1
                self.logger.info(f"✅ 썸네일 업로드 완료")
            else:
                self.logger.error(f"❌ 썸네일 업로드 실패")
        
        # 3. 씬 이미지 업로드 (scenes 디렉토리)
        self.logger.info(f"🎬 씬 이미지 업로드 시작")
        if os.path.exists(scenes_dir):
            scene_files = sorted([f for f in os.listdir(scenes_dir) 
                                if f.endswith('.jpg')])
            self.logger.info(f"📸 발견된 scene 파일: {len(scene_files)}개")
            
            for i, scene_file in enumerate(scene_files):
                scene_path = os.path.join(scenes_dir, scene_file)
                remote_scene_path = os.path.join(remote_base_path, scene_file)
                
                self.logger.info(f"📤 씬 업로드 [{i+1}/{len(scene_files)}]: {scene_path} -> {remote_scene_path}")
                if self.storage_manager.upload_file(scene_path, remote_scene_path):
                    uploaded += 1
                    self.logger.info(f"✅ scene 업로드 성공: {scene_file}")
                else:
                    self.logger.error(f"❌ scene 업로드 실패: {scene_file}")
                
                progress = 85 + int((uploaded / file_count) * 10)
                self.update_progress(progress, f"📤 씬 업로드 중: {scene_file}", context)
        else:
            self.logger.warning(f"⚠️ scenes 디렉토리가 없음: {scenes_dir}")
        
        # 4. 그룹화된 이미지 업로드 (grouped 디렉토리)
        self.logger.info(f"🎨 그룹 이미지 업로드 시작")
        if os.path.exists(grouped_dir):
            grouped_files = sorted([f for f in os.listdir(grouped_dir) 
                                  if f.endswith('.jpg')])
            self.logger.info(f"🖼️ 발견된 grouped 파일: {len(grouped_files)}개")
            
            for i, grouped_file in enumerate(grouped_files):
                grouped_path = os.path.join(grouped_dir, grouped_file)
                remote_grouped_path = os.path.join(remote_base_path, grouped_file)
                
                self.logger.info(f"📤 그룹 업로드 [{i+1}/{len(grouped_files)}]: {grouped_path} -> {remote_grouped_path}")
                if self.storage_manager.upload_file(grouped_path, remote_grouped_path):
                    uploaded += 1
                    self.logger.info(f"✅ grouped 업로드 성공: {grouped_file}")
                else:
                    self.logger.error(f"❌ grouped 업로드 실패: {grouped_file}")
                
                progress = 85 + int((uploaded / file_count) * 10)
                self.update_progress(progress, f"📤 그룹 이미지 업로드 중: {grouped_file}", context)
        else:
            self.logger.warning(f"⚠️ grouped 디렉토리가 없음: {grouped_dir}")
        
        # 5. 분석 결과 업로드
        if video.analysis_result:
            analysis_path = os.path.join(video.session_dir, "analysis_result.json")
            
            if not os.path.exists(analysis_path):
                import json
                os.makedirs(os.path.dirname(analysis_path), exist_ok=True)
                with open(analysis_path, 'w', encoding='utf-8') as f:
                    json.dump(video.analysis_result, f, ensure_ascii=False, indent=2)
            
            remote_analysis_path = os.path.join(remote_base_path, "analysis_result.json")
            
            self.logger.info(f"📄 분석 결과 업로드: {analysis_path} -> {remote_analysis_path}")
            if self.storage_manager.upload_file(analysis_path, remote_analysis_path):
                uploaded += 1
                self.logger.info(f"✅ 분석 결과 업로드 완료")
            else:
                self.logger.error(f"❌ 분석 결과 업로드 실패")
        
        self.logger.info(f"📊 업로드 완료: {uploaded}/{file_count}개 파일")
        self.update_progress(95, "✅ 스토리지 업로드 완료", context)
        
        return context
