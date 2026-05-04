"""
================================================================================
ChatArquivo — Interface Web (Streamlit)
================================================================================

Frontend do ChatArquivo: assistente de IA conversacional sobre o Arquivo.pt.

BUGS CORRIGIDOS nesta versão:
  - [FIX] Perguntas de exemplo agora preenchem correctamente o campo de pesquisa
          (resolvido via st.session_state + key dinâmica, sem st.form)
  - [FIX] Spinner de carregamento já não torna o painel "Como funciona" invisível
          (resolvido movendo o spinner para dentro da coluna de conversa)
  - [FIX] Botão de copiar resposta adicionado a cada mensagem do assistente
  - [FIX] Seta da barra lateral sempre visível (CSS corrigido)
  - [FIX] Campo de texto submete correctamente ao clicar Pesquisar mesmo quando
          preenchido via exemplo (sem st.form, controlo manual via on_change/button)
  - [FIX] Respostas da API renderizam Markdown (negrito, listas, etc.)
  - [FIX] Overflow de texto longo nas mensagens corrigido

Para correr:
    $ export GEMINI_API_KEY="AIzaSy..."
    $ streamlit run app.py

Autor: [O teu nome]
Prémio Arquivo.pt 2026
================================================================================
"""

import streamlit as st
from arquivo_rag import responder_pergunta

# ---------------------------------------------------------------------------
# Configuração da página
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="ChatArquivo — A Máquina do Tempo com IA",
    page_icon="🕰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# CSS — Visual documental/editorial. Correcções de bugs visuais incluídas.
# ---------------------------------------------------------------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=Source+Serif+4:ital,opsz,wght@0,8..60,300;0,8..60,400;1,8..60,300&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --fundo:      #F5F0E8;
    --papel:      #FDFAF4;
    --borda:      #C8B99A;
    --texto:      #1A1208;
    --subtexto:   #5C4A2A;
    --destaque:   #8B1A1A;
    --link:       #2C4A7C;
    --sombra:     rgba(139, 90, 43, 0.12);
    --fonte-t:    'Playfair Display', Georgia, serif;
    --fonte-c:    'Source Serif 4', Georgia, serif;
    --fonte-m:    'JetBrains Mono', 'Courier New', monospace;
}

/* ── Base ─────────────────────────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: var(--fonte-c) !important;
    background-color: var(--fundo) !important;
    color: var(--texto) !important;
}
#MainMenu, footer { visibility: hidden; }
.stDeployButton { display: none; }

/* ── [FIX] Seta da barra lateral — sempre visível, não apenas no hover ── */
[data-testid="collapsedControl"],
button[kind="header"],
.st-emotion-cache-1rtdyuf,
.st-emotion-cache-pkbazv {
    opacity: 1 !important;
    visibility: visible !important;
    color: var(--subtexto) !important;
}

/* ── Cabeçalho ────────────────────────────────────────────────────── */
.cab {
    text-align: center;
    padding: 1.8rem 0 1.2rem;
    border-bottom: 3px double var(--borda);
    margin-bottom: 1.5rem;
}
.cab h1 {
    font-family: var(--fonte-t) !important;
    font-size: 3rem !important;
    font-weight: 900 !important;
    letter-spacing: -1px;
    color: var(--texto) !important;
    margin: 0 0 0.2rem !important;
    line-height: 1.1;
}
.cab .sub {
    font-style: italic;
    font-size: 1rem;
    color: var(--subtexto);
}
.cab .deco {
    font-family: var(--fonte-m);
    font-size: 0.65rem;
    color: var(--borda);
    letter-spacing: 4px;
    text-transform: uppercase;
    margin-top: 0.4rem;
}

