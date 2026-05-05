"""
================================================================================
DECEPTIO - Interface Web (Streamlit)
================================================================================
Ferramenta de analise de narrativas historicas usando o Arquivo.pt.
Prémio Arquivo.pt 2026

Para correr:
    export GEMINI_API_KEY="AIzaSy..."
    streamlit run app.py
================================================================================
"""

import streamlit as st
import re
import base64
from deceptio_rag import analisar_topico

# ── Configuração ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title = "DECEPTIO - Analise de Narrativas Historicas",
    page_icon  = "🧭",
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
[data-testid="collapsedControl"] { opacity: 1 !important; visibility: visible !important; }

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
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
}
.logo-area { display: flex; align-items: center; gap: 1.2rem; }
.logo-icon {
    width: 52px; height: 52px;
    background: var(--vermelho);
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.6rem;
    flex-shrink: 0;
    box-shadow: 0 0 20px rgba(255,45,85,0.4);
}
.logo-text h1 {
    font-family: var(--mono) !important;
    font-size: 2.2rem !important;
    font-weight: 700 !important;
    letter-spacing: 6px !important;
    color: var(--texto) !important;
    margin: 0 !important;
    line-height: 1 !important;
}
.logo-text .tagline {
    font-family: var(--mono);
    font-size: 0.65rem;
    color: var(--vermelho);
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-top: 0.3rem;
}
.header-stats {
    display: flex;
    gap: 1.5rem;
    flex-shrink: 0;
}
.stat-pill {
    text-align: center;
    padding: 0.4rem 1rem;
    border: 1px solid var(--borda);
    border-radius: 4px;
    background: var(--bg2);
}
.stat-num {
    font-family: var(--mono);
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--verde);
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
.stTextInput > div > div > input {
    background: var(--bg2) !important;
    border: 1px solid var(--borda2) !important;
    border-radius: 6px !important;
    color: var(--texto) !important;
    font-family: var(--fonte) !important;
    font-size: 1rem !important;
    padding: 0.7rem 1rem !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--vermelho) !important;
    box-shadow: 0 0 0 2px rgba(255,45,85,0.15) !important;
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
    font-size: 0.65rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.5px !important;
    padding: 0.65rem 0.55rem !important;
    text-align: center !important;
    white-space: nowrap !important;
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
    font-family: var(--mono);
    font-size: 0.6rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--borda2);
    margin-bottom: 0.4rem;
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
    font-size: 0.6rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--subtexto);
    margin-bottom: 0.6rem;
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
    border-top: 1px solid var(--borda);
    padding: 1rem 0 0.3rem;
    margin-top: 1.5rem;
    background: var(--bg);
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
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────

