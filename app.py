"""
================================================================================
ChatArquivo — Interface Web (Streamlit)
================================================================================

Frontend do ChatArquivo: um assistente de IA conversacional que usa o Arquivo.pt
como base de conhecimento histórico. A interface permite:

  • Fazer perguntas em linguagem natural sobre a história da Internet portuguesa
  • Filtrar resultados por intervalo temporal
  • Ver as fontes históricas do Arquivo.pt que fundamentam cada resposta
  • Manter o histórico de conversa dentro da sessão
  • Explorar exemplos pré-definidos para guiar novos utilizadores

Para correr localmente:
  $ streamlit run app.py

Para correr com a tua chave de API:
    $ export GEMINI_API_KEY="AIzaSy..."
    $ streamlit run app.py

Dependências: ver requirements.txt

Autor: [O teu nome]
Prémio Arquivo.pt 2026
================================================================================
"""

import streamlit as st
from arquivo_rag import responder_pergunta

# ---------------------------------------------------------------------------
# Configuração da página Streamlit
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title = "ChatArquivo — A Máquina do Tempo com IA",
    page_icon  = "🕰️",
    layout     = "wide",
    initial_sidebar_state = "expanded",
)

# ---------------------------------------------------------------------------
# CSS personalizado — Visual austero e documental, inspirado em arquivo histórico
# Paleta: creme envelhecido, sépia, preto tipográfico, vermelho de selo
# ---------------------------------------------------------------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=Source+Serif+4:ital,wght@0,300;0,400;1,300&family=JetBrains+Mono:wght@400;500&display=swap');

/* Cores globais — paleta de arquivo histórico */
:root {
    --cor-fundo:      #F5F0E8;
    --cor-papel:      #FDFAF4;
    --cor-borda:      #C8B99A;
    --cor-texto:      #1A1208;
    --cor-subtexto:   #5C4A2A;
    --cor-destaque:   #8B1A1A;
    --cor-link:       #2C4A7C;
    --cor-sombra:     rgba(139, 90, 43, 0.15);
    --fonte-titulo:   'Playfair Display', Georgia, serif;
    --fonte-corpo:    'Source Serif 4', Georgia, serif;
    --fonte-mono:     'JetBrains Mono', monospace;
}

/* Reset geral */
html, body, [class*="css"] {
    font-family: var(--fonte-corpo) !important;
    background-color: var(--cor-fundo) !important;
    color: var(--cor-texto) !important;
}

/* Esconde elementos da UI do Streamlit */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* Cabeçalho principal */
.cabecalho-principal {
    text-align: center;
    padding: 2rem 0 1rem;
    border-bottom: 3px double var(--cor-borda);
    margin-bottom: 1.5rem;
}

.cabecalho-principal h1 {
    font-family: var(--fonte-titulo) !important;
    font-size: 3.2rem !important;
    font-weight: 900 !important;
    letter-spacing: -1px;
    color: var(--cor-texto) !important;
    margin: 0 0 0.2rem !important;
    line-height: 1.1;
}

.cabecalho-principal .subtitulo {
    font-family: var(--fonte-corpo);
    font-style: italic;
    font-size: 1.05rem;
    color: var(--cor-subtexto);
    letter-spacing: 0.5px;
}

.cabecalho-principal .linha-decorativa {
    font-size: 0.75rem;
    color: var(--cor-borda);
    letter-spacing: 4px;
    text-transform: uppercase;
    margin-top: 0.5rem;
}

/* Balões de conversa — estilo telegrama/recorte de jornal */
.mensagem-utilizador {
    background: var(--cor-destaque);
    color: #FFF8EE !important;
    padding: 1rem 1.3rem;
    border-radius: 2px;
    margin: 0.8rem 0;
    font-size: 1rem;
    line-height: 1.6;
    box-shadow: 3px 3px 0 rgba(0,0,0,0.15);
    border-left: 4px solid #5C0000;
}

.mensagem-assistente {
    background: var(--cor-papel);
    color: var(--cor-texto) !important;
    padding: 1.2rem 1.5rem;
    border-radius: 2px;
    margin: 0.8rem 0;
    font-size: 0.97rem;
    line-height: 1.8;
    border: 1px solid var(--cor-borda);
    border-left: 4px solid var(--cor-link);
    box-shadow: 3px 3px 0 var(--cor-sombra);
}

.label-mensagem {
    font-family: var(--fonte-mono);
    font-size: 0.65rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    opacity: 0.6;
    margin-bottom: 0.4rem;
}

