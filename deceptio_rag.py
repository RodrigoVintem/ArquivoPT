"""
================================================================================
DECEPTIO — Motor RAG de Auditoria de Desinformação (4 Camadas)
================================================================================

Pipeline especializado na deteção de desinformação histórica na Internet
portuguesa. Usa o Arquivo.pt como fonte primária e o Google Gemini como
auditor inteligente.

CAMADA 1 — Query Expansion (Gemini Flash Lite)
  Gera 3 queries optimizadas. Dá prioridade a fontes .pt e publico.pt.

CAMADA 2 — Retrieval Multi-Query paralelo (Arquivo.pt)
  3 queries × 15 resultados = até 45 candidatos únicos.
  Boost de relevância para fontes publico.pt (Menção Honrosa).

CAMADA 3 — Re-ranking por Relevância para Desinformação (Gemini Flash Lite)
  Seleciona os 5 documentos mais úteis para confirmar ou refutar a afirmação.

CAMADA 4 — Auditoria de Factos (Gemini Flash)
  Cruza os documentos históricos com o conhecimento global do LLM.
  Emite um VEREDITO claro com citações verificáveis.

Prémio Arquivo.pt 2026 — DECEPTIO
Autor: [O teu nome] · [Faculdade/Universidade]
================================================================================
"""

import os
import re
import json
import time
import concurrent.futures
import requests
import tomllib
from bs4 import BeautifulSoup
from google import genai
from google.genai import types as genai_types

# ── Constantes ────────────────────────────────────────────────────────────────

ARQUIVO_URL        = "https://arquivo.pt/textsearch"
RESULTADOS_QUERY   = 15        # por query → 3 queries = até 45 candidatos
NUM_DOCS_RERANKED  = 5         # documentos que chegam à Camada 4
MAX_CHARS_PAGINA   = 2500      # caracteres extraídos por página
HTTP_TIMEOUT       = 15        # segundos por pedido HTTP
SEARCH_TIMEOUT     = 45        # Arquivo.pt pode demorar em queries amplas

# Modelos por função
MODELO_LEVE   = "gemini-2.5-flash-lite"   # C1 e C3: rápido e barato
MODELO_FORTE  = "gemini-2.5-flash"         # C4: qualidade máxima

FALLBACK_LEVE  = ["gemini-2.5-flash-lite", "gemini-2.0-flash"]
FALLBACK_FORTE = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.5-flash-lite"]

# ── Cliente Gemini ─────────────────────────────────────────────────────────────

def _ler_chave_gemini() -> str:
    """Lê a chave Gemini de env vars, Streamlit secrets ou .env local."""
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if key:
        return key

    secrets_path = os.path.join(os.getcwd(), ".streamlit", "secrets.toml")
    try:
        with open(secrets_path, "rb") as f:
            secrets = tomllib.load(f)
        key = str(secrets.get("GEMINI_API_KEY", "")).strip()
        if key:
            return key
    except FileNotFoundError:
        pass
    except Exception:
        pass

    env_path = os.path.join(os.getcwd(), ".env")
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                name, value = line.split("=", 1)
                if name.strip() == "GEMINI_API_KEY":
                    return value.strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    except Exception:
        pass

    return ""


def _cliente() -> tuple:
    """Retorna (cliente, "") ou (None, msg_erro)."""
    key = _ler_chave_gemini()
    if not key:
        return None, (
            "⚠️ **GEMINI_API_KEY não configurada.**\n\n"
            "Configura a chave de uma destas formas:\n\n"
            "```toml\n# .streamlit/secrets.toml\nGEMINI_API_KEY = \"AIzaSy...\"\n```\n\n"
            "```bash\n# .env\nGEMINI_API_KEY=AIzaSy...\n```\n\n"
            "Depois reinicia o Streamlit.\n\n"
            "Chave gratuita em: https://aistudio.google.com/"
        )
    return genai.Client(api_key=key), ""


def _erro_quota(err: str) -> bool:
    err_l = err.lower()
    return "429" in err or "quota" in err_l or "rate" in err_l or "resource_exhausted" in err_l


def _erro_auth(err: str) -> bool:
    err_l = err.lower()
    return "403" in err or "api_key" in err_l or "permission_denied" in err_l


