"""
================================================================================
DECEPTIO - Interface Web (Streamlit)
================================================================================
Ferramenta de análise de narrativas históricas usando o Arquivo.pt.
Prémio Arquivo.pt 2026

Para correr:
    export GEMINI_API_KEY="AIzaSy..."
    streamlit run app.py
================================================================================
"""

import streamlit as st
import re
import base64
import html
from deceptio_rag import analisar_topico

# ── Configuração ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title = "DECEPTIO - Mapa de Narrativas Históricas",
    page_icon  = "🔍",
    layout     = "wide",
    initial_sidebar_state = "expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

:root {
    --bg:        #0A0A0F;
    --bg2:       #111118;
    --bg3:       #18181F;
    --borda:     #2A2A38;
    --borda2:    #3A3A50;
    --texto:     #E8E8F0;
    --subtexto:  #8888AA;
    --vermelho:  #FF2D55;
    --verde:     #00FF88;
    --amarelo:   #FFB800;
    --azul:      #4D9EFF;
    --roxo:      #9B5DE5;
    --fonte:     'Space Grotesk', sans-serif;
    --mono:      'JetBrains Mono', monospace;
}

/* ── Reset ─── */
html, body, [class*="css"] {
    font-family: var(--fonte) !important;
    background-color: var(--bg) !important;
    color: var(--texto) !important;
}
#MainMenu, footer, .stDeployButton { display: none !important; }
/* ── Botões de Abrir/Fechar Sidebar sempre visíveis ─── */
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapseButton"],
button[kind="header"] {
    opacity: 1 !important;
    visibility: visible !important;
    color: var(--subtexto) !important;
}

/* Ajuste vertical: manter o botão ligeiramente acima do texto da sidebar */
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapseButton"] {
    position: relative !important;
    top: 2rem !important;
    z-index: 1000 !important;
}

/* ── Scrollbar ─── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--borda2); border-radius: 2px; }

/* ── Cabeçalho ─── */
.header {
    padding: 0.2rem 0 0.9rem;
    border-bottom: 1px solid var(--borda);
    margin-bottom: 1rem;
    position: relative;
}
.header-grid {
    display: flex;
    align-items: flex-end; 
    justify-content: space-between;
    gap: 1rem;
    padding-bottom: 0.2rem;
}
.logo-area { display: flex; align-items: center; gap: 1.2rem; }
.logo-icon {
    width: 78px;             
    height: 78px;            
    background: var(--vermelho);
    border-radius: 14px;     
    display: flex; align-items: center; justify-content: center;
    font-size: 2.6rem;       
    flex-shrink: 0;
    box-shadow: 0 4px 24px rgba(255,45,85,0.45); 
    transform: translateY(12px);
}
.logo-text { transform: translateY(4px); }
.logo-text h1 {
    font-family: var(--mono) !important;
    font-size: 2.2rem !important;
    font-weight: 700 !important;
    letter-spacing: 6px !important;
    color: var(--texto) !important;
    margin: 0 0 -4px 0 !important; 
    line-height: 1 !important;
}
.logo-text .tagline {
    font-family: var(--mono);
    font-size: 0.85rem;
    color: var(--vermelho);
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-top: 0 !important; 
}
.header-stats {
    display: flex;
    gap: 1rem;
    flex-shrink: 0;
    margin-bottom: -0.4rem; 
}
.stat-pill {
    text-align: center;
    padding: 0.6rem 0; 
    min-width: 110px;  
    border: 1px solid var(--borda);
    border-radius: 6px;
    background: var(--bg2);
    display: flex;
    flex-direction: column;
    justify-content: center;
}
.stat-num {
    font-family: var(--mono);
    font-size: 1.5rem; 
    font-weight: 700;
    color: var(--verde);
    line-height: 1.1;
}
.stat-label {
    font-size: 0.62rem;
    color: var(--subtexto);
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* ── Sidebar ─── */
section[data-testid="stSidebar"] {
    background: var(--bg2) !important;
    border-right: 1px solid var(--borda) !important;
}
section[data-testid="stSidebar"] div[data-testid="stSidebarContent"] {
    padding-top: 0 !important;
    transform: translateY(-2rem);
}
section[data-testid="stSidebar"] .block-container {
    padding-top: 0 !important;
    margin-top: 0 !important;
}
section[data-testid="stSidebar"] * { color: var(--texto) !important; }

/* ── Botões de exemplo ─── */
.stButton > button {
    background: var(--bg3) !important;
    color: var(--subtexto) !important;
    border: 1px solid var(--borda) !important;
    border-radius: 4px !important;
    font-family: var(--fonte) !important;
    font-size: 0.8rem !important;
    text-align: left !important;
    padding: 0.5rem 0.8rem !important;
    width: 100% !important;
    transition: all 0.15s !important;
    white-space: normal !important;
    height: auto !important;
    line-height: 1.4 !important;
}
.stButton > button:hover {
    background: var(--bg3) !important;
    border-color: var(--vermelho) !important;
    color: var(--texto) !important;
    box-shadow: 0 0 8px rgba(255,45,85,0.2) !important;
}

/* ── Input ─── */
.stTextInput { margin-bottom: 0 !important; }
.stTextInput > label { margin-bottom: 0.35rem !important; }
.stTextInput div[data-baseweb="input"] {
    min-height: 52px !important;
    height: 52px !important;
    background: var(--bg2) !important;
    border: 1px solid var(--borda2) !important;
    border-radius: 6px !important;
    box-shadow: none !important;
}
.stTextInput div[data-baseweb="input"] > div {
    height: 52px !important;
    box-shadow: none !important;
}
.stTextInput > div > div > input {
    background: var(--bg2) !important;
    border: 1px solid var(--borda2) !important;
    border-radius: 6px !important;
    color: var(--texto) !important;
    font-family: var(--fonte) !important;
    font-size: 1rem !important;
    padding: 0 1rem !important;
    height: 52px !important; 
    line-height: 52px !important;
    box-shadow: none !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--vermelho) !important;
    box-shadow: none !important;
    outline: none !important;
}
.stTextInput > div > div > input::placeholder { color: var(--subtexto) !important; }

