#!/usr/bin/env python3
"""
포트폴리오 파일명 정리 스크립트 (자동 실행)
greatminds 포트폴리오 파일들을 체계적인 명명 규칙에 따라 정리합니다.
"""

import os
import shutil
import csv
from pathlib import Path
import re
import datetime

def generate_new_filename(old_filename):
    """기존 파일명을 새로운 명명 규칙에 따라 변환"""
    
    # 기본값
    year = '2024'
    client = 'MISC'
    project = 'UNKNOWN'
    version = 'FINAL'
    language = ''
    location = ''
    
    # 확장자 추출 (mov를 mp4로 통일)
    ext = old_filename.split('.')[-1].lower()
    if ext == 'mov':
        ext = 'mp4'
    
    # 연도 추출
    if '20241219' in old_filename:
        year = '2024'
    elif '20210527' in old_filename:
        year = '2021'
    elif '20201029' in old_filename:
        year = '2020'
    elif '2020' in old_filename:
        year = '2020'
    elif '2021' in old_filename:
        year = '2021'
    elif '2022' in old_filename:
        year = '2022'
    elif '2023' in old_filename:
        year = '2023'
    elif any(x in old_filename for x in ['0526', '0308', '0929', '1021', '1214']):
        year = '2024'
    
    # 클라이언트 및 프로젝트 식별
    if '나눔온택트' in old_filename:
        client = 'SHARING'
        if '트레일러' in old_filename:
            project = 'TRAILER'
        elif '정유인' in old_filename:
            project = 'JEONGYUIN'
        elif '주경진' in old_filename:
            project = 'JUGYEONGJIN'
        elif '보이비' in old_filename:
            project = 'BOYB'
        elif '플로리안' in old_filename:
            project = 'FLORIAN'
        elif '종합편' in old_filename:
            project = 'TOTAL'
        elif '장기기증' in old_filename:
            project = 'ORGANDONATION'
        else:
            project = 'SHARING'
    
    elif any(x in old_filename for x in ['Wine Club', 'In-Flight', 'In-flight']):
        client = 'KOREA'
        project = 'WINECLUB'
        if '[AU]' in old_filename:
            location = 'AU'
        elif '[US]' in old_filename:
            location = 'US'
        elif '[EU]' in old_filename:
            location = 'EU'
    
    elif '현대모터스튜디오' in old_filename or ('현대' in old_filename and '부산' in old_filename):
        client = 'HYUND'
        project = 'BUSAN'
        clip_match = re.search(r'Clip\s*(\d+)', old_filename)
        if clip_match:
            location = clip_match.group(1).zfill(2)
    
    elif '현대건설기계' in old_filename:
        client = 'HYUND'
        if '친환경' in old_filename:
            project = 'ECO'
        else:
            project = 'BRANDFILM'
    
    elif any(x in old_filename for x in ['항공기', '안전성']):
        client = 'KOREA'
        project = 'AIRCRAFT'
    
    elif '공황발작' in old_filename:
        client = 'KOREA'
        project = 'PANIC'
    
    elif '호흡요법' in old_filename:
        client = 'KOREA'
        project = 'BREATHING'
    
    elif 'Livery' in old_filename:
        client = 'KOREA'
        project = 'LIVERY'
    
    elif '랜선아트' in old_filename:
        client = 'POSCO'
        if '앨리스' in old_filename:
            project = 'ALICE'
        elif '오월의숲' in old_filename:
            project = 'MAYFOREST'
        elif '김지아나' in old_filename:
            project = 'KIMJIANA'
        else:
            project = 'ONLINEART'
    
    elif any(x in old_filename for x in ['포스코', '나나펠릭스']):
        client = 'POSCO'
        project = 'NANAPLIX'
    
    elif '서부시장' in old_filename:
        client = 'MARKET'
        if '하이라이트' in old_filename:
            project = 'HIGHLIGHT'
        elif '통합편' in old_filename:
            project = 'TOTAL'
        elif '아카이브' in old_filename:
            project = 'ARCHIVE'
        else:
            project = 'MARKET'
    
    elif 'Bangladesh' in old_filename:
        client = 'DOC'
        project = 'FACTORIES'
        location = 'BD'
    
    elif 'Vietnam' in old_filename:
        client = 'DOC'
        project = 'FACTORIES'
        location = 'VN'
    
    elif any(x in old_filename for x in ['A Patch of Ground', 'aPatchOfGround']):
        client = 'DOC'
        project = 'PATCHOFGROUND'
    
    elif 'FLEXFIT' in old_filename:
        client = 'FLEXFIT'
        if 'NU' in old_filename:
            project = 'NU'
        elif 'Lyocell' in old_filename:
            project = 'LYOCELL'
        else:
            project = 'FLEXFIT'
    
    elif 'GBC' in old_filename:
        client = 'GBC'
        project = 'HIGHLIGHT'
    
    elif 'WGC' in old_filename:
        client = 'WGC'
        project = 'OPENING'
    
    elif 'MOP' in old_filename:
        client = 'MOP'
        if '공정' in old_filename:
            project = 'PROCESS'
        else:
            project = 'BRANDFILM'
    
    elif '기아' in old_filename:
        client = 'KIA'
        if '서문욱' in old_filename:
            project = 'SEOMUNUK'
        elif '홍세진' in old_filename:
            project = 'HONGSEJIN'
        elif '이준성' in old_filename:
            project = 'LEEJUNSUNG'
        else:
            project = 'KIA'
    
    elif any(x in old_filename for x in ['신한', 'Shinhan']):
        client = 'SHINHAN'
        project = 'HR'
    
    elif '네모즈랩' in old_filename:
        client = 'NEMOZ'
        project = 'NEMOZLAB'
    
    elif '뉴튠' in old_filename:
        client = 'NEWTUNE'
        project = 'NEWTUNE'
    
    elif '루나르트' in old_filename:
        client = 'LUNART'
        project = 'LUNART'
    
    elif '3PM' in old_filename:
        client = '3PM'
        project = '3PM'
    
    elif '용산역사박물관' in old_filename:
        client = 'YONGSAN'
        project = 'MUSEUM'
    
    elif 'Finflow' in old_filename:
        client = 'FINFLOW'
        project = 'SPOT'
    
    elif '초록여행' in old_filename:
        client = 'GREENTRIP'
        if '비전' in old_filename:
            project = 'VISION'
        elif '스케치' in old_filename:
            project = 'SKETCH'
        else:
            project = 'GREENTRIP'
    
    elif '전설의메이커' in old_filename:
        client = 'LEGEND'
        if '종합편' in old_filename:
            project = 'TOTAL'
        elif any(x in old_filename for x in ['팹랩', '이노베이션']):
            project = 'FABLAB'
        elif '마을공방' in old_filename:
            project = 'WORKSHOP'
        else:
            project = 'LEGEND'
    
    elif '선너무는혁신가' in old_filename:
        client = 'INNOVATOR'
        project = 'SISO'
    
    elif 'YP' in old_filename and '50th' in old_filename:
        client = 'YP'
        project = 'YP50TH'
    
    elif 'ULSAN' in old_filename:
        client = 'MISC'
        project = 'ULSAN'
    
    elif 'bkl태평양' in old_filename:
        client = 'BKL'
        project = 'PACIFIC'
    
    # 개별 인물 이름들
    elif '송하나' in old_filename:
        client = 'MISC'
        project = 'SONGHANA'
    elif '신희조' in old_filename:
        client = 'MISC'
        project = 'SHINHIJO'
    elif '이루다' in old_filename:
        client = 'MISC'
        project = 'IRUDA'
    elif '이호윤' in old_filename:
        client = 'MISC'
        project = 'IHOYUN'
    elif '정은석' in old_filename:
        client = 'MISC'
        project = 'JEONGEUNSEOK'
    elif '김용민' in old_filename:
        client = 'MISC'
        project = 'KIMYONGMIN'
    elif '노진경' in old_filename:
        client = 'MISC'
        project = 'NOJINGYEONG'
    elif '김예은' in old_filename:
        client = 'MISC'
        project = 'KIMYEEUN'
    elif '정민수' in old_filename:
        client = 'MISC'
        project = 'JEONGMINSU'
    
    # 기타 프로젝트들
    elif '기대영상' in old_filename:
        client = 'MISC'
        project = 'EXPECTATION'
    elif '아카이브' in old_filename:
        client = 'MISC'
        project = 'ARCHIVE'
    elif '성과영상' in old_filename:
        client = 'MISC'
        project = 'ACHIEVEMENT'
    elif '패키지여행' in old_filename:
        client = 'MISC'
        project = 'PACKAGETRAVEL'
    
    # 버전 식별
    if any(x in old_filename for x in ['Clean', '클린']):
        version = 'CLEAN'
    elif any(x in old_filename for x in ['Draft', 'draft']):
        version = 'DRAFT'
    elif 'rev' in old_filename.lower():
        rev_match = re.search(r'rev\s*(\d+)', old_filename, re.IGNORECASE)
        version = f'REV{rev_match.group(1).zfill(2)}' if rev_match else 'REV01'
    elif any(x in old_filename for x in ['Final', 'Fin', 'final']):
        version = 'FINAL'
    
    # 언어 식별
    if any(x in old_filename for x in ['_KOR', '_Kor', '한글']):
        language = 'KOR'
    elif '_ENG' in old_filename:
        language = 'ENG'
    elif any(x in old_filename for x in ['nonSub', 'noSub']):
        language = 'NOSUB'
    elif re.search(r'[가-힣]', old_filename):
        language = 'KOR'
    else:
        language = 'ENG'
    
    # 새 파일명 조합
    new_name = f'{year}_{client}_{project}'
    if location:
        new_name += f'-{location}'
    new_name += f'_{version}'
    if language:
        new_name += f'_{language}'
    new_name += f'.{ext}'
    
    return new_name

