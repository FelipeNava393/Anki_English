"""
utils.py
--------
Funções auxiliares de interface e formatação usadas pelas páginas.
"""

from __future__ import annotations

from datetime import datetime

import streamlit as st

# Cores por nível de dificuldade (usadas nos "badges")
CORES_DIFICULDADE = {
    "Fácil": "#16a34a",
    "Médio": "#d97706",
    "Difícil": "#dc2626",
}

CSS = """
<style>
    /* Layout mais enxuto e moderno */
    .block-container { padding-top: 2rem; max-width: 1100px; }
    #MainMenu, footer { visibility: hidden; }

    .card {
        background: linear-gradient(145deg, #1f2937, #111827);
        color: #f9fafb;
        border-radius: 18px;
        padding: 2.5rem 2rem;
        text-align: center;
        box-shadow: 0 8px 24px rgba(0,0,0,.18);
        margin-bottom: 1rem;
    }
    .card h1 { font-size: 2.4rem; margin: 0; color: #ffffff; }
    .card p  { margin: .4rem 0 0; color: #cbd5e1; font-size: .95rem; }

    .answer-box {
        background: #f8fafc;
        border-left: 5px solid #2563eb;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: .8rem;
        color: #0f172a;
    }
    .badge {
        display: inline-block;
        padding: .15rem .6rem;
        border-radius: 999px;
        color: #fff;
        font-size: .75rem;
        font-weight: 600;
    }
</style>
"""


def aplicar_estilo() -> None:
    """Injeta o CSS base da aplicação."""
    st.markdown(CSS, unsafe_allow_html=True)


def titulo(texto: str, subtitulo: str = "") -> None:
    """Cabeçalho padronizado das páginas."""
    st.markdown(f"## {texto}")
    if subtitulo:
        st.caption(subtitulo)


def badge(texto: str, cor: str = "#2563eb") -> str:
    return f"<span class='badge' style='background:{cor}'>{texto}</span>"


def badge_dificuldade(nivel: str) -> str:
    return badge(nivel, CORES_DIFICULDADE.get(nivel, "#2563eb"))


def card_palavra(palavra: str, legenda: str = "") -> None:
    """Card grande usado no modo flashcard."""
    st.markdown(
        f"<div class='card'><h1>{palavra}</h1><p>{legenda}</p></div>",
        unsafe_allow_html=True,
    )


def bloco_resposta(rotulo: str, valor: str) -> None:
    """Bloco destacado com tradução / significado / exemplo."""
    if not valor:
        return
    st.markdown(
        f"<div class='answer-box'><strong>{rotulo}</strong><br>{valor}</div>",
        unsafe_allow_html=True,
    )


def formatar_data(iso: str | None, padrao: str = "—") -> str:
    """Converte uma data ISO do banco para o formato brasileiro."""
    if not iso:
        return padrao
    try:
        return datetime.fromisoformat(iso).strftime("%d/%m/%Y")
    except ValueError:
        return padrao


def barra_progresso(valor: float, total: int) -> None:
    """Barra de progresso segura contra divisão por zero."""
    st.progress(min(1.0, valor / total) if total else 0.0)


def limpar_estado(prefixo: str) -> None:
    """Remove do session_state todas as chaves de uma sessão de estudo."""
    for chave in [k for k in st.session_state if k.startswith(prefixo)]:
        del st.session_state[chave]