def _erro_modelo_indisponivel(err: str) -> bool:
    err_l = err.lower()
    return "404" in err or "not_found" in err_l or "is not found" in err_l


def _gemini(cliente, modelos: list, prompt: str, system: str,
            temp: float = 0.1, tokens: int = 512) -> str | None:
    """
    Chama o Gemini com fallback automático entre modelos.
    Retorna o texto da resposta, ou None se todos falharem.
    """
    cfg = genai_types.GenerateContentConfig(
        system_instruction = system,
        temperature        = temp,
        max_output_tokens  = tokens,
    )
    for modelo in modelos:
        try:
            r = cliente.models.generate_content(
                model    = modelo,
                contents = [genai_types.Content(role="user", parts=[genai_types.Part(text=prompt)])],
                config   = cfg,
            )
            if r.candidates and r.text and r.text.strip():
                return r.text.strip()
        except Exception as e:
            err = str(e)
            if _erro_quota(err):
                time.sleep(1)
            elif _erro_auth(err):
                return None   # Erro de auth — inutíl tentar outros modelos
            elif _erro_modelo_indisponivel(err):
                print(f"[Gemini] Modelo indisponível: {modelo}")
            # 404 / outros → tenta o próximo
    return None


# ── CAMADA 1: Query Expansion ─────────────────────────────────────────────────

_SYS_QUERIES = """És um especialista em pesquisa de arquivos históricos portugueses.
Dado um tema ou afirmação para verificação de factos, gera 3 queries de pesquisa
optimizadas para um motor de busca de arquivo web (busca por keywords, não semântica).

REGRAS:
- MÁXIMO 2 a 4 palavras fundamentais por query (mais do que isto falha na API)
- Query 1: termos gerais do tema (ex: "bug ano 2000")
- Query 2: termos específicos / nomes próprios (ex: "Y2K bancos falhas")
- Query 3: variante com sinónimos (ex: "millennium bug computadores")
- NUNCA uses stop words (o, a, de, do, que, em, para, com, etc)
- NÃO incluas a palavra "Portugal" ou "português" (já estamos a pesquisar num arquivo nacional)

Responde APENAS com JSON sem texto extra:
{"queries": ["query 1", "query 2", "query 3"]}"""


def gerar_queries(afirmacao: str, cliente) -> list[str]:
    """
    CAMADA 1: Gera 3 queries optimizadas para a API do Arquivo.pt.

    Exemplos de transformação:
      "O Y2K ia destruir os bancos portugueses"
        → ["bug ano 2000 Y2K bancos", "millennium bug Portugal informática 1999", "Y2K pânico exagerado desmistificado"]
      "A Ponte Vasco da Gama tinha falhas em 1998"
        → ["ponte vasco gama inauguração 1998", "ponte vasco gama falhas estruturais", "ponte vasco gama segurança obra"]
    """
    print(f"[C1] Afirmação: '{afirmacao[:60]}'")

    raw = _gemini(
        cliente = cliente,
        modelos = FALLBACK_LEVE,
        prompt  = f"Afirmação a verificar: {afirmacao}",
        system  = _SYS_QUERIES,
        temp    = 0.3,
        tokens  = 200,
    )

    if raw:
        try:
            limpo  = re.sub(r"```(?:json)?", "", raw).strip().strip("`")
            dados  = json.loads(limpo)
            qs     = [q.strip() for q in dados.get("queries", []) if isinstance(q, str) and q.strip()][:3]
            if len(qs) >= 1:
                print(f"[C1] Queries: {qs}")
                return qs
        except Exception as e:
            print(f"[C1] Falha JSON: {e} | Raw: {raw[:80]}")

    # Fallback manual: extrai keywords simples
    stop = {"o","a","os","as","um","uma","que","se","em","de","do","da","dos","das",
            "para","com","por","foi","era","é","na","no","nos","nas","ao","à","ia",
            "isso","isto","quando","onde","quem","qual","tinha","tem","têm","ser"}
    q = re.sub(r"[?!.,;:()\[\]]+", "", afirmacao.lower())
    kw = [w for w in q.split() if w not in stop and len(w) > 2]
    fallback = " ".join(kw[:6])
    print(f"[C1] Fallback query: '{fallback}'")
    return [fallback]


