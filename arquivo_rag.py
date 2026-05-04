"""
================================================================================
ChatArquivo — Motor RAG (Retrieval-Augmented Generation)
================================================================================

Módulo central do sistema. Responsável por:
    1. Consultar a API de pesquisa de texto do Arquivo.pt
    2. Extrair e limpar o texto HTML dos resultados históricos
    3. Construir um contexto documental datado e citável
    4. Enviar esse contexto + pergunta do utilizador a um LLM (Gemini)
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
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai

# ---------------------------------------------------------------------------
# Configuração da API do Arquivo.pt
# Documentação: https://arquivo.pt/api
# ---------------------------------------------------------------------------

ARQUIVO_TEXTSEARCH_URL = "https://arquivo.pt/textsearch"
ARQUIVO_BASE_URL       = "https://arquivo.pt"

# Número de resultados a recuperar do Arquivo.pt (mais = mais contexto, mas mais lento)
NUM_RESULTADOS = 8

# Comprimento máximo de texto extraído por página (em caracteres)
# O Gemini 1.5 Pro suporta bem contexto mais longo
MAX_CHARS_POR_PAGINA = 2000


# ---------------------------------------------------------------------------
# PASSO 1 — Pesquisa no Arquivo.pt
# ---------------------------------------------------------------------------

def pesquisar_arquivo(query: str, from_year: str = None, to_year: str = None) -> list[dict]:
    """
    Consulta a API de pesquisa de texto do Arquivo.pt e devolve uma lista
    de resultados com metadados (URL original, data de captura, snippet, etc.).

    Parâmetros:
        query      — Texto de pesquisa livre (ex: "crise financeira Portugal 2011")
        from_year  — Ano de início do intervalo temporal (ex: "2008"), opcional
        to_year    — Ano de fim do intervalo temporal (ex: "2012"), opcional

    Retorna:
        Lista de dicionários com campos: title, url, tstamp, linkToArchive, snippet
    """
    params = {
        "q":        query,
        "maxItems": NUM_RESULTADOS,
        "prettyPrint": "false",
    }

    # Filtro temporal opcional — muito útil para perguntas históricas precisas
    if from_year:
        params["from"] = f"{from_year}0101000000"
    if to_year:
        params["to"]   = f"{to_year}1231235959"

    try:
        resposta = requests.get(ARQUIVO_TEXTSEARCH_URL, params=params, timeout=15)
        resposta.raise_for_status()
        dados = resposta.json()

        # A API devolve os resultados dentro de "response_items"
        return dados.get("response_items", [])

    except requests.RequestException as e:
        # Falha de rede ou API indisponível — devolve lista vazia para não quebrar o fluxo
        print(f"[Arquivo.pt] Erro na pesquisa: {e}")
        return []


# ---------------------------------------------------------------------------
# PASSO 2 — Extração e limpeza de texto HTML
# ---------------------------------------------------------------------------

def extrair_texto_pagina(url_arquivo: str) -> str:
    """
    Faz download de uma página arquivada e extrai o texto legível,
    removendo scripts, estilos, navegação e outros elementos não-informativos.

    Utiliza BeautifulSoup para parsing HTML robusto.

    Parâmetros:
        url_arquivo — URL de acesso à versão arquivada (ex: linkToArchive do resultado)

    Retorna:
        String com o texto limpo da página, truncada a MAX_CHARS_POR_PAGINA
    """
    try:
        headers = {"User-Agent": "ChatArquivo/1.0 (Premio Arquivo.pt 2026; investigacao academica)"}
        resposta = requests.get(url_arquivo, headers=headers, timeout=10)
        resposta.raise_for_status()

        soup = BeautifulSoup(resposta.content, "html.parser")

        # Remove elementos que não contêm conteúdo informativo
        for tag in soup(["script", "style", "nav", "header", "footer",
                         "aside", "form", "button", "iframe", "noscript"]):
            tag.decompose()

        # Extrai texto e normaliza espaços em branco
        texto = soup.get_text(separator=" ", strip=True)
        texto = re.sub(r"\s+", " ", texto).strip()

        return texto[:MAX_CHARS_POR_PAGINA]

    except Exception as e:
        # Página inacessível ou formato não suportado — devolve string vazia
        print(f"[Extração] Não foi possível extrair {url_arquivo}: {e}")
        return ""


# ---------------------------------------------------------------------------
# PASSO 3 — Construção do contexto documental
# ---------------------------------------------------------------------------

def construir_contexto(resultados: list[dict]) -> tuple[str, list[dict]]:
    """
    Para cada resultado do Arquivo.pt, extrai o texto da página arquivada
    e constrói um bloco de contexto estruturado que será enviado ao LLM.

    Cada documento inclui: número, data de captura, URL original, e texto extraído.
    Este formato permite ao LLM citar fontes de forma precisa e verificável.

    Parâmetros:
        resultados — Lista de resultados da função pesquisar_arquivo()

    Retorna:
        (contexto_str, fontes_lista)
        - contexto_str: texto formatado para incluir no prompt do LLM
        - fontes_lista: lista de dicionários com metadados das fontes usadas
    """
    blocos_contexto = []
    fontes = []

    for i, item in enumerate(resultados, start=1):
        titulo      = item.get("title", "Sem título")
        url_orig    = item.get("originalURL", item.get("url", ""))
        data_cap    = item.get("tstamp", "")
        link_arch   = item.get("linkToArchive", "")
        snippet     = item.get("snippet", "")

        # Formata a data de captura legível (ex: 20021015120000 → 15/10/2002)
        data_legivel = formatar_data(data_cap)

        # Tenta extrair o texto completo da página; se falhar, usa o snippet da API
        texto = extrair_texto_pagina(link_arch) if link_arch else ""
        if not texto and snippet:
            texto = snippet

        if not texto:
            continue  # Ignora resultados sem conteúdo recuperável

        # Bloco de contexto formatado para o LLM
        bloco = (
            f"[DOCUMENTO {i}]\n"
            f"Título: {titulo}\n"
            f"Data de captura: {data_legivel}\n"
            f"URL original: {url_orig}\n"
            f"Conteúdo:\n{texto}\n"
        )
        blocos_contexto.append(bloco)

        # Registo da fonte para exibição na interface
        fontes.append({
            "numero":     i,
            "titulo":     titulo,
            "data":       data_legivel,
            "url_orig":   url_orig,
            "link_arch":  link_arch,
        })

    contexto_str = "\n" + "="*60 + "\n".join(blocos_contexto)
    return contexto_str, fontes


# ---------------------------------------------------------------------------
# PASSO 4 — Geração de resposta com LLM (Google Gemini Pro)
# ---------------------------------------------------------------------------

# System prompt cuidadosamente elaborado para garantir:
# - Rigor histórico (não inventar factos)
# - Citação obrigatória de fontes do Arquivo.pt
# - Resposta estruturada e acessível a não-especialistas
SYSTEM_PROMPT = """És o ChatArquivo, um assistente de inteligência artificial especializado em \
história de Portugal e da Internet portuguesa, construído sobre o Arquivo.pt — o repositório \
nacional de páginas web históricas.

