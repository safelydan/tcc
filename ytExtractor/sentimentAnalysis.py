import os
import glob
import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
from wordcloud import WordCloud, STOPWORDS as wc_stopwords
from textblob import TextBlob
from sklearn.feature_extraction.text import TfidfVectorizer
from transformers import pipeline

# Configurações iniciais
nltk.download('vader_lexicon')
nltk.download('stopwords')
sns.set_style("whitegrid")

# Criação da pasta de resultados
results_dir = "results"
os.makedirs(results_dir, exist_ok=True)

# Leitura dos CSVs
pasta_csv = "./comments"
arquivos_csv = glob.glob(os.path.join(pasta_csv, "*.csv"))

if not arquivos_csv:
    print("Nenhum arquivo CSV encontrado na pasta especificada.")
    exit()

df = pd.concat([pd.read_csv(arquivo) for arquivo in arquivos_csv], ignore_index=True)
print("Total de registros lidos:", len(df))

if 'comment' not in df.columns:
    print("Coluna 'comment' não encontrada no dataset.")
    exit()

# Pré-processamento
stop_words = set(stopwords.words('portuguese')).union({
    'aren', 'couldn', 'didn', 'doesn', 'don', 'hadn', 'hasn', 'haven', 'isn', 'let',
    'll', 'mustn', 're', 'shan', 'shouldn', 've', 'wasn', 'weren', 'won', 'wouldn'
})

def clean_text(text):
    text = str(text).lower().strip()
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'[^a-zA-ZÀ-ÿ\s]', '', text)
    text = ' '.join([word for word in text.split() if word not in stop_words])
    return text

df['comment'] = df['comment'].fillna("").apply(clean_text)

# Modelos de sentimento
sia = SentimentIntensityAnalyzer()
sentiment_pipeline = pipeline("sentiment-analysis", model="nlptown/bert-base-multilingual-uncased-sentiment")

def sentimento_vader(text):
    score = sia.polarity_scores(text)['compound']
    return 'positivo' if score >= 0.3 else 'negativo' if score <= -0.3 else 'neutro'

def sentimento_textblob(text):
    score = TextBlob(text).sentiment.polarity
    return 'positivo' if score > 0.1 else 'negativo' if score < -0.1 else 'neutro'

def sentimento_bert(text):
    try:
        result = sentiment_pipeline(text[:512])[0]
        return result['label'].lower()
    except Exception as e:
        return "erro"

# Aplicando classificações
df['sentimento_vader'] = df['comment'].apply(sentimento_vader)
df['sentimento_textblob'] = df['comment'].apply(sentimento_textblob)
df['sentimento_bert'] = df['comment'].apply(sentimento_bert)

# Gráficos
def plot_sentimento(coluna, palette, filename):
    plt.figure(figsize=(8, 6))
    sns.countplot(data=df, x=coluna, hue=coluna, palette=palette, legend=False)
    plt.title(f"Distribuição de sentimentos ({coluna})")
    plt.xlabel("Sentimento")
    plt.ylabel("Contagem")
    plt.savefig(os.path.join(results_dir, filename), dpi=300)
    plt.close()

plot_sentimento('sentimento_vader', 'pastel', 'distribuicao_sentimentos_vader.png')
plot_sentimento('sentimento_textblob', 'Set2', 'distribuicao_sentimentos_textblob.png')
plot_sentimento('sentimento_bert', 'muted', 'distribuicao_sentimentos_bert.png')

# Wordclouds
custom_stopwords = set(wc_stopwords).union(stop_words)

def gerar_wordcloud(texto, titulo, nome_arquivo):
    if texto.strip():
        wc = WordCloud(width=800, height=400, background_color='white',
                       stopwords=custom_stopwords, max_words=50).generate(texto)
        plt.figure(figsize=(10, 5))
        plt.imshow(wc, interpolation='bilinear')
        plt.axis('off')
        plt.title(titulo)
        plt.savefig(os.path.join(results_dir, nome_arquivo), dpi=300)
        plt.close()

for sentimento in ['positivo', 'negativo', 'neutro']:
    texto = ' '.join(df[df['sentimento_vader'] == sentimento]['comment'])
    gerar_wordcloud(texto, f'Palavras mais frequentes em comentários {sentimento} (VADER)', f"wordcloud_{sentimento}.png")

# Bigramas com TF-IDF
irrelevantes = {"song", "music", "lyrics", "vibe", "sound", "track", "please", "listen"}

def extrair_ngrams_tfidf(df_filtrado, n, filename):
    if df_filtrado.empty:
        print(f"Nenhum comentário disponível para {filename}.")
        return pd.DataFrame()

    vectorizer = TfidfVectorizer(ngram_range=(n, n), stop_words=list(custom_stopwords))
    x = vectorizer.fit_transform(df_filtrado['comment'])
    try:
        palavras = vectorizer.get_feature_names_out()
    except:
        palavras = vectorizer.get_feature_names()
    df_tfidf = pd.DataFrame(x.toarray(), columns=palavras).sum().sort_values(ascending=False)
    df_tfidf = df_tfidf[df_tfidf.index.map(lambda x: not any(word in irrelevantes for word in x.split()))]

    df_tfidf.head(10).to_csv(os.path.join(results_dir, filename))
    return df_tfidf.head(10)

print("\nTop 10 bigramas mais relevantes em comentários positivos:")
print(extrair_ngrams_tfidf(df[df['sentimento_vader'] == 'positivo'], 2, "bigramas_positivos_filtrados.csv"))

print("\nTop 10 bigramas mais relevantes em comentários negativos:")
print(extrair_ngrams_tfidf(df[df['sentimento_vader'] == 'negativo'], 2, "bigramas_negativos_filtrados.csv"))

# Estatísticas
def estatisticas_descritivas(df):
    return df.describe(include='all')

df_stats = estatisticas_descritivas(df)
df_stats.to_csv(os.path.join(results_dir, "estatisticas_descritivas.csv"))
print("\nEstatísticas descritivas salvas.")
