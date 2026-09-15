"""
views/home.py
-------------
Página inicial (dashboard) com os principais indicadores de aprendizado.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

import database as db
from utils import titulo, formatar_data


def render() -> None:
    titulo("🏠 Início", "Visão geral do seu progresso no vocabulário")

    stats = db.global_stats()

    # --- Indicadores principais -------------------------------------------
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Palavras cadastradas", stats["total"])
    c2.metric("Palavras estudadas", stats["estudadas"])
    c3.metric("Para revisar hoje", stats["a_revisar"])
    c4.metric("Taxa de acerto", f"{stats['taxa_acerto']:.0f}%")

    if stats["total"] == 0:
        st.info(
            "Seu banco está vazio. Vá em **➕ Adicionar Palavra** para cadastrar "
            "sua primeira palavra ou use o botão de exemplo abaixo."
        )
        if st.button("Carregar 10 palavras de exemplo"):
            _carregar_exemplos()
            st.rerun()
        return

    st.divider()

    col_esq, col_dir = st.columns([1, 1])

    # --- Palavras com mais erros ------------------------------------------
    with col_esq:
        st.subheader("🔁 Palavras que mais erro")
        dificeis = db.hardest_words(limit=8)
        if dificeis:
            df = pd.DataFrame(dificeis)
            df.columns = ["Inglês", "Português", "Acertos", "Erros"]
            st.dataframe(df, hide_index=True, use_container_width=True)
        else:
            st.success("Nenhum erro registrado até agora. Continue assim!")

    # --- Evolução do aprendizado ------------------------------------------
    with col_dir:
        st.subheader("📈 Evolução do aprendizado")
        log = db.study_log_dataframe()
        if log.empty:
            st.caption("Estude alguns cards para ver seu gráfico de evolução.")
        else:
            log["dia"] = pd.to_datetime(log["created_at"]).dt.date
            evolucao = (
                log.groupby("dia")
                .agg(Revisões=("id", "count"), Acertos=("correct", "sum"))
                .reset_index()
                .set_index("dia")
            )
            st.line_chart(evolucao)

    st.divider()

    # --- Próximas revisões -------------------------------------------------
    st.subheader("⏰ Fila de revisão")
    due = db.due_words(limit=10)
    if not due:
        st.success("Tudo em dia! Nenhuma palavra vencida para revisar agora.")
    else:
        st.caption(f"{db.count_due_words()} palavra(s) aguardando revisão.")
        tabela = pd.DataFrame(
            [
                {
                    "Inglês": w["english"],
                    "Português": w["portuguese"],
                    "Dificuldade": w["difficulty"],
                    "Última revisão": formatar_data(w["last_review"], "nunca"),
                }
                for w in due
            ]
        )
        st.dataframe(tabela, hide_index=True, use_container_width=True)


def _carregar_exemplos() -> None:
    """Insere um pequeno conjunto inicial para o usuário testar a aplicação."""
    exemplos = [
        dict(english="achieve", portuguese="alcançar, conquistar",
             definition="to successfully complete something",
             example="She achieved all her goals this year.",
             category="Verbos", difficulty="Médio"),
        dict(english="reliable", portuguese="confiável",
             definition="able to be trusted",
             example="He is a reliable colleague.",
             category="Adjetivos", difficulty="Fácil"),
        dict(english="deadline", portuguese="prazo final",
             definition="the latest time to finish something",
             example="The deadline is next Friday.",
             category="Trabalho", difficulty="Fácil"),
        dict(english="improve", portuguese="melhorar",
             definition="to make something better",
             example="I want to improve my English.",
             category="Verbos", difficulty="Fácil"),
        dict(english="insight", portuguese="percepção, visão clara",
             definition="a deep understanding of something",
             example="The report gives useful insights.",
             category="Negócios", difficulty="Difícil"),
        dict(english="in charge of", portuguese="responsável por",
             definition="having control or responsibility",
             example="She is in charge of the project.",
             category="Expressões", difficulty="Médio"),
        dict(english="gather", portuguese="reunir, coletar",
             definition="to collect things or people together",
             example="We need to gather more data.",
             category="Verbos", difficulty="Médio"),
        dict(english="shortage", portuguese="escassez, falta",
             definition="a situation when there is not enough of something",
             example="There is a shortage of skilled workers.",
             category="Negócios", difficulty="Difícil"),
        dict(english="overview", portuguese="visão geral",
             definition="a short description of the main points",
             example="Here is an overview of the process.",
             category="Negócios", difficulty="Médio"),
        dict(english="on purpose", portuguese="de propósito",
             definition="intentionally",
             example="He did it on purpose.",
             category="Expressões", difficulty="Fácil"),
    ]
    inseridas = db.bulk_insert(exemplos)
    st.toast(f"{inseridas} palavras de exemplo adicionadas!", icon="✅")
