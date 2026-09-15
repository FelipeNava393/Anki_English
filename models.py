"""
models.py
---------
Estruturas de dados da aplicação.

Como o projeto usa SQLite puro, os "models" aqui são dataclasses simples
que servem para transportar dados entre as camadas com tipagem clara.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional

# Opções fixas usadas nos formulários e filtros
DIFICULDADES = ["Fácil", "Médio", "Difícil"]

# Classificações do flashcard -> (é acerto?, peso para o algoritmo)
AVALIACOES = {
    "Errei": 0,
    "Difícil": 1,
    "Acertei": 2,
    "Fácil": 3,
}


@dataclass
class Word:
    """Representa uma palavra/expressão do vocabulário."""

    english: str
    portuguese: str
    definition: str = ""
    example: str = ""
    category: str = "Geral"
    difficulty: str = "Médio"
    notes: str = ""
    id: Optional[int] = None
    created_at: Optional[str] = None
    correct_count: int = 0
    wrong_count: int = 0
    last_review: Optional[str] = None
    next_review: Optional[str] = None
    interval_days: int = 0
    ease: float = 2.5
    repetitions: int = 0

    @classmethod
    def from_row(cls, row: dict) -> "Word":
        """Cria um Word a partir de um dicionário vindo do banco."""
        campos = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in row.items() if k in campos})

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def tentativas(self) -> int:
        return self.correct_count + self.wrong_count

    @property
    def taxa_acerto(self) -> float:
        return (self.correct_count / self.tentativas * 100) if self.tentativas else 0.0


@dataclass
class QuizQuestion:
    """Uma pergunta gerada pelo módulo de quiz."""

    word_id: int
    tipo: str            # multipla_escolha | digitar
    direcao: str         # en_pt | pt_en
    enunciado: str
    resposta: str
    opcoes: list[str] = field(default_factory=list)
    dica: str = ""


@dataclass
class QuizResult:
    """Resultado consolidado de uma sessão de quiz."""

    total: int = 0
    acertos: int = 0
    erros: int = 0
    revisar: list[str] = field(default_factory=list)

    @property
    def percentual(self) -> float:
        return (self.acertos / self.total * 100) if self.total else 0.0
