# DECEPTIO - Analise de Narrativas Historicas

Premio Arquivo.pt 2026

DECEPTIO e um MVP para explorar como um tema foi narrado ao longo do tempo na Web portuguesa arquivada.

Em vez de receber uma afirmacao isolada e devolver apenas um veredito, a primeira versao foca-se neste fluxo:

1. O utilizador introduz um tema.
2. O sistema encontra artigos relevantes no Arquivo.pt.
3. O sistema extrai as alegacoes principais dos documentos.
4. O sistema agrupa alegacoes por ano e por fonte.
5. A interface mostra:
   - linha temporal principal;
   - visao geral da fiabilidade das fontes;
   - contradicoes e desacordos;
   - resumo da mudanca narrativa.

## Exemplos de temas

- Bug do Ano 2000 em Portugal
- Entrada do Euro em Portugal
- EXPO 98 e impacto economico
- Internet em Portugal nos anos 90
- Crise financeira de 2008 nos bancos portugueses
- Ponte Vasco da Gama na imprensa portuguesa

## Arquitetura

```text
Tema do utilizador
        |
        v
C1: Query expansion
        |
        v
C2: Retrieval multi-query no Arquivo.pt
        |
        v
C3: Re-ranking dos artigos mais relevantes
        |
        v
C4: Extracao de texto + analise de narrativa com IA
        |
        v
Timeline, fontes, desacordos e mudanca narrativa
```

## Instalacao

Pre-requisitos:

- Python 3.11+
- API key do Google Gemini, configurada como `GEMINI_API_KEY`

```bash
pip install -r requirements.txt
```

Windows PowerShell:

```powershell
$env:GEMINI_API_KEY="AIzaSy..."
streamlit run app.py
```

Linux / macOS:

```bash
export GEMINI_API_KEY="AIzaSy..."
streamlit run app.py
```

A aplicacao abre em `http://localhost:8501`.

## Teste em terminal

```bash
python teste_rag.py "Bug do Ano 2000 em Portugal"
```

## Estrutura do projeto

```text
DECEPTIO/
├── app.py            # Interface Streamlit
├── deceptio_rag.py   # Pipeline Arquivo.pt + Gemini
├── teste_rag.py      # Teste rapido em terminal
├── requirements.txt
└── README.md
```

## Notas de rigor

- Todas as leituras devem citar documentos do Arquivo.pt como `[DOC N]`.
- A analise separa evidencia documental de inferencia do modelo.
- Quando a amostra for fraca ou contraditoria, o sistema deve dizer isso claramente.
- Fontes `.pt` e `publico.pt` continuam a receber prioridade no retrieval.