/* Caixa de fontes do Arquivo.pt */
.caixa-fontes {
    background: #F0EBE0;
    border: 1px dashed var(--cor-borda);
    border-radius: 2px;
    padding: 1rem 1.2rem;
    margin-top: 0.6rem;
    font-size: 0.85rem;
}

.caixa-fontes-titulo {
    font-family: var(--fonte-mono);
    font-size: 0.65rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--cor-subtexto);
    margin-bottom: 0.5rem;
    font-weight: 500;
}

.fonte-item {
    padding: 0.3rem 0;
    border-bottom: 1px dotted var(--cor-borda);
    line-height: 1.4;
}

.fonte-item:last-child { border-bottom: none; }

.fonte-data {
    font-family: var(--fonte-mono);
    font-size: 0.75rem;
    color: var(--cor-destaque);
    font-weight: 500;
}

/* Barra lateral */
section[data-testid="stSidebar"] {
    background-color: #EDE7D9 !important;
    border-right: 2px solid var(--cor-borda);
}

section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 {
    font-family: var(--fonte-titulo) !important;
    color: var(--cor-texto) !important;
}

/* Botões de exemplo */
.stButton > button {
    background: transparent !important;
    color: var(--cor-link) !important;
    border: 1px solid var(--cor-link) !important;
    border-radius: 2px !important;
    font-family: var(--fonte-corpo) !important;
    font-size: 0.82rem !important;
    font-style: italic;
    text-align: left !important;
    padding: 0.4rem 0.8rem !important;
    width: 100%;
    transition: all 0.15s ease;
}

.stButton > button:hover {
    background: var(--cor-link) !important;
    color: white !important;
}

/* Input de pesquisa */
.stTextInput > div > div > input,
.stTextArea textarea {
    font-family: var(--fonte-corpo) !important;
    font-size: 1rem !important;
    background: var(--cor-papel) !important;
    border: 1px solid var(--cor-borda) !important;
    border-radius: 2px !important;
    color: var(--cor-texto) !important;
}

/* Sliders de ano */
.stSlider { margin: 0.5rem 0; }

/* Spinner de carregamento */
.stSpinner > div {
    border-color: var(--cor-destaque) !important;
}

/* Separador horizontal */
hr {
    border: none;
    border-top: 2px double var(--cor-borda);
    margin: 1.5rem 0;
}

/* Selectbox */
.stSelectbox > div > div {
    background: var(--cor-papel) !important;
    border: 1px solid var(--cor-borda) !important;
    border-radius: 2px !important;
}

/* Aviso / info boxes */
.stAlert {
    border-radius: 2px !important;
    font-family: var(--fonte-corpo) !important;
}

/* Área de conversa com scroll */
.area-conversa {
    max-height: 65vh;
    overflow-y: auto;
    padding-right: 0.5rem;
}

