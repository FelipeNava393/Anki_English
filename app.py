"""
app.py
------
Ponto de entrada da aplicação Streamlit.

Responsável apenas por:
- Configurar a página.
- Inicializar o banco de dados.
- Montar a navegação lateral e chamar a página escolhida.

Execute com:  streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

import database as db
from utils import aplicar_estilo
from views import add_word, flashcards, home, manage, quiz_page, random_words, stats

# --- Configuração geral da página -----------------------------------------
st.set_page_config(
    page_title="Vocabulário EN | Estudo de Inglês",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Cria as tabelas na primeira execução
db.init_db()
aplicar_estilo()

# --- Mapa de páginas -------------------------------------------------------
PAGINAS = {
    "🏠 Início": home.render,
    "📚 Estudar Flashcards": flashcards.render,
    "🎯 Quiz": quiz_page.render,
    "🎲 Palavras Aleatórias": random_words.render,
    "➕ Adicionar Palavra": add_word.render,
    "📝 Gerenciar Vocabulário": manage.render,
    "📊 Estatísticas": stats.render,
}


def main() -> None:
    with st.sidebar:
        st.title("🧠 Meu Inglês")
        st.caption("Flashcards e revisão espaçada")
        pagina = st.radio("Navegação", list(PAGINAS.keys()), label_visibility="collapsed")

        st.divider()
        resumo = db.global_stats()
        st.metric("Palavras", resumo["total"])
        st.metric("Para revisar hoje", resumo["a_revisar"])
        st.caption("Dados salvos localmente em vocabulario.db")

    # Renderiza a página selecionada
    PAGINAS[pagina]()


if __name__ == "__main__":
    main()
