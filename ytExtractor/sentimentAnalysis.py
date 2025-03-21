import os
import glob
import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import nltk
from nltk.sentiment import sentimentintensityanalyzer
from nltk.corpus import stopwords
from wordcloud import wordcloud, stopwords as wc_stopwords
from textblob import textblob
from sklearn.feature_extraction.text import tfidfvectorizer
from transformers import pipeline, autotokenizer

nltk.download('vader_lexicon')
nltk.download('stopwords')

sns.set_style("whitegrid")

results_dir = "results"
if not os.path.exists(results_dir):
    os.makedirs(results_dir)

pasta_csv = r"./comments"
arquivos_csv = glob.glob(os.path.join(pasta_csv, "*.csv"))

if not arquivos_csv:
    print("nenhum arquivo csv encontrado na pasta especificada.")
    exit()

lista_dfs = [pd.read_csv(arquivo) for arquivo in arquivos_csv]
df = pd.concat(lista_dfs, ignore_index=True)

print("total de registros lidos:", len(df))

if 'comment' not in df.columns:
    print("coluna 'comment' não encontrada no dataset.")
else:
    stop_words = set(stopwords.words('portuguese')).union({
        'aren', 'couldn', 'didn', 'doesn', 'don', 'hadn', 'hasn', 'haven', 'isn', 'let', 
        'll', 'mustn', 're', 'shan', 'shouldn', 've', 'wasn', 'weren', 'won', 'wouldn'
    })

    def clean_text(text):
        text = str(text).lower().strip()
        text = re.sub(r'http\\S+', '', text)
        text = re.sub(r'[^a-zA-ZÀ-ÿ\\s\\U0001F600-\\U0001F64F\\U0001F300-\\U0001F5FF\\U0001F680-\\U0001F6FF]', '', text)
        text = ' '.join([word for word in text.split() if word not in stop_words])
        return text

    df['comment'] = df['comment'].fillna("").apply(clean_text)

    sia = sentimentintensityanalyzer()
    sentiment_pipeline = pipeline("sentiment-analysis", truncation=True, max_length=512)

    def sentimento_vader(texto):
        score = sia.polarity_scores(texto)['compound']
        if score >= 0.3:
            return 'positivo'
        elif score <= -0.3:
            return 'negativo'
        else:
            return 'neutro'

    def sentimento_textblob(texto):
        score = textblob(texto).sentiment.polarity
        if score > 0.1:
            return 'positivo'
        elif score < -0.1:
            return 'negativo'
        else:
            return 'neutro'

    def sentimento_bert(texto):
        result = sentiment_pipeline(texto)[0]
        return result['label'].lower()

    df['sentimento_vader'] = df['comment'].apply(sentimento_vader)
    df['sentimento_textblob'] = df['comment'].apply(sentimento_textblob)
    df['sentimento_bert'] = df['comment'].apply(sentimento_bert)

    plt.figure(figsize=(8, 6))
    sns.countplot(data=df, x='sentimento_vader', hue="sentimento_vader", palette='pastel', legend=False)
    plt.title("distribuição de sentimentos (vader)")
    plt.xlabel("sentimento")
    plt.ylabel("contagem")
    plt.savefig(os.path.join(results_dir, "distribuicao_sentimentos_vader.png"), dpi=300)
    plt.close()

    plt.figure(figsize=(8, 6))
    sns.countplot(data=df, x='sentimento_textblob', hue="sentimento_textblob", palette='set2', legend=False)
    plt.title("distribuição de sentimentos (textblob)")
    plt.xlabel("sentimento")
    plt.ylabel("contagem")
    plt.savefig(os.path.join(results_dir, "distribuicao_sentimentos_textblob.png"), dpi=300)
    plt.close()

    plt.figure(figsize=(8, 6))
    sns.countplot(data=df, x='sentimento_bert', hue="sentimento_bert", palette='muted', legend=False)
    plt.title("distribuição de sentimentos (bert)")
    plt.xlabel("sentimento")
    plt.ylabel("contagem")
    plt.savefig(os.path.join(results_dir, "distribuicao_sentimentos_bert.png"), dpi=300)
    plt.close()

    custom_stopwords = set(wc_stopwords).union(stop_words)

    def gerar_wordcloud(texto, titulo, nome_arquivo):
        if texto.strip():
            wordcloud = wordcloud(width=800, height=400, background_color='white',
                                  stopwords=custom_stopwords, max_words=50).generate(texto)
            plt.figure(figsize=(10, 5))
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            plt.title(titulo)
            plt.savefig(os.path.join(results_dir, nome_arquivo), dpi=300)
            plt.close()

    for sentimento in ['positivo', 'negativo', 'neutro']:
        texto = ' '.join(df[df['sentimento_vader'] == sentimento]['comment'])
        gerar_wordcloud(texto, f'palavras mais frequentes em comentários {sentimento} (vader)',
                        f"wordcloud_{sentimento}.png")

    irrelevantes = {"song", "music", "lyrics", "vibe", "sound", "track", "please", "listen"}

    def extrair_ngrams_tfidf(df_filtrado, n, filename):
        if df_filtrado.empty:
            print(f"nenhum comentário disponível para {filename}.")
            return pd.DataFrame()

        vectorizer = tfidfvectorizer(ngram_range=(n, n), stop_words=list(custom_stopwords))
        x = vectorizer.fit_transform(df_filtrado['comment'])

        df_tfidf = pd.DataFrame(x.toarray(), columns=vectorizer.get_feature_names_out()).sum().sort_values(ascending=False)
        df_tfidf = df_tfidf[df_tfidf.index.map(lambda x: not any(word in irrelevantes for word in x.split()))]

        df_tfidf.head(10).to_csv(os.path.join(results_dir, filename))
        return df_tfidf.head(10)

    print("\\ntop 10 bigramas mais relevantes em comentários positivos:")
    print(extrair_ngrams_tfidf(df[df['sentimento_vader'] == 'positivo'], 2, "bigramas_positivos_filtrados.csv"))

    print("\\ntop 10 bigramas mais relevantes em comentários negativos:")
    print(extrair_ngrams_tfidf(df[df['sentimento_vader'] == 'negativo'], 2, "bigramas_negativos_filtrados.csv"))

    def estatisticas_descritivas(df):
        stats_categoricas = df.describe(include=['object'])
        stats_numericas = df.describe()
        stats_combinadas = pd.concat([stats_categoricas, stats_numericas], axis=1)
        return stats_combinadas

    df_stats = estatisticas_descritivas(df)
    df_stats.to_csv(os.path.join(results_dir, "estatisticas_descritivas.csv"))
    print("\\nestatísticas descritivas salvas.")
