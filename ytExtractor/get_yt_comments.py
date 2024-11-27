import os
import pandas as pd
from time import sleep
from googleapiclient.discovery import build

def get_video_ids_and_titles_from_playlist(api_key, playlist_id):
    """
    Obtém todos os IDs de vídeos e seus títulos de uma playlist do YouTube.
    """
    youtube = build('youtube', 'v3', developerKey=api_key)

    videos = []
    request = youtube.playlistItems().list(
        part="snippet",
        playlistId=playlist_id,
        maxResults=50  # Limite por página
    )

    while request:
        response = request.execute()
        for item in response['items']:
            video_id = item['snippet']['resourceId']['videoId']
            title = item['snippet']['title']
            videos.append((video_id, title))

        request = youtube.playlistItems().list_next(request, response)

    return videos

def get_comments(api_key, video_id, title, keywords, max_comments=100):
    """
    Coleta comentários de um vídeo com base em palavras-chave.
    """
    youtube = build('youtube', 'v3', developerKey=api_key)

    request = youtube.commentThreads().list(
        part="snippet,replies",
        videoId=video_id,
        textFormat="plainText",
        maxResults=100
    )

    output_dir = "comments"
    os.makedirs(output_dir, exist_ok=True)

    df = pd.DataFrame(columns=["comment", "replies", "user_name", "date"])
    comment_count = 0

    while request and comment_count < max_comments:
        replies = []
        comments = []
        dates = []
        user_names = []
        try:
            response = request.execute()
            for item in response['items']:
                comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
                
                if any(keyword.lower() in comment.lower() for keyword in keywords):
                    comments.append(comment)
                    user_name = item['snippet']['topLevelComment']['snippet']['authorDisplayName']
                    user_names.append(user_name)
                    date = item['snippet']['topLevelComment']['snippet']['publishedAt']
                    dates.append(date)
                    replycount = item['snippet']['totalReplyCount']
                    if replycount > 0:
                        replies.append([])
                        for reply in item['replies']['comments']:
                            reply_text = reply['snippet']['textDisplay']
                            replies[-1].append(reply_text)
                    else:
                        replies.append([])

                    comment_count += 1
                    if comment_count >= max_comments:
                        break

            df2 = pd.DataFrame({
                "comment": comments,
                "replies": replies,
                "user_name": user_names,
                "date": dates
            })
            df = pd.concat([df, df2], ignore_index=True)

            output_path = os.path.join(output_dir, f"{title}_comments.csv")
            df.to_csv(output_path, index=False, encoding='utf-8')

            if comment_count >= max_comments:
                break

            sleep(2)
            request = youtube.commentThreads().list_next(request, response)
        except Exception as e:
            error_message = str(e)
            if "commentsDisabled" in error_message:
                print(f"Skipping video '{title}' ({video_id}): Comments are disabled.")
            else:
                print(f"Error processing video '{title}' ({video_id}): {e}")
            break

# Exemplo de uso da função:
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

# Obtém todos os IDs de vídeos e títulos da playlist
videos = get_video_ids_and_titles_from_playlist(api_key, playlist_id)

# Coleta comentários de todos os vídeos da playlist
for video_id, title in videos:
    print(f"Processing video: {title} - {video_id}")
    get_comments(api_key, video_id, title, keywords)
