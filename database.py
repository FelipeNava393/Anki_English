"""
database.py
-----------
Camada de acesso ao banco de dados SQLite.

Responsabilidades:
- Criar a conexão e o schema (tabelas).
- Operações CRUD de vocabulário.
- Registro do histórico de estudo.
- Consultas usadas pelo dashboard / estatísticas.

Tudo é local: o arquivo `vocabulario.db` é criado na pasta do projeto.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, date
from pathlib import Path
from typing import Any, Iterable, Optional

import pandas as pd

# Caminho do banco (sempre ao lado dos arquivos .py do projeto)
DB_PATH = Path(__file__).parent / "vocabulario.db"


# ---------------------------------------------------------------------------
# Conexão e schema
# ---------------------------------------------------------------------------
def get_connection() -> sqlite3.Connection:
    """Abre uma conexão com o SQLite retornando linhas como dicionários."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db() -> None:
    """Cria as tabelas caso ainda não existam. Seguro para chamar sempre."""
    with get_connection() as conn:
        conn.executescript(
            """
            -- Vocabulário -------------------------------------------------
            CREATE TABLE IF NOT EXISTS words (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                english       TEXT NOT NULL COLLATE NOCASE,
                portuguese    TEXT NOT NULL,
                definition    TEXT DEFAULT '',
                example       TEXT DEFAULT '',
                category      TEXT DEFAULT 'Geral',
                difficulty    TEXT DEFAULT 'Médio',
                notes         TEXT DEFAULT '',
                created_at    TEXT NOT NULL,
                correct_count INTEGER NOT NULL DEFAULT 0,
                wrong_count   INTEGER NOT NULL DEFAULT 0,
                last_review   TEXT,
                next_review   TEXT,
                interval_days INTEGER NOT NULL DEFAULT 0,
                ease          REAL    NOT NULL DEFAULT 2.5,
                repetitions   INTEGER NOT NULL DEFAULT 0
            );

            CREATE UNIQUE INDEX IF NOT EXISTS idx_words_english
                ON words (english COLLATE NOCASE);

            -- Histórico de estudo ----------------------------------------
            CREATE TABLE IF NOT EXISTS study_log (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                word_id    INTEGER NOT NULL,
                mode       TEXT NOT NULL,          -- flashcard | quiz | aleatorio
                rating     TEXT,                   -- errei | dificil | acertei | facil
                correct    INTEGER NOT NULL,       -- 0 ou 1
                created_at TEXT NOT NULL,
                FOREIGN KEY (word_id) REFERENCES words (id) ON DELETE CASCADE
            );

            -- Sessões de quiz --------------------------------------------
            CREATE TABLE IF NOT EXISTS quiz_sessions (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TEXT NOT NULL,
                total      INTEGER NOT NULL,
                correct    INTEGER NOT NULL,
                wrong      INTEGER NOT NULL
            );
            """
        )


# ---------------------------------------------------------------------------
# CRUD de vocabulário
# ---------------------------------------------------------------------------
def word_exists(english: str, exclude_id: Optional[int] = None) -> bool:
    """Verifica duplicidade de palavra (ignorando maiúsculas/minúsculas)."""
    sql = "SELECT id FROM words WHERE english = ? COLLATE NOCASE"
    params: list[Any] = [english.strip()]
    if exclude_id is not None:
        sql += " AND id <> ?"
        params.append(exclude_id)
    with get_connection() as conn:
        return conn.execute(sql, params).fetchone() is not None


def add_word(
    english: str,
    portuguese: str,
    definition: str = "",
    example: str = "",
    category: str = "Geral",
    difficulty: str = "Médio",
    notes: str = "",
) -> int:
    """Insere uma nova palavra e devolve o id criado.

    Levanta ValueError se a palavra já existir.
    """
    english = english.strip()
    if not english or not portuguese.strip():
        raise ValueError("Palavra em inglês e tradução são obrigatórias.")
    if word_exists(english):
        raise ValueError(f"A palavra '{english}' já está cadastrada.")

    now = datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO words (english, portuguese, definition, example,
                               category, difficulty, notes, created_at, next_review)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                english,
                portuguese.strip(),
                definition.strip(),
                example.strip(),
                (category or "Geral").strip(),
                difficulty,
                notes.strip(),
                now,
                date.today().isoformat(),  # disponível para revisão imediatamente
            ),
        )
        return int(cur.lastrowid)


def update_word(word_id: int, **fields: Any) -> None:
    """Atualiza campos editáveis de uma palavra."""
    permitidos = {
        "english",
        "portuguese",
        "definition",
        "example",
        "category",
        "difficulty",
        "notes",
    }
    dados = {k: v for k, v in fields.items() if k in permitidos}
    if not dados:
        return
    if "english" in dados and word_exists(str(dados["english"]), exclude_id=word_id):
        raise ValueError(f"Já existe outra palavra '{dados['english']}'.")

    sets = ", ".join(f"{k} = ?" for k in dados)
    with get_connection() as conn:
        conn.execute(
            f"UPDATE words SET {sets} WHERE id = ?", (*dados.values(), word_id)
        )


