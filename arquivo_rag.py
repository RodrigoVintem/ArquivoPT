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

# Número de resultados a recuperar. 8 garante contexto rico sem exceder limites.
NUM_RESULTADOS = 8

# Comprimento máximo de texto extraído por página (em caracteres).
# 2000 chars ≈ 500 tokens — bom equilíbrio entre contexto e custo de API.
MAX_CHARS_POR_PAGINA = 2000

# Timeout para pedidos HTTP ao Arquivo.pt (segundos)
HTTP_TIMEOUT = 12


# ---------------------------------------------------------------------------
# PASSO 1 — Pesquisa no Arquivo.pt
# ---------------------------------------------------------------------------

def _construir_query_arquivo(pergunta: str) -> str:
    """
    Constrói a query mais eficaz para a API do Arquivo.pt a partir de uma
    pergunta em linguagem natural.

    ESTRATÉGIA CORRETA:
    A API textsearch do Arquivo.pt aceita linguagem natural e operadores booleanos.
    NÃO se deve reduzir a pergunta a keywords simples — isso perde contexto semântico
    e retorna resultados irrelevantes (ex: "presidente Portugal" devolve qualquer
    página com essas palavras, não necessariamente sobre o presidente).

    Em vez disso:
    - Remove apenas artigos soltos e pontuação desnecessária
    - Preserva nomes próprios, datas e termos técnicos
    - Usa aspas para expressões-chave quando a pergunta é específica

    Parâmetros:
        pergunta — Pergunta em linguagem natural

    Retorna:
        String de query optimizada para o Arquivo.pt
    """
    # Remove pontuação de fim de frase mas preserva hífen e apóstrofe
    q = re.sub(r"[?!.,;:]+$", "", pergunta.strip())

    # Remove prefixos interrogativos comuns que não acrescentam valor à pesquisa
    # mas preserva os termos substantivos que se seguem
    prefixos = [
        r"^(diz[- ]me|explica[- ]me|quero saber|podes dizer)\s+",
        r"^(what|who|when|where|how)\s+",
    ]
    for p in prefixos:
        q = re.sub(p, "", q, flags=re.IGNORECASE)

    # Normaliza espaços múltiplos
    q = re.sub(r"\s+", " ", q).strip()

    print(f"[RAG] Query para Arquivo.pt: '{q}'")
    return q


def pesquisar_arquivo(pergunta: str, from_year: str = None, to_year: str = None) -> list[dict]:
    """
    Consulta a API de pesquisa de texto do Arquivo.pt e devolve uma lista
    de resultados com metadados (URL original, data de captura, snippet, etc.).

    A API suporta linguagem natural — não é necessário reduzir a keywords.
    Faz uma segunda tentativa sem filtro temporal se a primeira vier vazia,
    garantindo sempre resultados mesmo com datas mal configuradas.

    Parâmetros:
        pergunta   — Pergunta em linguagem natural
        from_year  — Ano de início do intervalo temporal (ex: "2008"), opcional
        to_year    — Ano de fim do intervalo temporal (ex: "2012"), opcional

    Retorna:
        Lista de dicionários com campos: title, originalURL, tstamp, linkToArchive, snippet
    """
    query = _construir_query_arquivo(pergunta)

    params = {
        "q":           query,
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
            headers={"User-Agent": "ChatArquivo/2.0 (Premio Arquivo.pt 2026)"}
        )
        resposta.raise_for_status()
        dados = resposta.json()
        resultados = dados.get("response_items", [])

        # Se não há resultados com filtro temporal, tenta sem filtro
        # Isto evita o erro "não encontrado" quando o utilizador usa datas muito restritas
        if not resultados and (from_year or to_year):
            print("[RAG] Sem resultados com filtro temporal — a tentar sem filtro...")
            params_sem_filtro = {"q": query, "maxItems": NUM_RESULTADOS, "prettyPrint": "false"}
            resp2 = requests.get(
                ARQUIVO_TEXTSEARCH_URL,
                params=params_sem_filtro,
                timeout=HTTP_TIMEOUT,
                headers={"User-Agent": "ChatArquivo/2.0 (Premio Arquivo.pt 2026)"}
            )
            resp2.raise_for_status()
            resultados = resp2.json().get("response_items", [])

        print(f"[RAG] {len(resultados)} resultados encontrados no Arquivo.pt")
        return resultados

    except requests.Timeout:
        print("[RAG] Timeout na API do Arquivo.pt")
        return []
    except requests.HTTPError as e:
        print(f"[RAG] Erro HTTP do Arquivo.pt: {e.response.status_code}")
        return []
    except (requests.RequestException, ValueError) as e:
        print(f"[RAG] Erro ao contactar Arquivo.pt: {e}")
        return []


