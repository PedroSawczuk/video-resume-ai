import os
import re
import yt_dlp

def formattedYoutubeTitle(title):
    title = re.sub(r'[^\w\s-]', '', title).strip().lower()
    title = re.sub(r'[-\s]+', '-', title)
    return title

def getDownloadFolder():
    return os.path.join(os.getcwd(), "media-download")

def fetchYoutubeAudio(url):
    try:
        folderPath = getDownloadFolder()
        os.makedirs(folderPath, exist_ok=True)

        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)

        title = formattedYoutubeTitle(info.get('title', 'video'))
        outputPath = os.path.join(folderPath, f"{title}.%(ext)s")

        ydlOptions = {
            'format': 'bestaudio/best',
            'outtmpl': outputPath,
            'quiet': False,
            'noplaylist': True,
            'no_warnings': True,
            'progress_with_newline': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'm4a',
                'preferredquality': '192',
            }]
        }

        with yt_dlp.YoutubeDL(ydlOptions) as ydl:
            ydl.download([url])

        print(f"Sucesso! {outputPath.replace('%(ext)s', 'm4a')}")

    except Exception as e:
        print(f"Erro! {e}")

url = input("Adicione a URL do vídeo: ").strip().lower()
fetchYoutubeAudio(url)
