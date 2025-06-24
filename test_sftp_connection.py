# debug_sftp_connection.py
"""
SFTP 연결 디버깅 테스트 스크립트
포트 63063 사용
"""

import os
import sys
import paramiko
from datetime import datetime

# 프로젝트 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

# 환경변수 로드
from dotenv import load_dotenv
load_dotenv()

# 로깅 설정
import logging
logging.basicConfig(level=logging.DEBUG)
paramiko.util.log_to_file('sftp_debug.log')


def test_basic_ssh_connection():
    """기본 SSH 연결 테스트"""
    print("\n=== 기본 SSH 연결 테스트 ===\n")
    
    host = os.getenv("SYNOLOGY_HOST", "nas.greatminds.kr")
    port = int(os.getenv("SFTP_PORT", "63063"))
    username = os.getenv("SYNOLOGY_USER", "dav")
    password = os.getenv("SYNOLOGY_PASS", "dav123")
    
    print(f"연결 정보:")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  User: {username}")
    print()
    
    # SSH 클라이언트 생성
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # SSH 연결
        print("1. SSH 연결 시도...")
        ssh.connect(
            hostname=host,
            port=port,
            username=username,
            password=password,
            timeout=30,
            look_for_keys=False,
            allow_agent=False
        )
        print("   ✅ SSH 연결 성공!")
        
        # 연결 테스트 - 간단한 명령 실행
        print("\n2. 연결 확인 (whoami 명령)...")
        stdin, stdout, stderr = ssh.exec_command("whoami")
        result = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        
        if result:
            print(f"   ✅ 현재 사용자: {result}")
        if error:
            print(f"   ❌ 오류: {error}")
        
        # 홈 디렉토리 확인
        print("\n3. 홈 디렉토리 확인...")
        stdin, stdout, stderr = ssh.exec_command("pwd")
        home_dir = stdout.read().decode().strip()
        print(f"   홈 디렉토리: {home_dir}")
        
        # /volume1/dav 디렉토리 확인
        print("\n4. /volume1/dav 디렉토리 확인...")
        stdin, stdout, stderr = ssh.exec_command("ls -la /volume1/dav/")
        result = stdout.read().decode()
        error = stderr.read().decode()
        
        if result:
            print("   디렉토리 내용:")
            for line in result.split('\n')[:10]:  # 처음 10줄만
                if line.strip():
                    print(f"   {line}")
        if error:
            print(f"   ❌ 오류: {error}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ SSH 연결 실패: {e}")
        print(f"   오류 타입: {type(e).__name__}")
        return False
    finally:
        ssh.close()


