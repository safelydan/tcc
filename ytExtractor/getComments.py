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
    """Remove termos como 'Remastered', 'Live', 'HD' do título para melhorar a busca da letra."""
    return re.sub(r'\(.*?\)|\[.*?\]|Remastered|Live|HD|Official', '', title, flags=re.IGNORECASE).strip()

def normalize_filename(name):
    """Normaliza o nome do arquivo para evitar problemas no sistema de arquivos."""
    valid_chars = f"-_.() {string.ascii_letters}{string.digits}"
    return ''.join(c for c in name if c in valid_chars).replace(' ', '_')

lyrics_cache = {}

def get_lyrics(song_title, artist=""):
    """Obtém a letra da música usando a API do Lyrics.ovh, com cache para evitar requisições duplicadas."""
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
    """Verifica se o comentário contém um trecho similar à letra da música com uma comparação mais robusta."""
    comment = re.sub(r'[^\w\s]', '', comment.lower().strip())
    
    # Verifica linha por linha da letra se alguma é muito parecida com o comentário
    for line in lyrics:
        line_clean = re.sub(r'[^\w\s]', '', line.lower().strip())
        similarity = SequenceMatcher(None, comment, line_clean).ratio()
        if similarity >= threshold:
            return True
    return False

def is_verse(comment):
    """Verifica se o comentário parece uma estrofe (mais de uma linha)."""
    return len(comment.split('\n')) > 1  # Se houver mais de uma linha, é considerado uma estrofe

def get_video_ids_and_titles(api_key, playlist_id):
    """Obtém IDs e títulos dos vídeos da playlist especificada."""
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

def get_comments(api_key, video_id, title, keywords, max_comments=100, output_dir="comments"):
    """Extrai comentários dos vídeos, filtrando por palavras-chave e evitando letras da música em formato de estrofes."""
    youtube = build('youtube', 'v3', developerKey=api_key)
    request = youtube.commentThreads().list(part="snippet,replies", videoId=video_id, textFormat="plainText", maxResults=100)

    os.makedirs(output_dir, exist_ok=True)
    df = pd.DataFrame(columns=["comment", "replies", "user_name", "date"])
    comment_count = 0
    lyrics = get_lyrics(title)

    keyword_pattern = re.compile('|'.join(re.escape(word) for word in keywords), re.IGNORECASE)

    while request and comment_count < max_comments:
        replies, comments, dates, user_names = [], [], [], []
        try:
            response = request.execute()
            for item in response.get('items', []):
                comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
                # Verifica se o comentário é uma estrofe ou contém a letra da música
                if not is_verse(comment) and keyword_pattern.search(comment) and not is_similar(comment, lyrics):
                    comments.append(comment)
                    user_name = item['snippet']['topLevelComment']['snippet']['authorDisplayName']
                    user_names.append(user_name)
                    date = item['snippet']['topLevelComment']['snippet']['publishedAt']
                    dates.append(date)
                    replycount = item['snippet']['totalReplyCount']
                    replies.append(
                        [reply['snippet']['textDisplay'] for reply in item.get('replies', {}).get('comments', [])] if replycount > 0 else []
                    )
                    comment_count += 1
                    if comment_count >= max_comments:
                        break
            df2 = pd.DataFrame({"comment": comments, "replies": replies, "user_name": user_names, "date": dates})
            df = pd.concat([df, df2], ignore_index=True)
            df.to_csv(os.path.join(output_dir, f"{normalize_filename(title)}_comments.csv"), index=False, encoding='utf-8')
            if comment_count >= max_comments:
                break
            sleep(2)
            request = youtube.commentThreads().list_next(request, response)
        except HttpError as e:
            if "commentsDisabled" in str(e):
                print(f"Comentários desativados para '{title}' ({video_id}). Pulando...")
            else:
                print(f"Erro ao processar '{title}' ({video_id}): {e}")
            break
        except Exception as e:
            print(f"Erro inesperado em '{title}': {e}")
            break

def main():
    api_key = 'AIzaSyD_0nNX7jPiWLiTxEZ17_22oHkyMbB_ny8'
    playlist_id = 'PL5vXKG03DXKEt5sCKoGi0kST_rLk6vnYS'
    keywords = [
        "melody", "harmony", "lyrics", "poetic", "emotion", "arrangement",
        "vibe", "depth", "feeling", "rhythm", "instrumental", "chords",
        "sentimental", "verse", "chorus", "connection", "narrative",
        "story", "meaning", "authentic", "creativity", "catchy", "inspiring",
        "smooth", "timbre", "tone", "progression", "atmosphere", "dynamic",
        "soulful", "powerful", "impactful"
    ]
    videos = get_video_ids_and_titles(api_key, playlist_id)
    print(f"Total de vídeos encontrados: {len(videos)}\n")

    for video_id, title in videos:
        print(f"Iniciando processamento: {title} - {video_id}")
        get_comments(api_key, video_id, title, keywords)
        print(f"Processamento finalizado para: {title}\n")

if __name__ == "__main__":
    main()
