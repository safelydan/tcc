import os
import re
import string
import pandas as pd
from time import sleep
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import requests
from difflib import SequenceMatcher

def clean_song_title(title):
    """remove termos como 'remastered', 'live', 'hd' do título para melhorar a busca da letra."""
    return re.sub(r'\(.*?\)|\[.*?\]|Remastered|Live|HD|Official', '', title, flags=re.IGNORECASE).strip()

def normalize_filename(name):
    """normaliza o nome do arquivo para evitar problemas no sistema de arquivos."""
    valid_chars = f"-_.() {string.ascii_letters}{string.digits}"
    return ''.join(c for c in name if c in valid_chars).replace(' ', '_')

lyrics_cache = {}

def get_lyrics(song_title, artist=""):
    """obtém a letra da música usando a api do lyrics.ovh, com cache para evitar requisições duplicadas."""
    song_title = clean_song_title(song_title)
    key = f"{artist}_{song_title}".lower()
    if key in lyrics_cache:
        return lyrics_cache[key]

    url = f"https://api.lyrics.ovh/v1/{artist}/{song_title}"
    response = requests.get(url)
    if response.status_code == 200:
        lyrics = [line.strip().lower() for line in response.json().get("lyrics", "").split('\n') if line.strip()]
        lyrics_cache[key] = lyrics
        return lyrics
    return []

def is_similar(comment, lyrics, threshold=0.8):
    """verifica se o comentário contém um trecho similar à letra da música com uma comparação mais robusta."""
    comment = re.sub(r'[^\w\s]', '', comment.lower().strip())
    
    for line in lyrics:
        line_clean = re.sub(r'[^\w\s]', '', line.lower().strip())
        similarity = SequenceMatcher(None, comment, line_clean).ratio()
        if similarity >= threshold:
            return True
    return False

def is_verse(comment):
    """verifica se o comentário parece uma estrofe (mais de uma linha)."""
    return len(comment.split('\n')) > 1  # se houver mais de uma linha, é considerado uma estrofe

def get_video_ids_and_titles(api_key, playlist_id):
    """obtém ids e títulos dos vídeos da playlist especificada."""
    youtube = build('youtube', 'v3', developerKey=api_key)
    videos = []
    request = youtube.playlistItems().list(part="snippet", playlistId=playlist_id, maxResults=50)
    while request:
        response = request.execute()
        for item in response.get('items', []):
            video_id = item['snippet']['resourceId']['videoId']
            title = item['snippet']['title']
            videos.append((video_id, title))
        request = youtube.playlistItems().list_next(request, response)
    return videos

def get_comments(api_key, video_id, title, keywords, max_comments=300, output_dir="comments"):
    """extrai apenas comentários principais dos vídeos, filtrando por palavras-chave e evitando letras da música em formato de estrofes."""
    youtube = build('youtube', 'v3', developerKey=api_key)
    os.makedirs(output_dir, exist_ok=True)

    # verifica se o arquivo já existe e pula se necessário
    filename = os.path.join(output_dir, f"{normalize_filename(title)}_comments.csv")
    if os.path.exists(filename):
        print(f"arquivo '{filename}' já existe. pulando {title}...")
        return

    request = youtube.commentThreads().list(part="snippet", videoId=video_id, textFormat="plainText", maxResults=100)
    df = pd.DataFrame(columns=["comment", "user_name", "date"])
    comment_count = 0
    lyrics = get_lyrics(title)

    keyword_pattern = re.compile('|'.join(re.escape(word) for word in keywords), re.IGNORECASE)

    while request and comment_count < max_comments:
        comments, dates, user_names = [], [], []
        try:
            response = request.execute()
            for item in response.get('items', []):
                comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
                
                if not is_verse(comment) and keyword_pattern.search(comment) and not is_similar(comment, lyrics):
                    comments.append(comment)
                    user_name = item['snippet']['topLevelComment']['snippet']['authorDisplayName']
                    user_names.append(user_name)
                    date = item['snippet']['topLevelComment']['snippet']['publishedAt']
                    dates.append(date)
                    comment_count += 1
                    if comment_count >= max_comments:
                        break

            df2 = pd.DataFrame({"comment": comments, "user_name": user_names, "date": dates})
            df = pd.concat([df, df2], ignore_index=True)
            df.to_csv(filename, index=False, encoding='utf-8')
            if comment_count >= max_comments:
                break
            sleep(2)
            request = youtube.commentThreads().list_next(request, response)
        except HttpError as e:
            if "commentsDisabled" in str(e):
                print(f"comentários desativados para '{title}' ({video_id}). pulando...")
            else:
                print(f"erro ao processar '{title}' ({video_id}): {e}")
            break
        except Exception as e:
            print(f"erro inesperado em '{title}': {e}")
            break

def main():
    api_key = 'AIzaSyD_0nNX7jPiWLiTxEZ17_22oHkyMbB_ny8'
    playlist_id = 'PL5vXKG03DXKG1YRARCr9qd6yymBreQ0wS'
    keywords = [
        # aspectos musicais gerais
        "melody", "harmony", "rhythm", "tempo", "beat", "chords", "notes",
        "tone", "timbre", "instrumental", "composition", "arrangement",
        "progression", "pitch", "acoustic", "orchestration",

        # elementos vocais e letra
        "lyrics", "poetic", "verse", "chorus", "bridge", "vocal", "falsetto",
        "intonation", "resonance", "phrasing", "lyrical",

        # produção musical e mixagem
        "mixing", "mastering", "stereo", "equalization", "reverb", "distortion",
        "compression", "effects", "sampling", "synth", "autotune",

        # emoções e impacto sonoro
        "emotion", "soulful", "heartfelt", "powerful", "passionate", "deep",
        "intense", "expressive", "atmosphere", "haunting",

        # estilos e gêneros musicais
        "jazzy", "bluesy", "funky", "orchestral", "electronic", "synthwave",
        "ballad", "anthemic", "cinematic", "acoustic", "indie", "grunge",

        # impacto e conexão emocional
        "catchy", "earworm", "vibe", "nostalgic", "chills", "uplifting",
        "dreamy", "hypnotic", "soothing", "meditative",

        # narrativa e significado
        "story", "meaningful", "authentic", "metaphorical", "relatable",
        "message", "theme", "symbolism",

        # **críticas negativas**
        "boring", "repetitive", "generic", "forgettable",
        "lifeless", "annoying", "overproduced", "autotuned",
        "monotonous", "weak", "shallow", "bland",
        "meaningless", "cliché", "cringe", "overrated",
        "disappointing", "noisy", "distorted", "unbalanced",
        "bad lyrics", "bad production", "bad mixing", "waste of time",

        # **palavrões e insultos**
        "shit", "fuck", "trash", "garbage", "sucks",
        "stupid", "idiot", "terrible", "worst", "awful",
        "pathetic", "lame", "wtf", "hell no",
        "fucking trash", "worst song ever", "so bad",
        "ugly voice", "stupid lyrics"

    ]

    
    videos = get_video_ids_and_titles(api_key, playlist_id)
    print(f"total de vídeos encontrados: {len(videos)}\n")

    for video_id, title in videos:
        print(f"iniciando processamento: {title} - {video_id}")
        get_comments(api_key, video_id, title, keywords)
        print(f"processamento finalizado para: {title}\n")

if __name__ == "__main__":
    main()