# ── CAMADA 2: Retrieval Multi-Query ───────────────────────────────────────────

def _pesquisar(query: str, from_year: str = None, to_year: str = None) -> list[dict]:
    """Executa um pedido HTTP à API do Arquivo.pt para uma query."""
    params = {
        "q":           query,
        "maxItems":    RESULTADOS_QUERY,
        "prettyPrint": "false",
    }
    if from_year:
        params["from"] = f"{from_year}0101000000"
    if to_year:
        params["to"]   = f"{to_year}1231235959"

    try:
        r = requests.get(
            ARQUIVO_URL,
            params  = params,
            timeout = SEARCH_TIMEOUT,
            headers = {"User-Agent": "Deceptio/1.0 (Premio Arquivo.pt 2026)"},
        )
        r.raise_for_status()
        resultados = r.json().get("response_items", [])
        print(f"[C2] '{query[:35]}' -> {len(resultados)} resultados")
        return resultados
    except requests.Timeout:
        print(f"[C2] Timeout: '{query[:35]}' - retry reduzido")
        try:
            params["maxItems"] = 5
            r = requests.get(
                ARQUIVO_URL,
                params=params,
                timeout=SEARCH_TIMEOUT,
                headers={"User-Agent": "Deceptio/1.0 (Premio Arquivo.pt 2026)"},
            )
            r.raise_for_status()
            resultados = r.json().get("response_items", [])
            print(f"[C2] Retry '{query[:35]}' -> {len(resultados)} resultados")
            return resultados
        except Exception as e:
            print(f"[C2] Retry falhou ({type(e).__name__}): '{query[:35]}'")
            return []
    except Exception as e:
        print(f"[C2] Erro ({type(e).__name__}): '{query[:35]}'")
        return []


def _score_fonte(item: dict) -> float:
    """
    Atribui um score de boost a documentos de fontes prioritárias.
    Fontes do publico.pt recebem boost máximo (Menção Honrosa Público).
    Outras fontes .pt recebem boost moderado.
    """
    url = item.get("originalURL", item.get("url", "")).lower()
    if "publico.pt" in url:
        return 2.0   # Boost máximo — relevante para Menção Honrosa Público
    if url.endswith(".pt") or ".pt/" in url:
        return 1.3   # Boost moderado — fontes nacionais
    return 1.0


def pesquisar_multi_query(queries: list[str],
                          from_year: str = None,
                          to_year:   str = None) -> list[dict]:
    """
    CAMADA 2: Executa as queries em paralelo, deduplica por URL e aplica
    boost de relevância para fontes .pt e publico.pt.
    """
    todos: list[dict] = []
    urls_vistas: set  = set()

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        futuros = {ex.submit(_pesquisar, q, from_year, to_year): q for q in queries}
        for fut in concurrent.futures.as_completed(futuros):
            resultados = fut.result()

            # Fallback sem filtro temporal se veio vazio
            if not resultados and (from_year or to_year):
                resultados = _pesquisar(futuros[fut])

            for item in resultados:
                url = item.get("originalURL", item.get("url", ""))
                if url and url not in urls_vistas:
                    urls_vistas.add(url)
                    item["_score"] = _score_fonte(item)  # Anexa score para re-ranking
                    todos.append(item)

    # Ordena por score (fontes .pt primeiro) antes do re-ranking
    todos.sort(key=lambda x: x.get("_score", 1.0), reverse=True)
    print(f"[C2] {len(todos)} candidatos únicos (ordenados por relevância de fonte)")
    return todos


# ── CAMADA 3: Re-ranking por Relevância para Desinformação ───────────────────

_SYS_RERANK = """És um especialista em análise de narrativas históricas e verificação de factos.
Recebeste um tema ou afirmação e uma lista de documentos históricos.

Seleciona os documentos mais úteis para compreender a evolução da narrativa, incluindo documentos que confirmem, refutem, contextualizem ou mostrem desacordos.
Prioriza:
1. Documentos que tratem directamente do tema (não apenas mencionem palavras coincidentes)
2. Documentos que contenham dados, estatísticas ou declarações oficiais relevantes
3. Documentos de fontes jornalísticas (.pt) — especialmente publico.pt
4. Documentos próximos da data dos acontecimentos mencionados
5. Variedade de fontes (evita múltiplos documentos do mesmo site)

Responde APENAS com JSON sem texto extra:
{"indices": [0, 3, 1, 7, 2], "nota": "frase curta sobre os docs selecionados"}"""


