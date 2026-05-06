# 🔍 DECEPTIO - Mapa de Narrativas Históricas

**Candidatura ao Prémio Arquivo.pt 2026**

🌐 **[EXPERIMENTAR A DEMO ONLINE](https://deceptio.streamlit.app)**

O DECEPTIO é uma ferramenta inteligente para explorar como um tema ou narrativa mudou ao longo do tempo na Web portuguesa arquivada.

Em vez de receber uma afirmação isolada e devolver apenas um veredito binário, o DECEPTIO foca-se na auditoria da narrativa:

1. O utilizador introduz um tema histórico.
2. O sistema encontra artigos relevantes no Arquivo.pt.
3. Extrai as alegações principais dos documentos.
4. Agrupa alegações por ano e por fonte.
5. A interface apresenta:
   * Linha temporal principal;
   * Visão geral da fiabilidade das fontes;
   * Contradições e desacordos detetados;
   * Resumo de como a narrativa mudou.

## 🧪 Exemplos de Temas Analisados

- Bug do Ano 2000 em Portugal
- Entrada do Euro em Portugal
- EXPO 98 e impacto económico
- Internet em Portugal nos anos 90
- Crise financeira de 2008 nos bancos portugueses
- Ponte Vasco da Gama na imprensa portuguesa

## ⚙️ Arquitetura RAG (4 Camadas)
```text
Tema do utilizador
        |
        v
C1: Query Expansion (A IA gera 3 queries otimizadas)
        |
        v
C2: Retrieval (Pesquisa multi-query no Arquivo.pt com boost para .pt e publico.pt)
        |
        v
C3: Re-ranking (A IA seleciona os artigos mais relevantes)
        |
        v
C4: Análise IA (Extração de texto + cruzamento de factos)
        |
        v
Timeline, Fontes, Desacordos e Mudança Narrativa
```

## 🛠️ Instalação Local
Pré-requisitos:

- Python 3.11+
- API key do Google Gemini, configurada como GEMINI_API_KEY

```bash
# Instalar dependências
pip install -r requirements.txt
```

Para correr (Windows PowerShell):

```powershell
$env:GEMINI_API_KEY="AIzaSy..."
streamlit run app.py
```

Para correr (Linux / macOS):

```bash
export GEMINI_API_KEY="AIzaSy..."
streamlit run app.py
```

A aplicação abre em http://localhost:8501.

📂 Estrutura do Projeto
```text
DECEPTIO/
├── app.py            # Interface Streamlit (Frontend)
├── deceptio_rag.py   # Motor de RAG 4-Camadas (Backend)
├── teste_rag.py      # Script de teste rápido em terminal
├── requirements.txt  # Dependências
└── README.md
```

🎯 Notas de Rigor e Menção Honrosa
Todas as leituras feitas pela IA citam obrigatoriamente os documentos do Arquivo.pt usando o formato [DOC N].
A análise separa rigorosamente a evidência documental da inferência do modelo.
Quando a amostra for fraca, fragmentada ou contraditória, o sistema relata a inconclusividade de forma transparente.
Menção Honrosa: O pipeline de Retrieval (C2) aplica um multiplicador de relevância específico para priorizar fontes nacionais (.pt) e o jornal Público (publico.pt).
