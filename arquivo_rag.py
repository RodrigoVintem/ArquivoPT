"""
================================================================================
ChatArquivo — Motor RAG (Retrieval-Augmented Generation)
================================================================================

Módulo central do sistema. Responsável por:
    1. Consultar a API de pesquisa de texto do Arquivo.pt
    2. Extrair e limpar o texto HTML dos resultados históricos
    3. Construir um contexto documental datado e citável
    4. Enviar esse contexto + pergunta do utilizador ao LLM (Gemini)
    5. Devolver a resposta gerada com fontes rastreáveis

Arquitetura RAG (Retrieval-Augmented Generation):
  Pergunta → Arquivo.pt API → Extração HTML → Contexto → LLM → Resposta citada

Autor: [O teu nome]
Instituição: [A tua faculdade/universidade]
Prémio Arquivo.pt 2026
================================================================================
"""

import os
import re
import time
import requests
from bs4 import BeautifulSoup
from google import genai
from google.genai import types as genai_types

# ---------------------------------------------------------------------------
# Configuração da API do Arquivo.pt
# Documentação: https://arquivo.pt/api
# ---------------------------------------------------------------------------

ARQUIVO_TEXTSEARCH_URL = "https://arquivo.pt/textsearch"

# Número de resultados a recuperar. 10 com query otimizada garante contexto rico e precisão.
NUM_RESULTADOS = 10

# Comprimento máximo de texto extraído por página (em caracteres).
# 2000 chars ≈ 500 tokens — bom equilíbrio entre contexto e custo de API.
MAX_CHARS_POR_PAGINA = 2000

# Timeout para pedidos HTTP ao Arquivo.pt (segundos)
HTTP_TIMEOUT = 20


# ---------------------------------------------------------------------------
# PASSO 1 — Expansão de Query com IA e Pesquisa no Arquivo.pt
# ---------------------------------------------------------------------------

def otimizar_query_com_ia(pergunta: str, api_key: str) -> str:
    """
    Técnica HyDE: Usa um modelo LLM ultrarrápido (Flash-Lite) para 
    adicionar contexto semântico à query antes de ir ao motor léxico do Arquivo.pt.
    """
    if not api_key:
        return pergunta

    cliente = genai.Client(api_key=api_key)
    prompt = (
        f"O utilizador quer saber: '{pergunta}'.\n"
        f"Gera apenas UMA query de pesquisa (máximo 6 palavras) para um motor de busca antigo.\n"
        f"Adiciona o contexto português implícito (ex: se perguntar por 'presidente', "
        f"adiciona 'república portugal'). Se não houver ano na pergunta, foca-te nos termos essenciais.\n"
        f"Não uses pontuação, não dês explicações. Responde APENAS com as palavras-chave."
    )
    
    try:
        resp = cliente.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt
        )
        query_otimizada = resp.text.strip().replace('"', '').replace('\n', ' ')
        print(f"[RAG] 🧠 Expansão de Query: '{pergunta}' -> '{query_otimizada}'")
        return query_otimizada
    except Exception as e:
        print(f"[RAG] ⚠️ Falha na expansão com IA (fallback ativado): {e}")
        # Fallback de segurança: limpa a string básica
        q = re.sub(r"[?!.,;:]+$", "", pergunta.strip())
        return re.sub(r"\s+", " ", q).strip()

def pesquisar_arquivo(query_otimizada: str, from_year: str = None, to_year: str = None) -> list[dict]:
    """Consulta a API de pesquisa do Arquivo.pt com a query já tratada pela IA."""
    params = {
        "q":           query_otimizada,
        "maxItems":    NUM_RESULTADOS,
        "prettyPrint": "false",
    }

    if from_year:
        params["from"] = f"{from_year}0101000000"
    if to_year:
        params["to"]   = f"{to_year}1231235959"

    try:
        resposta = requests.get(
            ARQUIVO_TEXTSEARCH_URL,
            params=params,
            timeout=HTTP_TIMEOUT,
            headers={"User-Agent": "ChatArquivo/3.0 (Premio Arquivo.pt 2026)"}
        )
        resposta.raise_for_status()
        dados = resposta.json()
        resultados = dados.get("response_items", [])

        if not resultados and (from_year or to_year):
            print("[RAG] Sem resultados com data. A tentar sem filtro temporal...")
            params_sem_filtro = {"q": query_otimizada, "maxItems": NUM_RESULTADOS, "prettyPrint": "false"}
            resp2 = requests.get(
                ARQUIVO_TEXTSEARCH_URL, params=params_sem_filtro, timeout=HTTP_TIMEOUT
            )
            resp2.raise_for_status()
            resultados = resp2.json().get("response_items", [])

        print(f"[RAG] 🔎 {len(resultados)} resultados encontrados no Arquivo.pt")
        return resultados

    except Exception as e:
        print(f"[RAG] ❌ Erro ao contactar Arquivo.pt: {e}")
        return []


