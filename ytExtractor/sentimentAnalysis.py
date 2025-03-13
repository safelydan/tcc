import os
import glob
import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
from wordcloud import WordCloud, STOPWORDS
from textblob import TextBlob
from sklearn.feature_extraction.text import TfidfVectorizer

# Baixar recursos necessários
nltk.download('vader_lexicon')
nltk.download('stopwords')

# Configuração do Seaborn
sns.set_style("whitegrid")

# Criar pasta para salvar resultados, se não existir
results_dir = "results"
if not os.path.exists(results_dir):
    os.makedirs(results_dir)

# 1. Leitura de todos os arquivos CSV de uma pasta
pasta_csv = r"./comments"
arquivos_csv = glob.glob(os.path.join(pasta_csv, "*.csv"))

# Verifica se existem arquivos antes de continuar
if not arquivos_csv:
    print("Nenhum arquivo CSV encontrado na pasta especificada.")
    exit()

# Leitura e concatenação dos dataframes
lista_dfs = [pd.read_csv(arquivo) for arquivo in arquivos_csv]
df = pd.concat(lista_dfs, ignore_index=True)

print("Total de registros lidos:", len(df))

# 2. Pré-processamento aprimorado de texto
if 'comment' not in df.columns:
    print("Coluna 'comment' não encontrada no dataset.")
else:
    stop_words = set(stopwords.words('portuguese')).union({'musica', 'video', 'bom', 'top', 'legal', 'som'})

    def clean_text(text):
        """Remove links e caracteres especiais, mas mantém emojis."""
        text = str(text).lower().strip()
        text = re.sub(r'http\S+', '', text)  # Remove links
        text = re.sub(r'[^a-zA-ZÀ-ÿ\s\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF]', '', text)  # Mantém emojis
        text = ' '.join([word for word in text.split() if word not in stop_words])  # Remove stopwords
        return text

    df['comment'] = df['comment'].fillna("").apply(clean_text)

    # 3. Inicialização do analisador de sentimentos (Vader e TextBlob) com limiares ajustados
    sia = SentimentIntensityAnalyzer()

    def sentimento_vader(texto):
        score = sia.polarity_scores(texto)['compound']
        if score >= 0.3:
            return 'positivo'
        elif score <= -0.3:
            return 'negativo'
        else:
            return 'neutro'

    def sentimento_textblob(texto):
        score = TextBlob(texto).sentiment.polarity
        if score > 0.1:
            return 'positivo'
        elif score < -0.1:
            return 'negativo'
        else:
            return 'neutro'

    # Aplicação dos analisadores
    df['sentimento_vader'] = df['comment'].apply(sentimento_vader)
    df['sentimento_textblob'] = df['comment'].apply(sentimento_textblob)

    # 4. Visualizações detalhadas e salvamento dos plots

    # Distribuição de Sentimentos (Vader)
    plt.figure(figsize=(8, 6))
    sns.countplot(data=df, x='sentimento_vader', hue="sentimento_vader", palette='pastel', legend=False)
    plt.title("Distribuição de Sentimentos (Vader)")
    plt.xlabel("Sentimento")
    plt.ylabel("Contagem")
    plt.savefig(os.path.join(results_dir, "distribuicao_sentimentos_vader.png"), dpi=300)
    plt.close()

    # Distribuição de Sentimentos (TextBlob)
    plt.figure(figsize=(8, 6))
    sns.countplot(data=df, x='sentimento_textblob', hue="sentimento_textblob", palette='Set2', legend=False)
    plt.title("Distribuição de Sentimentos (TextBlob)")
    plt.xlabel("Sentimento")
    plt.ylabel("Contagem")
    plt.savefig(os.path.join(results_dir, "distribuicao_sentimentos_textblob.png"), dpi=300)
    plt.close()

    # 5. Nuvens de palavras
    custom_stopwords = set(STOPWORDS).union(stop_words)

    def gerar_wordcloud(texto, titulo, nome_arquivo):
        if texto.strip():
            wordcloud = WordCloud(width=800, height=400, background_color='white',
                                  stopwords=custom_stopwords, max_words=50).generate(texto)
            plt.figure(figsize=(10, 5))
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            plt.title(titulo)
            plt.savefig(os.path.join(results_dir, nome_arquivo), dpi=300)
            plt.close()

    # Gera nuvem de palavras para cada sentimento
    for sentimento in ['positivo', 'negativo', 'neutro']:
        texto = ' '.join(df[df['sentimento_vader'] == sentimento]['comment'])
        gerar_wordcloud(texto, f'Palavras Mais Frequentes em Comentários {sentimento.capitalize()} (Vader)',
                        f"wordcloud_{sentimento}.png")

    # 6. Análise de bigramas otimizados usando TF-IDF
    irrelevantes = {"song", "music", "lyrics", "vibe", "sound", "track", "please", "listen"}

    def extrair_ngrams_tfidf(df_filtrado, n, filename):
        """Extrai n-grams mais relevantes usando TF-IDF e remove termos irrelevantes."""
        if df_filtrado.empty:
            print(f"Nenhum comentário disponível para {filename}.")
            return pd.DataFrame()

        vectorizer = TfidfVectorizer(ngram_range=(n, n), stop_words=list(custom_stopwords))
        X = vectorizer.fit_transform(df_filtrado['comment'])

        df_tfidf = pd.DataFrame(X.toarray(), columns=vectorizer.get_feature_names_out()).sum().sort_values(ascending=False)
        df_tfidf = df_tfidf[df_tfidf.index.map(lambda x: not any(word in irrelevantes for word in x.split()))]

        df_tfidf.head(10).to_csv(os.path.join(results_dir, filename))
        return df_tfidf.head(10)

    print("\nTop 10 bigramas mais relevantes em comentários positivos:")
    print(extrair_ngrams_tfidf(df[df['sentimento_vader'] == 'positivo'], 2, "bigramas_positivos_filtrados.csv"))

    print("\nTop 10 bigramas mais relevantes em comentários negativos:")
    print(extrair_ngrams_tfidf(df[df['sentimento_vader'] == 'negativo'], 2, "bigramas_negativos_filtrados.csv"))

    # 7. Estatísticas descritivas aprimoradas
    def estatisticas_descritivas(df):
        """Gera estatísticas descritivas categóricas e numéricas separadamente."""
        stats_categoricas = df.describe(include=['object'])
        stats_numericas = df.describe()
        stats_combinadas = pd.concat([stats_categoricas, stats_numericas], axis=1)
        return stats_combinadas

    df_stats = estatisticas_descritivas(df)
    df_stats.to_csv(os.path.join(results_dir, "estatisticas_descritivas.csv"))
    print("\nEstatísticas descritivas salvas.")
