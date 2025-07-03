# integrations/storage/sftp_async.py
"""비동기 SFTP 클라이언트 - asyncssh 사용"""
import asyncio
import asyncssh
import os
import time
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from datetime import datetime
from config.settings import Settings
from utils.logger import get_logger


class AsyncSFTPStorage:
    """비동기 SFTP 스토리지 클라이언트"""
    
    def __init__(self):
        self.settings = Settings()
        self.logger = get_logger(__name__)
        
        # .env에서 SFTP 설정 로드
        self.host = os.getenv("SFTP_HOST")
        self.port = int(os.getenv("SFTP_PORT", "22"))
        self.username = os.getenv("SFTP_USER")
        self.password = os.getenv("SFTP_PASS")
        
        # WebDAV와 동일한 기본 경로 사용
        self.base_path = os.getenv("WEBDAV_ROOT", "/dav/videoRef").rstrip('/')
        
        # 동시 업로드 설정
        self.max_concurrent = int(os.getenv("SFTP_MAX_CONCURRENT", "5"))
        self.chunk_size = int(os.getenv("SFTP_CHUNK_SIZE", "32768"))  # 32KB
        
        # 설정 검증
        self._validate_config()
        
    def _validate_config(self):
        """SFTP 설정 검증"""
        missing_configs = []
        
        if not self.host:
            missing_configs.append("SFTP_HOST")
        if not self.username:
            missing_configs.append("SFTP_USER")
        if not self.password:
            missing_configs.append("SFTP_PASS")
            
        if missing_configs:
            error_msg = f"필수 SFTP 설정이 누락되었습니다: {', '.join(missing_configs)}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
            
        # 설정 로그 (비밀번호는 마스킹)
        self.logger.info(f"📋 비동기 SFTP 설정:")
        self.logger.info(f"  - Host: {self.host}")
        self.logger.info(f"  - Port: {self.port}")
        self.logger.info(f"  - User: {self.username}")
        self.logger.info(f"  - Base Path: {self.base_path}")
        self.logger.info(f"  - 최대 동시 연결: {self.max_concurrent}")
    
    async def _create_remote_directory(self, sftp: asyncssh.SFTPClient, remote_path: str):
        """원격 디렉토리 생성 (재귀적)"""
        path_parts = Path(remote_path).parts
        current_path = ""
        
        for part in path_parts:
            if not part or part == '/':
                continue
                
            current_path = f"{current_path}/{part}" if current_path else f"/{part}"
            
            try:
                await sftp.stat(current_path)
            except asyncssh.SFTPNoSuchFile:
                try:
                    await sftp.mkdir(current_path)
                    self.logger.debug(f"📁 디렉토리 생성: {current_path}")
                except asyncssh.SFTPFailure:
                    # 이미 존재하는 경우 무시
                    pass
    
    async def _upload_single_file(self, conn: asyncssh.SSHClientConnection, 
                                  local_path: str, remote_path: str,
                                  progress_callback=None, task_id: int = 0) -> Dict:
        """단일 파일 업로드 (비동기)"""
        start_time = time.time()
        result = {
            "local_path": local_path,
            "remote_path": remote_path,
            "success": False,
            "error": None,
            "size": 0,
            "duration": 0,
            "task_id": task_id
        }
        
        try:
            # 파일 크기 확인
            file_size = os.path.getsize(local_path)
            result["size"] = file_size
            
            async with conn.start_sftp_client() as sftp:
                # 전체 경로 구성
                if remote_path.startswith('video_analysis/'):
                    full_remote_path = f"{self.base_path}/{remote_path}"
                else:
                    full_remote_path = remote_path
                
                # 경로 정규화
                full_remote_path = full_remote_path.replace('\\', '/')
                full_remote_path = full_remote_path.replace('//', '/')
                
                # 디렉토리 생성
                remote_dir = os.path.dirname(full_remote_path)
                await self._create_remote_directory(sftp, remote_dir)
                
                # 파일이 이미 존재하는지 확인
                try:
                    remote_stat = await sftp.stat(full_remote_path)
                    if remote_stat.size == file_size:
                        self.logger.info(f"⏭️  파일이 이미 존재함 (동일한 크기): {full_remote_path}")
                        result["success"] = True
                        result["duration"] = time.time() - start_time
                        return result
                except asyncssh.SFTPNoSuchFile:
                    pass
                
                # 진행률 콜백을 위한 래퍼 함수
                bytes_transferred = 0
                
                def progress_handler(src_path, dst_path, bytes_so_far, total_bytes):
                    nonlocal bytes_transferred
                    bytes_transferred = bytes_so_far
                    if progress_callback:
                        progress_callback(local_path, bytes_so_far, total_bytes)
                
                # 파일 업로드 (진행률 추적 포함)
                file_name = os.path.basename(local_path)
                self.logger.info(f"🔄 [Task-{task_id}] 동시 업로드 시작: {file_name} ({self._format_size(file_size)})")
                self.logger.debug(f"   └─ 전체 경로: {local_path} -> {full_remote_path}")
                
                # 진행률 콜백이 있을 때만 progress_handler 사용
                if progress_callback:
                    await sftp.put(local_path, full_remote_path, 
                                 progress_handler=progress_handler,
                                 block_size=self.chunk_size)
                else:
                    await sftp.put(local_path, full_remote_path, 
                                 block_size=self.chunk_size)
                
                # 업로드 검증
                remote_stat = await sftp.stat(full_remote_path)
                if remote_stat.size != file_size:
                    raise Exception(f"파일 크기 불일치: 로컬 {file_size} != 원격 {remote_stat.size}")
                
                result["success"] = True
                elapsed = time.time() - start_time
                speed = file_size / elapsed if elapsed > 0 else 0
                self.logger.info(f"✅ [Task-{task_id}] 업로드 완료: {file_name} ({elapsed:.2f}초, {self._format_size(speed)}/s)")
                
        except Exception as e:
            result["error"] = str(e)
            self.logger.error(f"❌ 업로드 실패 ({local_path}): {e}")
        
        result["duration"] = time.time() - start_time
        return result
    
    async def upload_files_batch(self, file_pairs: List[Tuple[str, str]], 
                                progress_callback=None) -> List[Dict]:
        """
        여러 파일을 동시에 업로드
        
        Args:
            file_pairs: [(local_path, remote_path), ...] 형태의 리스트
            progress_callback: 진행률 콜백 함수 (optional)
            
        Returns:
            각 파일의 업로드 결과 리스트
        """
        self.logger.info(f"🚀 배치 업로드 시작: {len(file_pairs)}개 파일")
        self.logger.info(f"⚙️  동시 업로드 설정: 최대 {self.max_concurrent}개 연결")
        start_time = time.time()
        
        # 동시 연결 수 제한을 위한 세마포어
        semaphore = asyncio.Semaphore(self.max_concurrent)
        active_tasks = set()  # 현재 활성 태스크 추적
        
        async def upload_with_limit(local_path: str, remote_path: str, task_id: int):
            async with semaphore:
                active_tasks.add(task_id)
                active_count = len(active_tasks)
                self.logger.info(f"🎯 [동시성] 활성 업로드: {active_count}개 (Task-{task_id} 시작)")
                
                try:
                    # 각 업로드마다 새로운 연결 생성 (동시성 문제 방지)
                    async with asyncssh.connect(
                        self.host, 
                        port=self.port,
                        username=self.username, 
                        password=self.password,
                        known_hosts=None  # 호스트 키 검증 비활성화 (필요시 조정)
                    ) as conn:
                        result = await self._upload_single_file(
                            conn, local_path, remote_path, progress_callback, task_id
                        )
                        return result
                finally:
                    active_tasks.discard(task_id)
                    remaining = len(active_tasks)
                    self.logger.info(f"🎯 [동시성] Task-{task_id} 종료, 남은 활성 업로드: {remaining}개")
        
        # 모든 업로드 작업을 동시에 실행
        tasks = [
            upload_with_limit(local_path, remote_path, task_id) 
            for task_id, (local_path, remote_path) in enumerate(file_pairs, 1)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 예외 처리
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                local_path, remote_path = file_pairs[i]
                final_results.append({
                    "local_path": local_path,
                    "remote_path": remote_path,
                    "success": False,
                    "error": str(result),
                    "size": 0,
                    "duration": 0
                })
            else:
                final_results.append(result)
        
        # 요약 출력
        total_time = time.time() - start_time
        successful = sum(1 for r in final_results if r["success"])
        total_size = sum(r["size"] for r in final_results if r["success"])
        
        self.logger.info(f"📊 배치 업로드 완료:")
        self.logger.info(f"  - 성공: {successful}/{len(file_pairs)}")
        self.logger.info(f"  - 총 크기: {self._format_size(total_size)}")
        self.logger.info(f"  - 소요 시간: {total_time:.2f}초")
        self.logger.info(f"  - 평균 속도: {self._format_size(total_size / total_time)}/s")
        
        return final_results
    
    async def upload_file(self, local_path: str, remote_path: str) -> bool:
        """
        단일 파일 업로드 (기존 인터페이스와 호환)
        
        Args:
            local_path: 로컬 파일 경로
            remote_path: 원격 저장 경로
            
        Returns:
            업로드 성공 여부
        """
        results = await self.upload_files_batch([(local_path, remote_path)])
        return results[0]["success"] if results else False
    
    async def test_connection(self) -> bool:
        """SFTP 연결 테스트"""
        try:
            self.logger.info(f"🔌 비동기 SFTP 연결 테스트: {self.host}:{self.port}")
            
            async with asyncssh.connect(
                self.host, 
                port=self.port,
                username=self.username, 
                password=self.password,
                known_hosts=None
            ) as conn:
                async with conn.start_sftp_client() as sftp:
                    # base_path 존재 확인
                    try:
                        await sftp.stat(self.base_path)
                        self.logger.info(f"✅ 기본 경로 확인: {self.base_path}")
                    except asyncssh.SFTPNoSuchFile:
                        self.logger.warning(f"⚠️ 기본 경로가 존재하지 않습니다: {self.base_path}")
                        # 기본 경로 생성 시도
                        await self._create_remote_directory(sftp, self.base_path)
            
            self.logger.info("✅ 비동기 SFTP 연결 테스트 성공")
            return True
            
        except asyncssh.Error as e:
            self.logger.error(f"❌ SSH 연결 오류: {e}")
            return False
        except Exception as e:
            self.logger.error(f"❌ 연결 테스트 실패: {e}")
            return False
    
    def _format_size(self, size_bytes: int) -> str:
        """바이트를 읽기 쉬운 형식으로 변환"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"


# 동기 래퍼 함수들 (기존 코드와의 호환성을 위해)
def upload_file_sync(storage: AsyncSFTPStorage, local_path: str, remote_path: str) -> bool:
    """동기 방식으로 단일 파일 업로드"""
    return asyncio.run(storage.upload_file(local_path, remote_path))


def upload_files_batch_sync(storage: AsyncSFTPStorage, file_pairs: List[Tuple[str, str]], 
                           progress_callback=None) -> List[Dict]:
    """동기 방식으로 배치 업로드"""
    return asyncio.run(storage.upload_files_batch(file_pairs, progress_callback))


def test_connection_sync(storage: AsyncSFTPStorage) -> bool:
    """동기 방식으로 연결 테스트"""
    return asyncio.run(storage.test_connection())