def reranking(afirmacao: str, candidatos: list[dict], cliente,
              n: int = NUM_DOCS_RERANKED) -> list[dict]:
    """
    CAMADA 3: Seleciona os N candidatos mais úteis para auditar a afirmação.
    Em caso de falha do modelo, devolve os N primeiros (que já estão ordenados
    pelo score de fonte da Camada 2).
    """
    if len(candidatos) <= n:
        return candidatos

    print(f"[C3] Re-ranking de {len(candidatos)} candidatos...")

    # Representa cada candidato de forma compacta para o modelo avaliar
    lista = []
    for i, item in enumerate(candidatos):
        titulo  = item.get("title", "")[:80]
        snippet = item.get("snippet", "")[:200]
        url     = item.get("originalURL", item.get("url", ""))[:70]
        data    = formatar_data(item.get("tstamp", ""))
        score   = item.get("_score", 1.0)
        publico = " [PÚBLICO.PT ⭐]" if "publico.pt" in url.lower() else ""
        lista.append(f"[{i}]{publico} {data} | {url}\n    Título: {titulo}\n    Snippet: {snippet}")

    raw = _gemini(
        cliente = cliente,
        modelos = FALLBACK_LEVE,
        prompt  = f"Afirmação: {afirmacao}\n\nDocumentos:\n\n" + "\n\n".join(lista),
        system  = _SYS_RERANK,
        temp    = 0.0,    # Determinístico
        tokens  = 200,
    )

    if raw:
        try:
            limpo   = re.sub(r"```(?:json)?", "", raw).strip().strip("`")
            dados   = json.loads(limpo)
            indices = [i for i in dados.get("indices", [])
                       if isinstance(i, int) and 0 <= i < len(candidatos)][:n]
            nota    = dados.get("nota", "")
            if nota:
                print(f"[C3] Nota: {nota}")
            if len(indices) >= 2:
                sel = [candidatos[i] for i in indices]
                print(f"[C3] Selecionados: {len(sel)} documentos")
                return sel
        except Exception as e:
            print(f"[C3] Falha JSON: {e}")

    print(f"[C3] Fallback - usando primeiros {n}")
    return candidatos[:n]


# ── CAMADA 4a: Extração de HTML ───────────────────────────────────────────────

def extrair_texto(url: str) -> str:
    """
    Faz download de uma página arquivada e extrai o texto editorial.
    Gere encoding (iso-8859-1 comum em páginas dos anos 90-2000),
    remove elementos não-informativos e tenta isolar o conteúdo principal.
    """
    try:
        r = requests.get(
            url,
            headers = {
                "User-Agent":      "Deceptio/1.0 (Premio Arquivo.pt 2026; investigacao academica)",
                "Accept-Language": "pt-PT,pt;q=0.9",
            },
            timeout = HTTP_TIMEOUT,
        )
        r.raise_for_status()

        # Encoding: verifica Content-Type header antes de assumir UTF-8
        ct = r.headers.get("Content-Type", "").lower()
        if "charset=" in ct:
            charset = ct.split("charset=")[-1].split(";")[0].strip()
            try:
                html = r.content.decode(charset, errors="replace")
            except LookupError:
                html = r.content.decode("utf-8", errors="replace")
        elif r.encoding and r.encoding.lower() in ("iso-8859-1","latin-1","windows-1252","cp1252"):
            html = r.content.decode(r.encoding, errors="replace")
        else:
            html = r.content.decode("utf-8", errors="replace")

        soup = BeautifulSoup(html, "lxml")

        # Remove elementos não-editoriais
        for tag in soup(["script","style","nav","header","footer","aside",
                          "form","button","iframe","noscript","figure",
                          "figcaption","picture","menu"]):
            tag.decompose()

        # Localiza o conteúdo editorial principal
        P_ID    = re.compile(r"(content|conteudo|noticia|artigo|texto|corpo|main|news|article)", re.I)
        P_CLASS = re.compile(r"(content|conteudo|noticia|artigo|texto|corpo|article|news|story)", re.I)

        zona = (
            soup.find("article") or soup.find("main") or
            soup.find(id=P_ID)   or soup.find(class_=P_CLASS) or
            soup.find("body")
        )

        texto = (zona or soup).get_text(separator=" ", strip=True)
        texto = re.sub(r"[\r\n\t\xa0]+", " ", texto)
        texto = re.sub(r" {2,}", " ", texto).strip()

        return texto[:MAX_CHARS_PAGINA]

    except requests.Timeout:
        print(f"[C4a] Timeout: {url[:60]}")
        return ""
    except Exception as e:
        print(f"[C4a] Falha ({type(e).__name__}): {url[:55]}")
        return ""


