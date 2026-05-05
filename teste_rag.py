"""
DECEPTIO - Script de teste do Best MVP.

Uso:
    python teste_rag.py
    python teste_rag.py "Bug do Ano 2000 em Portugal"
"""

import sys

from deceptio_rag import analisar_topico


SEP = "=" * 70

TEMAS_TESTE = [
    "Bug do Ano 2000 em Portugal",
    "Entrada do Euro em Portugal",
    "Internet em Portugal nos anos 90",
]


def testar_topico(topico: str, from_year: str = None, to_year: str = None):
    print(f"\n{SEP}")
    print("DECEPTIO - ANALISE DE NARRATIVA")
    print(f"Tema: {topico}")
    print(SEP)

    resposta, fontes = analisar_topico(topico, from_year=from_year, to_year=to_year)

    print("\nANALISE")
    print(SEP)
    print(resposta)

    print(f"\nFONTES DO ARQUIVO.PT ({len(fontes)})")
    print(SEP)
    for f in fontes:
        print(f"[DOC {f['numero']}] {f['titulo'][:70]}")
        print(f"  Data: {f['data']}")
        print(f"  URL:  {f['url_orig'][:90]}")
        print(f"  Arch: {f['link_arch'][:90]}")
        print()

    return resposta, fontes


if __name__ == "__main__":
    if len(sys.argv) > 1:
        tema = " ".join(sys.argv[1:])
    else:
        tema = TEMAS_TESTE[0]
        print("(Sem argumento - a usar tema de teste predefinido)")

    testar_topico(tema)