O teu papel é responder a perguntas usando EXCLUSIVAMENTE os documentos históricos fornecidos, \
capturados pelo Arquivo.pt entre os anos 1990 e 2026.

REGRAS OBRIGATÓRIAS:
1. Baseia a tua resposta APENAS no conteúdo dos documentos fornecidos. Nunca inventes factos.
2. Cita sempre os documentos que usaste, referindo o número [DOCUMENTO N] e a data de captura.
3. Se os documentos não contiverem informação suficiente para responder, diz-o claramente e \
   explica que resultados foram encontrados.
4. Escreve em português europeu, de forma clara, rigorosa e acessível.
5. Organiza a resposta com um resumo inicial, seguido de detalhes com citações das fontes.
6. No final, indica explicitamente quais os documentos do Arquivo.pt que fundamentaram a resposta.

Lembra-te: és uma janela para o passado. A tua missão é preservar e democratizar \
o acesso à memória digital portuguesa."""


def gerar_resposta(pergunta: str, contexto: str, historico: list[dict] = None) -> str:
    """
    Envia a pergunta do utilizador, o contexto documental do Arquivo.pt,
    e o histórico de conversa para o Gemini (Google API).

    O LLM actua como historiador/jornalista que analisa documentos primários
    e sintetiza uma resposta fundamentada e citável.

    Parâmetros:
        pergunta   — Pergunta do utilizador em linguagem natural
        contexto   — Texto com os documentos históricos extraídos do Arquivo.pt
        historico  — Lista de mensagens anteriores (para manter contexto de conversa)

    Retorna:
        String com a resposta gerada pelo LLM
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "⚠️ Erro: GEMINI_API_KEY não está configurada no terminal."

    genai.configure(api_key=api_key)

    modelo = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        system_instruction=SYSTEM_PROMPT,
    )

    gemini_history = []
    if historico:
        for msg in historico:
            role = "user" if msg.get("role") == "user" else "model"
            gemini_history.append({"role": role, "parts": [msg.get("content", "")]})

    chat = modelo.start_chat(history=gemini_history)

    prompt_atual = (
        f"Documentos históricos recuperados do Arquivo.pt:\n\n"
        f"{contexto}\n\n"
        f"{'='*60}\n\n"
        f"Pergunta: {pergunta}"
    )

    try:
        resposta = chat.send_message(prompt_atual)
        return resposta.text
    except Exception as e:
        return f"⚠️ Erro ao contactar o Gemini: {e}"