def construir_contexto(docs: list[dict]) -> tuple[str, list[dict]]:
    """
    Extrai o texto de cada documento e constrói o bloco de contexto
    para o prompt da Camada 4b. Cada bloco é numerado e inclui
    metadados para o LLM citar correctamente.
    """
    blocos = []
    fontes = []

    for i, item in enumerate(docs, start=1):
        titulo    = item.get("title",       "Sem título").strip()
        url_orig  = item.get("originalURL", item.get("url", "")).strip()
        tstamp    = item.get("tstamp",      "")
        link_arch = item.get("linkToArchive", "").strip()
        snippet   = item.get("snippet",     "").strip()

        data = formatar_data(tstamp)

        texto = extrair_texto(link_arch) if link_arch else ""
        if not texto:
            texto = snippet
        if not texto:
            print(f"[C4a] Documento {i} sem conteudo - ignorado")
            continue

        # Flag Público para dar destaque visual na UI
        is_publico = "publico.pt" in url_orig.lower()

        blocos.append(
            f"[DOC {i}]{'  ★ PÚBLICO.PT' if is_publico else ''}\n"
            f"Título: {titulo}\n"
            f"Data de captura: {data}\n"
            f"URL: {url_orig}\n"
            f"Texto:\n{texto}\n"
        )
        fontes.append({
            "numero":     i,
            "titulo":     titulo,
            "data":       data,
            "url_orig":   url_orig,
            "link_arch":  link_arch,
            "is_publico": is_publico,
        })

    sep = "\n" + "─" * 50 + "\n"
    return sep.join(blocos), fontes


# ── CAMADA 4b: Auditoria de Factos ────────────────────────────────────────────

_SYS_AUDITORIA = """És o DECEPTIO, um auditor de inteligência artificial especializado em \
combater a desinformação e verificar factos históricos da Internet portuguesa.

Recebes uma afirmação e documentos históricos reais do Arquivo.pt (focados em sites .pt, \
incluindo o publico.pt).

A TUA MISSÃO — segue EXACTAMENTE esta estrutura:

**VEREDITO:** [escolhe UM: MITO HISTÓRICO | FACTO CONFIRMADO | VERDADE PARCIAL | PÂNICO INJUSTIFICADO | INCONCLUSIVO]

**Resumo:** 2-3 frases directas a explicar o veredito.

**O que diziam os documentos na época:**
Cita os documentos [DOC N] com a data e o que afirmavam. Se existe discrepância \
entre diferentes fontes da época, menciona-a.

**O que sabemos hoje (conhecimento global):**
Cruza com o teu conhecimento histórico e científico consolidado. Onde há diferença \
entre a narrativa da época e a realidade histórica, explica claramente.

**Conclusão:**
Frase final de síntese.

REGRAS ABSOLUTAS:
1. O VEREDITO tem de aparecer na primeira linha, em negrito, no formato exacto acima.
2. Cita sempre [DOC N] quando usas informação de um documento específico.
3. Distingue claramente: "na época dizia-se X" vs "hoje sabemos que Y".
4. Se os documentos forem insuficientes, diz-o no veredito (INCONCLUSIVO) e explica porquê.
5. Escreve em português europeu (Portugal). Tom analítico e directo, como um jornalista de investigação."""