def delete_word(word_id: int) -> None:
    """Remove a palavra e todo o histórico associado."""
    with get_connection() as conn:
        conn.execute("DELETE FROM words WHERE id = ?", (word_id,))


def get_word(word_id: int) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM words WHERE id = ?", (word_id,)).fetchone()
    return dict(row) if row else None


def list_words(
    search: str = "",
    category: str = "Todas",
    difficulty: str = "Todas",
) -> list[dict]:
    """Lista palavras aplicando busca textual e filtros."""
    sql = "SELECT * FROM words WHERE 1 = 1"
    params: list[Any] = []

    if search.strip():
        sql += " AND (english LIKE ? OR portuguese LIKE ?)"
        termo = f"%{search.strip()}%"
        params += [termo, termo]
    if category and category != "Todas":
        sql += " AND category = ?"
        params.append(category)
    if difficulty and difficulty != "Todas":
        sql += " AND difficulty = ?"
        params.append(difficulty)

    sql += " ORDER BY english COLLATE NOCASE"
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def list_categories() -> list[str]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT category FROM words WHERE category <> '' ORDER BY category"
        ).fetchall()
    return [r["category"] for r in rows]


def count_words() -> int:
    with get_connection() as conn:
        return int(conn.execute("SELECT COUNT(*) c FROM words").fetchone()["c"])


# ---------------------------------------------------------------------------
# Revisão / agendamento
# ---------------------------------------------------------------------------
def save_review(
    word_id: int,
    correct: bool,
    rating: str,
    next_review: str,
    interval_days: int,
    ease: float,
    repetitions: int,
    mode: str = "flashcard",
) -> None:
    """Grava o resultado de uma revisão e atualiza o agendamento da palavra."""
    now = datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE words
               SET correct_count = correct_count + ?,
                   wrong_count   = wrong_count + ?,
                   last_review   = ?,
                   next_review   = ?,
                   interval_days = ?,
                   ease          = ?,
                   repetitions   = ?
             WHERE id = ?
            """,
            (
                1 if correct else 0,
                0 if correct else 1,
                now,
                next_review,
                interval_days,
                ease,
                repetitions,
                word_id,
            ),
        )
        conn.execute(
            """
            INSERT INTO study_log (word_id, mode, rating, correct, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (word_id, mode, rating, 1 if correct else 0, now),
        )


def save_quiz_session(total: int, correct: int, wrong: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO quiz_sessions (started_at, total, correct, wrong) VALUES (?, ?, ?, ?)",
            (datetime.now().isoformat(timespec="seconds"), total, correct, wrong),
        )


def due_words(limit: int = 50) -> list[dict]:
    """Palavras cuja próxima revisão já venceu (ou nunca foram estudadas)."""
    hoje = date.today().isoformat()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM words
             WHERE next_review IS NULL OR date(next_review) <= date(?)
             ORDER BY (wrong_count - correct_count) DESC,
                      COALESCE(date(next_review), '0001-01-01') ASC
             LIMIT ?
            """,
            (hoje, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def count_due_words() -> int:
    hoje = date.today().isoformat()
    with get_connection() as conn:
        return int(
            conn.execute(
                "SELECT COUNT(*) c FROM words "
                "WHERE next_review IS NULL OR date(next_review) <= date(?)",
                (hoje,),
            ).fetchone()["c"]
        )


# ---------------------------------------------------------------------------
# Consultas para estatísticas
# ---------------------------------------------------------------------------
def words_dataframe() -> pd.DataFrame:
    with get_connection() as conn:
        return pd.read_sql_query("SELECT * FROM words", conn)


def study_log_dataframe() -> pd.DataFrame:
    with get_connection() as conn:
        return pd.read_sql_query(
            """
            SELECT l.*, w.english
              FROM study_log l
              LEFT JOIN words w ON w.id = l.word_id
             ORDER BY l.created_at
            """,
            conn,
        )


def global_stats() -> dict:
    """Números agregados usados no dashboard."""
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) c FROM words").fetchone()["c"]
        estudadas = conn.execute(
            "SELECT COUNT(*) c FROM words WHERE last_review IS NOT NULL"
        ).fetchone()["c"]
        acertos = conn.execute(
            "SELECT COALESCE(SUM(correct_count), 0) s FROM words"
        ).fetchone()["s"]
        erros = conn.execute(
            "SELECT COALESCE(SUM(wrong_count), 0) s FROM words"
        ).fetchone()["s"]

    tentativas = acertos + erros
    return {
        "total": total,
        "estudadas": estudadas,
        "a_revisar": count_due_words(),
        "acertos": acertos,
        "erros": erros,
        "taxa_acerto": (acertos / tentativas * 100) if tentativas else 0.0,
    }


def hardest_words(limit: int = 10) -> list[dict]:
    """Palavras com mais erros (as que mais precisam de atenção)."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT english, portuguese, correct_count, wrong_count
              FROM words
             WHERE wrong_count > 0
             ORDER BY wrong_count DESC, correct_count ASC
             LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def bulk_insert(words: Iterable[dict]) -> int:
    """Importa várias palavras de uma vez (ignora duplicadas). Retorna quantas entraram."""
    inseridas = 0
    for w in words:
        try:
            add_word(**w)
            inseridas += 1
        except ValueError:
            continue
    return inseridas