/* ── Botão primário ─── */
.stButton > button[kind="primary"],
button[data-testid="baseButton-primary"] {
    background: var(--vermelho) !important;
    color: white !important;
    border: none !important;
    border-radius: 6px !important;
    font-family: var(--mono) !important;
    font-size: 0.75rem !important;
    font-weight: 700 !important;
    letter-spacing: 1px !important;
    padding: 0 1rem !important;
    height: 52px !important; 
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    box-shadow: 0 0 16px rgba(255,45,85,0.35) !important;
    transition: all 0.15s !important;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 0 24px rgba(255,45,85,0.55) !important;
    transform: translateY(-1px) !important;
}

/* ── Checkbox e toggle ─── */
.stCheckbox label, .stCheckbox span { color: var(--subtexto) !important; font-size: 0.85rem !important; }
.stNumberInput > div > div > input {
    background: var(--bg2) !important;
    border: 1px solid var(--borda) !important;
    color: var(--texto) !important;
    font-family: var(--mono) !important;
    border-radius: 4px !important;
}

/* ── Spinner ─── */
.stSpinner > div { border-top-color: var(--vermelho) !important; }

/* ── HR ─── */
hr { border: none !important; border-top: 1px solid var(--borda) !important; margin: 1.2rem 0 !important; }

/* ── Alerta ─── */
.stAlert { background: var(--bg2) !important; border-radius: 4px !important; color: var(--subtexto) !important; }

/* ── Bloco de afirmação (input do utilizador) ─── */
.bloco-afirmacao {
    background: var(--bg2);
    border: 1px solid var(--borda);
    border-left: 3px solid var(--subtexto);
    border-radius: 6px;
    padding: 0.9rem 1.2rem;
    margin: 1rem 0 0.5rem;
    font-size: 0.95rem;
    color: var(--subtexto);
    line-height: 1.5;
}
.bloco-afirmacao .label-q {
    font-family: var(--fonte);
    font-size: 0.95rem;
    letter-spacing: 0.5px;
    text-transform: none;
    color: var(--texto);
    margin-bottom: 0.6rem;
    font-weight: 600;
}

/* ── Card de resultado ─── */
.card-resultado {
    background: var(--bg2);
    border: 1px solid var(--borda);
    border-radius: 8px;
    overflow: hidden;
    margin: 0.4rem 0 0.8rem;
}
.card-resultado-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem 1.4rem;
    border-bottom: 1px solid var(--borda);
    background: var(--bg3);
}
.card-resultado-body {
    padding: 1.2rem 1.4rem;
    font-size: 0.95rem;
    line-height: 1.75;
    color: var(--texto);
}

/* ── Veredito badges ─── */
.veredito {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    font-family: var(--mono);
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    padding: 0.3rem 0.8rem;
    border-radius: 4px;
    text-transform: uppercase;
    white-space: nowrap;
}
.v-mito       { background: rgba(255,45,85,0.15);  color: var(--vermelho); border: 1px solid var(--vermelho); }
.v-verdade    { background: rgba(0,255,136,0.1);   color: var(--verde);    border: 1px solid var(--verde); }
.v-parcial    { background: rgba(255,184,0,0.12);  color: var(--amarelo);  border: 1px solid var(--amarelo); }
.v-panico     { background: rgba(77,158,255,0.12); color: var(--azul);     border: 1px solid var(--azul); }
.v-inconcl    { background: rgba(155,93,229,0.12); color: var(--roxo);     border: 1px solid var(--roxo); }
.v-default    { background: rgba(136,136,170,0.1); color: var(--subtexto); border: 1px solid var(--borda2); }

/* ── Fontes / documentos ─── */
.fontes-container {
    background: var(--bg3);
    border: 1px solid var(--borda);
    border-radius: 6px;
    padding: 0.9rem 1.1rem;
    margin: 0.2rem 0 1.2rem;
}
.fontes-titulo {
    font-family: var(--mono);
    font-size: 0.95rem;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: var(--texto);
    margin-bottom: 0.8rem;
}
.fonte-row {
    display: flex;
    align-items: flex-start;
    gap: 0.7rem;
    padding: 0.45rem 0;
    border-bottom: 1px solid var(--borda);
    font-size: 0.82rem;
    line-height: 1.4;
    word-break: break-word;
}
.fonte-row:last-child { border-bottom: none; }
.fonte-badge {
    font-family: var(--mono);
    font-size: 0.58rem;
    background: var(--borda);
    color: var(--subtexto);
    padding: 2px 6px;
    border-radius: 3px;
    white-space: nowrap;
    flex-shrink: 0;
    margin-top: 1px;
}
.fonte-badge.publico { background: rgba(255,45,85,0.2); color: var(--vermelho); }
.fonte-data { color: var(--subtexto); font-family: var(--mono); font-size: 0.72rem; flex-shrink: 0; }
.fonte-link a { color: var(--azul) !important; text-decoration: none !important; }
.fonte-link a:hover { color: var(--texto) !important; text-decoration: underline !important; }
.fonte-url { color: var(--borda2); font-size: 0.72rem; font-family: var(--mono); }