# ---------------------------------------------------------------------------
# PASSO 2 — Extração e limpeza de texto HTML
# ---------------------------------------------------------------------------

def _parece_portugues(texto: str) -> bool:
    texto_norm = texto.lower()
    if re.search(r"[ãõçáéíóúâêôà]", texto_norm):
        return True
    palavras_pt = {
        "como", "que", "quem", "quando", "onde", "porque", "porquê",
        "portugal", "portugues", "portugueses", "portuguesa", "portuguesas",
        "meios", "comunicacao", "comunicação", "noticia", "noticiada",
        "reagiram", "sobre", "crise", "euro", "internet", "presidente",
        "partido", "ano", "anos",
    }
    tokens = set(re.findall(r"[a-zA-ZÀ-ÿ]+", texto_norm))
    return len(tokens & palavras_pt) >= 2


def _limpar_query_arquivo(query: str) -> str:
    query = re.sub(r"[?!.,;:]+$", "", query.strip())
    return re.sub(r"\s+", " ", query).strip()


def _termos_importantes(texto: str) -> list[str]:
    stopwords = {
        "a", "o", "os", "as", "um", "uma", "uns", "umas", "de", "do", "da",
        "dos", "das", "em", "no", "na", "nos", "nas", "por", "para", "com",
        "sem", "e", "ou", "que", "quem", "qual", "quais", "quando", "onde",
        "como", "era", "foi", "foram", "estava", "estavam", "the", "and",
        "or", "of", "in", "on", "to", "for", "was", "were", "who", "what",
        "which", "did", "how", "he", "she", "it", "they", "his", "her",
    }
    termos = []
    for token in re.findall(r"[A-Za-zÀ-ÿ0-9][A-Za-zÀ-ÿ0-9'-]*", texto):
        termo = token.strip("'")
        if len(termo) < 3 and not re.fullmatch(r"\d{4}", termo):
            continue
        if termo.lower() in stopwords:
            continue
        termos.append(termo)
    return termos


def _traduzir_pergunta_para_pesquisa_pt(pergunta: str, api_key: str) -> str:
    pergunta = pergunta.strip()
    if not pergunta or _parece_portugues(pergunta) or not api_key:
        return pergunta
    prompt = (
        "Translate this search question into European Portuguese for searching Arquivo.pt. "
        "Return only the translated search question.\n\n"
        "Preserve quoted text, backticked text, URLs, hashtags, acronyms, proper names, "
        "years, and exact foreign words/phrases explicitly being searched literally.\n\n"
        f"Question: {pergunta}"
    )
    try:
        cliente = genai.Client(api_key=api_key)
        resp = cliente.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
            config=genai_types.GenerateContentConfig(temperature=0.0, max_output_tokens=128),
        )
        traducao = (resp.text or "").strip().strip('"')
        if traducao:
            print(f"[RAG] Tradução para pesquisa PT: '{pergunta}' -> '{traducao}'")
            return traducao
    except Exception as e:
        print(f"[RAG] Falha na tradução da query (fallback ativado): {e}")
    return pergunta


