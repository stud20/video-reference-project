# integrations/storage/sftp_batch_wrapper.py
"""기존 시스템과 비동기 SFTP를 연결하는 래퍼"""
import asyncio
from typing import List, Tuple, Optional, Dict
from .sftp_async import AsyncSFTPStorage
from utils.logger import get_logger


class SFTPBatchUploader:
    """배치 업로드를 위한 편의 클래스"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.async_storage = AsyncSFTPStorage()
        
    def upload_batch(self, file_pairs: List[Tuple[str, str]], 
                    progress_callback=None) -> List[Dict]:
        """
        동기 방식으로 배치 업로드 실행
        
        Args:
            file_pairs: [(local_path, remote_path), ...] 튜플 리스트
            progress_callback: 진행률 콜백 함수
            
        Returns:
            업로드 결과 리스트
        """
        # 이벤트 루프 처리
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 이미 실행 중인 루프가 있는 경우 (예: Jupyter, Streamlit)
                import nest_asyncio
                nest_asyncio.apply()
                return loop.run_until_complete(
                    self.async_storage.upload_files_batch(file_pairs, progress_callback)
                )
        except RuntimeError:
            # 새 이벤트 루프 생성
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        try:
            return loop.run_until_complete(
                self.async_storage.upload_files_batch(file_pairs, progress_callback)
            )
        finally:
            # 생성한 루프는 정리
            if not loop.is_running():
                loop.close()
    
    def upload_single(self, local_path: str, remote_path: str) -> bool:
        """단일 파일 업로드 (기존 인터페이스와 호환)"""
        results = self.upload_batch([(local_path, remote_path)])
        return results[0]["success"] if results else False
    
    def test_connection(self) -> bool:
        """연결 테스트"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import nest_asyncio
                nest_asyncio.apply()
                return loop.run_until_complete(self.async_storage.test_connection())
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        try:
            return loop.run_until_complete(self.async_storage.test_connection())
        finally:
            if not loop.is_running():
                loop.close()


# 사용 예제
if __name__ == "__main__":
    # 배치 업로더 생성
    uploader = SFTPBatchUploader()
    
    # 연결 테스트
    if uploader.test_connection():
        print("✅ 연결 성공!")
        
        # 파일 목록 준비
        files_to_upload = [
            ("local/file1.mp4", "remote/videos/file1.mp4"),
            ("local/file2.mp4", "remote/videos/file2.mp4"),
            ("local/file3.mp4", "remote/videos/file3.mp4"),
        ]
        
        # 배치 업로드 실행
        results = uploader.upload_batch(files_to_upload)
        
        # 결과 확인
        for result in results:
            if result["success"]:
                print(f"✅ {result['local_path']} 업로드 성공")
            else:
                print(f"❌ {result['local_path']} 업로드 실패: {result['error']}")