/* ── Ecrã de boas-vindas ─── */
.welcome {
    border: 1px solid var(--borda);
    border-radius: 8px;
    padding: 0.5rem 1.7rem;
    text-align: center;
    background: var(--bg2);
    margin: 0.4rem 0 0.75rem;
    margin-top: -0.04rem;
    position: relative;
    overflow: hidden;
}
.welcome::before {
    content: '';
    position: absolute;
    top: -50%; left: -50%;
    width: 200%; height: 200%;
    background: radial-gradient(circle at 50% 50%, rgba(255,45,85,0.04) 0%, transparent 60%);
    pointer-events: none;
}
.welcome-icon { font-size: 1.5rem; margin-bottom: 0.1rem; }
.welcome h2 {
    font-family: var(--mono) !important;
    font-size: 1.05rem !important;
    font-weight: 700 !important;
    color: var(--texto) !important;
    margin-bottom: 0.55rem !important;
    letter-spacing: 1px;
}
.welcome p { color: var(--subtexto); font-size: 0.84rem; line-height: 1.55; max-width: 460px; margin: 0 auto; }

/* ── Painel lateral de instruções ─── */
.painel-info {
    background: var(--bg2);
    border: 1px solid var(--borda);
    border-radius: 8px;
    padding: 1.2rem;
    font-size: 0.82rem;
    line-height: 1.65;
    position: sticky;
    top: 1rem;
}
.painel-info h4 {
    font-family: var(--mono) !important;
    font-size: 0.75rem !important;
    font-weight: 700 !important;
    color: var(--vermelho) !important;
    letter-spacing: 2px;
    text-transform: uppercase;
    border-bottom: 1px solid var(--borda);
    padding-bottom: 0.5rem;
    margin-bottom: 0.8rem !important;
}
.painel-info .step {
    display: flex; gap: 0.7rem; margin-bottom: 0.8rem; align-items: flex-start;
}
.step-num {
    font-family: var(--mono);
    font-size: 0.7rem;
    color: var(--vermelho);
    background: rgba(255,45,85,0.1);
    border: 1px solid rgba(255,45,85,0.3);
    border-radius: 3px;
    padding: 1px 6px;
    flex-shrink: 0;
    margin-top: 1px;
}
.painel-info .step p { margin: 0; color: var(--subtexto); font-size: 0.8rem; }
.painel-info .step strong { color: var(--texto); }
.legend-item {
    display: flex; align-items: center; gap: 0.5rem;
    margin: 0.3rem 0; font-size: 0.75rem; color: var(--subtexto);
}
.legend-dot {
    width: 8px; height: 8px; border-radius: 2px; flex-shrink: 0;
}

/* ── Área de input ─── */
.input-area {
    padding: 1rem 0 0.3rem !important;
    margin-top: 0.5rem !important;
    background: transparent !important; 
    border-top: none !important;        
}

/* ── Copiar botão ─── */
.copy-btn {
    background: var(--bg3) !important;
    border: 1px solid var(--borda) !important;
    color: var(--subtexto) !important;
    font-family: var(--mono) !important;
    font-size: 0.68rem !important;
    padding: 2px 10px !important;
    border-radius: 3px;
    cursor: pointer;
    transition: all 0.1s;
    float: right;
    margin-bottom: 0.4rem;
}
.copy-btn:hover { border-color: var(--borda2) !important; color: var(--texto) !important; }

/* ── Markdown overrides ─── */
.card-resultado-body h1,.card-resultado-body h2,.card-resultado-body h3 {
    color: var(--texto) !important; font-family: var(--fonte) !important;
    margin-top: 1rem !important; margin-bottom: 0.4rem !important;
}
.card-resultado-body strong { color: var(--texto); }
.card-resultado-body em { color: var(--subtexto); }
.card-resultado-body ul, .card-resultado-body ol { padding-left: 1.2rem; }
.card-resultado-body li { margin-bottom: 0.3rem; }
.card-resultado-body code {
    background: var(--bg3); color: var(--verde);
    padding: 1px 5px; border-radius: 3px; font-family: var(--mono); font-size: 0.85em;
}
.card-resultado-body a { color: var(--azul) !important; }
.secao-resposta {
    font-family: var(--mono);
    font-size: 1.05rem;
    font-weight: 700;
    margin: 1.35rem 0 0.65rem;
    padding-bottom: 0.35rem;
    border-bottom: 1px solid var(--borda);
}
.secao-1 { color: var(--vermelho); }
.secao-2 { color: var(--verde); }
.secao-3 { color: var(--amarelo); }
.secao-4 { color: var(--azul); }
.secao-5 { color: var(--roxo); }
.paragrafo-resposta {
    margin: 0.55rem 0;
    line-height: 1.7;
}
.bullet-resposta {
    display: grid;
    grid-template-columns: 0.9rem 1fr;
    gap: 0.55rem;
    margin: 0.45rem 0;
    line-height: 1.65;
}
.bullet-resposta::before {
    content: "•";
    color: var(--vermelho);
    font-family: var(--mono);
}
.ano-resposta {
    display: inline-block;
    margin: 0.9rem 0 0.25rem;
    padding: 0.12rem 0.45rem;
    border: 1px solid var(--borda2);
    border-radius: 3px;
    color: var(--texto);
    background: var(--bg3);
    font-family: var(--mono);
    font-size: 0.78rem;
    font-weight: 700;
}
.doc-link {
    color: var(--azul) !important;
    font-family: var(--mono);
    font-size: 0.88em;
    text-decoration: none !important;
    border-bottom: 1px solid rgba(77,158,255,0.45);
}
.doc-link:hover {
    color: var(--texto) !important;
    border-bottom-color: var(--texto);
}
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────

