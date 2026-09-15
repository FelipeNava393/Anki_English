"""
views/random_words.py
---------------------
Modo aleatório: sorteia N palavras do banco (com filtros opcionais)
para uma revisão rápida, card a card.
"""

from __future__ import annotations

import streamlit as st

import database as db
from models import DIFICULDADES
from study import registrar_resposta, sortear_aleatorias
from utils import titulo, card_palavra, bloco_resposta, limpar_estado

PREFIXO = "rd_"


def render() -> None:
    titulo("🎲 Palavras Aleatórias", "Sorteie palavras do seu banco para uma revisão rápida")

    if db.count_words() == 0:
        st.info("Cadastre palavras antes de usar o modo aleatório.")
        return

    if "rd_fila" not in st.session_state:
        with st.form("rd_config"):
            c1, c2, c3 = st.columns(3)
            quantidade = c1.number_input("Quantas palavras?", 1, 100, 5)
            categoria = c2.selectbox("Categoria", ["Todas"] + db.list_categories())
            dificuldade = c3.selectbox("Dificuldade", ["Todas"] + DIFICULDADES)
            sortear = st.form_submit_button("🎲 Sortear", type="primary", use_container_width=True)

        if sortear:
            fila = sortear_aleatorias(int(quantidade), categoria, dificuldade)
            if not fila:
                st.warning("Nenhuma palavra encontrada com esses filtros.")
                return
            st.session_state["rd_fila"] = fila
            st.session_state["rd_indice"] = 0
            st.session_state["rd_mostrar"] = False
            st.rerun()
        return

    fila = st.session_state["rd_fila"]
    indice = st.session_state["rd_indice"]

    if indice >= len(fila):
        st.success("🎉 Você passou por todas as palavras sorteadas!")
        if st.button("🔄 Sortear novamente", type="primary", use_container_width=True):
            limpar_estado(PREFIXO)
            st.rerun()
        return

    palavra = fila[indice]
    st.progress(indice / len(fila), text=f"Palavra {indice + 1} de {len(fila)}")
    card_palavra(palavra["english"], f"{palavra['category']} · {palavra['difficulty']}")

    if not st.session_state.get("rd_mostrar"):
        if st.button("👁️ Mostrar significado", type="primary", use_container_width=True):
            st.session_state["rd_mostrar"] = True
            st.rerun()
    else:
        bloco_resposta("Tradução", palavra["portuguese"])
        bloco_resposta("Significado", palavra["definition"])
        bloco_resposta("Exemplo", palavra["example"])

        c1, c2 = st.columns(2)
        if c1.button("😖 Não sabia", use_container_width=True):
            _avancar(palavra, "Errei")
        if c2.button("🙂 Já sabia", use_container_width=True):
            _avancar(palavra, "Acertei")

    st.divider()
    if st.button("Encerrar", use_container_width=True):
        limpar_estado(PREFIXO)
        st.rerun()


def _avancar(palavra: dict, rating: str) -> None:
    registrar_resposta(palavra, rating, mode="aleatorio")
    st.session_state["rd_indice"] += 1
    st.session_state["rd_mostrar"] = False
    st.rerun()
