import yt_dlp

url = "https://www.youtube.com/watch?v=K_OcgLJNvVA"
ydl_opts = {'quiet': True}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(url, download=False)
    
    print(f"업로더: {info.get('uploader')}")
    print(f"업로드 날짜: {info.get('upload_date')}")
    print(f"태그: {info.get('tags')}")
    print(f"설명: {info.get('description')[:100]}...")
    print(f"언어: {info.get('language')}")
    print(f"댓글수: {info.get('comment_count')}")