/* ── Mensagens ────────────────────────────────────────────────────── */
.msg-user {
    background: #EAE3D5;
    border-left: 4px solid var(--subtexto);
    padding: 0.9rem 1.2rem;
    border-radius: 2px;
    margin: 0.8rem 0 0.4rem;
    font-size: 1rem;
    line-height: 1.6;
    box-shadow: 2px 2px 0 rgba(0,0,0,0.04);
    word-break: break-word;
}
.msg-assistente {
    background: var(--papel);
    border: 1px solid var(--borda);
    border-left: 4px solid var(--link);
    padding: 1.1rem 1.4rem 0.8rem;
    border-radius: 2px;
    margin: 0.3rem 0 0.4rem;
    font-size: 0.96rem;
    line-height: 1.8;
    box-shadow: 3px 3px 0 var(--sombra);
    word-break: break-word;
    /* [FIX] Garante que o texto não "vaza" para além da caixa */
    overflow-wrap: break-word;
}
.label {
    font-family: var(--fonte-m);
    font-size: 0.6rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    opacity: 0.55;
    margin-bottom: 0.35rem;
    display: block;
}

/* ── Fontes ───────────────────────────────────────────────────────── */
.fontes {
    background: #F0EBE0;
    border: 1px dashed var(--borda);
    border-radius: 2px;
    padding: 0.8rem 1.1rem;
    margin: 0.2rem 0 0.8rem;
    font-size: 0.82rem;
}
.fontes-tit {
    font-family: var(--fonte-m);
    font-size: 0.62rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--subtexto);
    margin-bottom: 0.5rem;
    font-weight: 500;
}
.fonte-item {
    padding: 0.28rem 0;
    border-bottom: 1px dotted var(--borda);
    line-height: 1.4;
    word-break: break-word;
}
.fonte-item:last-child { border-bottom: none; }
.fonte-data {
    font-family: var(--fonte-m);
    font-size: 0.72rem;
    color: var(--destaque);
    font-weight: 500;
}
.num-doc {
    display: inline-block;
    background: var(--link);
    color: white;
    font-family: var(--fonte-m);
    font-size: 0.62rem;
    padding: 1px 5px;
    border-radius: 2px;
    margin-right: 4px;
    white-space: nowrap;
}

/* ── Barra lateral ────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background-color: #EDE7D9 !important;
    border-right: 2px solid var(--borda);
}
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    font-family: var(--fonte-t) !important;
    color: var(--texto) !important;
}

/* ── Botões gerais ────────────────────────────────────────────────── */
.stButton > button {
    background: transparent !important;
    color: var(--link) !important;
    border: 1px solid var(--link) !important;
    border-radius: 2px !important;
    font-family: var(--fonte-c) !important;
    font-size: 0.82rem !important;
    font-style: italic;
    text-align: left !important;
    padding: 0.4rem 0.8rem !important;
    width: 100%;
    transition: all 0.15s ease;
    white-space: normal !important;   /* permite quebra de linha */
    height: auto !important;
}
.stButton > button:hover {
    background: var(--link) !important;
    color: white !important;
}

/* ── Botão de copiar — estilo discreto ───────────────────────────── */
button[title="Copiar resposta"] {
    background: transparent !important;
    border: 1px solid var(--borda) !important;
    color: var(--subtexto) !important;
    font-size: 0.75rem !important;
    padding: 2px 8px !important;
    float: right;
    font-style: normal !important;
    font-family: var(--fonte-m) !important;
    width: auto !important;
}
button[title="Copiar resposta"]:hover {
    background: var(--borda) !important;
    color: var(--texto) !important;
}

/* ── Input e área de texto ───────────────────────────────────────── */
.stTextInput > div > div > input {
    font-family: var(--fonte-c) !important;
    font-size: 1rem !important;
    background: var(--papel) !important;
    border: 1px solid var(--borda) !important;
    border-radius: 2px !important;
    color: var(--texto) !important;
    padding: 0.55rem 0.8rem !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--link) !important;
    box-shadow: 0 0 0 2px rgba(44,74,124,0.15) !important;
}

/* ── Spinner — [FIX] não afecta o painel lateral ─────────────────── */
.stSpinner > div { border-top-color: var(--destaque) !important; }

/* ── Select / number input ───────────────────────────────────────── */
.stSelectbox > div > div,
.stNumberInput > div > div > input {
    background: var(--papel) !important;
    border: 1px solid var(--borda) !important;
    border-radius: 2px !important;
    font-family: var(--fonte-c) !important;
}

/* ── Separador horizontal ─────────────────────────────────────────── */
hr { border: none; border-top: 2px double var(--borda); margin: 1.2rem 0; }

