"""
views/stats.py
--------------
Página de estatísticas detalhadas: desempenho por categoria, por dificuldade,
histórico de revisões e ranking de palavras problemáticas.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

import database as db
from utils import titulo


def render() -> None:
    titulo("📊 Estatísticas", "Acompanhe sua evolução em detalhes")

    words = db.words_dataframe()
    if words.empty:
        st.info("Sem dados ainda. Cadastre e estude algumas palavras.")
        return

    stats = db.global_stats()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total de palavras", stats["total"])
    c2.metric("Total de acertos", int(stats["acertos"]))
    c3.metric("Total de erros", int(stats["erros"]))
    c4.metric("Taxa de acerto", f"{stats['taxa_acerto']:.1f}%")

    st.divider()

    # --- Distribuições -----------------------------------------------------
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Palavras por categoria")
        por_categoria = words["category"].value_counts().rename_axis("Categoria")
        st.bar_chart(por_categoria)

    with col2:
        st.subheader("Palavras por dificuldade")
        por_dificuldade = words["difficulty"].value_counts().rename_axis("Dificuldade")
        st.bar_chart(por_dificuldade)

    st.divider()

    # --- Desempenho por categoria -----------------------------------------
    st.subheader("Desempenho por categoria")
    desempenho = (
        words.groupby("category")[["correct_count", "wrong_count"]].sum().reset_index()
    )
    desempenho["tentativas"] = desempenho["correct_count"] + desempenho["wrong_count"]
    desempenho["Taxa de acerto (%)"] = (
        desempenho["correct_count"] / desempenho["tentativas"].replace(0, pd.NA) * 100
    ).round(1)
    desempenho = desempenho.rename(
        columns={
            "category": "Categoria",
            "correct_count": "Acertos",
            "wrong_count": "Erros",
            "tentativas": "Tentativas",
        }
    )
    st.dataframe(
        desempenho[["Categoria", "Acertos", "Erros", "Tentativas", "Taxa de acerto (%)"]],
        hide_index=True,
        use_container_width=True,
    )

    st.divider()

    # --- Histórico de revisões --------------------------------------------
    st.subheader("Histórico de revisões")
    log = db.study_log_dataframe()
    if log.empty:
        st.caption("Nenhuma revisão registrada até o momento.")
        return

    log["dia"] = pd.to_datetime(log["created_at"]).dt.date
    diario = (
        log.groupby("dia")
        .agg(Revisões=("id", "count"), Acertos=("correct", "sum"))
        .reset_index()
    )
    diario["Erros"] = diario["Revisões"] - diario["Acertos"]
    st.bar_chart(diario.set_index("dia")[["Acertos", "Erros"]])

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Revisões por modo de estudo")
        por_modo = log["mode"].value_counts().rename_axis("Modo")
        st.bar_chart(por_modo)
    with col4:
        st.subheader("Palavras com mais erros")
        dificeis = db.hardest_words(limit=10)
        if dificeis:
            df = pd.DataFrame(dificeis)
            df.columns = ["Inglês", "Português", "Acertos", "Erros"]
            st.dataframe(df, hide_index=True, use_container_width=True)
        else:
            st.success("Nenhum erro registrado.")
