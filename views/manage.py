"""
views/manage.py
---------------
Banco de palavras: pesquisa, filtros, edição e exclusão de registros.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

import database as db
from models import DIFICULDADES
from utils import titulo, formatar_data


def render() -> None:
    titulo("📝 Gerenciar Vocabulário", "Pesquise, edite e exclua suas palavras")

    # --- Filtros -----------------------------------------------------------
    col1, col2, col3 = st.columns([2, 1, 1])
    busca = col1.text_input("🔎 Pesquisar", placeholder="palavra em inglês ou português")
    categoria = col2.selectbox("Categoria", ["Todas"] + db.list_categories())
    dificuldade = col3.selectbox("Dificuldade", ["Todas"] + DIFICULDADES)

    palavras = db.list_words(busca, categoria, dificuldade)
    st.caption(f"{len(palavras)} palavra(s) encontrada(s).")

    if not palavras:
        st.info("Nenhuma palavra encontrada com esses filtros.")
        return

    # --- Tabela geral ------------------------------------------------------
    tabela = pd.DataFrame(
        [
            {
                "Inglês": w["english"],
                "Português": w["portuguese"],
                "Categoria": w["category"],
                "Dificuldade": w["difficulty"],
                "Acertos": w["correct_count"],
                "Erros": w["wrong_count"],
                "Próxima revisão": formatar_data(w["next_review"], "hoje"),
            }
            for w in palavras
        ]
    )
    st.dataframe(tabela, hide_index=True, use_container_width=True)

    # Exportação simples do banco (CSV local)
    st.download_button(
        "⬇️ Exportar CSV",
        tabela.to_csv(index=False).encode("utf-8-sig"),
        file_name="vocabulario.csv",
        mime="text/csv",
    )

    st.divider()

    # --- Edição de um registro --------------------------------------------
    st.subheader("✏️ Editar ou excluir")
    opcoes = {f"{w['english']} — {w['portuguese']}": w["id"] for w in palavras}
    escolha = st.selectbox("Selecione a palavra", list(opcoes.keys()))
    word = db.get_word(opcoes[escolha])
    if not word:
        return

    with st.form(f"form_editar_{word['id']}"):
        c1, c2 = st.columns(2)
        english = c1.text_input("Inglês", value=word["english"])
        portuguese = c2.text_input("Português", value=word["portuguese"])
        definition = st.text_area("Definição", value=word["definition"] or "", height=80)
        example = st.text_area("Exemplo", value=word["example"] or "", height=80)

        c3, c4 = st.columns(2)
        category = c3.text_input("Categoria", value=word["category"] or "Geral")
        difficulty = c4.selectbox(
            "Dificuldade",
            DIFICULDADES,
            index=DIFICULDADES.index(word["difficulty"])
            if word["difficulty"] in DIFICULDADES
            else 1,
        )
        notes = st.text_area("Observações", value=word["notes"] or "", height=70)

        col_salvar, col_excluir = st.columns(2)
        salvar = col_salvar.form_submit_button(
            "💾 Salvar alterações", type="primary", use_container_width=True
        )
        excluir = col_excluir.form_submit_button("🗑️ Excluir palavra", use_container_width=True)

    if salvar:
        try:
            db.update_word(
                word["id"],
                english=english,
                portuguese=portuguese,
                definition=definition,
                example=example,
                category=category,
                difficulty=difficulty,
                notes=notes,
            )
            st.success("Alterações salvas.")
            st.rerun()
        except ValueError as erro:
            st.warning(f"⚠️ {erro}")

    if excluir:
        db.delete_word(word["id"])
        st.success(f"'{word['english']}' foi excluída.")
        st.rerun()

    # Estatísticas individuais da palavra selecionada
    with st.expander("📊 Histórico desta palavra"):
        m1, m2, m3 = st.columns(3)
        m1.metric("Acertos", word["correct_count"])
        m2.metric("Erros", word["wrong_count"])
        m3.metric("Intervalo atual", f"{word['interval_days']} dia(s)")
        st.caption(
            f"Última revisão: {formatar_data(word['last_review'], 'nunca')} · "
            f"Próxima revisão: {formatar_data(word['next_review'], 'hoje')}"
        )
