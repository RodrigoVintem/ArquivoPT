"""
================================================================================
ChatArquivo — Script de Teste do Motor RAG
================================================================================

Testa o pipeline RAG completo sem precisar de abrir o Streamlit.
Útil para desenvolvimento, debugging e demonstrações em terminal.

Uso:
    python teste_rag.py

    ou com pergunta directa:
    python teste_rag.py "O que se dizia sobre Y2K em Portugal?"

Autor: [O teu nome]
Prémio Arquivo.pt 2026
================================================================================
"""

import sys
import json
from arquivo_rag import pesquisar_arquivo, construir_contexto, gerar_resposta, responder_pergunta

# Separador visual para o terminal
SEP = "=" * 70


def testar_pesquisa_arquivo(query: str, from_year: str = None, to_year: str = None):
    """Testa apenas o passo 1: pesquisa na API do Arquivo.pt"""
    print(f"\n{SEP}")
    print(f"PASSO 1 — Pesquisa no Arquivo.pt")
    print(f"Query: '{query}'")
    if from_year: print(f"De: {from_year}  Até: {to_year}")
    print(SEP)

    resultados = pesquisar_arquivo(query, from_year, to_year)

    print(f"✓ {len(resultados)} resultados encontrados\n")
    for i, r in enumerate(resultados, 1):
        print(f"[{i}] {r.get('title', 'Sem título')[:60]}")
        print(f"    Data: {r.get('tstamp', 'N/A')}")
        print(f"    URL:  {r.get('originalURL', r.get('url', 'N/A'))[:70]}")
        print()

    return resultados


def testar_pipeline_completo(pergunta: str, from_year: str = None, to_year: str = None):
    """Testa o pipeline RAG completo: Pesquisa → Extracção → Contexto → LLM → Resposta"""
    print(f"\n{SEP}")
    print(f"PIPELINE RAG COMPLETO")
    print(f"Pergunta: '{pergunta}'")
    print(SEP)

    print("\n⏳ A processar... (pode demorar 10-30 segundos)")

    resposta, fontes = responder_pergunta(pergunta, from_year, to_year)

    print(f"\n{SEP}")
    print("RESPOSTA DO CHATARQUIVO:")
    print(SEP)
    print(resposta)

    print(f"\n{SEP}")
    print(f"FONTES DO ARQUIVO.PT ({len(fontes)} documentos):")
    print(SEP)
    for f in fontes:
        print(f"[DOC {f['numero']}] {f['titulo'][:60]}")
        print(f"  Data:  {f['data']}")
        print(f"  URL:   {f['url_orig'][:70]}")
        print(f"  Arch:  {f['link_arch'][:70]}")
        print()

    return resposta, fontes


# ---------------------------------------------------------------------------
# Testes predefinidos
# ---------------------------------------------------------------------------

PERGUNTAS_TESTE = [
    # Tecnologia histórica
    "Como era descrito o Bug do Ano 2000 na Internet portuguesa antes do ano 2000?",

    # Economia
    "O que se dizia sobre a introdução das notas de euro em Portugal em 2002?",

    # Política
    "Como era noticiada a entrada de Portugal na moeda única europeia?",
]


if __name__ == "__main__":
    print("\n🕰️  ChatArquivo — Teste do Motor RAG")
    print("Prémio Arquivo.pt 2026\n")

    # Usa a pergunta passada como argumento, ou a primeira da lista de testes
    if len(sys.argv) > 1:
        pergunta = " ".join(sys.argv[1:])
    else:
        pergunta = PERGUNTAS_TESTE[0]
        print(f"(Sem argumento — a usar pergunta de teste predefinida)")

    # Executa o pipeline completo
    testar_pipeline_completo(pergunta)
