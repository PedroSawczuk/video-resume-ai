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
        
        print("Download foi concluído com sucesso! \n Agora iniciando a transcrição do áudio...")

        transcribeAudioToText(finalPath)

    except Exception as e:
        print(f"Erro ao fazer o download do vídeo! {e}")
        transcriptionsPath = fetchTranscriptionsPath()
        shutil.rmtree(mediaDownloadPath)
        shutil.rmtree(transcriptionsPath)

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
        
        print(f"Transcrição salva em: transcriptions/{os.path.basename(videoTranscriptionTitle)}.txt! \n Agora iniciando a análise do áudio...")

        analyzeYoutubeAudioWithAI(f"{videoTranscriptionTitle}.txt")

        mediaDownloadPath = fetchMediaDownloadPath()

    except Exception as e:
        print(f"Erro durante transcrição: {e}")
        shutil.rmtree(mediaDownloadPath)
        shutil.rmtree(transcriptionsPath)

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
                Atue como um analista narrativo e crítico de vídeos do YouTube. Você é especializado em extrair sentido, emoção e estrutura de vídeos longos, transformando transcrições em análises editoriais que expliquem o conteúdo a fundo, mesmo para quem nunca viu o vídeo.

                Receberá abaixo:
                - O título do vídeo
                - A transcrição completa
                
                Com base nisso, produza uma análise completa, profunda e bem escrita. Sua tarefa é ir além de um simples resumo. Você deve:

                ### 🎬 Estrutura do texto final:

                1. Apresentação e Contexto Inicial
                - Apresente o vídeo com uma breve contextualização: quem é o criador, de onde vem o conteúdo, qual o objetivo aparente do vídeo e qual o público-alvo.
                - Explique o tom inicial e a expectativa que o vídeo cria.

                2. Resumo Narrativo Estruturado
                - Faça um resumo cronológico, destacando todas as principais seções do vídeo com subtítulos, se necessário.
                - Aprofunde em cada ideia discutida com riqueza de detalhes, inclusive trechos mais emocionais, reflexivos ou polêmicos.
                - Destaque trechos de fala importantes, e interprete o que o autor está tentando comunicar (não apenas repita).

                3. Análise de Tom e Emoções
                - Analise o tom do vídeo ao longo do tempo (ex: melancólico, crítico, nostálgico, inspirador).
                - Aponte momentos de virada emocional e como isso afeta o entendimento geral.
                - Se for uma homenagem ou despedida, comente o peso emocional.

                4. Subtextos e Intenções Não Ditas
                - Aprofunde nas entrelinhas: o que o vídeo sugere sem dizer diretamente?
                - Existe crítica implícita? Nostalgia? Arrependimento? Esperança?

                5. Impacto no público e comunidade
                - Como esse vídeo pode afetar a base de fãs, o público geral ou a comunidade retratada?
                - Existe alguma mensagem implícita para pessoas próximas do autor, para a fanbase ou para si mesmo?

                6. Encerramento e Reflexão Final
                - Explique como o vídeo encerra e qual a mensagem principal deixada.
                - Se houver chamada à ação, diga qual é e por que ela importa.
                - Feche com uma interpretação crítica: qual o real sentido do vídeo? Por que ele foi feito? O que ele quer provocar?

                ### 📌 Regras de escrita:
                - Use uma linguagem envolvente, clara e madura.
                - Não seja genérico. Escreva como quem realmente viu e refletiu sobre o vídeo.
                - Evite linguagem robótica ou listas secas. Prefira parágrafos bem construídos e com fluidez.
                - Escreva no idioma original do vídeo.
                - NÃO invente informações. Baseie-se apenas no texto transcrito, mas interprete profundamente o que está presente ali.

                Agora, com base nessas instruções, produza uma análise completa do vídeo abaixo:

                Título do vídeo: {ytTitleArray[0]}

                Transcrição completa:
                {transcriptionText}
                """
            ]
        )

        videoResumeTitle = formattedYoutubeTitle(
            f"resume-{os.path.basename(transcriptionPath).replace('.txt', '').replace('transcription-', '')}"
        )
        videoResumeTitle = os.path.join(resumesPath, videoResumeTitle)

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
        shutil.rmtree(mediaDownloadPath)
        shutil.rmtree(transcriptionsPath)

url = input("Adicione a URL do vídeo: ").strip()
fetchYoutubeAudio(url)