def test_sftp_connection():
    """SFTP 연결 테스트"""
    print("\n\n=== SFTP 연결 테스트 ===\n")
    
    host = os.getenv("SYNOLOGY_HOST", "nas.greatminds.kr")
    port = int(os.getenv("SFTP_PORT", "63063"))
    username = os.getenv("SYNOLOGY_USER", "dav")
    password = os.getenv("SYNOLOGY_PASS", "dav123")
    
    transport = None
    sftp = None
    
    try:
        # Transport 생성
        print("1. Transport 객체 생성...")
        transport = paramiko.Transport((host, port))
        transport.set_log_channel("paramiko.transport")
        print("   ✅ Transport 생성 성공")
        
        # 인증
        print("\n2. 사용자 인증...")
        transport.connect(username=username, password=password)
        print("   ✅ 인증 성공")
        
        # SFTP 클라이언트 생성
        print("\n3. SFTP 서브시스템 시작...")
        sftp = paramiko.SFTPClient.from_transport(transport)
        print("   ✅ SFTP 클라이언트 생성 성공")
        
        # 현재 디렉토리 확인
        print("\n4. 현재 작업 디렉토리...")
        cwd = sftp.getcwd() or sftp.normalize('.')
        print(f"   현재 디렉토리: {cwd}")
        
        # 루트 디렉토리 내용 확인
        print("\n5. 루트 디렉토리 내용...")
        try:
            items = sftp.listdir('/')
            print(f"   루트 디렉토리 항목 ({len(items)}개):")
            for item in items[:10]:  # 처음 10개만
                print(f"   - {item}")
        except Exception as e:
            print(f"   ❌ 루트 디렉토리 접근 실패: {e}")
        
        # /volume1/dav 경로 확인
        print("\n6. /volume1/dav 경로 확인...")
        try:
            sftp.stat('/volume1/dav')
            print("   ✅ /volume1/dav 디렉토리 존재")
            
            # videoRef 디렉토리 확인
            try:
                sftp.stat('/volume1/dav/videoRef')
                print("   ✅ /volume1/dav/videoRef 디렉토리 존재")
            except:
                print("   ⚠️ /volume1/dav/videoRef 디렉토리 없음 - 생성 필요")
                # 디렉토리 생성 시도
                try:
                    sftp.mkdir('/volume1/dav/videoRef')
                    print("   ✅ videoRef 디렉토리 생성 성공")
                except Exception as e:
                    print(f"   ❌ videoRef 디렉토리 생성 실패: {e}")
        except Exception as e:
            print(f"   ❌ /volume1/dav 경로 접근 실패: {e}")
            
            # 대체 경로 시도
            print("\n   대체 경로 확인 중...")
            for alt_path in ['/dav', '/home/dav', f'/home/{username}']:
                try:
                    items = sftp.listdir(alt_path)
                    print(f"   ✅ {alt_path} 접근 가능 ({len(items)}개 항목)")
                    break
                except:
                    print(f"   ❌ {alt_path} 접근 불가")
        
        # 테스트 파일 업로드
        print("\n7. 테스트 파일 업로드...")
        test_content = f"SFTP 테스트 - {datetime.now()}"
        test_filename = f"sftp_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        # 로컬 테스트 파일 생성
        with open(test_filename, 'w') as f:
            f.write(test_content)
        
        # 업로드 시도 (여러 경로)
        upload_paths = [
            f'/volume1/dav/videoRef/{test_filename}',
            f'/dav/videoRef/{test_filename}',
            f'/home/{username}/{test_filename}',
            test_filename  # 현재 디렉토리
        ]
        
        for remote_path in upload_paths:
            try:
                print(f"   업로드 시도: {remote_path}")
                sftp.put(test_filename, remote_path)
                print(f"   ✅ 업로드 성공: {remote_path}")
                
                # 업로드 확인
                stat = sftp.stat(remote_path)
                print(f"   파일 크기: {stat.st_size} bytes")
                
                # 파일 삭제 (정리)
                sftp.remove(remote_path)
                print(f"   ✅ 테스트 파일 삭제 완료")
                break
                
            except Exception as e:
                print(f"   ❌ 업로드 실패: {e}")
        
        # 로컬 파일 정리
        os.remove(test_filename)
        
        return True
        
    except Exception as e:
        print(f"\n❌ SFTP 연결 실패: {e}")
        print(f"오류 타입: {type(e).__name__}")
        
        import traceback
        print("\n상세 오류:")
        print(traceback.format_exc())
        
        return False
        
    finally:
        if sftp:
            sftp.close()
        if transport:
            transport.close()


def check_env_settings():
    """환경변수 설정 확인"""
    print("=== 환경변수 확인 ===\n")
    
    settings = {
        "SYNOLOGY_HOST": os.getenv("SYNOLOGY_HOST"),
        "SFTP_PORT": os.getenv("SFTP_PORT"),
        "SYNOLOGY_USER": os.getenv("SYNOLOGY_USER"),
        "SYNOLOGY_PASS": os.getenv("SYNOLOGY_PASS")
    }
    
    for key, value in settings.items():
        if key == "SYNOLOGY_PASS" and value:
            print(f"{key}: {'*' * len(value)}")
        else:
            print(f"{key}: {value or 'Not set'}")
    
    print("\n.env 파일 위치:", os.path.join(current_dir, '.env'))
    print()


if __name__ == "__main__":
    print("=" * 70)
    print("SFTP 연결 디버깅 테스트")
    print("=" * 70)
    
    # 환경변수 확인
    check_env_settings()
    
    # 기본 SSH 연결 테스트
    ssh_success = test_basic_ssh_connection()
    
    # SFTP 연결 테스트
    if ssh_success:
        test_sftp_connection()
    else:
        print("\nSSH 연결 실패로 SFTP 테스트를 건너뜁니다.")
        print("\n가능한 원인:")
        print("1. 포트 63063이 올바른 SFTP/SSH 포트인지 확인")
        print("2. 공유기 포트포워딩 설정 확인")
        print("3. Synology 방화벽 설정 확인")
        print("4. SFTP 서비스 활성화 상태 확인")
    
    print("\n" + "=" * 70)
    print("디버그 로그는 'sftp_debug.log' 파일을 확인하세요.")
    print("=" * 70)