/* ── Ecrã de boas-vindas ─────────────────────────────────────────── */
.boas-vindas {
    text-align: center;
    padding: 3rem 2rem;
    color: var(--subtexto);
    border: 1px dashed var(--borda);
    background: var(--papel);
    border-radius: 2px;
    margin: 1rem 0;
}
.boas-vindas .icone { font-size: 2.5rem; margin-bottom: 1rem; }
.boas-vindas .titulo {
    font-family: var(--fonte-t);
    font-size: 1.35rem;
    margin-bottom: 0.7rem;
    color: var(--texto);
}
.boas-vindas p { font-style: italic; font-size: 0.95rem; line-height: 1.7; }

/* ── Painel "Como funciona" ──────────────────────────────────────── */
.como-funciona {
    background: var(--papel);
    border: 1px solid var(--borda);
    border-radius: 2px;
    padding: 1rem;
    font-size: 0.82rem;
    line-height: 1.65;
    position: sticky;
    top: 1rem;
}
.como-funciona h4 {
    font-family: var(--fonte-t);
    font-size: 1rem;
    font-weight: 700;
    border-bottom: 1px solid var(--borda);
    padding-bottom: 0.35rem;
    margin-bottom: 0.7rem;
    color: var(--texto);
}
.como-funciona p { margin: 0.5rem 0; }
.como-funciona .nota {
    font-style: italic;
    color: var(--subtexto);
    font-size: 0.76rem;
    border-top: 1px dashed var(--borda);
    margin-top: 0.8rem;
    padding-top: 0.6rem;
}

/* ── Área de input fixa no fundo ─────────────────────────────────── */
.area-input {
    background: var(--fundo);
    border-top: 2px double var(--borda);
    padding: 0.8rem 0 0.3rem;
    margin-top: 1.2rem;
}

/* ── Aviso de erro / info ─────────────────────────────────────────── */
.stAlert { border-radius: 2px !important; font-family: var(--fonte-c) !important; }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Inicialização do estado da sessão
# ---------------------------------------------------------------------------