def check_duplicates(file_mappings):
    """중복 파일명 체크 및 해결"""
    new_names = [mapping['new'] for mapping in file_mappings]
    duplicates = {}
    
    for i, name in enumerate(new_names):
        if new_names.count(name) > 1:
            if name not in duplicates:
                duplicates[name] = []
            duplicates[name].append(i)
    
    # 중복 해결
    for dup_name, indices in duplicates.items():
        for i, index in enumerate(indices):
            base_name, ext = dup_name.rsplit('.', 1)
            file_mappings[index]['new'] = f'{base_name}_{str(i+1).zfill(2)}.{ext}'
    
    return file_mappings, duplicates

def main():
    # 포트폴리오 폴더 경로
    portfolio_path = Path('/Volumes/Works/Website Portfolio')
    
    if not portfolio_path.exists():
        print(f"❌ 폴더를 찾을 수 없습니다: {portfolio_path}")
        return
    
    print("🎬 greatminds 포트폴리오 파일명 정리 자동 실행")
    print("=" * 60)
    print(f"⏰ 시작 시간: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 현재 파일 목록 가져오기
    video_files = []
    for ext in ['*.mp4', '*.mov']:
        video_files.extend(portfolio_path.glob(ext))
    
    print(f"📁 발견된 비디오 파일: {len(video_files)}개")
    
    # 파일명 변환 매핑 생성
    file_mappings = []
    for file_path in video_files:
        old_name = file_path.name
        new_name = generate_new_filename(old_name)
        file_mappings.append({
            'old': old_name,
            'new': new_name,
            'path': file_path
        })
    
    # 중복 체크 및 해결
    file_mappings, duplicates = check_duplicates(file_mappings)
    
    if duplicates:
        print(f"⚠️  중복 파일명 {len(duplicates)}개 발견 및 자동 해결")
        for dup_name, indices in duplicates.items():
            print(f"   🔸 {dup_name}: {len(indices)}개 파일")
    else:
        print("✅ 중복 파일명 없음")
    
    # 백업 폴더 생성
    backup_path = portfolio_path / '_BACKUP_ORIGINAL'
    backup_path.mkdir(exist_ok=True)
    print(f"\n💾 백업 폴더 생성: {backup_path}")
    
    # CSV 로그 파일 생성
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = portfolio_path / f'rename_log_{timestamp}.csv'
    
    # 파일 리네이밍 실행
    print(f"\n🚀 파일 리네이밍 실행 중... (총 {len(file_mappings)}개)")
    print("-" * 60)
    
    success_count = 0
    error_count = 0
    
    with open(log_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Old_Name', 'New_Name', 'Status', 'Error', 'Timestamp'])
        
        for i, mapping in enumerate(file_mappings, 1):
            try:
                old_path = mapping['path']
                new_path = portfolio_path / mapping['new']
                backup_file = backup_path / mapping['old']
                
                # 백업 생성
                shutil.copy2(old_path, backup_file)
                
                # 파일 리네이밍
                old_path.rename(new_path)
                
                writer.writerow([mapping['old'], mapping['new'], 'SUCCESS', '', 
                               datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
                success_count += 1
                
                # 진행상황 표시
                if i % 10 == 0 or i == len(file_mappings):
                    print(f"📦 진행: {i}/{len(file_mappings)} ({i/len(file_mappings)*100:.1f}%)")
                
                # 몇 개 예시 출력
                if i <= 5:
                    print(f"✅ {mapping['old']}")
                    print(f"   → {mapping['new']}")
                
            except Exception as e:
                writer.writerow([mapping['old'], mapping['new'], 'ERROR', str(e),
                               datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
                error_count += 1
                print(f"❌ {mapping['old']}: {e}")
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 작업 완료 결과:")
    print(f"✅ 성공: {success_count}개")
    print(f"❌ 실패: {error_count}개") 
    print(f"💾 백업 위치: {backup_path}")
    print(f"📋 로그 파일: {log_file}")
    print(f"⏰ 완료 시간: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if error_count == 0:
        print("\n🎉 모든 파일이 성공적으로 정리되었습니다!")
        
        # 클라이언트별 정리 결과 요약
        client_count = {}
        for mapping in file_mappings:
            client = mapping['new'].split('_')[1]
            client_count[client] = client_count.get(client, 0) + 1
        
        print("\n📂 클라이언트별 정리 결과:")
        for client, count in sorted(client_count.items()):
            print(f"   {client}: {count}개")
            
    else:
        print(f"\n⚠️  {error_count}개 파일에서 오류가 발생했습니다. 로그를 확인해주세요.")

if __name__ == "__main__":
    main()