def auditar(afirmacao: str, contexto: str, historico: list[dict], cliente) -> str:
    """
    CAMADA 4b: Gera o veredito de desinformação cruzando os documentos
    históricos com o conhecimento global do Gemini.
    """
    # Histórico limitado a 3 trocas para não exceder quota
    hist = (historico or [])[-6:]
    conteudos = []
    for msg in hist:
        role = "user" if msg.get("role") == "user" else "model"
        c    = msg.get("content", "").strip()
        if c:
            conteudos.append(genai_types.Content(
                role=role,
                parts=[genai_types.Part(text=c)]
            ))

    prompt = (
        f"Afirmação a verificar: **{afirmacao}**\n\n"
        f"Documentos históricos do Arquivo.pt:\n\n"
        f"{'─'*50}\n{contexto}\n{'─'*50}\n\n"
        f"Analisa a afirmação com base nos documentos e emite o teu veredito."
    )
    conteudos.append(genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=prompt)]
    ))

    cfg = genai_types.GenerateContentConfig(
        system_instruction = _SYS_AUDITORIA,
        temperature        = 0.2,
        max_output_tokens  = 2048,
    )

    ultimo_erro = ""
    teve_quota = False
    teve_modelo_indisponivel = False
    for modelo in FALLBACK_FORTE:
        try:
            r = cliente.models.generate_content(
                model=modelo, contents=conteudos, config=cfg
            )
            if r.candidates and r.text and r.text.strip():
                print(f"[C4b] Veredito gerado via {modelo}")
                return r.text.strip()
        except Exception as e:
            ultimo_erro = str(e)
            if _erro_quota(ultimo_erro):
                teve_quota = True
                time.sleep(2)
            elif _erro_auth(ultimo_erro):
                return "⚠️ **Erro de autenticação (403).** Verifica a tua `GEMINI_API_KEY` em https://aistudio.google.com/"
            elif _erro_modelo_indisponivel(ultimo_erro):
                teve_modelo_indisponivel = True
                print(f"[C4b] Modelo indisponível: {modelo}")

    if teve_quota:
        return "⏳ **Limite de pedidos atingido.** O plano gratuito permite 15 pedidos/minuto. Aguarda 60s."
    if teve_modelo_indisponivel:
        return "⚠️ **Modelo Gemini indisponível.** Tenta novamente ou confirma no Google AI Studio quais os modelos activos para a tua chave."
    return f"⚠️ **Erro ao gerar veredito.**\n`{ultimo_erro[:200]}`"


# ── Best MVP: análise de narrativa por tema ──────────────────────────────────

_SYS_ANALISE_TOPICO = """Es o DECEPTIO, um analista de narrativas historicas baseado no Arquivo.pt.

Recebes um TEMA introduzido pelo utilizador e documentos historicos reais recolhidos no Arquivo.pt.

A TUA MISSAO e transformar os documentos numa analise exploravel. Segue EXACTAMENTE esta estrutura:

**Tema analisado:** [tema]

**1. Linha temporal principal**
- Agrupa por ano.
- Para cada ano, resume as principais alegacoes encontradas e cita [DOC N].
- Se houver poucos documentos, diz que a linha temporal e parcial.

**2. Alegacoes principais por ano e fonte**
- Lista as alegacoes centrais.
- Indica ano, fonte/documento e se a fonte apresenta a alegacao como facto, previsao, opiniao, alerta ou contestacao.

**3. Fiabilidade das fontes**
- Resume a diversidade de fontes, proximidade temporal, tipo de fonte e sinais de cautela.
- Nao atribuas uma pontuacao numerica absoluta; usa avaliacoes como "forte", "media", "limitada" ou "incerta".

**4. Contradicoes e desacordos**
- Identifica pontos em que documentos discordam entre si, mudam de enfase ou apresentam incerteza.
- Se nao houver contradicoes claras, explica que a amostra nao e suficiente para as confirmar.

**5. Mudanca da narrativa**
- Explica como a narrativa evolui ao longo do tempo: origem, intensificacao, correcao, normalizacao ou desaparecimento.

**Resumo executivo**
3 a 5 bullets com a leitura final.

Termina sempre a resposta com a linha:
FIM_DA_ANALISE

REGRAS ABSOLUTAS:
1. Cita sempre [DOC N] quando usas informacao de documentos.
2. Nao inventes fontes nem alegacoes nao presentes no contexto.
3. Distingue evidencias documentais de inferencias tuas.
4. Escreve em portugues europeu, com tom analitico e claro.
5. Se a resposta for longa, privilegia frases compactas em vez de cortar seco."""