/* Número do documento fonte */
.num-doc {
    display: inline-block;
    background: var(--cor-link);
    color: white;
    font-family: var(--fonte-mono);
    font-size: 0.65rem;
    padding: 1px 5px;
    border-radius: 2px;
    margin-right: 4px;
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Inicialização do estado da sessão Streamlit
# ---------------------------------------------------------------------------

# O Streamlit recria a página a cada interação; o session_state persiste dados
if "historico_display" not in st.session_state:
    # Lista de tuplos (pergunta, resposta, fontes) para exibição
    st.session_state.historico_display = []

if "historico_llm" not in st.session_state:
    # Histórico no formato genérico (convertido para Gemini no backend)
    st.session_state.historico_llm = []

if "pergunta_exemplo" not in st.session_state:
    # Pergunta injetada pelos botões de exemplo
    st.session_state.pergunta_exemplo = ""


# ---------------------------------------------------------------------------
# Cabeçalho principal
# ---------------------------------------------------------------------------

st.markdown("""
<div class="cabecalho-principal">
    <div class="linha-decorativa">✦ Arquivo.pt × Inteligência Artificial ✦</div>
    <h1>ChatArquivo</h1>
    <div class="subtitulo">A Máquina do Tempo com IA — Consulta a memória da Internet portuguesa</div>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Barra lateral — configuração e exemplos
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("## 🕰️ ChatArquivo")
    st.markdown(
        "*Assistente de IA que usa os documentos históricos do **Arquivo.pt** "
        "para responder às tuas perguntas sobre o passado da Internet portuguesa.*"
    )

    st.markdown("---")

    # --- Filtro temporal ---
    st.markdown("### 📅 Intervalo Temporal")
    st.caption("Limita a pesquisa a um período histórico específico.")

    usar_filtro_tempo = st.checkbox("Activar filtro por anos", value=False)

    from_year, to_year = None, None
    if usar_filtro_tempo:
        col1, col2 = st.columns(2)
        with col1:
            from_year = str(st.number_input("De", min_value=1996, max_value=2025, value=2000, step=1))
        with col2:
            to_year   = str(st.number_input("Até", min_value=1996, max_value=2025, value=2010, step=1))

    st.markdown("---")

    # --- Perguntas de exemplo ---
    st.markdown("### 💡 Perguntas de Exemplo")
    st.caption("Clica para usar como ponto de partida.")

    exemplos = [
        "O que se dizia sobre a adoção do Euro em Portugal em 2002?",
        "Como reagiram os jornais portugueses ao Bug do Ano 2000 (Y2K)?",
        "Qual era a situação política em Portugal durante o PREC em 1975?",
        "Como foi noticiada a entrada de Portugal na União Europeia em 1986?",
        "O que se escrevia sobre o Sporting e o Benfica no início dos anos 2000?",
        "Como eram apresentadas as primeiras páginas web portuguesas nos anos 1990?",
        "Qual a cobertura mediática do terramoto de 1755 na web histórica?",
        "O que dizia a imprensa sobre a crise financeira de 2008 em Portugal?",
    ]

    for exemplo in exemplos:
        # Cada botão injeta o exemplo no campo de texto via session_state
        if st.button(f"📰 {exemplo[:55]}...", key=exemplo):
            st.session_state.pergunta_exemplo = exemplo

    st.markdown("---")

    # --- Botão de limpar histórico ---
    if st.button("🗑️ Limpar conversa", use_container_width=True):
        st.session_state.historico_display = []
        st.session_state.historico_llm    = []
        st.session_state.pergunta_exemplo = ""
        st.rerun()

    st.markdown("---")
    st.caption(
        "**ChatArquivo** foi desenvolvido para o **Prémio Arquivo.pt 2026**. "
        "Usa a API do [Arquivo.pt](https://arquivo.pt) e a API Gemini Pro (Google) "
        "numa arquitectura RAG (*Retrieval-Augmented Generation*)."
    )


# ---------------------------------------------------------------------------
# Área principal — histórico de conversa
# ---------------------------------------------------------------------------

col_conversa, col_info = st.columns([3, 1])

with col_conversa:

    # Exibe o histórico de conversa da sessão actual
    if st.session_state.historico_display:
        for pergunta, resposta, fontes in st.session_state.historico_display:

            # Mensagem do utilizador
            st.markdown(f"""
            <div class="mensagem-utilizador">
                <div class="label-mensagem">▶ Utilizador</div>
                {pergunta}
            </div>
            """, unsafe_allow_html=True)

            # Resposta do assistente
            st.markdown(f"""
            <div class="mensagem-assistente">
                <div class="label-mensagem">📜 ChatArquivo</div>
                {resposta.replace(chr(10), '<br>')}
            </div>
            """, unsafe_allow_html=True)

            # Fontes do Arquivo.pt — mostradas de forma compacta
            if fontes:
                fontes_html = '<div class="caixa-fontes">'
                fontes_html += '<div class="caixa-fontes-titulo">📁 Fontes do Arquivo.pt utilizadas</div>'
                for f in fontes:
                    link = f.get("link_arch", "#")
                    titulo = f.get("titulo", "Sem título")[:80]
                    data   = f.get("data", "")
                    num    = f.get("numero", "")
                    url_o  = f.get("url_orig", "")
                    fontes_html += f"""
                    <div class="fonte-item">
                        <span class="num-doc">DOC {num}</span>
                        <span class="fonte-data">{data}</span> —
                        <a href="{link}" target="_blank" style="color: var(--cor-link);">{titulo}</a><br>
                        <small style="color: var(--cor-subtexto); font-style: italic;">{url_o[:70]}</small>
                    </div>"""
                fontes_html += '</div>'
                st.markdown(fontes_html, unsafe_allow_html=True)

            st.markdown("<hr>", unsafe_allow_html=True)

    else:
        # Ecrã de boas-vindas quando não há histórico
        st.markdown("""
        <div style="text-align:center; padding: 3rem 2rem; color: #5C4A2A; border: 1px dashed #C8B99A; background: #FDFAF4; border-radius: 2px;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🗞️</div>
            <div style="font-family: 'Playfair Display', serif; font-size: 1.4rem; margin-bottom: 0.8rem;">
                Consulta a memória da Internet portuguesa
            </div>
            <div style="font-style: italic; font-size: 0.95rem; line-height: 1.7;">
                Faz uma pergunta sobre qualquer acontecimento histórico português.<br>
                O ChatArquivo irá pesquisar documentos reais do <strong>Arquivo.pt</strong><br>
                e usar IA para sintetizar uma resposta fundamentada com fontes verificáveis.
            </div>
        </div>
        """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Área de input — campo de pergunta e botão de submissão
# ---------------------------------------------------------------------------

st.markdown("<br>", unsafe_allow_html=True)

# O campo pré-preenche com o exemplo clicado na barra lateral (se houver)
valor_inicial = st.session_state.get("pergunta_exemplo", "")

with st.form(key="form_pergunta", clear_on_submit=True):
    col_input, col_btn = st.columns([5, 1])

    with col_input:
        pergunta_input = st.text_input(
            label       = "A tua pergunta",
            value       = valor_inicial,
            placeholder = "Ex: O que se dizia sobre a crise do euro em Portugal em 2011?",
            label_visibility = "collapsed",
        )

    with col_btn:
        submeter = st.form_submit_button(
            "🔍 Pesquisar",
            use_container_width = True,
        )

# Limpa o exemplo após ser usado
if valor_inicial:
    st.session_state.pergunta_exemplo = ""


# ---------------------------------------------------------------------------
# Processamento da pergunta — pipeline RAG
# ---------------------------------------------------------------------------

if submeter and pergunta_input.strip():

    pergunta_limpa = pergunta_input.strip()

    with st.spinner("A pesquisar no Arquivo.pt e a analisar com o Gemini..."):

        # Chama o motor RAG com a pergunta e os filtros temporais opcionais
        resposta, fontes = responder_pergunta(
            pergunta  = pergunta_limpa,
            from_year = from_year if usar_filtro_tempo else None,
            to_year   = to_year   if usar_filtro_tempo else None,
            historico = st.session_state.historico_llm,
        )

    # Guarda no histórico de display (para mostrar na UI)
    st.session_state.historico_display.append((pergunta_limpa, resposta, fontes))

    # Guarda no histórico do LLM (para manter contexto em perguntas de seguimento)
    # Nota: não incluímos o contexto completo no histórico para evitar exceder o token limit
    st.session_state.historico_llm.append({"role": "user",  "content": pergunta_limpa})
    st.session_state.historico_llm.append({"role": "model", "content": resposta})

    # Recarrega a página para exibir a nova mensagem
    st.rerun()

elif submeter:
    st.warning("Por favor, escreve uma pergunta antes de pesquisar.")


# ---------------------------------------------------------------------------
# Coluna de informação lateral — painel "Como funciona"
# ---------------------------------------------------------------------------

with col_info:
    st.markdown("""
    <div style="background: #FDFAF4; border: 1px solid #C8B99A; border-radius: 2px; padding: 1rem; font-size: 0.82rem; line-height: 1.6;">
        <div style="font-family: 'Playfair Display', serif; font-size: 1rem; font-weight: 700; margin-bottom: 0.8rem; border-bottom: 1px solid #C8B99A; padding-bottom: 0.4rem;">
            ⚙️ Como funciona
        </div>
        <p><strong>1. Pesquisa</strong><br>
        A tua pergunta é enviada à API do <em>Arquivo.pt</em>, que devolve páginas históricas relevantes.</p>
        <p><strong>2. Extracção</strong><br>
        O texto de cada página é extraído e limpo (HTML → texto legível).</p>
        <p><strong>3. Geração</strong><br>
        O <b>Gemini Pro (Google)</b> sintetiza uma resposta citada.</p>
        <p><strong>4. Fontes</strong><br>
        Cada resposta inclui links verificáveis para os documentos originais no Arquivo.pt.</p>
        <hr style="border: 1px dashed #C8B99A;">
        <div style="font-style: italic; color: #5C4A2A; font-size: 0.78rem;">
            Arquitectura RAG<br>
            (Retrieval-Augmented Generation)<br><br>
            O sistema nunca inventa factos — todas as respostas são baseadas em documentos reais preservados pelo Arquivo.pt.
        </div>
    </div>
    """, unsafe_allow_html=True)
