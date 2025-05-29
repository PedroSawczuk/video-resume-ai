import os
import re
import shutil
import yt_dlp
from dotenv import load_dotenv
from google import genai

load_dotenv()
apiKey = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=apiKey)

ytTitleArray = []

def formattedYoutubeTitle(title):
    title = re.sub(r'[^\w\s-]', '', title).strip().lower()
    title = re.sub(r'[-\s]+', '-', title)
    return title

def fetchMediaDownloadPath():
    return os.path.join(os.getcwd(), "media-download")

def fetchTranscriptionsPath():
    return os.path.join(os.getcwd(), "transcriptions")

def fetchResumesPath():
    return os.path.join(os.getcwd(), "resumes")

def fetchYoutubeAudio(url):
    try:
        mediaDownloadPath = fetchMediaDownloadPath()

        if not os.path.exists(mediaDownloadPath):
            os.makedirs(mediaDownloadPath, exist_ok=True)

        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
        
        formattedTitle = formattedYoutubeTitle(info.get('title', 'video'))
        originalTitle = info.get('title', 'video')
        ytTitleArray.append(originalTitle)
        audioFilePath = os.path.join(mediaDownloadPath, f"{formattedTitle}.%(ext)s")
        
        ydlOptions = {
            'format': 'bestaudio/best',
            'outtmpl': audioFilePath,
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
        
        finalPath = audioFilePath.replace('%(ext)s', 'm4a')
        
        print("Download foi concluído com sucesso! Agora iniciando a transcrição do áudio...")

        transcribeAudioToText(finalPath)

    except Exception as e:
        print(f"Erro! {e}")

def transcribeAudioToText(audioPath):
    try:
        uploadedFile = client.files.upload(file=audioPath)
        transcriptionsPath = fetchTranscriptionsPath()

        if not os.path.exists(transcriptionsPath):
            os.makedirs(transcriptionsPath, exist_ok=True)
        
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=["Analise esse audio e transcreva todo o conteúdo, por favor.", uploadedFile]
        ) 

        videoTranscriptionTitle = formattedYoutubeTitle(f"transcription-{os.path.basename(audioPath).replace('.m4a', '')}")
        videoTranscriptionTitle = os.path.join(transcriptionsPath, videoTranscriptionTitle)

        with open(f"{videoTranscriptionTitle}.txt", "w", encoding="utf-8") as f:
            f.write(response.text)
        
        print(f"Transcrição salva em: transcriptions/{os.path.basename(videoTranscriptionTitle)}.txt! Agora iniciando a análise do áudio...")

        analyzeYoutubeAudioWithAI(f"{videoTranscriptionTitle}.txt")

    except Exception as e:
        print(f"Erro durante análise: {e}")

def analyzeYoutubeAudioWithAI(transcriptionPath):
    try:
        resumesPath = fetchResumesPath()

        if not os.path.exists(resumesPath):
            os.makedirs(resumesPath, exist_ok=True)

        with open(transcriptionPath, "r", encoding="utf-8") as file:
            transcriptionText = file.read()

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                f"""
                Você é um analisador profissional de vídeos do YouTube. Quero que você faça o seguinte:

                1. Transcreva o áudio do vídeo de forma clara e organizada.
                2. Identifique os pontos principais abordados, como temas, ideias e tópicos relevantes.
                3. Resuma todo o conteúdo em um texto conciso, fácil de entender e direto ao ponto.
                4. Destaque qualquer conclusão, recomendação ou chamada para ação presente no vídeo.
                5. Evite jargões técnicos ou termos complexos, a menos que sejam essenciais para o entendimento.
                6. Use uma linguagem simples e acessível, como se estivesse explicando para alguém que não conhece o assunto.
                7. O resumo deve ser útil para qualquer pessoa que queira entender o conteúdo do vídeo sem precisar assisti-lo.
                8. O resumo deve ser claro, objetivo e conter todas as informações relevantes.
                9. O resumo deve ser escrito no idioma do áudio original.
                10. O resumo deve ser organizado de forma lógica, seguindo a estrutura do vídeo.
                11. O resumo deve conter os principais pontos discutidos no vídeo, sem perder o contexto.
                
                Resuma e organize as informações para que qualquer pessoa possa entender o conteúdo sem assistir ao vídeo.

                Aqui está o conteúdo transcrito do vídeo:

                {transcriptionText}

                E esse é o título do vídeo: {ytTitleArray[0]}.
                """
            ]
        )

        videoResumeTitle = formattedYoutubeTitle(
            f"resume-{os.path.basename(transcriptionPath).replace('.txt', '').replace('transcription-', '')}"
        )
        videoResumeTitle = os.path.join(resumesPath, videoResumeTitle)

        cleanVideoTitle = formattedYoutubeTitle(
            os.path.basename(videoResumeTitle).replace('.txt', '').replace('resume-', '')
        )

        ytTitle = ytTitleArray[0]

        with open(f"{videoResumeTitle}.md", "w", encoding="utf-8") as f:
            f.write(f"Resumo do vídeo: {ytTitle}\n\n")
            f.write(response.text)

        print(f"Sucesso no resumo! Resumo salvo em: resumes/{os.path.basename(videoResumeTitle)}.md")

        mediaDownloadPath = fetchMediaDownloadPath()
        transcriptionsPath = fetchTranscriptionsPath()

        shutil.rmtree(mediaDownloadPath)
        shutil.rmtree(transcriptionsPath)

    except Exception as e:
        print(f"Erro durante resumo: {e}")
    
url = input("Adicione a URL do vídeo: ").strip()
fetchYoutubeAudio(url)