# ---------------------------------------------------------------------------
# Pipeline principal — orquestra todos os passos
# ---------------------------------------------------------------------------

def responder_pergunta(
    pergunta: str,
    from_year: str = None,
    to_year: str   = None,
    historico: list[dict] = None
) -> tuple[str, list[dict]]:
    """
    Função de entrada principal do motor RAG.
    Orquestra os 4 passos: Pesquisa → Extração → Contexto → Geração.

    Parâmetros:
        pergunta   — Pergunta em linguagem natural
        from_year  — Filtro temporal de início (opcional)
        to_year    — Filtro temporal de fim (opcional)
        historico  — Histórico de conversa (opcional, para multi-turno)

    Retorna:
        (resposta_str, fontes_lista)
    """
    # Passo 1: Recuperar documentos históricos do Arquivo.pt
    resultados = pesquisar_arquivo(pergunta, from_year, to_year)

    if not resultados:
        mensagem_vazia = (
            "Não foram encontrados documentos no Arquivo.pt para esta pesquisa. "
            "Tenta reformular a pergunta ou alargar o intervalo temporal."
        )
        return mensagem_vazia, []

    # Passo 2 & 3: Extrair texto e construir contexto documental
    contexto, fontes = construir_contexto(resultados)

    if not fontes:
        mensagem_vazia = (
            "Os documentos encontrados não puderam ser acedidos para extração de conteúdo. "
            "O Arquivo.pt pode estar temporariamente sobrecarregado. Tenta novamente."
        )
        return mensagem_vazia, []

    # Passo 4: Gerar resposta com o LLM usando os documentos como contexto
    resposta = gerar_resposta(pergunta, contexto, historico)

    return resposta, fontes


# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------

def formatar_data(tstamp: str) -> str:
    """
    Converte o timestamp do Arquivo.pt (formato: YYYYMMDDHHmmss)
    para uma data legível em português (ex: "15 de outubro de 2002").
    """
    meses = [
        "", "janeiro", "fevereiro", "março", "abril", "maio", "junho",
        "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
    ]
    try:
        ano = tstamp[0:4]
        mes = int(tstamp[4:6])
        dia = tstamp[6:8]
        return f"{dia} de {meses[mes]} de {ano}"
    except (IndexError, ValueError):
        return tstamp  # Devolve o original se não conseguir converter
