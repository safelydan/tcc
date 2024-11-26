import pandas as pd
from time import sleep
from googleapiclient.discovery import build

def get_comments(api_key, video_id, keywords, max_comments=100):
    # Inicialização do cliente da API do YouTube
    youtube = build('youtube', 'v3', developerKey=api_key)

    # Configuração da requisição da API
    request = youtube.commentThreads().list(
        part="snippet,replies",
        videoId=video_id,
        textFormat="plainText",
        maxResults=100  # Limita a 100 comentários por página
    )

    # Inicializa o DataFrame principal
    df = pd.DataFrame(columns=["comment", "replies", "user_name", "date"])

    comment_count = 0  # Contador de comentários

    # Iteração através de resultados paginados
    while request and comment_count < max_comments:
        replies = []
        comments = []
        dates = []
        user_names = []
        try:
            response = request.execute()
            for item in response['items']:
                comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
                
                # Verifica se alguma das palavras-chave está no comentário
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

            # Adiciona os dados filtrados ao DataFrame
            df2 = pd.DataFrame({
                "comment": comments,
                "replies": replies,
                "user_name": user_names,
                "date": dates
            })
            df = pd.concat([df, df2], ignore_index=True)

            # Salva os comentários coletados em um arquivo CSV
            df.to_csv(f"{video_id}_filtered_comments.csv", index=False, encoding='utf-8')

            # Se atingiu o limite de 100, encerra a coleta
            if comment_count >= max_comments:
                break

            sleep(2)
            request = youtube.commentThreads().list_next(request, response)
        except Exception as e:
            print(str(e))
            sleep(10)
            df.to_csv(f"{video_id}_filtered_comments.csv", index=False, encoding='utf-8')
            break

# Exemplo de uso da função:
api_key = 'AIzaSyD_0nNX7jPiWLiTxEZ17_22oHkyMbB_ny8'
video_id = 'KQetemT1sWc'
keywords = [
    "melody", "harmony", "lyrics", "poetic", "emotion", "arrangement", 
    "vibe", "depth", "feeling", "rhythm", "instrumental", "chords", 
    "sentimental", "verse", "chorus", "connection", "narrative", 
    "story", "meaning", "authentic", "creativity", "catchy", "inspiring",
    "smooth", "timbre", "tone", "progression", "atmosphere", "dynamic",
    "soulful", "powerful", "impactful"
]
get_comments(api_key, video_id, keywords)