def analisar_narrativa_topico(topico: str, contexto: str, historico: list[dict], cliente) -> str:
    """Gera timeline, fiabilidade das fontes, desacordos e mudanca narrativa."""
    hist = (historico or [])[-6:]
    conteudos = []
    for msg in hist:
        role = "user" if msg.get("role") == "user" else "model"
        c = msg.get("content", "").strip()
        if c:
            conteudos.append(genai_types.Content(
                role=role,
                parts=[genai_types.Part(text=c)]
            ))

    prompt = (
        f"Tema introduzido pelo utilizador: **{topico}**\n\n"
        f"Documentos historicos do Arquivo.pt:\n\n"
        f"{'-'*50}\n{contexto}\n{'-'*50}\n\n"
        "Extrai as alegacoes principais, organiza-as por ano/fonte e produz a analise completa."
    )
    conteudos.append(genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=prompt)]
    ))

    cfg = genai_types.GenerateContentConfig(
        system_instruction=_SYS_ANALISE_TOPICO,
        temperature=0.2,
        max_output_tokens=8192,
    )

    ultimo_erro = ""
    teve_quota = False
    teve_modelo_indisponivel = False
    for modelo in FALLBACK_FORTE:
        try:
            r = cliente.models.generate_content(model=modelo, contents=conteudos, config=cfg)
            if r.candidates and r.text and r.text.strip():
                print(f"[MVP] Analise de narrativa gerada via {modelo}")
                texto = r.text.strip()
                if "FIM_DA_ANALISE" not in texto:
                    cfg_continuacao = genai_types.GenerateContentConfig(
                        system_instruction=_SYS_ANALISE_TOPICO,
                        temperature=0.2,
                        max_output_tokens=4096,
                    )
                    conteudos_continuacao = conteudos + [
                        genai_types.Content(
                            role="model",
                            parts=[genai_types.Part(text=texto)],
                        ),
                        genai_types.Content(
                            role="user",
                            parts=[genai_types.Part(
                                text=(
                                    "A resposta anterior ficou incompleta. Continua exactamente "
                                    "a partir do ponto onde parou, sem repetir o que ja foi escrito, "
                                    "e termina com FIM_DA_ANALISE."
                                )
                            )],
                        ),
                    ]
                    r2 = cliente.models.generate_content(
                        model=modelo,
                        contents=conteudos_continuacao,
                        config=cfg_continuacao,
                    )
                    if r2.candidates and r2.text and r2.text.strip():
                        texto = f"{texto.rstrip()}\n\n{r2.text.strip()}"
                return texto.replace("FIM_DA_ANALISE", "").strip()
        except Exception as e:
            ultimo_erro = str(e)
            if _erro_quota(ultimo_erro):
                teve_quota = True
                time.sleep(2)
            elif _erro_auth(ultimo_erro):
                return "⚠️ **Erro de autenticação (403).** Verifica a tua `GEMINI_API_KEY` em https://aistudio.google.com/"
            elif _erro_modelo_indisponivel(ultimo_erro):
                teve_modelo_indisponivel = True
                print(f"[MVP] Modelo indisponível: {modelo}")

    if teve_quota:
        return "⏳ **Limite de pedidos atingido.** O plano gratuito permite 15 pedidos/minuto. Aguarda 60s."
    if teve_modelo_indisponivel:
        return "⚠️ **Modelo Gemini indisponível.** Tenta novamente ou confirma no Google AI Studio quais os modelos activos para a tua chave."
    return f"⚠️ **Erro ao gerar análise.**\n`{ultimo_erro[:200]}`"


