"""
views/quiz_page.py
------------------
Página de Quiz: perguntas geradas automaticamente a partir do vocabulário.

Tipos: Inglês→Português, Português→Inglês, múltipla escolha, digitar a resposta.
Ao final mostra acertos, erros, percentual e palavras a revisar.
"""

from __future__ import annotations

import streamlit as st

import database as db
from models import DIFICULDADES
from quiz import TIPOS_QUIZ, consolidar_resultado, gerar_quiz, resposta_correta
from study import registrar_resposta_simples
from utils import titulo, limpar_estado

PREFIXO = "qz_"


def render() -> None:
    titulo("🎯 Quiz", "Teste seu vocabulário com perguntas automáticas")

    if db.count_words() < 2:
        st.info("Cadastre pelo menos 2 palavras para gerar um quiz.")
        return

    if "qz_perguntas" not in st.session_state:
        _tela_configuracao()
        return

    perguntas = st.session_state["qz_perguntas"]
    indice = st.session_state["qz_indice"]

    if indice >= len(perguntas):
        _tela_final()
        return

    pergunta = perguntas[indice]
    st.progress(indice / len(perguntas), text=f"Pergunta {indice + 1} de {len(perguntas)}")
    st.markdown(f"### {pergunta.enunciado}")

    # --- Resposta ainda não enviada ---------------------------------------
    if not st.session_state.get("qz_feedback"):
        if pergunta.tipo == "multipla_escolha":
            escolha = st.radio(
                "Escolha a alternativa correta:",
                pergunta.opcoes,
                key=f"qz_op_{indice}",
                index=None,
            )
            if st.button("Responder", type="primary", use_container_width=True):
                if escolha is None:
                    st.warning("Selecione uma alternativa.")
                else:
                    _avaliar(pergunta, escolha, escolha == pergunta.resposta)
        else:
            digitada = st.text_input(
                "Digite sua resposta:", key=f"qz_txt_{indice}", placeholder="sua resposta"
            )
            if st.button("Responder", type="primary", use_container_width=True):
                _avaliar(pergunta, digitada, resposta_correta(digitada, pergunta.resposta))

        if pergunta.dica:
            with st.expander("💡 Ver dica"):
                st.write(pergunta.dica)
        return

    # --- Feedback da resposta ---------------------------------------------
    feedback = st.session_state["qz_feedback"]
    if feedback["correct"]:
        st.success(f"✅ Correto! Resposta: **{pergunta.resposta}**")
    else:
        st.error(
            f"❌ Errado. Você respondeu: *{feedback['dada'] or '(vazio)'}* · "
            f"Resposta correta: **{pergunta.resposta}**"
        )
    if pergunta.dica:
        st.caption(f"Exemplo/definição: {pergunta.dica}")

    rotulo = "Próxima pergunta" if indice + 1 < len(perguntas) else "Ver resultado"
    if st.button(rotulo, type="primary", use_container_width=True):
        st.session_state["qz_indice"] += 1
        st.session_state["qz_feedback"] = None
        st.rerun()


def _tela_configuracao() -> None:
    with st.form("qz_config"):
        c1, c2 = st.columns(2)
        quantidade = c1.number_input("Número de perguntas", 1, 50, 10)
        tipo = c2.selectbox("Tipo de pergunta", TIPOS_QUIZ)
        c3, c4 = st.columns(2)
        categoria = c3.selectbox("Categoria", ["Todas"] + db.list_categories())
        dificuldade = c4.selectbox("Dificuldade", ["Todas"] + DIFICULDADES)
        iniciar = st.form_submit_button("▶️ Começar quiz", type="primary", use_container_width=True)

    if iniciar:
        perguntas = gerar_quiz(int(quantidade), tipo, categoria, dificuldade)
        if not perguntas:
            st.warning("Não há palavras suficientes com esses filtros.")
            return
        st.session_state["qz_perguntas"] = perguntas
        st.session_state["qz_indice"] = 0
        st.session_state["qz_feedback"] = None
        st.session_state["qz_respostas"] = []
        st.rerun()


def _avaliar(pergunta, dada: str, correto: bool) -> None:
    """Registra a resposta no banco e guarda para o resumo final."""
    word = db.get_word(pergunta.word_id)
    if word:
        registrar_resposta_simples(word, correto, mode="quiz")
    st.session_state["qz_respostas"].append(
        {"correct": correto, "english": word["english"] if word else pergunta.resposta}
    )
    st.session_state["qz_feedback"] = {"correct": correto, "dada": dada}
    st.rerun()


def _tela_final() -> None:
    resultado = consolidar_resultado(st.session_state.get("qz_respostas", []))
    db.save_quiz_session(resultado.total, resultado.acertos, resultado.erros)

    st.success("🏁 Quiz finalizado!")
    c1, c2, c3 = st.columns(3)
    c1.metric("Acertos", resultado.acertos)
    c2.metric("Erros", resultado.erros)
    c3.metric("Percentual", f"{resultado.percentual:.0f}%")
    st.progress(resultado.percentual / 100)

    if resultado.revisar:
        st.warning("📌 Palavras para revisar: " + ", ".join(sorted(set(resultado.revisar))))
    else:
        st.balloons()
        st.info("Excelente! Você acertou todas as perguntas.")

    if st.button("🔄 Novo quiz", type="primary", use_container_width=True):
        limpar_estado(PREFIXO)
        st.rerun()
