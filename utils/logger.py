# utils/logger.py
import logging
import os
from datetime import datetime
import streamlit as st
from typing import Optional
import threading

class StreamlitLogHandler(logging.Handler):
    """Streamlit 세션에 로그를 저장하는 핸들러"""
    
    def __init__(self):
        super().__init__()
        self._lock = threading.Lock()
    
    def emit(self, record):
        """로그 레코드를 Streamlit 세션 상태에 추가"""
        try:
            # Streamlit 세션이 있는지 확인
            if hasattr(st, 'session_state'):
                with self._lock:
                    # 로그 버퍼가 없으면 생성
                    if 'log_buffer' not in st.session_state:
                        st.session_state.log_buffer = []
                    
                    # 로그 메시지 포맷팅
                    msg = self.format(record)
                    
                    # INFO 레벨만 저장하고, 메시지 부분만 추출
                    if record.levelname == 'INFO':
                        # 메시지에서 INFO 이후 부분만 추출
                        parts = msg.split(' - ')
                        if len(parts) >= 4:
                            clean_msg = parts[3]  # 실제 메시지 부분
                            
                            # 로그 버퍼에 추가 (최대 50개 유지)
                            st.session_state.log_buffer.append({
                                'time': datetime.now(),
                                'message': clean_msg,
                                'level': record.levelname
                            })
                            
                            # 버퍼 크기 제한
                            if len(st.session_state.log_buffer) > 50:
                                st.session_state.log_buffer.pop(0)
        except Exception:
            # 로깅 중 오류는 무시
            pass


def get_logger(name: str) -> logging.Logger:
    """로거 인스턴스 생성"""
    logger = logging.getLogger(name)
    
    # 이미 핸들러가 있으면 반환
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # 부모 로거의 핸들러 상속 방지
    logger.propagate = False
    
    # 로그 디렉토리 생성
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # 파일 핸들러
    log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y%m%d')}.log")
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Streamlit 핸들러 추가
    streamlit_handler = StreamlitLogHandler()
    streamlit_handler.setLevel(logging.INFO)
    
    # 포맷터
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    streamlit_handler.setFormatter(formatter)
    
    # 핸들러 추가
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.addHandler(streamlit_handler)
    
    return logger


def get_recent_logs(count: int = 10) -> list:
    """최근 로그 메시지 가져오기"""
    if hasattr(st, 'session_state') and 'log_buffer' in st.session_state:
        return st.session_state.log_buffer[-count:]
    return []


def clear_log_buffer():
    """로그 버퍼 초기화"""
    if hasattr(st, 'session_state') and 'log_buffer' in st.session_state:
        st.session_state.log_buffer = []