def analisar_topico(
    topico: str,
    from_year: str = None,
    to_year: str = None,
    historico: list[dict] = None,
) -> tuple[str, list[dict]]:
    """
    Entrada principal do Best MVP.

    Fluxo:
        Tema -> artigos relevantes -> alegacoes principais -> agrupamento
        por ano/fonte -> timeline, fiabilidade, desacordos e mudanca narrativa.
    """
    print(f"\n{'='*60}")
    print(f"[DECEPTIO MVP] Tema: '{topico[:70]}'")

    cliente, err = _cliente()
    if not cliente:
        return err, []

    queries = gerar_queries(topico, cliente)
    candidatos = pesquisar_multi_query(queries, from_year, to_year)
    if not candidatos:
        return (
            "📭 **Nenhum artigo encontrado no Arquivo.pt.**\n\n"
            "- Reformula o tema com nomes, datas ou termos mais específicos\n"
            "- Experimenta sem filtro temporal\n"
            "- O Arquivo.pt pode estar temporariamente indisponível: https://arquivo.pt"
        ), []

    seleccionados = reranking(topico, candidatos, cliente, n=8)
    contexto, fontes = construir_contexto(seleccionados)
    if not fontes:
        return (
            "📄 **Artigos encontrados, mas conteúdo não extraível.**\n\n"
            f"Foram encontrados {len(candidatos)} candidato(s), mas as páginas arquivadas "
            "podem usar formatos não suportados (Flash, PDF, imagem). Tenta reformular."
        ), []

    analise = analisar_narrativa_topico(topico, contexto, historico or [], cliente)
    return analise, fontes


# ── Pipeline principal ────────────────────────────────────────────────────────

def analisar_afirmacao(
    afirmacao: str,
    from_year: str        = None,
    to_year:   str        = None,
    historico: list[dict] = None,
) -> tuple[str, list[dict]]:
    """
    Função de entrada principal do DECEPTIO.
    Orquestra as 4 camadas: Query Expansion → Retrieval → Re-ranking → Auditoria.

    Parâmetros:
        afirmacao — Afirmação/mito a verificar
        from_year — Filtro temporal de início (opcional)
        to_year   — Filtro temporal de fim (opcional)
        historico — Histórico de conversa (para perguntas de seguimento)

    Retorna:
        (veredito_markdown, fontes_lista)
    """
    print(f"\n{'='*60}")
    print(f"[DECEPTIO] Afirmação: '{afirmacao[:70]}'")

    cliente, err = _cliente()
    if not cliente:
        return err, []

    # C1 — Query expansion
    queries = gerar_queries(afirmacao, cliente)

    # C2 — Retrieval multi-query
    candidatos = pesquisar_multi_query(queries, from_year, to_year)
    if not candidatos:
        return (
            "📭 **Nenhum documento encontrado no Arquivo.pt.**\n\n"
            "- Reformula a afirmação com termos mais específicos\n"
            "- Experimenta sem filtro temporal\n"
            "- O Arquivo.pt pode estar temporariamente indisponível: https://arquivo.pt"
        ), []

    # C3 — Re-ranking
    seleccionados = reranking(afirmacao, candidatos, cliente)

    # C4a — Extração HTML + contexto
    contexto, fontes = construir_contexto(seleccionados)
    if not fontes:
        return (
            "📄 **Documentos encontrados mas conteúdo não extraível.**\n\n"
            f"Foram encontrados {len(candidatos)} candidato(s), mas as páginas arquivadas "
            "podem usar formatos não suportados (Flash, PDF, imagem). Tenta reformular."
        ), []

    # C4b — Auditoria de factos
    veredito = auditar(afirmacao, contexto, historico or [], cliente)

    return veredito, fontes


# ── Utilitário ────────────────────────────────────────────────────────────────

def formatar_data(tstamp: str) -> str:
    """Converte YYYYMMDDHHmmss → "D de mês de AAAA"."""
    MESES = ["","janeiro","fevereiro","março","abril","maio","junho",
             "julho","agosto","setembro","outubro","novembro","dezembro"]
    try:
        if len(tstamp) < 8:
            return tstamp
        ano = tstamp[0:4]
        mes = int(tstamp[4:6])
        dia = tstamp[6:8].lstrip("0") or "1"
        return f"{dia} de {MESES[mes]} de {ano}" if 1 <= mes <= 12 else tstamp
    except (IndexError, ValueError):
        return tstamp