defaults = {
    "historico":       [],   
    "historico_llm":   [],   
    "input_actual":    "",
    "n_input":         0,
    "total_analisados": 0,
    "total_mitos":     0,
    "idioma":          "pt", # Adicionado pela colega
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ── Helpers de Tradução ───────────────────────────────────────────────────────

TEXTOS = {
    "pt": {
        "language": "Idioma",
        "tagline": "Mapa de narrativas históricas · Arquivo.pt × IA",
        "analysed": "Analisados",
        "sources": "Fontes",
        "sidebar_caption": "O DECEPTIO é uma ferramenta para analisar como uma narrativa mudou ao longo do tempo.\n\nPara tal, analisa artigos do Arquivo.pt, extrai alegações e cria timelines. Avalia a fiabilidade das fontes, encontra contradições e diferenças revelando mudanças numa narrativa ao longo do tempo.",
        "time_filter": "📅 Filtro Temporal",
        "time_filter_caption": "Procura apenas documentos dentro do período selecionado.",
        "enable_year_filter": "Ativar procura por anos",
        "from": "De",
        "to": "Até",
        "test_cases": "🧪 Casos de Teste",
        "test_cases_caption": "Temas históricos para explorar.",
        "cases": [
            "Bug do Ano 2000 em Portugal",
            "Entrada do Euro em Portugal",
            "EXPO 98 e impacto económico",
            "Internet em Portugal nos anos 90",
            "Crise financeira de 2008 nos bancos portugueses",
            "Ponte Vasco da Gama na imprensa portuguesa",
            "Gripe A nos media portugueses",
            "Ensino superior e propinas em Portugal",
        ],
        "clear": "🗑️ Limpar análises",
        "sidebar_footer": "**DECEPTIO** — Candidatura ao Prémio Arquivo.pt 2026\n\nUsa a API do [Arquivo.pt](https://arquivo.pt) e Inteligência Artificial (LLMs) numa arquitetura RAG de 4 camadas. Dá prioridade a fontes `.pt` e textos do [Público](https://publico.pt).",
        "how_it_works": "⚙ Como Funciona",
        "c1_title": "Query Expansion",
        "c1_text": "A IA gera 3 queries otimizadas para a pergunta realizada pelo utilizador e utiliza-as para navegar o Arquivo.pt.",
        "c2_title": "Retrieval",
        "c2_text": "Recupera até 45 documentos de diferentes fontes e atribui pontos a cada um baseado na sua relevância. Atribui pontos bónus a fontes <code>.pt</code> e <code>publico.pt</code>.",
        "c3_title": "Re-ranking",
        "c3_text": "Com base nas pontuações atribuídas, seleciona os artigos mais relevantes.",
        "c4_title": "Análise IA",
        "c4_text": "Extrai alegações, organiza a timeline e identifica diferenças.",
        "expected": "Resultado esperado",
        "timeline": "Linha temporal principal",
        "claims": "Alegações por ano e fonte",
        "reliability": "Fiabilidade das fontes",
        "disagreements": "Contradições e diferenças",
        "change": "Mudança da narrativa",
        "analysis_badge": "ANÁLISE DE NARRATIVA",
        "submitted_topic": "Tema submetido",
        "copy": "📋 Copiar",
        "copied": "✓ Copiado",
        "copy_error": "Erro",
        "archive_sources": "📁 Fontes do Arquivo.pt",
        "welcome_title": "ANÁLISE DE NARRATIVAS HISTÓRICAS",
        "welcome_text": "Introduz um tema e o <strong>DECEPTIO</strong> encontra artigos relevantes no <strong>Arquivo.pt</strong>, extrai alegações, organiza uma timeline e destaca diferenças entre fontes.",
        "topic_label": "Tema",
        "topic_placeholder": "Ex: Bug do Ano 2000 em Portugal...",
        "analyse": "ANALISAR",
        "spinner": "🔍 A pesquisar artigos no Arquivo.pt e a construir a análise...",
        "empty_warning": "✏️ Escreve um tema para analisar.",
    },
    "en": {
        "language": "Language",
        "tagline": "Historical narrative map · Arquivo.pt × AI",
        "analysed": "Analysed",
        "sources": "Sources",
        "sidebar_caption": "DECEPTIO is a tool for analyzing how a narrative changed over time. To do this, it analyzes articles from Arquivo.pt, extracts claims and creates timelines. It evaluates source reliability, finds contradictions and disagreements, revealing changes in a narrative over time.",
        "time_filter": "📅 Time Filter",
        "time_filter_caption": "Search only for documents within the selected period.",
        "enable_year_filter": "Enable search by year",
        "from": "From",
        "to": "To",
        "test_cases": "🧪 Test Cases",
        "test_cases_caption": "Historical topics to explore.",
        "cases": [
            "Year 2000 bug in Portugal",
            "Introduction of the Euro in Portugal",
            "EXPO 98 and economic impact",
            "Internet in Portugal in the 1990s",
            "2008 financial crisis in Portuguese banks",
            "Vasco da Gama Bridge in the Portuguese press",
            "Swine flu in Portuguese media",
            "Higher education and tuition fees in Portugal",
        ],
        "clear": "🗑️ Clear analyses",
        "sidebar_footer": "**DECEPTIO** — Arquivo.pt Award 2026 Application\n\nUses the [Arquivo.pt](https://arquivo.pt) API and Artificial Intelligence (LLMs) in a 4-layer RAG architecture. Prioritizes `.pt` sources and texts from [Público](https://publico.pt).",
        "how_it_works": "⚙ How It Works",
        "c1_title": "Query Expansion",
        "c1_text": "The AI generates 3 optimized queries for the user's question and uses them to navigate Arquivo.pt.",
        "c2_title": "Retrieval",
        "c2_text": "Retrieves up to 45 documents from different sources and assigns points to each based on its relevance. Awards bonus points to <code>.pt</code> and <code>publico.pt</code> sources.",
        "c3_title": "Re-ranking",
        "c3_text": "Based on the assigned scores, selects the most relevant articles.",
        "c4_title": "AI Analysis",
        "c4_text": "Extracts claims, organizes the timeline and identifies disagreements.",
        "expected": "Expected output",
        "timeline": "Main timeline",
        "claims": "Claims by year and source",
        "reliability": "Source reliability",
        "disagreements": "Contradictions and disagreements",
        "change": "Narrative change",
        "analysis_badge": "NARRATIVE ANALYSIS",
        "submitted_topic": "Submitted topic",
        "copy": "📋 Copy",
        "copied": "✓ Copied",
        "copy_error": "Error",
        "archive_sources": "📁 Arquivo.pt Sources",
        "welcome_title": "HISTORICAL NARRATIVE ANALYSIS",
        "welcome_text": "Enter a topic and <strong>DECEPTIO</strong> finds relevant articles in <strong>Arquivo.pt</strong>, extracts claims, organizes a timeline, and highlights disagreements between sources.",
        "topic_label": "Topic",
        "topic_placeholder": "Ex: Year 2000 bug in Portugal...",
        "analyse": "ANALYSE",
        "spinner": "🔍 Searching Arquivo.pt articles and building the analysis...",
        "empty_warning": "✏️ Write a topic to analyse.",
    },
}

def tr(chave: str):
    return TEXTOS.get(st.session_state.idioma, TEXTOS["pt"]).get(chave, chave)

def classificar_veredito(texto: str) -> tuple[str, str, str]:
    if not any(x in texto for x in ["⚠️", "⏳", "📭", "📄", "Erro", "Error", "Limite de pedidos", "Request limit"]):
        return "v-default", "🧭", tr("analysis_badge")

    t = texto.upper()
    if st.session_state.idioma == "en":
        if any(x in t for x in ["AUTHENTICATION", "API KEY", "GEMINI_API_KEY"]):
            return "v-inconcl", "⚠️", "AUTHENTICATION ERROR"
        if any(x in t for x in ["REQUEST LIMIT", "RATE LIMIT", "QUOTA"]):
            return "v-inconcl", "⏳", "RATE LIMIT"
        if any(x in t for x in ["MODEL", "UNAVAILABLE"]):
            return "v-inconcl", "⚠️", "MODEL UNAVAILABLE"
        if any(x in t for x in ["NO ARTICLE", "NO DOCUMENT", "NO RESULTS"]):
            return "v-inconcl", "📭", "NO SOURCES"

    if any(x in t for x in ["MITO HISTÓRICO", "MITO HISTORICO", "FALSO", "DESINFORMAÇÃO", "DESINFORMACAO"]):
        return "v-mito",   "🔴", "MITO HISTÓRICO"
    if any(x in t for x in ["PÂNICO INJUSTIFICADO", "PANICO INJUSTIFICADO", "EXAGERADO", "ALARME INJUSTIFICADO"]):
        return "v-panico", "🔵", "PÂNICO INJUSTIFICADO"
    if any(x in t for x in ["VERDADE PARCIAL", "PARCIALMENTE VERDADEIRO", "PARCIALMENTE CORRETO", "PARCIALMENTE CORRECTO"]):
        return "v-parcial","🟡", "VERDADE PARCIAL"
    if any(x in t for x in ["FACTO COMPROVADO", "FACTO CONFIRMADO", "VERDADE CONFIRMADA", "VERDADEIRO", "CONFIRMADO"]):
        return "v-verdade","🟢", "FACTO CONFIRMADO"
    if any(x in t for x in ["INCONCLUSIVO", "INFORMAÇÃO INSUFICIENTE", "INFORMACAO INSUFICIENTE", "SEM DADOS"]):
        return "v-inconcl","🟣", "INCONCLUSIVO"
    return "v-default", "🧭", tr("analysis_badge")

def html_fontes(fontes: list[dict]) -> str:
    if not fontes:
        return ""
    html = f'<div class="fontes-container"><div class="fontes-titulo">{tr("archive_sources")}</div>'
    for f in fontes:
        link   = f.get("link_arch", "#") or "#"
        titulo = f.get("titulo", "Sem título")[:85]
        data   = f.get("data", "")
        num    = f.get("numero", "")
        url_o  = f.get("url_orig", "")
        badge_cls = "publico" if "publico.pt" in url_o.lower() else ""
        html += (
            f'<div class="fonte-row">'
            f'<span class="fonte-badge {badge_cls}">DOC {num}</span>'
            f'<span class="fonte-data">{data}</span>'
            f'<span class="fonte-link">'
            f'<a href="{link}" target="_blank" rel="noopener">{titulo}</a>'
            f'<br><span class="fonte-url">{url_o[:70]}</span>'
            f'</span>'
            f'</div>'
        )
    html += '</div>'
    return html

def linkar_docs(texto: str, fontes: list[dict]) -> str:
    links = {str(f.get("numero")): (f.get("link_arch") or "#") for f in fontes}

    def link(n: str) -> str:
        return f"[DOC {n}]({links[n]})" if n in links else f"DOC {n}"

    def sub_ref(m):
        return link(m.group(1))

    def sub_lista(m):
        nums = re.findall(r"\d+", m.group(1))
        if not nums:
            return m.group(0)
        return ", ".join(link(n) for n in nums)

    texto = re.sub(r"\[\s*((?:DOC(?:UMENTO)?S?\s*:?\s*)?\d+(?:\s*(?:,|;|e|and)\s*(?:DOC(?:UMENTO)?S?\s*:?\s*)?\d+)+)\s*\](?!\()", sub_lista, texto, flags=re.IGNORECASE)
    texto = re.sub(r"\[\[\s*DOC(?:UMENTO)?\s*:?\s*(\d+)\s*\]\](?!\()", sub_ref, texto, flags=re.IGNORECASE)
    texto = re.sub(r"\[\s*DOC(?:UMENTO)?\s*:?\s*(\d+)\s*\](?!\()", sub_ref, texto, flags=re.IGNORECASE)
    return re.sub(r"(?<!\[)\bDOC(?:UMENTO)?\s*:?\s*(\d+)\b(?!\]\()", sub_ref, texto, flags=re.IGNORECASE)

def colorir_titulos(texto: str) -> str:
    # 1. Vermelho
    texto = re.sub(r"\*?\*?1\. Linha temporal principal\*?\*?", r"<h4 style='color: var(--vermelho); margin-top: 1.5rem;'>1. Linha temporal principal</h4>", texto)
    # EN version
    texto = re.sub(r"\*?\*?1\. Main timeline\*?\*?", r"<h4 style='color: var(--vermelho); margin-top: 1.5rem;'>1. Main timeline</h4>", texto)
    
    # 2. Verde
    texto = re.sub(r"\*?\*?2\. Alega[cç][oõ]es principais.*\*\*?", r"<h4 style='color: var(--verde); margin-top: 1.5rem;'>2. Alegações por ano e fonte</h4>", texto)
    # EN version
    texto = re.sub(r"\*?\*?2\. Claims by year and source.*\*\*?", r"<h4 style='color: var(--verde); margin-top: 1.5rem;'>2. Claims by year and source</h4>", texto)
    
    # 3. Amarelo
    texto = re.sub(r"\*?\*?3\. Fiabilidade das fontes\*?\*?", r"<h4 style='color: var(--amarelo); margin-top: 1.5rem;'>3. Fiabilidade das fontes</h4>", texto)
    # EN version
    texto = re.sub(r"\*?\*?3\. Source reliability\*?\*?", r"<h4 style='color: var(--amarelo); margin-top: 1.5rem;'>3. Source reliability</h4>", texto)
    
    # 4. Azul
    texto = re.sub(r"\*?\*?4\. Contradi[cç][oõ]es e diferenças\*?\*?", r"<h4 style='color: var(--azul); margin-top: 1.5rem;'>4. Contradições e diferenças</h4>", texto)
    # EN version
    texto = re.sub(r"\*?\*?4\. Contradictions and disagreements\*?\*?", r"<h4 style='color: var(--azul); margin-top: 1.5rem;'>4. Contradictions and disagreements</h4>", texto)
    
    # 5. Roxo
    texto = re.sub(r"\*?\*?5\. Mudan[cç]a da narrativa\*?\*?", r"<h4 style='color: var(--roxo); margin-top: 1.5rem;'>5. Mudança da narrativa</h4>", texto)
    # EN version
    texto = re.sub(r"\*?\*?5\. Narrative change\*?\*?", r"<h4 style='color: var(--roxo); margin-top: 1.5rem;'>5. Narrative change</h4>", texto)
    
    return texto


def formatar_resposta_html(texto: str, fontes: list[dict]) -> str:
    """Renderiza a resposta como HTML consistente, com DOC links reais."""
    links = {str(f.get("numero")): (f.get("link_arch") or "#") for f in fontes}

    def normalizar(txt: str) -> str:
        txt = txt.strip()
        if len(txt) >= 2 and txt[0] == txt[-1] and txt[0] in {"'", '"'}:
            txt = txt[1:-1].strip()
        txt = txt.replace("\r\n", "\n").replace("\r", "\n")
        txt = re.sub(r"\s+-\s+(?=(?:\d{4}:|[A-ZÁÉÍÓÚÂÊÔÃÕÇ]))", "\n- ", txt)
        txt = re.sub(r"\s+\*\s+(?=(?:\d{4}:|[A-ZÁÉÍÓÚÂÊÔÃÕÇ]))", "\n* ", txt)
        txt = re.sub(r"(?<!\n)(\*\*?[1-5]\.\s*)", r"\n\1", txt)
        txt = re.sub(
            r"(?<!\n)(?<!DOC\s)(?<!DOC\s)(\b(?:19|20)\d{2}:)",
            r"\n\1",
            txt,
        )
        return txt

    def doc_link(n: str) -> str:
        if n in links:
            return (
                f'<a class="doc-link" href="{html.escape(links[n], quote=True)}" '
                f'target="_blank" rel="noopener">DOC {n}</a>'
            )
        return f"DOC {n}"

    def linkificar_docs(txt: str) -> str:
        placeholders: dict[str, str] = {}

        def guardar(anchor: str) -> str:
            key = f"@@DOC_LINK_{len(placeholders)}@@"
            placeholders[key] = anchor
            return key

        def markdown_doc(m):
            n = m.group(1)
            url = m.group(2)
            return guardar(
                f'<a class="doc-link" href="{html.escape(url, quote=True)}" '
                f'target="_blank" rel="noopener">DOC {n}</a>'
            )

        def lista_doc(m):
            nums = re.findall(r"\d+", m.group(1))
            return guardar(", ".join(doc_link(n) for n in nums))

        def ref_doc(m):
            return guardar(doc_link(m.group(1)))

        txt = re.sub(
            r"\[\s*DOC(?:UMENTO)?\s*:?\s*(\d+)\s*\]\(([^)]+)\)",
            markdown_doc,
            txt,
            flags=re.IGNORECASE,
        )
        txt = re.sub(
            r"\[\s*((?:DOC(?:UMENTO)?S?\s*:?\s*)?\d+(?:\s*(?:,|;|e|and)\s*(?:DOC(?:UMENTO)?S?\s*:?\s*)?\d+)+)\s*\](?!\()",
            lista_doc,
            txt,
            flags=re.IGNORECASE,
        )
        txt = re.sub(r"\[\[\s*DOC(?:UMENTO)?\s*:?\s*(\d+)\s*\]\](?!\()", ref_doc, txt, flags=re.IGNORECASE)
        txt = re.sub(r"\[\s*DOC(?:UMENTO)?\s*:?\s*(\d+)\s*\](?!\()", ref_doc, txt, flags=re.IGNORECASE)
        txt = re.sub(r"(?<!\[)\bDOC(?:UMENTO)?\s*:?\s*(\d+)\b(?!\]\()", ref_doc, txt, flags=re.IGNORECASE)

        escaped = html.escape(txt)
        for key, anchor in placeholders.items():
            escaped = escaped.replace(key, anchor)
        escaped = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", escaped)
        escaped = escaped.replace("*", "")
        return escaped

    def secao(linha: str) -> tuple[int, str] | None:
        limpa = linha.strip()
        limpa = re.sub(r"^[\s*#-]+", "", limpa)
        limpa = re.sub(r"[\s*:*.]+$", "", limpa).strip()
        padroes = [
            (1, r"^(?:1\.\s*)?(?:Linha temporal principal|Main timeline)\s*:?$"),
            (2, r"^(?:2\.\s*)?(?:Alega[cç][oõ]es.*fonte|Claims by year and source|Main claims by year and source|Main allegations by year and source|Main allegations.*)\s*:?$"),
            (3, r"^(?:3\.\s*)?(?:Fiabilidade das fontes|Source reliability|Reliability of sources|Reliability of the sources)\s*:?$"),
            (4, r"^(?:4\.\s*)?(?:Contradi[cç][oõ]es.*|Contradictions and disagreements)\s*:?$"),
            (5, r"^(?:5\.\s*)?(?:Mudan[cç]a da narrativa|Narrative change)\s*:?$"),
        ]
        titulos = {
            1: tr("timeline"),
            2: tr("claims"),
            3: tr("reliability"),
            4: tr("disagreements"),
            5: tr("change"),
        }
        for idx, pattern in padroes:
            if re.match(pattern, limpa, flags=re.IGNORECASE):
                return idx, f'<div class="secao-resposta secao-{idx}">{html.escape(titulos[idx])}</div>'
        return None

    partes = []
    secao_atual = 0
    for linha in normalizar(texto).splitlines():
        linha = linha.strip()
        if not linha or linha == "*":
            continue
        secao_detectada = secao(linha)
        if secao_detectada:
            secao_atual, bloco_secao = secao_detectada
            partes.append(bloco_secao)
            continue

        linha = re.sub(r"^\*+|\*+$", "", linha).strip()
        ano_match = re.match(r"^((?:19|20)\d{2}):\s*(.*)$", linha)
        if ano_match:
            ano, resto = ano_match.groups()
            partes.append(f'<div class="ano-resposta">{ano}</div>')
            if resto.strip():
                partes.append(f'<div class="bullet-resposta"><div>{linkificar_docs(resto.strip())}</div></div>')
            continue

        if re.match(r"^[-•*]\s+", linha):
            conteudo = re.sub(r"^[-•*]\s+", "", linha).strip()
            conteudo = re.sub(r"^\*+|\*+$", "", conteudo).strip()
            partes.append(f'<div class="bullet-resposta"><div>{linkificar_docs(conteudo)}</div></div>')
        elif secao_atual == 2 and linha:
            partes.append(f'<div class="bullet-resposta"><div>{linkificar_docs(linha)}</div></div>')
        else:
            partes.append(f'<div class="paragrafo-resposta">{linkificar_docs(linha)}</div>')
    return "\n".join(partes)

# ── Cabeçalho ─────────────────────────────────────────────────────────────────

n_analisados = st.session_state.total_analisados
n_mitos      = st.session_state.total_mitos

st.markdown(f"""
<div class="header">
  <div class="header-grid">
    <div class="logo-area">
      <div class="logo-icon">🔍</div>
      <div class="logo-text">
        <h1>DECEPTIO</h1>
        <div class="tagline">{tr("tagline")}</div>
      </div>
    </div>
    <div class="header-stats">
      <div class="stat-pill">
        <div class="stat-num">{n_analisados}</div>
        <div class="stat-label">{tr("analysed")}</div>
      </div>
      <div class="stat-pill">
        <div class="stat-num" style="color:var(--vermelho)">{n_mitos}</div>
        <div class="stat-label">{tr("sources")}</div>
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🔍 DECEPTIO")
    st.radio(
        tr("language"),
        options=["pt", "en"],
        format_func=lambda x: "Português" if x == "pt" else "English",
        key="idioma",
        horizontal=True,
    )
    st.markdown(f"""
    <div style="text-align: left; font-size: 0.9rem; line-height: 1.6; color: #8888AA; margin-top: 0.5rem;">
      <p>{tr("sidebar_caption")}</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    st.markdown(f"#### {tr('time_filter')}")
    st.caption(tr("time_filter_caption"))
    usar_filtro = st.checkbox(tr("enable_year_filter"), value=False)
    from_year, to_year = None, None
    if usar_filtro:
        c1, c2 = st.columns(2)
        with c1:
            from_year = str(st.number_input(tr("from"), min_value=1996, max_value=2025, value=1998, step=1))
        with c2:
            to_year   = str(st.number_input(tr("to"), min_value=1996, max_value=2025, value=2005, step=1))

    st.markdown("---")
    st.markdown(f"#### {tr('test_cases')}")
    st.caption(tr("test_cases_caption"))

    casos = tr("cases")

    for i, caso in enumerate(casos):
        if st.button(f"🧪 {caso[:50]}…", key=f"caso_{i}"):
            st.session_state.input_actual = caso
            st.session_state.n_input += 1
            st.rerun()

    st.markdown("---")
    if st.button(tr("clear"), use_container_width=True):
        st.session_state.historico      = []
        st.session_state.historico_llm  = []
        st.session_state.input_actual   = ""
        st.session_state.total_analisados = 0
        st.session_state.total_mitos    = 0
        st.rerun()

    st.markdown("---")
    st.caption(tr("sidebar_footer"))


# ── Layout principal ──────────────────────────────────────────────────────────

col_main, col_side = st.columns([3, 1])

# ── Painel lateral de instruções ──────────────────────────────────────────────

with col_side:
    st.markdown(f"""
    <div class="painel-info">
      <h4>{tr("how_it_works")}</h4>

      <div class="step">
        <span class="step-num">C1</span>
        <p><strong>{tr("c1_title")}</strong><br>{tr("c1_text")}</p>
      </div>
      <div class="step">
        <span class="step-num">C2</span>
        <p><strong>{tr("c2_title")}</strong><br>{tr("c2_text")}</p>
      </div>
      <div class="step">
        <span class="step-num">C3</span>
        <p><strong>{tr("c3_title")}</strong><br>{tr("c3_text")}</p>
      </div>
      <div class="step">
        <span class="step-num">C4</span>
        <p><strong>{tr("c4_title")}</strong><br>{tr("c4_text")}</p>
      </div>

      <hr style="border-color: #2A2A38; margin: 0.8rem 0;">

      <div style="font-size:0.72rem; color: #8888AA; margin-bottom:0.5rem; text-transform:uppercase; letter-spacing:1px; font-family: var(--mono);">{tr("expected")}</div>
      <div class="legend-item"><div class="legend-dot" style="background:#FF2D55"></div> {tr("timeline")}</div>
      <div class="legend-item"><div class="legend-dot" style="background:#00FF88"></div> {tr("claims")}</div>
      <div class="legend-item"><div class="legend-dot" style="background:#FFB800"></div> {tr("reliability")}</div>
      <div class="legend-item"><div class="legend-dot" style="background:#4D9EFF"></div> {tr("disagreements")}</div>
      <div class="legend-item"><div class="legend-dot" style="background:#9B5DE5"></div> {tr("change")}</div>
    </div>
    """, unsafe_allow_html=True)


# ── Área de conversa ──────────────────────────────────────────────────────────

with col_main:

    if st.session_state.historico:
        for afirmacao, resposta, fontes in st.session_state.historico:
            css, emoji, label = classificar_veredito(resposta)

            # Tema do utilizador
            st.markdown(
                f'<div class="bloco-afirmacao">'
                f'<div class="label-q">{tr("submitted_topic")}</div>'
                f'<div style="font-size: 1rem; color: var(--texto); display: flex; align-items: center; gap: 0.5rem;">'
                f'<span style="color: var(--vermelho);">▶</span> {afirmacao}'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True
            )

            resp_b64 = base64.b64encode(resposta.encode("utf-8")).decode("ascii")
            
            bloco_completo = f"""
<div class="card-resultado">
    <div class="card-resultado-header">
        <span class="veredito {css}">{emoji} {label}</span>
        <span style="font-family:var(--mono);font-size:0.7rem;color:var(--subtexto);margin-left:auto;">DECEPTIO · Arquivo.pt</span>
    </div>
    <div class="card-resultado-body">
        <div style="text-align:right;margin-bottom:0.5rem;">
            <button class="copy-btn" data-copy="{resp_b64}"
              onclick="
                const bytes = Uint8Array.from(atob(this.dataset.copy), c => c.charCodeAt(0));
                const text = new TextDecoder().decode(bytes);
                navigator.clipboard.writeText(text).then(
                  () => {{this.textContent='{tr("copied")}';setTimeout(() => this.textContent='{tr("copy")}',2000)}},
                  () => {{this.textContent='{tr("copy_error")}';setTimeout(() => this.textContent='{tr("copy")}',2000)}}
                                );
                            ">{tr("copy")}</button>
        </div>

{formatar_resposta_html(resposta, fontes)}

    </div>
</div>
"""
            st.markdown(bloco_completo, unsafe_allow_html=True)

            # Fontes
            st.markdown(html_fontes(fontes), unsafe_allow_html=True)
            st.markdown("<hr>", unsafe_allow_html=True)

    else:
        # Ecrã de boas-vindas
        st.markdown(f"""
        <div class="welcome">
          <div class="welcome-icon">🔍</div>
          <h2>{tr("welcome_title")}</h2>
          <p>{tr("welcome_text")}</p>
        </div>
        """, unsafe_allow_html=True)

    # ── Campo de input ─────────────────────────────────────────────────────────
    st.markdown('<div class="input-area">', unsafe_allow_html=True)
    col_in, col_btn = st.columns([5, 1])

    with col_in:
        input_val = st.text_input(
            label            = tr("topic_label"),
            value            = st.session_state.input_actual,
            placeholder      = tr("topic_placeholder"),
            label_visibility = "collapsed",
            key              = f"input_{st.session_state.n_input}",
        )
    with col_btn:
        analisar = st.button(tr("analyse"), use_container_width=True, type="primary")

    st.markdown("</div>", unsafe_allow_html=True)


# ── Processamento ─────────────────────────────────────────────────────────────

texto_final = input_val.strip() if input_val.strip() else st.session_state.input_actual.strip()

if analisar and texto_final:
    st.session_state.input_actual = texto_final

    with col_main:
        with st.spinner(tr("spinner")):
            resposta, fontes = analisar_topico(
                topico    = texto_final,
                from_year = from_year if usar_filtro else None,
                to_year   = to_year   if usar_filtro else None,
                historico = st.session_state.historico_llm,
                idioma    = st.session_state.idioma,
            )

    # Atualiza contadores
    st.session_state.total_analisados += 1
    if fontes:
        st.session_state.total_mitos += len(fontes)

    st.session_state.historico.append((texto_final, resposta, fontes))
    st.session_state.historico_llm.append({"role": "user",  "content": texto_final})
    st.session_state.historico_llm.append({"role": "model", "content": resposta})

    st.session_state.input_actual = ""
    st.session_state.n_input += 1
    st.rerun()

elif analisar:
    st.warning(tr("empty_warning"))
