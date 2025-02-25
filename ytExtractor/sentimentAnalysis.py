# script aprimorado para analise de sentimentos com nuvens de palavras diferenciadas

import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
from wordcloud import WordCloud, STOPWORDS
from textblob import TextBlob
from sklearn.feature_extraction.text import CountVectorizer

# baixar recursos necessarios
nltk.download('vader_lexicon')
nltk.download('stopwords')

# configuracao do seaborn
sns.set_style("whitegrid")

pasta_csv = r"C:\Users\daniel\Desktop\tcc\ytExtractor\comments"  # ajuste o caminho conforme necessario
arquivos_csv = glob.glob(os.path.join(pasta_csv, "*.csv"))

# leitura e concatenacao dos dataframes
lista_dfs = [pd.read_csv(arquivo) for arquivo in arquivos_csv]
df = pd.concat(lista_dfs, ignore_index=True)

print("total de registros lidos:", len(df))

# 2. pre-processamento aprimorado de texto
if 'comment' not in df.columns:
    print("coluna 'comment' nao encontrada no dataset.")
else:
    stop_words = set(stopwords.words('portuguese')).union({'musica', 'video', 'bom', 'top', 'legal', 'som'})
    df['comment'] = df['comment'].astype(str).str.lower().str.strip()
    df['comment'] = df['comment'].apply(lambda x: ' '.join([word for word in x.split() if word not in stop_words]))

    # 3. inicializacao do analisador de sentimentos (vader e textblob) com limiares ajustados
    sia = SentimentIntensityAnalyzer()

    def sentimento_vader(texto):
        score = sia.polarity_scores(texto)['compound']
        if score >= 0.4:  # limiar ajustado para diferenciar melhor os sentimentos
            return 'positivo'
        elif score <= -0.4:
            return 'negativo'
        else:
            return 'neutro'

    def sentimento_textblob(texto):
        score = TextBlob(texto).sentiment.polarity
        if score > 0.2:
            return 'positivo'
        elif score < -0.2:
            return 'negativo'
        else:
            return 'neutro'

    # aplicacao dos analisadores
    df['sentimento_vader'] = df['comment'].apply(sentimento_vader)
    df['sentimento_textblob'] = df['comment'].apply(sentimento_textblob)

    # 4. visualizacoes detalhadas
    plt.figure(figsize=(8, 6))
    sns.countplot(data=df, x='sentimento_vader', palette='pastel')
    plt.title("Distribuicao de Sentimentos (Vader)")
    plt.xlabel("Sentimento")
    plt.ylabel("Contagem")
    plt.show()

    plt.figure(figsize=(8, 6))
    sns.countplot(data=df, x='sentimento_textblob', palette='Set2')
    plt.title("Distribuicao de Sentimentos (TextBlob)")
    plt.xlabel("Sentimento")
    plt.ylabel("Contagem")
    plt.show()

    # 5. nuvens de palavras com stopwords personalizadas e palavras mais informativas
    custom_stopwords = set(STOPWORDS).union(stop_words)

    def gerar_wordcloud(texto, titulo):
        wordcloud = WordCloud(width=800, height=400, background_color='white',
                              stopwords=custom_stopwords, max_words=50).generate(texto)
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title(titulo)
        plt.show()

    # comentarios positivos
    positivo = ' '.join(df[df['sentimento_vader'] == 'positivo']['comment'])
    gerar_wordcloud(positivo, 'Palavras Mais Frequentes em Comentarios Positivos (Vader)')

    # comentarios negativos
    negativo = ' '.join(df[df['sentimento_vader'] == 'negativo']['comment'])
    gerar_wordcloud(negativo, 'Palavras Mais Frequentes em Comentarios Negativos (Vader)')

    # comentarios neutros
    neutro = ' '.join(df[df['sentimento_vader'] == 'neutro']['comment'])
    gerar_wordcloud(neutro, 'Palavras Mais Frequentes em Comentarios Neutros (Vader)')

    # 6. analise de bigramas para comentarios positivos
    print("\nTop 10 bigramas em comentarios positivos:")
    vectorizer = CountVectorizer(ngram_range=(2, 2), stop_words=list(custom_stopwords))
    X = vectorizer.fit_transform(df[df['sentimento_vader'] == 'positivo']['comment'])
    frequencia_bigramas = pd.DataFrame(X.toarray(), columns=vectorizer.get_feature_names_out()).sum().sort_values(ascending=False)
    print(frequencia_bigramas.head(10))

    # 7. analise de bigramas para comentarios negativos
    print("\nTop 10 bigramas em comentarios negativos:")
    X_neg = vectorizer.fit_transform(df[df['sentimento_vader'] == 'negativo']['comment'])
    frequencia_bigramas_neg = pd.DataFrame(X_neg.toarray(), columns=vectorizer.get_feature_names_out()).sum().sort_values(ascending=False)
    print(frequencia_bigramas_neg.head(10))

# 8. estatisticas descritivas
print("\nestatisticas descritivas do dataframe:")
print(df.describe(include='all'))