def gerar_queries_pesquisa(pergunta: str, api_key: str) -> list[str]:
    pergunta_pt = _traduzir_pergunta_para_pesquisa_pt(pergunta, api_key)
    queries = [_limpar_query_arquivo(pergunta_pt)]
    termos = _termos_importantes(pergunta_pt)
    if termos:
        queries.append(" ".join(termos[:8]))
    quoted = re.findall(r'"([^"]+)"|`([^`]+)`', pergunta)
    quoted_terms = [a or b for a, b in quoted if (a or b)]
    anos = re.findall(r"\b(?:19|20)\d{2}\b", pergunta_pt)
    if quoted_terms:
        queries.append(" ".join(f'"{q}"' for q in quoted_terms[:3]) + (" " + " ".join(anos) if anos else ""))
    if api_key:
        query_ia = otimizar_query_com_ia(pergunta_pt, api_key)
        if query_ia:
            queries.append(_limpar_query_arquivo(query_ia))
        prompt = (
            "Create 3 high-recall Arquivo.pt textsearch queries in European Portuguese for this question. "
            "Return only one query per line.\n\n"
            "Rules:\n"
            "- Do not answer the question.\n"
            "- Do not inject external facts; only rewrite the user's information need as search queries.\n"
            "- Preserve years, acronyms, proper names, URLs, and quoted foreign terms.\n"
            "- Prefer concise noun phrases and exact quoted phrases when useful.\n"
            "- Avoid overly broad single-word queries.\n\n"
            f"Original question: {pergunta}\n"
            f"Portuguese search question: {pergunta_pt}"
        )
        try:
            cliente = genai.Client(api_key=api_key)
            resp = cliente.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt,
                config=genai_types.GenerateContentConfig(temperature=0.0, max_output_tokens=192),
            )
            for linha in (resp.text or "").splitlines():
                linha = re.sub(r"^\s*[-*\d.)]+\s*", "", linha).strip().strip('"')
                if linha:
                    queries.append(_limpar_query_arquivo(linha))
        except Exception as e:
            print(f"[RAG] Falha ao gerar queries extra (fallback ativado): {e}")
    if pergunta_pt != pergunta:
        queries.append(_limpar_query_arquivo(pergunta))
    unicas = []
    vistas = set()
    for query in queries:
        query = _limpar_query_arquivo(query)
        if query and query.lower() not in vistas:
            vistas.add(query.lower())
            unicas.append(query)
    print(f"[RAG] Queries de pesquisa: {unicas[:5]}")
    return unicas[:5]


