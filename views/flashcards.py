"""
views/flashcards.py
-------------------
Modo de estudo com flashcards.

Fluxo:
1. Usuário configura a sessão (quantidade, categoria, dificuldade).
2. Vê apenas a palavra em inglês.
3. Clica em "Mostrar resposta".
4. Classifica: Errei / Difícil / Acertei / Fácil.
5. A classificação alimenta a repetição espaçada (study.py).
"""

from __future__ import annotations

import streamlit as st

import database as db
from models import DIFICULDADES
from study import montar_sessao, registrar_resposta
from utils import titulo, card_palavra, bloco_resposta, limpar_estado

PREFIXO = "fc_"


def render() -> None:
    titulo("📚 Estudar Flashcards", "Revise seu vocabulário no estilo Anki")

    if db.count_words() == 0:
        st.info("Cadastre palavras antes de estudar.")
        return

    # --- Configuração da sessão -------------------------------------------
    if "fc_fila" not in st.session_state:
        _tela_configuracao()
        return

    fila: list[dict] = st.session_state["fc_fila"]
    indice: int = st.session_state["fc_indice"]

    # --- Fim da sessão -----------------------------------------------------
    if indice >= len(fila):
        _tela_final()
        return

    palavra = fila[indice]

    st.progress((indice) / len(fila), text=f"Card {indice + 1} de {len(fila)}")
    card_palavra(palavra["english"], palavra["category"])

    # --- Frente do card ----------------------------------------------------
    if not st.session_state.get("fc_mostrar"):
        if st.button("👁️ Mostrar resposta", type="primary", use_container_width=True):
            st.session_state["fc_mostrar"] = True
            st.rerun()
        if st.button("Encerrar sessão", use_container_width=True):
            limpar_estado(PREFIXO)
            st.rerun()
        return

    # --- Verso do card -----------------------------------------------------
    bloco_resposta("Tradução", palavra["portuguese"])
    bloco_resposta("Significado", palavra["definition"])
    bloco_resposta("Exemplo", palavra["example"])
    if palavra["notes"]:
        bloco_resposta("Observações", palavra["notes"])

    st.write("**Como foi sua resposta?**")
    c1, c2, c3, c4 = st.columns(4)
    avaliacoes = [
        (c1, "😖 Errei", "Errei"),
        (c2, "😕 Difícil", "Difícil"),
        (c3, "🙂 Acertei", "Acertei"),
        (c4, "😎 Fácil", "Fácil"),
    ]
    for coluna, rotulo, rating in avaliacoes:
        if coluna.button(rotulo, use_container_width=True, key=f"fc_btn_{rating}"):
            _responder(palavra, rating)


def _tela_configuracao() -> None:
    """Formulário inicial da sessão de flashcards."""
    with st.form("fc_config"):
        c1, c2, c3 = st.columns(3)
        quantidade = c1.number_input("Quantos cards?", 1, 100, 10)
        categoria = c2.selectbox("Categoria", ["Todas"] + db.list_categories())
        dificuldade = c3.selectbox("Dificuldade", ["Todas"] + DIFICULDADES)
        somente_revisao = st.checkbox(
            "Priorizar palavras que vencerem a revisão (recomendado)", value=True
        )
        iniciar = st.form_submit_button("▶️ Iniciar sessão", type="primary", use_container_width=True)

    st.caption(f"📌 {db.count_due_words()} palavra(s) na fila de revisão de hoje.")

    if iniciar:
        fila = montar_sessao(int(quantidade), categoria, dificuldade, somente_revisao)
        if not fila:
            st.warning("Nenhuma palavra encontrada com esses filtros.")
            return
        st.session_state["fc_fila"] = fila
        st.session_state["fc_indice"] = 0
        st.session_state["fc_mostrar"] = False
        st.session_state["fc_resultados"] = []
        st.rerun()


def _responder(palavra: dict, rating: str) -> None:
    """Grava a avaliação e avança para o próximo card."""
    registrar_resposta(palavra, rating, mode="flashcard")
    st.session_state["fc_resultados"].append({"english": palavra["english"], "rating": rating})

    # "Errei" devolve o card para o fim da fila, como no Anki
    if rating == "Errei":
        st.session_state["fc_fila"].append(palavra)

    st.session_state["fc_indice"] += 1
    st.session_state["fc_mostrar"] = False
    st.rerun()


def _tela_final() -> None:
    """Resumo ao terminar a sessão."""
    resultados = st.session_state.get("fc_resultados", [])
    acertos = sum(1 for r in resultados if r["rating"] in ("Acertei", "Fácil"))
    erros = len(resultados) - acertos

    st.success("🎉 Sessão concluída!")
    c1, c2, c3 = st.columns(3)
    c1.metric("Cards revisados", len(resultados))
    c2.metric("Acertos", acertos)
    c3.metric("Aproveitamento", f"{(acertos / len(resultados) * 100) if resultados else 0:.0f}%")

    dificeis = sorted({r["english"] for r in resultados if r["rating"] in ("Errei", "Difícil")})
    if dificeis:
        st.warning("Palavras para reforçar: " + ", ".join(dificeis))

    if st.button("🔄 Nova sessão", type="primary", use_container_width=True):
        limpar_estado(PREFIXO)
        st.rerun()
