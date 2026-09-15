"""
views/add_word.py
-----------------
Página de cadastro de novas palavras/expressões.
Valida campos obrigatórios e alerta sobre duplicidade.
"""

from __future__ import annotations

import streamlit as st

import database as db
from models import DIFICULDADES
from utils import titulo


def render() -> None:
    titulo("➕ Adicionar Palavra", "Cadastre uma nova palavra ou expressão em inglês")

    categorias = db.list_categories()

    with st.form("form_nova_palavra", clear_on_submit=True):
        col1, col2 = st.columns(2)
        english = col1.text_input("Palavra / expressão em inglês *", placeholder="reliable")
        portuguese = col2.text_input("Tradução em português *", placeholder="confiável")

        definition = st.text_area(
            "Definição ou significado", placeholder="able to be trusted", height=80
        )
        example = st.text_area(
            "Frase de exemplo", placeholder="He is a reliable colleague.", height=80
        )

        col3, col4 = st.columns(2)
        categoria_escolhida = col3.selectbox(
            "Categoria / tema", ["➕ Nova categoria..."] + categorias
        )
        difficulty = col4.selectbox("Nível de dificuldade", DIFICULDADES, index=1)

        nova_categoria = ""
        if categoria_escolhida == "➕ Nova categoria...":
            nova_categoria = st.text_input("Nome da nova categoria", placeholder="Verbos")

        notes = st.text_area("Observações", height=70)

        enviado = st.form_submit_button("Salvar palavra", type="primary", use_container_width=True)

    if not enviado:
        st.caption("Campos marcados com * são obrigatórios.")
        return

    category = nova_categoria.strip() if nova_categoria.strip() else categoria_escolhida
    if category == "➕ Nova categoria...":
        category = "Geral"

    try:
        db.add_word(
            english=english,
            portuguese=portuguese,
            definition=definition,
            example=example,
            category=category,
            difficulty=difficulty,
            notes=notes,
        )
        st.success(f"✅ '{english.strip()}' cadastrada com sucesso!")
        st.balloons()
    except ValueError as erro:
        st.warning(f"⚠️ {erro}")