def pesquisar_arquivo_multi(queries: str | list[str], from_year: str = None, to_year: str = None) -> list[dict]:
    if isinstance(queries, str):
        queries = [queries]
    def params_para_query(query: str, incluir_datas: bool = True) -> dict:
        params = {
            "q":           query,
            "maxItems":    max(4, NUM_RESULTADOS // max(1, min(len(queries), 3))),
            "prettyPrint": "false",
        }
        if incluir_datas and from_year:
            params["from"] = f"{from_year}0101000000"
        if incluir_datas and to_year:
            params["to"] = f"{to_year}1231235959"
        return params
    def chave_resultado(item: dict) -> str:
        return item.get("linkToArchive") or item.get("originalURL") or item.get("url") or item.get("title", "")
    def executar(incluir_datas: bool) -> list[dict]:
        resultados = []
        vistos = set()
        headers = {"User-Agent": "ChatArquivo/3.0 (Premio Arquivo.pt 2026)"}
        for query in queries:
            resposta = requests.get(
                ARQUIVO_TEXTSEARCH_URL,
                params=params_para_query(query, incluir_datas),
                timeout=HTTP_TIMEOUT,
                headers=headers,
            )
            resposta.raise_for_status()
            for item in resposta.json().get("response_items", []):
                chave = chave_resultado(item)
                if chave and chave not in vistos:
                    vistos.add(chave)
                    resultados.append(item)
                if len(resultados) >= NUM_RESULTADOS:
                    break
            if len(resultados) >= NUM_RESULTADOS:
                break
        return resultados
    try:
        resultados = executar(incluir_datas=True)
        if not resultados and (from_year or to_year):
            print("[RAG] Sem resultados com data. A tentar sem filtro temporal...")
            resultados = executar(incluir_datas=False)
        print(f"[RAG] 🔎 {len(resultados)} resultados encontrados no Arquivo.pt")
        return resultados[:NUM_RESULTADOS]
    except Exception as e:
        print(f"[RAG] ❌ Erro ao contactar Arquivo.pt: {e}")
        return []


def extrair_texto_pagina(url_arquivo: str) -> str:
    """
    Faz download de uma página arquivada e extrai o texto legível,
    removendo scripts, estilos, navegação e outros elementos não-informativos.

    Utiliza BeautifulSoup com o parser lxml para máxima robustez.

    Estratégia de extracção:
    1. Remove elementos não-textuais (scripts, nav, ads, etc.)
    2. Tenta extrair de <article>, <main> ou <div class="content"> primeiro
       (conteúdo editorial principal, sem menus)
    3. Fallback para o body completo se não encontrar conteúdo estruturado
    4. Normaliza espaços e trunca ao limite definido

    Parâmetros:
        url_arquivo — URL de acesso à versão arquivada (linkToArchive do resultado)

    Retorna:
        String com o texto limpo, ou string vazia em caso de falha
    """
    try:
        headers = {
            "User-Agent": "ChatArquivo/2.0 (Premio Arquivo.pt 2026; investigacao academica)",
            "Accept-Language": "pt-PT,pt;q=0.9",
        }
        resposta = requests.get(url_arquivo, headers=headers, timeout=HTTP_TIMEOUT)
        resposta.raise_for_status()

        # Detecta encoding correctamente — muitas páginas antigas usam iso-8859-1
        if resposta.encoding and resposta.encoding.lower() in ("iso-8859-1", "latin-1", "windows-1252"):
            conteudo = resposta.content.decode("iso-8859-1", errors="replace")
        else:
            conteudo = resposta.text

        soup = BeautifulSoup(conteudo, "lxml")

        # Remove elementos que não contêm conteúdo editorial
        for tag in soup(["script", "style", "nav", "header", "footer",
                         "aside", "form", "button", "iframe", "noscript",
                         "figure", "figcaption", "picture"]):
            tag.decompose()

        # Tenta extrair o conteúdo principal (artigo/corpo) antes do fallback
        conteudo_principal = (
            soup.find("article") or
            soup.find("main") or
            soup.find(id=re.compile(r"(content|conteudo|artigo|texto|body)", re.I)) or
            soup.find(class_=re.compile(r"(content|conteudo|artigo|texto|article)", re.I)) or
            soup.find("body")
        )

        if conteudo_principal:
            texto = conteudo_principal.get_text(separator=" ", strip=True)
        else:
            texto = soup.get_text(separator=" ", strip=True)

        # Normaliza espaços múltiplos e caracteres de controlo
        texto = re.sub(r"[\r\n\t]+", " ", texto)
        texto = re.sub(r" {2,}", " ", texto).strip()

        return texto[:MAX_CHARS_POR_PAGINA]

    except requests.Timeout:
        print(f"[Extração] Timeout: {url_arquivo[:70]}")
        return ""
    except Exception as e:
        print(f"[Extração] Falha em {url_arquivo[:70]}: {type(e).__name__}")
        return ""


# ---------------------------------------------------------------------------
# PASSO 3 — Construção do contexto documental
# ---------------------------------------------------------------------------

def construir_contexto(resultados: list[dict], idioma_resposta: str = "pt") -> tuple[str, list[dict]]:
    """
    Para cada resultado do Arquivo.pt, extrai o texto da página arquivada
    e constrói um bloco de contexto estruturado que será enviado ao LLM.

    Cada documento inclui: número sequencial, data de captura legível,
    URL original e texto extraído. Este formato permite ao LLM citar fontes
    de forma precisa e verificável.

    Nota de performance: a extracção é feita sequencialmente para não sobrecarregar
    o Arquivo.pt. Com 8 resultados e timeout de 12s, o pior caso é ~96s.
    Na prática, a maioria das páginas responde em 1-3s.

    Parâmetros:
        resultados — Lista de resultados da função pesquisar_arquivo()

    Retorna:
        (contexto_str, fontes_lista)
        contexto_str — texto formatado para o prompt do LLM
        fontes_lista — metadados das fontes para exibição na UI
    """
    blocos_contexto = []
    fontes = []

    for i, item in enumerate(resultados, start=1):
        titulo_padrao = "Untitled" if idioma_resposta == "en" else "Sem título"
        titulo    = item.get("title", titulo_padrao).strip()
        url_orig  = item.get("originalURL", item.get("url", "")).strip()
        data_cap  = item.get("tstamp", "")
        link_arch = item.get("linkToArchive", "").strip()
        snippet   = item.get("snippet", "").strip()

        data_legivel = formatar_data(data_cap, idioma_resposta)

        # Tenta extrair o texto completo; usa o snippet como fallback
        texto = ""
        if link_arch:
            texto = extrair_texto_pagina(link_arch)
        if not texto:
            texto = snippet
        if not texto:
            print(f"[RAG] Documento {i} sem conteúdo recuperável, a ignorar.")
            continue

        bloco = (
            f"[DOCUMENTO {i}]\n"
            f"Título: {titulo}\n"
            f"Data de captura pelo Arquivo.pt: {data_legivel}\n"
            f"URL original: {url_orig}\n"
            f"Texto extraído:\n{texto}\n"
        )
        blocos_contexto.append(bloco)

        fontes.append({
            "numero":    i,
            "titulo":    titulo,
            "data":      data_legivel,
            "url_orig":  url_orig,
            "link_arch": link_arch,
        })

    separador = "\n" + ("─" * 50) + "\n"
    contexto_str = separador.join(blocos_contexto)
    return contexto_str, fontes


# ---------------------------------------------------------------------------
# PASSO 4 — Geração de resposta com LLM (Google Gemini)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """És o ChatArquivo, um assistente de inteligência artificial especializado em \
história de Portugal e da Internet portuguesa. És construído sobre o Arquivo.pt — o repositório \
nacional de páginas web históricas, que preserva documentos desde os anos 1990.

O teu papel é responder a perguntas usando EXCLUSIVAMENTE os documentos históricos fornecidos, \
capturados pelo Arquivo.pt.

REGRAS ABSOLUTAS — nunca as violes:
1. Baseia TODA a tua resposta no conteúdo dos documentos fornecidos. Nunca inventes factos.
2. Cita SEMPRE os documentos que usaste, referindo [DOCUMENTO N] e a sua data de captura.
3. Se os documentos fornecidos não contiverem informação suficiente, diz isso claramente \
   e descreve o que foi encontrado. Não especules nem inventes.
4. Escreve em português europeu (Portugal), de forma clara, rigorosa e acessível.
5. Estrutura a resposta com: (a) resumo em 2-3 frases; (b) desenvolvimento com citações; \
   (c) lista das fontes usadas no final.
6. Usa formatação Markdown (negrito, listas) para melhorar a legibilidade.

A tua missão: ser uma janela para o passado digital português, democratizando o acesso \
à memória histórica preservada pelo Arquivo.pt."""


# Modelos Gemini por ordem de preferencia.
# Mantem apenas modelos estaveis actuais para evitar 404 em modelos descontinuados.
MODELOS_GEMINI_PREFERENCIA = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
]


def gerar_resposta(
    pergunta: str,
    contexto: str,
    historico: list[dict] = None,
    idioma_resposta: str = "pt",
) -> str:
    """
    Envia a pergunta + contexto documental ao Google Gemini e devolve a resposta.

    Usa o novo SDK google-genai (substituto do deprecated google-generativeai).

    Gestão de histórico:
    Limitado às últimas 4 trocas (8 mensagens) para evitar erros de quota e
    não exceder o contexto do modelo.

    Gestão de modelos:
    Tenta os modelos por ordem de preferência — se o primeiro falhar (quota ou
    indisponibilidade), tenta o seguinte automaticamente.

    Parâmetros:
        pergunta  — Pergunta do utilizador
        contexto  — Documentos históricos do Arquivo.pt
        historico — Lista de dicts {"role": "user"/"model", "content": "..."} (opcional)

    Retorna:
        String com a resposta em Markdown
    """
    mensagens = {
        "pt": {
            "api_key_missing": (
                "⚠️ **Chave de API não configurada.**\n\n"
                "Define a variável de ambiente antes de iniciar o Streamlit:\n\n"
                "```bash\nexport GEMINI_API_KEY=\"AIzaSy...\"\nstreamlit run app.py\n```\n\n"
                "Obtém a tua chave gratuita em: https://aistudio.google.com/"
            ),
            "auth_error": (
                "⚠️ **Erro de autenticação com a API Gemini (403).**\n\n"
                "Verifica se a tua `GEMINI_API_KEY` é válida.\n\n"
                "Confirma em: https://aistudio.google.com/"
            ),
            "quota_error": (
                "⏳ **Limite de pedidos da API atingido.**\n\n"
                "Aguarda 60 segundos e tenta novamente.\n\n"
                "Verifica o consumo em: https://aistudio.google.com/"
            ),
            "models_unavailable": (
                "⚠️ **Não foi possível gerar uma resposta porque nenhum modelo Gemini configurado "
                "está disponível para esta chave de API.**\n\n"
                "Modelos testados: `{modelos}`\n\n"
                "Abre o Google AI Studio e confirma que modelos Gemini estão disponíveis para a tua chave."
            ),
            "generic_error": (
                "⚠️ **Não foi possível gerar uma resposta.**\n\n"
                "Erro: `{erro}`\n\n"
                "Verifica a ligação à internet e a validade da `GEMINI_API_KEY`."
            ),
            "empty_response": "A API Gemini não devolveu conteúdo utilizável.",
        },
        "en": {
            "api_key_missing": (
                "⚠️ **API key is not configured.**\n\n"
                "Set the environment variable before starting Streamlit:\n\n"
                "```bash\nexport GEMINI_API_KEY=\"AIzaSy...\"\nstreamlit run app.py\n```\n\n"
                "Get a free key at: https://aistudio.google.com/"
            ),
            "auth_error": (
                "⚠️ **Gemini API authentication error (403).**\n\n"
                "Check that your `GEMINI_API_KEY` is valid.\n\n"
                "Confirm it in: https://aistudio.google.com/"
            ),
            "quota_error": (
                "⏳ **Gemini API request limit reached.**\n\n"
                "Wait 60 seconds and try again.\n\n"
                "Check usage at: https://aistudio.google.com/"
            ),
            "models_unavailable": (
                "⚠️ **Could not generate an answer because no configured Gemini model is available "
                "for this API key.**\n\n"
                "Tried models: `{modelos}`\n\n"
                "Open Google AI Studio and confirm which Gemini models are available for your key."
            ),
            "generic_error": (
                "⚠️ **Could not generate an answer.**\n\n"
                "Error: `{erro}`\n\n"
                "Check your internet connection and that `GEMINI_API_KEY` is valid."
            ),
            "empty_response": "The Gemini API did not return usable content.",
        },
    }
    msg = mensagens["en" if idioma_resposta == "en" else "pt"]

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        return msg["api_key_missing"]

    # Inicializa o cliente com o novo SDK
    cliente = genai.Client(api_key=api_key)

    # Limita o histórico a 4 trocas para não exceder contexto nem quota
    historico_limitado = (historico or [])[-8:]

    # Constrói o histórico no formato do novo SDK (lista de Content objects)
    conteudos = []
    for msg in historico_limitado:
        role     = "user" if msg.get("role") == "user" else "model"
        conteudo = msg.get("content", "").strip()
        if conteudo:
            conteudos.append(genai_types.Content(
                role=role,
                parts=[genai_types.Part(text=conteudo)]
            ))

    instrucao_idioma = (
        "Answer in English. Keep source citations exactly as [DOCUMENTO N]. "
        "Translate summaries and explanations, but preserve proper names, URLs, "
        "dates, and source titles when needed."
        if idioma_resposta == "en"
        else "Responde em portugues europeu. Mantem as citacoes como [DOCUMENTO N]."
    )

    # Prompt actual com o contexto fresco do Arquivo.pt
    prompt_actual = (
        f"Os seguintes documentos históricos foram recuperados do Arquivo.pt "
        f"especificamente para responder a esta pergunta:\n\n"
        f"{'─'*50}\n"
        f"{contexto}\n"
        f"{'─'*50}\n\n"
        f"Pergunta do utilizador: {pergunta}\n\n"
        f"Instrucao de idioma: {instrucao_idioma}"
    )
    conteudos.append(genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=prompt_actual)]
    ))

    config_geracao = genai_types.GenerateContentConfig(
        system_instruction = SYSTEM_PROMPT,
        temperature        = 0.2,    # Baixa temperatura = respostas mais factuais
        max_output_tokens  = 2048,
    )

    # Tenta cada modelo por ordem até um funcionar
    ultimo_erro = ""
    erros_modelo = []
    for nome_modelo in MODELOS_GEMINI_PREFERENCIA:
        try:
            resposta = cliente.models.generate_content(
                model    = nome_modelo,
                contents = conteudos,
                config   = config_geracao,
            )

            # Verifica se a resposta tem conteúdo (pode ser bloqueada por safety filters)
            if not resposta.candidates:
                print(f"[RAG] {nome_modelo}: sem candidatos (safety filter?)")
                ultimo_erro = msg["empty_response"]
                continue

            texto = resposta.text
            if texto and texto.strip():
                print(f"[RAG] Resposta gerada com sucesso via {nome_modelo}")
                return texto.strip()
            else:
                print(f"[RAG] {nome_modelo}: resposta vazia")
                ultimo_erro = msg["empty_response"]
                continue

        except Exception as e:
            ultimo_erro = str(e)
            erros_modelo.append((nome_modelo, ultimo_erro))

            if "429" in ultimo_erro or "quota" in ultimo_erro.lower() or "rate" in ultimo_erro.lower():
                print(f"[RAG] {nome_modelo}: quota excedida, a tentar próximo modelo...")
                time.sleep(2)
                continue
            elif "404" in ultimo_erro or "not found" in ultimo_erro.lower():
                print(f"[RAG] {nome_modelo}: modelo indisponível, a tentar próximo...")
                continue
            elif "403" in ultimo_erro or "api_key" in ultimo_erro.lower() or "permission" in ultimo_erro.lower():
                # Erro de autenticação — inútil tentar outros modelos
                return msg["auth_error"]
            else:
                print(f"[RAG] {nome_modelo}: erro inesperado — {ultimo_erro[:120]}")
                continue

    # Todos os modelos falharam
    if "429" in ultimo_erro or "quota" in ultimo_erro.lower():
        return msg["quota_error"]

    if erros_modelo and all(
        "404" in erro or "not found" in erro.lower()
        for _, erro in erros_modelo
    ):
        modelos = ", ".join(nome for nome, _ in erros_modelo)
        return msg["models_unavailable"].format(modelos=modelos)

    return msg["generic_error"].format(erro=(ultimo_erro or msg["empty_response"])[:200])


# ---------------------------------------------------------------------------
# Pipeline principal — orquestra todos os passos
# ---------------------------------------------------------------------------

def responder_pergunta(
    pergunta:  str,
    from_year: str        = None,
    to_year:   str        = None,
    historico: list[dict] = None,
    idioma_resposta: str  = "pt",
) -> tuple[str, list[dict]]:
    
    print(f"\n{'='*60}")
    print(f"[RAG] Nova pergunta: '{pergunta}'")
    
    # Vamos buscar a API Key aqui para a podermos passar à nossa nova Camada 1
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()

    mensagens = {
        "pt": {
            "sem_resultados": "📭 **Não foram encontrados documentos no Arquivo.pt para esta pesquisa.**\n\nExperimenta reformular a pergunta.",
            "sem_conteudo": "📄 **Encontrei páginas, mas não foi possível extrair o seu conteúdo.**\n\nO Arquivo.pt pode estar sobrecarregado.",
        },
        "en": {
            "sem_resultados": "📭 **No documents were found in Arquivo.pt for this search.**\n\nTry rephrasing your question.",
            "sem_conteudo": "📄 **Pages were found, but their content could not be extracted.**\n\nArquivo.pt might be overloaded.",
        },
    }
    m = mensagens["en" if idioma_resposta == "en" else "pt"]

    # Passo 1A: gerar variantes genericas de pesquisa para o indice do Arquivo.pt
    queries_pesquisa = gerar_queries_pesquisa(pergunta, api_key)

    # Passo 1B: Recuperar documentos históricos do Arquivo.pt
    resultados = pesquisar_arquivo_multi(queries_pesquisa, from_year, to_year)

    if not resultados:
        return m["sem_resultados"], []

    # Passos 2 e 3: Extrair texto e construir contexto documental
    contexto, fontes = construir_contexto(resultados, idioma_resposta)

    if not fontes:
        return m["sem_conteudo"], []

    print(f"[RAG] 📚 Contexto construído com {len(fontes)} documentos")

    # Passo 4: Gerar resposta com o LLM (Gemini atua como Re-ranker e Gerador)
    resposta = gerar_resposta(pergunta, contexto, historico, idioma_resposta)

    return resposta, fontes


# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------

def formatar_data(tstamp: str, idioma: str = "pt") -> str:
    """
    Converte o timestamp do Arquivo.pt (formato: YYYYMMDDHHmmss)
    para uma data legível em português (ex: "15 de outubro de 2002").

    Devolve o timestamp original se não conseguir converter.
    """
    meses_pt = [
        "", "janeiro", "fevereiro", "março", "abril", "maio", "junho",
        "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
    ]
    meses_en = [
        "", "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    try:
        if len(tstamp) < 8:
            return tstamp
        ano = tstamp[0:4]
        mes = int(tstamp[4:6])
        dia = tstamp[6:8].lstrip("0") or "1"
        if not (1 <= mes <= 12):
            return tstamp
        if idioma == "en":
            return f"{meses_en[mes]} {dia}, {ano}"
        return f"{dia} de {meses_pt[mes]} de {ano}"
    except (IndexError, ValueError):
        return tstamp
