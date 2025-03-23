# Análise de Comentários Musicais do YouTube

Este projeto realiza **coleta inteligente de comentários** de vídeos musicais no YouTube e aplica **análise de sentimentos** e **mineração textual** nos comentários extraídos. O objetivo é identificar opiniões relevantes sobre aspectos musicais, eliminando letras das músicas e spam, e explorando o conteúdo com técnicas de NLP.

---

## Estrutura do Repositório

```
├── comments/                        # Pasta onde os CSVs de comentários serão salvos
├── results/                         # Saída dos gráficos, nuvens de palavras, bigramas e estatísticas
├── getComments.py                   # Script para coleta de comentários no YouTube
├── sentimentAnalysis.py             # Script de análise de sentimentos e mineração textual
├── README.md                        # Este arquivo
```

---

## 1. Coleta Inteligente de Comentários (`getComments.py`)

### Funcionalidades

- Acessa uma playlist do YouTube e extrai vídeos (título e ID).
- Coleta os principais comentários de cada vídeo, com um limite configurável.
- Filtra os comentários usando uma lista de **palavras-chave musicais** (melodia, ritmo, mixagem, etc.).
- Exclui automaticamente **letras de músicas** usando a API `lyrics.ovh` e verificação de similaridade com `SequenceMatcher`.
- Salva os comentários válidos em arquivos CSV por vídeo.

### Configuração

- Defina sua `API_KEY` do YouTube Data API v3.
- Configure o `playlist_id` da playlist que deseja extrair.
- Liste as `keywords` musicais que deseja filtrar nos comentários.

### Execução

```bash
python getComments.py
```

---

## 2. Análise de Sentimentos e Mineração Textual (`sentimentAnalysis.py`)

### Funcionalidades

- Lê todos os arquivos CSV da pasta `comments/`.
- Realiza pré-processamento textual (limpeza, remoção de stopwords).
- Aplica **três modelos de sentimento**:
  - **VADER** (lexicon-based)
  - **TextBlob** (análise de polaridade)
  - **BERT Multilíngue** (`nlptown/bert-base-multilingual-uncased-sentiment`)
- Gera gráficos de distribuição de sentimentos.
- Gera **nuvens de palavras** para cada polaridade (positivo, negativo, neutro).
- Extrai os **10 bigramas mais relevantes** com TF-IDF.
- Exporta estatísticas descritivas dos comentários.

### Execução

```bash
python sentimentAnalysis.py
```

---

## Requisitos

Instale as dependências com:

```bash
pip install -r requirements.txt
```

### Exemplo de `requirements.txt`

```
pandas
matplotlib
seaborn
nltk
wordcloud
textblob
scikit-learn
transformers
google-api-python-client
requests
```

Além disso, execute no seu ambiente Python:

```python
import nltk
nltk.download('vader_lexicon')
nltk.download('stopwords')
```

---

## Resultados Gerados

- **Gráficos de sentimento**: distribuição dos sentimentos por modelo (`.png`)
- **Nuvens de palavras**: palavras mais frequentes por polaridade
- **Bigramas relevantes**: arquivos `.csv` com bigramas filtrados
- **Estatísticas**: `estatisticas_descritivas.csv`

Todos os arquivos são salvos na pasta `results/`.

---

## Exemplo de Aplicação

Este projeto pode ser utilizado para:

- Avaliar o impacto emocional de músicas.
- Identificar tendências de produção musical com base em feedback dos ouvintes.
- Diferenciar comentários de apreciação musical de spam/letras repetidas.
- Treinar modelos de classificação de sentimentos musicais.

---

## Licença

Este projeto é livre para uso acadêmico e educacional. Cite a fonte se utilizar para publicações ou apresentações.

---

## Contato

Desenvolvido por **[Daniel Araujo Leal]**  
Email: **[danielaraujoleal985@gmail.com]**  
GitHub: [https://github.com/safelydan](https://github.com/safelydan)
