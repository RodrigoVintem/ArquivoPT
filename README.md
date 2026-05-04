# 🕰️ ChatArquivo — A Máquina do Tempo com IA

> **Prémio Arquivo.pt 2026** — Candidatura ao 1.º prémio  
> Assistente de Inteligência Artificial que usa o [Arquivo.pt](https://arquivo.pt) como base de conhecimento histórico

---

## O que é o ChatArquivo?

O **ChatArquivo** é um sistema de Inteligência Artificial que permite consultar, em linguagem natural, os documentos históricos preservados pelo **Arquivo.pt** desde os anos 1990.

Em vez de pesquisar por palavras-chave e abrir dezenas de links antigos, o utilizador faz uma pergunta — e o sistema recupera automaticamente os documentos relevantes, extrai o conteúdo, e usa a **API Google Gemini** para sintetizar uma resposta fundamentada, com citações verificáveis.

### Exemplos de perguntas:
- *"O que se dizia sobre a adoção do Euro em Portugal em 2002?"*
- *"Como reagiram os jornais portugueses ao Bug do Ano 2000?"*
- *"Qual era a situação económica de Portugal durante a crise de 2008?"*

---

## Arquitectura Técnica: RAG (Retrieval-Augmented Generation)

```
Pergunta do utilizador
        │
        ▼
┌─────────────────────┐
│   API Arquivo.pt    │  ← Pesquisa de texto histórico
│  (textsearch API)   │     (milhões de páginas desde 1996)
└─────────────────────┘
        │
        ▼ Resultados (URLs + snippets)
┌─────────────────────┐
│  Extracção HTML     │  ← BeautifulSoup
│  (texto limpo)      │     (remove scripts, nav, ads)
└─────────────────────┘
        │
        ▼ Contexto documental datado
┌─────────────────────┐
│   LLM Gemini Pro    │  ← Google API
│   (síntese com IA)  │     (system prompt rigoroso)
└─────────────────────┘
        │
        ▼
Resposta em linguagem natural
com fontes citadas e verificáveis
```

**Garantia de rigor:** O sistema nunca inventa factos. O LLM é instruído a basear-se exclusivamente nos documentos recuperados do Arquivo.pt. Se não houver informação suficiente, diz-o claramente.

---

## Instalação e Execução

### 1. Pré-requisitos
- Python 3.11 ou superior
- Conta no [Google AI Studio](https://aistudio.google.com/) (API key gratuita)

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Configurar a chave de API

```bash
# Linux / macOS
export GEMINI_API_KEY="AIzaSy..."

# Windows (PowerShell)
$env:GEMINI_API_KEY="AIzaSy..."
```

> A chave da API Google Gemini pode ser obtida em: https://aistudio.google.com/

### 4. Executar a aplicação

```bash
streamlit run app.py
```

A aplicação abre automaticamente em `http://localhost:8501`

---

## Estrutura do Projecto

```
ChatArquivo/
├── app.py              # Interface web (Streamlit) — frontend
├── arquivo_rag.py      # Motor RAG — lógica central
├── requirements.txt    # Dependências Python
└── README.md           # Esta documentação
```

### `arquivo_rag.py` — O Motor RAG

| Função | Responsabilidade |
|--------|-----------------|
| `pesquisar_arquivo()` | Consulta a API textsearch do Arquivo.pt |
| `extrair_texto_pagina()` | Faz download e limpa o HTML das páginas arquivadas |
| `construir_contexto()` | Agrega os textos num bloco de contexto documentado |
| `gerar_resposta()` | Envia contexto + pergunta ao LLM Gemini |
| `responder_pergunta()` | Pipeline completo: orquestra todos os passos |

### `app.py` — A Interface Web

- Interface de chat construída com Streamlit
- Design editorial inspirado em arquivo histórico
- Suporte a filtros temporais (ano de início e fim)
- Exibição das fontes do Arquivo.pt com links verificáveis
- Histórico de conversa dentro da sessão (multi-turno)
- 8 perguntas de exemplo para guiar novos utilizadores

---

## Impacto Social e Científico

### Para investigadores e jornalistas
O ChatArquivo **reduz de horas para segundos** o tempo necessário para consultar fontes primárias da Web histórica portuguesa. Um jornalista que investigue a cobertura mediática de um evento histórico não precisa de abrir dezenas de links individuais — obtém imediatamente uma síntese com fontes verificáveis.

### Para a educação
Estudantes e professores podem consultar o passado digital de Portugal de forma conversacional, democratizando o acesso à história contemporânea.

### Para o combate à desinformação
Ao fornecer fontes históricas verificáveis do Arquivo.pt, o sistema ajuda a contextualizar eventos e a verificar factos com documentação primária.

### Para a preservação da memória digital
O ChatArquivo demonstra concretamente o valor do Arquivo.pt, motivando a sua utilização e a consciência sobre a importância da preservação da Web.

---

## APIs Utilizadas

- **Arquivo.pt Text Search API**: `https://arquivo.pt/textsearch`  
  Documentação: https://github.com/arquivo/pwa-technologies/wiki/Arquivo.pt-API
  
- **Google Gemini API**: `https://generativelanguage.googleapis.com`  
        Modelos utilizados: `gemini-2.5-flash`, `gemini-2.5-flash-lite`, `gemini-2.5-pro`

---

## Autor

[O teu nome]  
[Faculdade/Universidade]  
[Email]  

**Prémio Arquivo.pt 2026**  
Candidatura submetida em maio de 2026
