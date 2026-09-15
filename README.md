# 🧠 Meu Inglês — Flashcards + Repetição Espaçada (Streamlit + SQLite)

Aplicação pessoal e 100% local para estudo de vocabulário em inglês, inspirada no Anki.

## Instalação

```bash
# 1. Criar e ativar um ambiente virtual (opcional, mas recomendado)
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

# 2. Instalar dependências
pip install -r requirements.txt
```

## Executar

```bash
streamlit run app.py
```

A aplicação abre em `http://localhost:8501`. O banco `vocabulario.db` é criado
automaticamente na primeira execução, na mesma pasta do projeto.

## Estrutura

```
app.py                 # entrada + navegação lateral
database.py            # SQLite: schema, CRUD, consultas
models.py              # dataclasses e constantes
study.py               # repetição espaçada e seleção de palavras
quiz.py                # geração automática de perguntas
utils.py               # estilo e componentes visuais
requirements.txt
views/
  home.py              # 🏠 Dashboard
  flashcards.py        # 📚 Estudar Flashcards
  quiz_page.py         # 🎯 Quiz
  random_words.py      # 🎲 Palavras Aleatórias
  add_word.py          # ➕ Adicionar Palavra
  manage.py            # 📝 Gerenciar Vocabulário
  stats.py             # 📊 Estatísticas
```

## Backup

Basta copiar o arquivo `vocabulario.db`. Também é possível exportar um CSV
pela página **Gerenciar Vocabulário**.