defaults = {
    "historico_display": [],   # Lista de (pergunta, resposta, fontes) para a UI
    "historico_llm":     [],   # Histórico no formato Gemini (role + content)
    "pergunta_actual":   "",   # Texto actual no campo de input
    "aguardar_resposta": False,# Flag: está a processar uma pergunta?
    "n_input":           0,    # Contador para forçar re-render do campo (ao injectar exemplo)
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ---------------------------------------------------------------------------
# Cabeçalho
# ---------------------------------------------------------------------------

st.markdown("""
<div class="cab">
    <div class="deco">✦ Arquivo.pt × Inteligência Artificial ✦</div>
    <h1>ChatArquivo</h1>
    <div class="sub">A Máquina do Tempo com IA — Consulta a memória da Internet portuguesa</div>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Barra lateral
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("## 🕰️ ChatArquivo")
    st.markdown(
        "*Assistente de IA que usa documentos históricos do **Arquivo.pt** "
        "para responder às tuas perguntas sobre o passado da Internet portuguesa.*"
    )
    st.markdown("---")

    # ── Filtro temporal ──────────────────────────────────────────────────
    st.markdown("### 📅 Intervalo Temporal")
    st.caption("Restringe a pesquisa a um período histórico.")
    usar_filtro = st.checkbox("Activar filtro por anos", value=False)

    from_year, to_year = None, None
    if usar_filtro:
        c1, c2 = st.columns(2)
        with c1:
            from_year = str(st.number_input("De", min_value=1996, max_value=2025, value=2000, step=1))
        with c2:
            to_year   = str(st.number_input("Até", min_value=1996, max_value=2025, value=2010, step=1))

    st.markdown("---")

    # ── Perguntas de exemplo ─────────────────────────────────────────────
    st.markdown("### 💡 Perguntas de Exemplo")
    st.caption("Clica para preencher o campo de pesquisa.")

    exemplos = [
        "O que se dizia sobre a adoção do Euro em Portugal em 2002?",
        "Como reagiram os meios de comunicação portugueses ao Bug do Ano 2000 (Y2K)?",
        "Quem era o Presidente da República de Portugal em 2010?",
        "Como foi noticiada a entrada de Portugal na União Europeia em 1986?",
        "O que escrevia a imprensa sobre a crise financeira de 2008 em Portugal?",
        "Como eram as primeiras páginas web portuguesas nos anos 1990?",
        "O que se dizia sobre o Mundial de Futebol de 2002 em Portugal?",
        "Como era descrita a Internet em Portugal no final dos anos 1990?",
    ]

    for exemplo in exemplos:
        # [FIX] Ao clicar, guarda o exemplo no session_state E incrementa o contador
        # de input para forçar o Streamlit a re-renderizar o campo com o novo valor.
        if st.button(f"📰 {exemplo[:52]}…", key=f"ex_{exemplo[:20]}"):
            st.session_state.pergunta_actual = exemplo
            st.session_state.n_input += 1  # Força novo widget key → re-renderiza com valor certo
            st.rerun()

    st.markdown("---")

    if st.button("🗑️ Limpar conversa", use_container_width=True):
        st.session_state.historico_display = []
        st.session_state.historico_llm    = []
        st.session_state.pergunta_actual  = ""
        st.rerun()

    st.markdown("---")
    st.caption(
        "**ChatArquivo** — Prémio Arquivo.pt 2026.\n\n"
        "Usa a API do [Arquivo.pt](https://arquivo.pt) e o Google Gemini "
        "numa arquitectura RAG (*Retrieval-Augmented Generation*)."
    )


# ---------------------------------------------------------------------------
# Layout principal: conversa (3) + painel info (1)
# ---------------------------------------------------------------------------

col_conv, col_info = st.columns([3, 1])

# ── Painel "Como funciona" (coluna direita) ─────────────────────────────
with col_info:
    st.markdown("""
    <div class="como-funciona">
        <h4>⚙️ Como funciona</h4>
        <p><strong>1. Pesquisa</strong><br>
        A tua pergunta é enviada à API do <em>Arquivo.pt</em>, que devolve páginas históricas relevantes.</p>
        <p><strong>2. Extracção</strong><br>
        O texto de cada página arquivada é extraído e limpo (HTML → texto legível).</p>
        <p><strong>3. Geração</strong><br>
        O <strong>Google Gemini</strong> sintetiza uma resposta fundamentada, citando as fontes.</p>
        <p><strong>4. Fontes</strong><br>
        Cada resposta inclui links verificáveis para os documentos originais no Arquivo.pt.</p>
        <div class="nota">
            Arquitectura <strong>RAG</strong><br>
            (Retrieval-Augmented Generation)<br><br>
            O sistema nunca inventa factos — as respostas baseiam-se exclusivamente em documentos
            reais preservados pelo Arquivo.pt.
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── Área de conversa (coluna esquerda) ──────────────────────────────────
with col_conv:

    # Histórico de conversa
    if st.session_state.historico_display:
        for idx, (perg, resp, fontes) in enumerate(st.session_state.historico_display):

            # Pergunta do utilizador
            st.markdown(
                f'<div class="msg-user"><span class="label">▶ Utilizador</span>{perg}</div>',
                unsafe_allow_html=True
            )

            # Resposta do assistente
            st.markdown(
                f'<div class="msg-assistente"><span class="label">📜 ChatArquivo</span>',
                unsafe_allow_html=True
            )
            # [FIX] Usa st.markdown nativo para renderizar Markdown da resposta (negrito, listas, etc.)
            st.markdown(resp)
            st.markdown("</div>", unsafe_allow_html=True)

            # [FIX] Botão de copiar por resposta
            # Usa um componente HTML com JavaScript para copiar para a área de transferência
            resposta_js = resp.replace("`", "\\`").replace("\\n", "\\\\n").replace("\n", "\\n")
            st.markdown(
                f"""<div style="text-align:right; margin: -0.5rem 0 0.5rem;">
                    <button onclick="navigator.clipboard.writeText(`{resposta_js}`).then(
                        ()=>this.textContent='✓ Copiado!',
                        ()=>this.textContent='Erro'
                    ); setTimeout(()=>this.textContent='📋 Copiar',2000);"
                    style="background:transparent; border:1px solid #C8B99A; border-radius:2px;
                    color:#5C4A2A; font-size:0.72rem; padding:2px 10px; cursor:pointer;
                    font-family:'JetBrains Mono',monospace;">
                    📋 Copiar
                    </button></div>""",
                unsafe_allow_html=True
            )

            # Fontes do Arquivo.pt
            if fontes:
                fontes_html = '<div class="fontes"><div class="fontes-tit">📁 Fontes do Arquivo.pt</div>'
                for f in fontes:
                    link  = f.get("link_arch", "#") or "#"
                    tit   = f.get("titulo", "Sem título")[:80]
                    data  = f.get("data", "")
                    num   = f.get("numero", "")
                    url_o = f.get("url_orig", "")[:70]
                    fontes_html += (
                        f'<div class="fonte-item">'
                        f'<span class="num-doc">DOC&nbsp;{num}</span>'
                        f'<span class="fonte-data">{data}</span> — '
                        f'<a href="{link}" target="_blank" rel="noopener" '
                        f'style="color:var(--link);">{tit}</a><br>'
                        f'<small style="color:var(--subtexto);font-style:italic;">{url_o}</small>'
                        f'</div>'
                    )
                fontes_html += '</div>'
                st.markdown(fontes_html, unsafe_allow_html=True)

            st.markdown("<hr>", unsafe_allow_html=True)

    else:
        # Ecrã de boas-vindas
        st.markdown("""
        <div class="boas-vindas">
            <div class="icone">🗞️</div>
            <div class="titulo">Consulta a memória da Internet portuguesa</div>
            <p>Faz uma pergunta sobre qualquer acontecimento histórico português.<br>
            O <strong>ChatArquivo</strong> pesquisa documentos reais do <strong>Arquivo.pt</strong>
            e usa IA para sintetizar uma resposta fundamentada com fontes verificáveis.</p>
        </div>
        """, unsafe_allow_html=True)

    # ── Campo de input ────────────────────────────────────────────────────
    st.markdown('<div class="area-input">', unsafe_allow_html=True)

    col_in, col_btn = st.columns([5, 1])

    with col_in:
        # [FIX] key dinâmica (inclui n_input) faz o Streamlit criar um widget novo
        # cada vez que um exemplo é injectado, garantindo que o value é aplicado.
        # Sem st.form → o valor não é "esquecido" pelo clear_on_submit.
        pergunta_input = st.text_input(
            label            = "Pergunta",
            value            = st.session_state.pergunta_actual,
            placeholder      = "Ex: O que se dizia sobre a crise do euro em Portugal em 2011?",
            label_visibility = "collapsed",
            key              = f"input_pergunta_{st.session_state.n_input}",
        )

    with col_btn:
        submeter = st.button("🔍 Pesquisar", use_container_width=True, type="primary")

    st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Processamento da pergunta
# ---------------------------------------------------------------------------

# Normaliza: usa o valor do campo (digitado) ou o valor do session_state (exemplo injectado)
texto_final = pergunta_input.strip() if pergunta_input.strip() else st.session_state.pergunta_actual.strip()

if submeter and texto_final:

    # Actualiza o session_state com o texto que vai ser processado
    st.session_state.pergunta_actual = texto_final

    # Spinner apenas na coluna de conversa — não afecta o painel info
    with col_conv:
        with st.spinner("🔍 A pesquisar no Arquivo.pt e a analisar documentos históricos…"):
            resposta, fontes = responder_pergunta(
                pergunta  = texto_final,
                from_year = from_year if usar_filtro else None,
                to_year   = to_year   if usar_filtro else None,
                historico = st.session_state.historico_llm,
            )

    # Guarda no histórico de display
    st.session_state.historico_display.append((texto_final, resposta, fontes))

    # Guarda no histórico do LLM (formato Gemini)
    st.session_state.historico_llm.append({"role": "user",  "content": texto_final})
    st.session_state.historico_llm.append({"role": "model", "content": resposta})

    # Limpa o campo após submissão e incrementa a key para re-renderizar
    st.session_state.pergunta_actual = ""
    st.session_state.n_input += 1

    st.rerun()

elif submeter:
    st.warning("✏️ Por favor, escreve uma pergunta antes de pesquisar.")