# ---------------------------------------------------------------------------
# PASSO 2 — Extração e limpeza de texto HTML
# ---------------------------------------------------------------------------

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

def construir_contexto(resultados: list[dict]) -> tuple[str, list[dict]]:
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
        titulo    = item.get("title", "Sem título").strip()
        url_orig  = item.get("originalURL", item.get("url", "")).strip()
        data_cap  = item.get("tstamp", "")
        link_arch = item.get("linkToArchive", "").strip()
        snippet   = item.get("snippet", "").strip()

        data_legivel = formatar_data(data_cap)

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


# Modelos Gemini por ordem de preferência.
# gemini-1.5-flash é o mais fiável e está disponível no tier gratuito.
# gemini-2.0-flash e gemini-2.5-flash são tentados primeiro se disponíveis.
MODELOS_GEMINI_PREFERENCIA = [
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
]


def gerar_resposta(pergunta: str, contexto: str, historico: list[dict] = None) -> str:
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
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        return (
            "⚠️ **Chave de API não configurada.**\n\n"
            "Define a variável de ambiente antes de iniciar o Streamlit:\n\n"
            "```bash\nexport GEMINI_API_KEY=\"AIzaSy...\"\nstreamlit run app.py\n```\n\n"
            "Obtém a tua chave gratuita em: https://aistudio.google.com/"
        )

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

    # Prompt actual com o contexto fresco do Arquivo.pt
    prompt_actual = (
        f"Os seguintes documentos históricos foram recuperados do Arquivo.pt "
        f"especificamente para responder a esta pergunta:\n\n"
        f"{'─'*50}\n"
        f"{contexto}\n"
        f"{'─'*50}\n\n"
        f"Pergunta do utilizador: {pergunta}"
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
                continue

            texto = resposta.text
            if texto and texto.strip():
                print(f"[RAG] Resposta gerada com sucesso via {nome_modelo}")
                return texto.strip()
            else:
                print(f"[RAG] {nome_modelo}: resposta vazia")
                continue

        except Exception as e:
            ultimo_erro = str(e)

            if "429" in ultimo_erro or "quota" in ultimo_erro.lower() or "rate" in ultimo_erro.lower():
                print(f"[RAG] {nome_modelo}: quota excedida, a tentar próximo modelo...")
                time.sleep(2)
                continue
            elif "404" in ultimo_erro or "not found" in ultimo_erro.lower():
                print(f"[RAG] {nome_modelo}: modelo indisponível, a tentar próximo...")
                continue
            elif "403" in ultimo_erro or "api_key" in ultimo_erro.lower() or "permission" in ultimo_erro.lower():
                # Erro de autenticação — inútil tentar outros modelos
                return (
                    "⚠️ **Erro de autenticação com a API Gemini (403).**\n\n"
                    "Verifica se a tua `GEMINI_API_KEY` é válida.\n\n"
                    "Confirma em: https://aistudio.google.com/"
                )
            else:
                print(f"[RAG] {nome_modelo}: erro inesperado — {ultimo_erro[:120]}")
                continue

    # Todos os modelos falharam
    if "429" in ultimo_erro or "quota" in ultimo_erro.lower():
        return (
            "⏳ **Limite de pedidos da API atingido.**\n\n"
            "O plano gratuito permite **15 pedidos/minuto** e **1 500/dia**. "
            "Aguarda 60 segundos e tenta novamente.\n\n"
            "Verifica o consumo em: https://aistudio.google.com/"
        )

    return (
        f"⚠️ **Não foi possível gerar uma resposta.**\n\n"
        f"Erro: `{ultimo_erro[:200]}`\n\n"
        f"Verifica a ligação à internet e a validade da `GEMINI_API_KEY`."
    )


# ---------------------------------------------------------------------------
# Pipeline principal — orquestra todos os passos
# ---------------------------------------------------------------------------

def responder_pergunta(
    pergunta:  str,
    from_year: str        = None,
    to_year:   str        = None,
    historico: list[dict] = None,
) -> tuple[str, list[dict]]:
    """
    Função de entrada principal do motor RAG.
    Orquestra os 4 passos: Pesquisa → Extracção → Contexto → Geração.

    Parâmetros:
        pergunta  — Pergunta em linguagem natural
        from_year — Filtro temporal de início (opcional)
        to_year   — Filtro temporal de fim (opcional)
        historico — Histórico de conversa (opcional, para perguntas de seguimento)

    Retorna:
        (resposta_str, fontes_lista)
        resposta_str — Texto em Markdown com a resposta e citações
        fontes_lista — Lista de dicts com metadados das fontes (para a UI)
    """
    print(f"\n{'='*60}")
    print(f"[RAG] Nova pergunta: '{pergunta}'")
    if from_year:
        print(f"[RAG] Filtro temporal: {from_year} → {to_year}")

    # Passo 1: Recuperar documentos históricos do Arquivo.pt
    resultados = pesquisar_arquivo(pergunta, from_year, to_year)

    if not resultados:
        return (
            "📭 **Não foram encontrados documentos no Arquivo.pt para esta pesquisa.**\n\n"
            "Sugestões:\n"
            "- Reformula a pergunta com termos mais simples ou mais específicos\n"
            "- Experimenta sem filtro temporal, ou com um intervalo mais alargado\n"
            "- Verifica a tua ligação à internet\n"
            "- O Arquivo.pt pode estar temporariamente indisponível (tenta em https://arquivo.pt)"
        ), []

    # Passos 2 e 3: Extrair texto e construir contexto documental
    contexto, fontes = construir_contexto(resultados)

    if not fontes:
        return (
            "📄 **Foram encontrados documentos no Arquivo.pt mas não foi possível extrair o seu conteúdo.**\n\n"
            "Isto pode acontecer quando as páginas arquivadas estão em formatos não suportados "
            "(Flash, PDF, imagens) ou quando o Arquivo.pt está sobrecarregado.\n\n"
            f"Encontrei {len(resultados)} resultado(s). Tenta novamente ou reformula a pergunta."
        ), []

    print(f"[RAG] Contexto construído com {len(fontes)} documentos")

    # Passo 4: Gerar resposta com o LLM
    resposta = gerar_resposta(pergunta, contexto, historico)

    return resposta, fontes


# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------

def formatar_data(tstamp: str) -> str:
    """
    Converte o timestamp do Arquivo.pt (formato: YYYYMMDDHHmmss)
    para uma data legível em português (ex: "15 de outubro de 2002").

    Devolve o timestamp original se não conseguir converter.
    """
    MESES = [
        "", "janeiro", "fevereiro", "março", "abril", "maio", "junho",
        "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
    ]
    try:
        if len(tstamp) < 8:
            return tstamp
        ano = tstamp[0:4]
        mes = int(tstamp[4:6])
        dia = tstamp[6:8].lstrip("0") or "1"
        if not (1 <= mes <= 12):
            return tstamp
        return f"{dia} de {MESES[mes]} de {ano}"
    except (IndexError, ValueError):
        return tstamp