defaults = {
    "historico":       [],   # lista de (afirmacao, resultado_dict, fontes)
    "historico_llm":   [],   # formato Gemini
    "input_actual":    "",
    "n_input":         0,
    "total_analisados": 0,
    "total_mitos":     0,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ── Helpers ───────────────────────────────────────────────────────────────────

def classificar_veredito(texto: str) -> tuple[str, str, str]:
    """
    Extrai o veredito do texto de resposta e devolve (classe_css, emoji, label).
    Procura pelo padrão **VEREDITO:** ou variantes no início da resposta.
    """
    if "Erro" not in texto and "Limite de pedidos" not in texto:
        return "v-default", "🧭", "ANÁLISE DE NARRATIVA"

    t = texto.upper()
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
    return "v-default", "🧭", "ANÁLISE DE NARRATIVA"


def html_fontes(fontes: list[dict]) -> str:
    """Constrói o HTML do painel de fontes do Arquivo.pt."""
    if not fontes:
        return ""
    html = '<div class="fontes-container"><div class="fontes-titulo">📁 Fontes do Arquivo.pt</div>'
    for f in fontes:
        link   = f.get("link_arch", "#") or "#"
        titulo = f.get("titulo", "Sem título")[:85]
        data   = f.get("data", "")
        num    = f.get("numero", "")
        url_o  = f.get("url_orig", "")
        # Destaca fontes do Público
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
    """Normaliza referências de fonte para links com o texto único DOC N."""
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

    # [DOC 1, DOC 2], [DOC 1, 2], [DOCS 1 e 2]
    texto = re.sub(
        r"\[\s*((?:DOC(?:UMENTO)?S?\s*:?\s*)?\d+(?:\s*(?:,|;|e|and)\s*(?:DOC(?:UMENTO)?S?\s*:?\s*)?\d+)+)\s*\](?!\()",
        sub_lista,
        texto,
        flags=re.IGNORECASE,
    )

    # [DOC 1], [DOCUMENTO: 1], [[DOC 1]]
    texto = re.sub(
        r"\[\[\s*DOC(?:UMENTO)?\s*:?\s*(\d+)\s*\]\](?!\()",
        sub_ref,
        texto,
        flags=re.IGNORECASE,
    )
    texto = re.sub(
        r"\[\s*DOC(?:UMENTO)?\s*:?\s*(\d+)\s*\](?!\()",
        sub_ref,
        texto,
        flags=re.IGNORECASE,
    )

    # Plain DOC 1, while avoiding already linked markdown text: [DOC 1](...)
    return re.sub(
        r"(?<!\[)\bDOC(?:UMENTO)?\s*:?\s*(\d+)\b(?!\]\()",
        sub_ref,
        texto,
        flags=re.IGNORECASE,
    )


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
        <div class="tagline">Mapa de narrativas históricas · Arquivo.pt × IA</div>
      </div>
    </div>
    <div class="header-stats">
      <div class="stat-pill">
        <div class="stat-num">{n_analisados}</div>
        <div class="stat-label">Analisados</div>
      </div>
      <div class="stat-pill">
        <div class="stat-num" style="color:var(--vermelho)">{n_mitos}</div>
        <div class="stat-label">Fontes</div>
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 🔍 DECEPTIO")
    st.caption(
        "Ferramenta para analisar como um tema mudou ao longo do tempo. "
        "Encontra artigos no **Arquivo.pt**, extrai alegações e mostra "
        "timeline, fiabilidade das fontes, desacordos e mudança narrativa."
    )
    st.markdown("---")

    st.markdown("#### 📅 Filtro Temporal")
    st.caption("Limita os documentos a um período histórico.")
    usar_filtro = st.checkbox("Ativar filtro por anos", value=False)
    from_year, to_year = None, None
    if usar_filtro:
        c1, c2 = st.columns(2)
        with c1:
            from_year = str(st.number_input("De", min_value=1996, max_value=2025, value=1998, step=1))
        with c2:
            to_year   = str(st.number_input("Até", min_value=1996, max_value=2025, value=2005, step=1))

    st.markdown("---")
    st.markdown("#### 🧪 Casos de Teste")
    st.caption("Temas históricos para explorar.")

    casos = [
        "Bug do Ano 2000 em Portugal",
        "Entrada do Euro em Portugal",
        "EXPO 98 e impacto económico",
        "Internet em Portugal nos anos 90",
        "Crise financeira de 2008 nos bancos portugueses",
        "Ponte Vasco da Gama na imprensa portuguesa",
        "Gripe A nos media portugueses",
        "Ensino superior e propinas em Portugal",
    ]

    for i, caso in enumerate(casos):
        if st.button(f"🧪 {caso[:50]}…", key=f"caso_{i}"):
            st.session_state.input_actual = caso
            st.session_state.n_input += 1
            st.rerun()

    st.markdown("---")
    if st.button("🗑️ Limpar análises", use_container_width=True):
        st.session_state.historico      = []
        st.session_state.historico_llm  = []
        st.session_state.input_actual   = ""
        st.session_state.total_analisados = 0
        st.session_state.total_mitos    = 0
        st.rerun()

    st.markdown("---")
    st.caption(
        "**DECEPTIO** — Prémio Arquivo.pt 2026\n\n"
        "Usa a API do [Arquivo.pt](https://arquivo.pt) e Google Gemini "
        "com RAG de 4 camadas. Dá prioridade a fontes `.pt` e ao [Público](https://publico.pt)."
    )


# ── Layout principal ──────────────────────────────────────────────────────────

col_main, col_side = st.columns([3, 1])

# ── Painel lateral de instruções ──────────────────────────────────────────────

with col_side:
    st.markdown("""
    <div class="painel-info">
      <h4>⚙ Como Funciona</h4>

      <div class="step">
        <span class="step-num">C1</span>
        <p><strong>Query Expansion</strong><br>O Gemini gera 3 queries optimizadas para o Arquivo.pt.</p>
      </div>
      <div class="step">
        <span class="step-num">C2</span>
        <p><strong>Retrieval</strong><br>Recupera até 45 documentos de fontes <code>.pt</code> e <code>publico.pt</code>.</p>
      </div>
      <div class="step">
        <span class="step-num">C3</span>
        <p><strong>Re-ranking</strong><br>Seleciona os artigos mais relevantes para o tema.</p>
      </div>
      <div class="step">
        <span class="step-num">C4</span>
        <p><strong>Análise IA</strong><br>Extrai alegações, organiza a timeline e identifica desacordos.</p>
      </div>

      <hr style="border-color: #2A2A38; margin: 0.8rem 0;">

      <div style="font-size:0.72rem; color: #8888AA; margin-bottom:0.5rem; text-transform:uppercase; letter-spacing:1px; font-family: var(--mono);">Resultado esperado</div>
      <div class="legend-item"><div class="legend-dot" style="background:#FF2D55"></div> Linha temporal principal</div>
      <div class="legend-item"><div class="legend-dot" style="background:#00FF88"></div> Alegações por ano e fonte</div>
      <div class="legend-item"><div class="legend-dot" style="background:#FFB800"></div> Fiabilidade das fontes</div>
      <div class="legend-item"><div class="legend-dot" style="background:#4D9EFF"></div> Contradições e desacordos</div>
      <div class="legend-item"><div class="legend-dot" style="background:#9B5DE5"></div> Mudança da narrativa</div>
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
                f'<div class="label-q">▶ Tema submetido</div>'
                f'{afirmacao}'
                f'</div>',
                unsafe_allow_html=True
            )

            # Card de resultado
            st.markdown(
                f'<div class="card-resultado">'
                f'<div class="card-resultado-header">'
                f'<span class="veredito {css}">{emoji} {label}</span>'
                f'<span style="font-family:var(--mono);font-size:0.7rem;color:var(--subtexto);margin-left:auto;">'
                f'DECEPTIO · Arquivo.pt</span>'
                f'</div>'
                f'<div class="card-resultado-body">',
                unsafe_allow_html=True
            )

            # Botão copiar + corpo da resposta
            resp_b64 = base64.b64encode(resposta.encode("utf-8")).decode("ascii")
            st.markdown(
                f"""<div style="text-align:right;margin-bottom:0.3rem;">
                <button class="copy-btn" data-copy="{resp_b64}"
                  onclick="
                    const bytes = Uint8Array.from(atob(this.dataset.copy), c => c.charCodeAt(0));
                    const text = new TextDecoder().decode(bytes);
                    navigator.clipboard.writeText(text).then(
                      () => {{this.textContent='✓ Copiado';setTimeout(() => this.textContent='📋 Copiar',2000)}},
                      () => {{this.textContent='Erro';setTimeout(() => this.textContent='📋 Copiar',2000)}}
                    );
                  ">📋 Copiar</button></div>""",
                unsafe_allow_html=True
            )
            st.markdown(linkar_docs(resposta, fontes))
            st.markdown("</div></div>", unsafe_allow_html=True)

            # Fontes
            st.markdown(html_fontes(fontes), unsafe_allow_html=True)
            st.markdown("<hr>", unsafe_allow_html=True)

    else:
        # Ecrã de boas-vindas
        st.markdown("""
        <div class="welcome">
          <div class="welcome-icon">🔍</div>
          <h2>ANÁLISE DE NARRATIVAS HISTÓRICAS</h2>
          <p>
            Introduz um tema e o <strong>DECEPTIO</strong> encontra artigos relevantes no
            <strong>Arquivo.pt</strong>, extrai alegações, organiza uma timeline e destaca
            desacordos entre fontes.
          </p>
        </div>
        """, unsafe_allow_html=True)

    # ── Campo de input ─────────────────────────────────────────────────────────
    st.markdown('<div class="input-area">', unsafe_allow_html=True)
    col_in, col_btn = st.columns([5, 1])

    with col_in:
        input_val = st.text_input(
            label            = "Tema",
            value            = st.session_state.input_actual,
            placeholder      = "Ex: Bug do Ano 2000 em Portugal...",
            label_visibility = "collapsed",
            key              = f"input_{st.session_state.n_input}",
        )
    with col_btn:
        analisar = st.button("ANALISAR", use_container_width=True, type="primary")

    st.markdown("</div>", unsafe_allow_html=True)


# ── Processamento ─────────────────────────────────────────────────────────────

texto_final = input_val.strip() if input_val.strip() else st.session_state.input_actual.strip()

if analisar and texto_final:
    st.session_state.input_actual = texto_final

    with col_main:
        with st.spinner("🔍 A pesquisar artigos no Arquivo.pt e a construir a análise..."):
            resposta, fontes = analisar_topico(
                topico    = texto_final,
                from_year = from_year if usar_filtro else None,
                to_year   = to_year   if usar_filtro else None,
                historico = st.session_state.historico_llm,
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
    st.warning("✏️ Escreve um tema para analisar.")
