"""
traducao.py
Tradução com detecção automática de idioma origem.
Usa deep_translator (compatível com Python 3.14).
Idioma alvo configurável em runtime.
"""

from deep_translator import GoogleTranslator, single_detection
from deep_translator.constants import GOOGLE_LANGUAGES_TO_CODES

_idioma_alvo = "pt"
_cache: dict[str, str] = {}
_SEP = "\n||||\n"


def get_idiomas_disponiveis() -> dict:
    """Retorna {nome_capitalizado: codigo} para popular o menu."""
    return {
        nome.capitalize(): codigo
        for nome, codigo in GOOGLE_LANGUAGES_TO_CODES.items()
    }


def set_idioma_alvo(codigo: str):
    """Muda o idioma alvo e limpa o cache."""
    global _idioma_alvo
    if codigo != _idioma_alvo:
        _idioma_alvo = codigo
        limpar_cache()


def traduzir_em_lote(blocos: list) -> list:
    if not blocos:
        return blocos

    novos_idx    = []
    novos_textos = []

    for i, bloco in enumerate(blocos):
        txt = bloco.get("texto", "").strip()
        if not txt:
            bloco["traducao"] = ""
        elif txt in _cache:
            bloco["traducao"] = _cache[txt]
        else:
            novos_idx.append(i)
            novos_textos.append(txt)

    if not novos_textos:
        return blocos

    try:
        junto = _SEP.join(novos_textos)

        traduzido = GoogleTranslator(
            source="auto",
            target=_idioma_alvo
        ).translate(junto) or ""

        partes = traduzido.split(_SEP)

        for j, idx in enumerate(novos_idx):
            trad = partes[j].strip() if j < len(partes) else blocos[idx]["texto"]
            blocos[idx]["traducao"] = trad
            _cache[blocos[idx]["texto"]] = trad

    except Exception as e:
        print(f"[Erro tradução] {e}")
        for idx in novos_idx:
            blocos[idx]["traducao"] = blocos[idx]["texto"]

    return blocos


def limpar_cache():
    _cache.clear()