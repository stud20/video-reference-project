#!/usr/bin/env python3
"""
포트폴리오 파일명 정리 스크립트 (수정된 클라이언트 코드)
- 대한항공: KA
- 현대자동차그룹: HMG 
- 현대건설기계: HCE
- 플렉스핏/유풍: YP
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
    if '20241219' in old_filename or '2024' in old_filename:
        year = '2024'
    elif '20210527' in old_filename or '2021' in old_filename:
        year = '2021'
    elif '20201029' in old_filename or '2020' in old_filename:
        year = '2020'
    elif '2022' in old_filename:
        year = '2022'
    elif '2023' in old_filename:
        year = '2023'
    elif '2025' in old_filename:
        year = '2025'
    elif any(x in old_filename for x in ['0526', '0308', '0929', '1021', '1214']):
        year = '2024'
    
    # === 클라이언트 및 프로젝트 식별 ===
    
    # 대한항공 (KA)
    if any(x in old_filename for x in ['대한항공', 'KoreanAir', 'Korean Air', 'Wine Club', 'In-Flight', 'In-flight', 'Livery', '항공기', '기내', '공황발작', '호흡요법']):
        client = 'KA'
        if any(x in old_filename for x in ['Wine Club', 'In-Flight', 'In-flight']):
            project = 'WINECLUB'
            if '[AU]' in old_filename:
                location = 'AU'
            elif '[US]' in old_filename:
                location = 'US'
            elif '[EU]' in old_filename:
                location = 'EU'
        elif 'Livery' in old_filename:
            project = 'LIVERY'
        elif any(x in old_filename for x in ['항공기', '안전성']):
            project = 'AIRCRAFT'
        elif '공황발작' in old_filename:
            project = 'PANIC'
        elif '호흡요법' in old_filename:
            project = 'BREATHING'
        elif 'insider stories' in old_filename:
            project = 'INSIDER'
            if 'CI' in old_filename:
                location = 'CI'
            elif 'CX' in old_filename:
                location = 'CX'
            elif 'ML' in old_filename:
                location = 'ML'
        else:
            project = 'KA'
    
    # 현대자동차그룹 (HMG)
    elif any(x in old_filename for x in ['현대자동차그룹', 'HMGLIFE', '현대오토에버']):
        client = 'HMG'
        if 'HMGLIFE' in old_filename:
            project = 'HMGLIFE'
            # 개별 인물 번호 추출
            person_match = re.search(r'HMGLIFE(\d+)', old_filename)
            if person_match:
                location = person_match.group(1)
        elif '현대오토에버' in old_filename:
            project = 'AUTOEVER'
            # 개별 직무소개 번호 추출
            if '이루다' in old_filename or '01' in old_filename:
                location = '01'
            elif '이호윤' in old_filename or '09' in old_filename:
                location = '09'
            elif '정은석' in old_filename or '05' in old_filename:
                location = '05'
            elif '김용민' in old_filename or '07' in old_filename:
                location = '07'
        elif '부산모터스튜디오' in old_filename or ('현대' in old_filename and '부산' in old_filename):
            project = 'BUSAN'
            clip_match = re.search(r'Clip\s*(\d+)', old_filename)
            if clip_match:
                location = clip_match.group(1).zfill(2)
        elif '서부시장' in old_filename:
            project = 'MARKET'
            if '하이라이트' in old_filename:
                project = 'MARKET-HL'
            elif '통합편' in old_filename:
                project = 'MARKET-TOTAL'
            elif '아카이브' in old_filename:
                project = 'MARKET-ARCHIVE'
            elif '기대영상' in old_filename:
                project = 'MARKET-EXPECT'
        else:
            project = 'HMG'
    
    # 현대건설기계 (HCE)
    elif any(x in old_filename for x in ['현대건설기계', '울산', 'ULSAN']):
        client = 'HCE'
        if '울산' in old_filename or 'ULSAN' in old_filename:
            project = 'ULSAN'
        elif '친환경' in old_filename:
            project = 'ECO'
        else:
            project = 'BRANDFILM'
    
    # 나눔온택트 (보건복지부)
    elif '나눔온택트' in old_filename:
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
    
    # 포스코 (POSCO)
    elif any(x in old_filename for x in ['포스코', 'POSCO', '랜선아트', '나나펠릭스']):
        client = 'POSCO'
        if '랜선아트' in old_filename:
            if '앨리스' in old_filename:
                project = 'ALICE'
            elif '오월의숲' in old_filename:
                project = 'MAYFOREST'
            elif '김지아나' in old_filename:
                project = 'KIMJIANA'
            else:
                project = 'ONLINEART'
        elif '나나펠릭스' in old_filename:
            project = 'NANAPLIX'
        else:
            project = 'POSCO'
    
    # 유풍/플렉스핏 (YP)
    elif any(x in old_filename for x in ['유풍', 'FLEXFIT', 'YP']):
        client = 'YP'
        if 'FLEXFIT' in old_filename:
            if 'NU' in old_filename:
                project = 'NU'
            elif 'Lyocell' in old_filename:
                project = 'LYOCELL'
            else:
                project = 'FLEXFIT'
        elif '50th' in old_filename:
            project = 'YP50TH'
        elif any(x in old_filename for x in ['Bangladesh', 'Vietnam', 'Factory', 'Factories']):
            project = 'FACTORIES'
            if 'Bangladesh' in old_filename:
                location = 'BD'
            elif 'Vietnam' in old_filename:
                location = 'VN'
        else:
            project = 'YP'
    
    # 기아
    elif '기아' in old_filename:
        client = 'KIA'
        if '초록여행' in old_filename:
            project = 'GREENTRIP'
            if '비전' in old_filename:
                project = 'GREENTRIP-VISION'
            elif '스케치' in old_filename:
                project = 'GREENTRIP-SKETCH'
            elif '성과영상' in old_filename:
                project = 'GREENTRIP-ACHIEVE'
            elif '패키지여행' in old_filename:
                project = 'GREENTRIP-PACKAGE'
        else:
            project = 'KIA'
    
    # 다큐멘터리
    elif any(x in old_filename for x in ['조호영', 'A Patch of Ground', 'aPatchOfGround', 'Copycat', 'MOVING WALK', '입체경']):
        client = 'DOC'
        if any(x in old_filename for x in ['A Patch of Ground', 'aPatchOfGround']):
            project = 'PATCHOFGROUND'
        elif 'Copycat' in old_filename:
            project = 'COPYCAT'
        elif 'MOVING WALK' in old_filename:
            project = 'MOVINGWALK'
        elif '입체경' in old_filename:
            project = 'STEREOSCOPE'
        else:
            project = 'DOC'
    
    # 기타 클라이언트들
    elif 'GBC' in old_filename:
        client = 'GBC'
        project = 'HIGHLIGHT'
    elif 'WGC' in old_filename:
        client = 'WGC'
        project = 'OPENING'
        if 'Evacuation' in old_filename:
            project = 'EVACUATION'
        elif 'Highlights' in old_filename:
            project = 'HIGHLIGHTS'
        elif 'Sketch' in old_filename:
            project = 'SKETCH'
    elif 'MOP' in old_filename:
        client = 'MOP'
        if '공정' in old_filename:
            project = 'PROCESS'
        else:
            project = 'BRANDFILM'
    elif '신한' in old_filename or 'Shinhan' in old_filename:
        client = 'SHINHAN'
        project = 'HR'
    elif '뮤콘' in old_filename:
        client = 'MUCON'
        if '네모즈랩' in old_filename:
            project = 'NEMOZLAB'
        elif '뉴튠' in old_filename:
            project = 'NEWTUNE'
        elif '루나르트' in old_filename:
            project = 'LUNART'
        elif '3PM' in old_filename:
            project = '3PM'
        else:
            project = 'MUCON'
    elif 'Finflow' in old_filename or '핀플로우' in old_filename:
        client = 'FINFLOW'
        project = 'SPOT'
    elif '용산역사박물관' in old_filename:
        client = 'YONGSAN'
        project = 'MUSEUM'
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
    elif 'bkl태평양' in old_filename or '법무법인태평양' in old_filename:
        client = 'BKL'
        project = 'PACIFIC'
    elif '에이락' in old_filename:
        client = 'ALAC'
        if 'Wallet' in old_filename:
            project = 'WALLET'
        elif 'NFT' in old_filename:
            project = 'NFT'
        elif 'mainnet' in old_filename:
            project = 'MAINNET'
        elif 'VR' in old_filename:
            project = 'VR'
        elif 'Tour' in old_filename:
            project = 'TOUR'
        elif 'BlockChain' in old_filename:
            project = 'BLOCKCHAIN'
        elif 'Main Page' in old_filename:
            project = 'MAINPAGE'
        else:
            project = 'WEBSITE'
    
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
    if any(x in old_filename for x in ['_KOR', '_Kor', '한글', '_Kor.mp4']):
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
    
    print("🎬 greatminds 포트폴리오 파일명 정리 (수정된 클라이언트 코드)")
    print("=" * 70)
    print("📝 변경사항:")
    print("   • 대한항공: KOREA → KA")
    print("   • 현대자동차그룹: HYUND → HMG")
    print("   • 현대건설기계: HYUND → HCE")
    print("   • 플렉스핏/유풍: FLEXFIT → YP")
    print(f"⏰ 시작 시간: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 현재 파일 목록 가져오기
    video_files = []
    for ext in ['*.mp4', '*.mov']:
        video_files.extend(portfolio_path.glob(ext))
    
    # .DS_Store와 로그 파일 제외
    video_files = [f for f in video_files if f.name not in ['.DS_Store', 'rename_log.csv'] and not f.name.startswith('rename_log_')]
    
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
    
    # 클라이언트별 미리보기
    client_preview = {}
    for mapping in file_mappings:
        client = mapping['new'].split('_')[1]
        if client not in client_preview:
            client_preview[client] = []
        client_preview[client].append(mapping)
    
    print("\n📋 클라이언트별 변환 미리보기:")
    print("-" * 70)
    for client, items in sorted(client_preview.items()):
        print(f"\n📂 {client} ({len(items)}개 파일)")
        for i, item in enumerate(items[:3]):  # 처음 3개만 표시
            print(f"   {i+1}. {item['old']}")
            print(f"      → {item['new']}")
        if len(items) > 3:
            print(f"      ... 외 {len(items) - 3}개 파일")
    
    # 백업 폴더 생성
    backup_path = portfolio_path / '_BACKUP_CURRENT'
    backup_path.mkdir(exist_ok=True)
    print(f"\n💾 백업 폴더 생성: {backup_path}")
    
    # CSV 로그 파일 생성
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = portfolio_path / f'rename_log_corrected_{timestamp}.csv'
    
    # 파일 리네이밍 실행
    print(f"\n🚀 파일 리네이밍 실행 중... (총 {len(file_mappings)}개)")
    print("-" * 70)
    
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
    print("\n" + "=" * 70)
    print("📊 작업 완료 결과:")
    print(f"✅ 성공: {success_count}개")
    print(f"❌ 실패: {error_count}개") 
    print(f"💾 백업 위치: {backup_path}")
    print(f"📋 로그 파일: {log_file}")
    print(f"⏰ 완료 시간: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if error_count == 0:
        print("\n🎉 모든 파일이 성공적으로 정리되었습니다!")
        
        # 클라이언트별 정리 결과 요약
        final_client_count = {}
        for mapping in file_mappings:
            client = mapping['new'].split('_')[1]
            final_client_count[client] = final_client_count.get(client, 0) + 1
        
        print("\n📂 최종 클라이언트별 정리 결과:")
        for client, count in sorted(final_client_count.items()):
            print(f"   {client}: {count}개")
            
    else:
        print(f"\n⚠️  {error_count}개 파일에서 오류가 발생했습니다. 로그를 확인해주세요.")

if __name__ == "__main__":
    main()
