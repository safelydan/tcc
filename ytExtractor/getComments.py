import os
import re
import pandas as pd
from time import sleep
from googleapiclient.discovery import build
import requests

def clean_song_title(title):
    """Remove termos como 'Remastered', 'Live', 'HD' do título para melhorar a busca da letra."""
    return re.sub(r'\(.*?\)|\[.*?\]|Remastered|Live|HD|Official', '', title, flags=re.IGNORECASE).strip()

def get_lyrics(song_title, artist=""):
    """Obtém a letra da música usando a API do Lyrics.ovh."""
    song_title = clean_song_title(song_title)
    url = f"https://api.lyrics.ovh/v1/{artist}/{song_title}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get("lyrics", "").split('\n')
    return []

def get_video_ids_and_titles(api_key, playlist_id):
    youtube = build('youtube', 'v3', developerKey=api_key)
    videos = []
    request = youtube.playlistItems().list(part="snippet", playlistId=playlist_id, maxResults=50)
    while request:
        response = request.execute()
        for item in response['items']:
            video_id = item['snippet']['resourceId']['videoId']
            title = item['snippet']['title']
            videos.append((video_id, title))
        request = youtube.playlistItems().list_next(request, response)
    return videos

def get_comments(api_key, video_id, title, keywords, max_comments=100):
    youtube = build('youtube', 'v3', developerKey=api_key)
    request = youtube.commentThreads().list(part="snippet,replies", videoId=video_id, textFormat="plainText", maxResults=100)
    output_dir = "comments"
    os.makedirs(output_dir, exist_ok=True)
    df = pd.DataFrame(columns=["comment", "replies", "user_name", "date"])
    comment_count = 0
    
    lyrics = get_lyrics(title)
    
    while request and comment_count < max_comments:
        replies, comments, dates, user_names = [], [], [], []
        try:
            response = request.execute()
            for item in response['items']:
                comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
                if any(keyword.lower() in comment.lower() for keyword in keywords):
                    if not any(line.strip().lower() in comment.lower() for line in lyrics if line.strip()):
                        comments.append(comment)
                        user_name = item['snippet']['topLevelComment']['snippet']['authorDisplayName']
                        user_names.append(user_name)
                        date = item['snippet']['topLevelComment']['snippet']['publishedAt']
                        dates.append(date)
                        replycount = item['snippet']['totalReplyCount']
                        replies.append([reply['snippet']['textDisplay'] for reply in item.get('replies', {}).get('comments', [])] if replycount > 0 else [])
                        comment_count += 1
                        if comment_count >= max_comments:
                            break
            df2 = pd.DataFrame({"comment": comments, "replies": replies, "user_name": user_names, "date": dates})
            df = pd.concat([df, df2], ignore_index=True)
            df.to_csv(os.path.join(output_dir, f"{title.replace('/', '_')}_comments.csv"), index=False, encoding='utf-8')
            if comment_count >= max_comments:
                break
            sleep(2)
            request = youtube.commentThreads().list_next(request, response)
        except Exception as e:
            if "commentsDisabled" in str(e):
                print(f"Skipping video '{title}' ({video_id}): Comments are disabled.")
            else:
                print(f"Error processing video '{title}' ({video_id}): {e}")
            break

def main():
    api_key = 'AIzaSyD_0nNX7jPiWLiTxEZ17_22oHkyMbB_ny8'
    playlist_id = 'PL0jp-uZ7a4g9FQWW5R_u0pz4yzV4RiOXu'  # ID da playlist
    keywords = [
        "melody", "harmony", "lyrics", "poetic", "emotion", "arrangement", 
        "vibe", "depth", "feeling", "rhythm", "instrumental", "chords", 
        "sentimental", "verse", "chorus", "connection", "narrative", 
        "story", "meaning", "authentic", "creativity", "catchy", "inspiring",
        "smooth", "timbre", "tone", "progression", "atmosphere", "dynamic",
        "soulful", "powerful", "impactful"
    ]
    videos = get_video_ids_and_titles(api_key, playlist_id)
    for video_id, title in videos:
        print(f"Processing video: {title} - {video_id}")
        get_comments(api_key, video_id, title, keywords)

if __name__ == "__main__":
    main()