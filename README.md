🔍 DECEPTIO — Detetor de Desinformação Histórica

Prémio Arquivo.pt 2026 — Candidatura ao 1.º Prémio + Menções Honrosas (Público · DNS.PT)
Sistema de Inteligência Artificial para auditoria de afirmações históricas com base em fontes arquivadas da Web portuguesa

O que é o DECEPTIO?

O DECEPTIO (latim: engano, ilusão) é um sistema de IA que analisa afirmações históricas — como mitos, teorias ou narrativas virais — e determina a sua veracidade com base em documentos reais preservados pelo Arquivo.pt.

Em vez de confiar em memória, opiniões ou fontes isoladas, o sistema:

Pesquisa automaticamente a Web histórica portuguesa
Seleciona as fontes mais relevantes
Cruza essa evidência com conhecimento global
Produz um veredito fundamentado e explicável
Exemplos de utilização
“O Bug do Ano 2000 causou falhas graves em Portugal?”
“Portugal faliu durante a crise de 2008?”
“Houve pânico real com a entrada no Euro?”
“A gripe A foi exagerada pelos media portugueses?”
Arquitectura Técnica: RAG com Auditoria de Factos
Afirmação do utilizador
        │
        ▼
┌────────────────────────────┐
│ C1: Query Expansion        │  ← Gemini Flash Lite
│ Gera múltiplas pesquisas   │     (variações semânticas)
└────────────────────────────┘
        │
        ▼
┌────────────────────────────┐
│ C2: Retrieval Multi-Query  │  ← Arquivo.pt API
│ Até 45 documentos históricos│    (prioridade .pt)
└────────────────────────────┘
        │
        ▼
┌────────────────────────────┐
│ C3: Re-ranking             │  ← Gemini Flash Lite
│ Seleciona os 5 mais relevantes
└────────────────────────────┘
        │
        ▼
┌────────────────────────────┐
│ C4: Auditoria de Factos    │  ← Gemini Flash
│ Análise crítica + veredito │
└────────────────────────────┘
        │
        ▼
Resposta estruturada com evidência
e fontes verificáveis
Sistema de Vereditos

O DECEPTIO não responde apenas — julga a veracidade da afirmação:

Veredito	Significado
🔴 MITO HISTÓRICO	Afirmação falsa com evidência documental
🟢 FACTO CONFIRMADO	Verdade comprovada por múltiplas fontes
🟡 VERDADE PARCIAL	Contém elementos verdadeiros, mas distorcidos
🔵 PÂNICO INJUSTIFICADO	Narrativa da época exagerou os factos
🟣 INCONCLUSIVO	Evidência insuficiente ou contraditória
Garantia de Rigor
O sistema privilegia fontes primárias arquivadas
Todas as respostas incluem referências verificáveis
O modelo é instruído a:
Não inventar factos
Distinguir evidência de interpretação
Assumir incerteza quando necessário
Impacto Social e Científico
Combate à desinformação

Permite verificar rapidamente narrativas históricas recorrentes na Internet, reduzindo a propagação de mitos.

Jornalismo e investigação

Facilita a análise da cobertura mediática ao longo do tempo, com acesso imediato a fontes primárias.

Educação

Transforma a história recente num sistema explorável e questionável, incentivando pensamento crítico.

Valorização do Arquivo.pt

Demonstra o potencial do arquivo da Web como ferramenta ativa de verificação de factos.

Menções Honrosas Visadas
Público → Prioridade a fontes publico.pt (destacadas com ⭐)
DNS.PT → Foco em domínios .pt via operadores de pesquisa
Instalação e Execução
Pré-requisitos
Python 3.11+
API Key do Google Gemini (Google AI Studio
)
Setup
pip install -r requirements.txt

# Linux / macOS
export GEMINI_API_KEY="AIzaSy..."

# Windows (PowerShell)
$env:GEMINI_API_KEY="AIzaSy..."
Executar
streamlit run app.py

A aplicação abre em: http://localhost:8501

Estrutura do Projeto
DECEPTIO/
├── app.py              # Interface Streamlit
├── arquivo_rag.py      # Pipeline RAG multi-camada
├── requirements.txt
└── README.md
Diferenciação Técnica
Multi-query retrieval → reduz viés de pesquisa única
Re-ranking com LLM → melhora precisão semântica
Auditoria de factos estruturada → não apenas resposta, mas avaliação crítica
Integração temporal implícita → análise baseada em contexto histórico real

Autor

Rodrigo Vintém
Instituto Superior Técnico - Alameda
rodrigo.vintem@tecnico.ulisboa.pt

Oleksandra Kozlova
Universidade NOVA FCT
!!!!Email por definir!!!!! - não submeter sem preencher
Prémio Arquivo.pt 2026
Candidatura submetida em Maio de 2026