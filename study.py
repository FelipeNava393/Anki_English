"""
study.py
--------
Regras de estudo e repetição espaçada (inspirado no SM-2 do Anki,
porém simplificado e fácil de ajustar).

Ideia central:
- Cada palavra guarda `interval_days`, `ease` e `repetitions`.
- A classificação do usuário (Errei / Difícil / Acertei / Fácil) define
  o próximo intervalo.
- Errou ou achou difícil -> volta a aparecer muito rápido.
"""

from __future__ import annotations

import random
from datetime import date, timedelta

from database import due_words, list_words, save_review
from models import AVALIACOES

# Multiplicadores por classificação (ajuste fino em um único lugar)
FATOR_EASE = {
    "Errei": -0.20,
    "Difícil": -0.15,
    "Acertei": 0.0,
    "Fácil": +0.15,
}

EASE_MINIMO = 1.3


def calcular_proxima_revisao(
    rating: str, interval_days: int, ease: float, repetitions: int
) -> tuple[int, float, int, str]:
    """Calcula o próximo agendamento de uma palavra.

    Retorna (novo_intervalo_em_dias, novo_ease, repeticoes, data_proxima_revisao).
    """
    ease = max(EASE_MINIMO, ease + FATOR_EASE.get(rating, 0.0))

    if rating == "Errei":
        # Reinicia o ciclo: reaparece no mesmo dia.
        repetitions = 0
        intervalo = 0
    elif rating == "Difícil":
        repetitions += 1
        intervalo = 1
    elif rating == "Acertei":
        repetitions += 1
        if repetitions == 1:
            intervalo = 1
        elif repetitions == 2:
            intervalo = 3
        else:
            intervalo = max(1, round(interval_days * ease))
    else:  # Fácil
        repetitions += 1
        if repetitions == 1:
            intervalo = 2
        elif repetitions == 2:
            intervalo = 5
        else:
            intervalo = max(2, round(interval_days * ease * 1.3))

    intervalo = min(intervalo, 365)  # teto de 1 ano
    proxima = (date.today() + timedelta(days=intervalo)).isoformat()
    return intervalo, round(ease, 2), repetitions, proxima


def registrar_resposta(word: dict, rating: str, mode: str = "flashcard") -> None:
    """Aplica a classificação do usuário e persiste tudo no banco."""
    intervalo, ease, reps, proxima = calcular_proxima_revisao(
        rating,
        int(word.get("interval_days") or 0),
        float(word.get("ease") or 2.5),
        int(word.get("repetitions") or 0),
    )
    save_review(
        word_id=int(word["id"]),
        correct=AVALIACOES.get(rating, 0) >= 2,
        rating=rating,
        next_review=proxima,
        interval_days=intervalo,
        ease=ease,
        repetitions=reps,
        mode=mode,
    )


def registrar_resposta_simples(word: dict, correto: bool, mode: str = "quiz") -> None:
    """Atalho usado pelo quiz, onde só existe certo/errado."""
    registrar_resposta(word, "Acertei" if correto else "Errei", mode=mode)


# ---------------------------------------------------------------------------
# Seleção de palavras para as sessões
# ---------------------------------------------------------------------------
def peso_da_palavra(word: dict) -> float:
    """Peso para sorteio: erros e dificuldade aumentam a chance de aparecer."""
    erros = int(word.get("wrong_count") or 0)
    acertos = int(word.get("correct_count") or 0)
    peso = 1.0 + erros * 1.5 - acertos * 0.2
    if word.get("difficulty") == "Difícil":
        peso += 1.5
    elif word.get("difficulty") == "Fácil":
        peso -= 0.3
    if not word.get("last_review"):
        peso += 1.0  # nunca estudada tem prioridade
    return max(0.3, peso)


def montar_sessao(
    quantidade: int = 10,
    category: str = "Todas",
    difficulty: str = "Todas",
    somente_revisao: bool = True,
) -> list[dict]:
    """Monta a lista de palavras de uma sessão de estudo.

    - `somente_revisao=True` prioriza as palavras vencidas (due).
    - Completa com sorteio ponderado caso falte palavra.
    """
    candidatas = (
        due_words(limit=500) if somente_revisao else list_words("", category, difficulty)
    )

    if somente_revisao and (category != "Todas" or difficulty != "Todas"):
        candidatas = [
            w
            for w in candidatas
            if (category == "Todas" or w["category"] == category)
            and (difficulty == "Todas" or w["difficulty"] == difficulty)
        ]

    if not candidatas:
        candidatas = list_words("", category, difficulty)
    if not candidatas:
        return []

    quantidade = min(quantidade, len(candidatas))
    selecionadas: list[dict] = []
    pool = list(candidatas)
    pesos = [peso_da_palavra(w) for w in pool]

    # Sorteio ponderado sem reposição
    for _ in range(quantidade):
        escolhida = random.choices(pool, weights=pesos, k=1)[0]
        idx = pool.index(escolhida)
        pool.pop(idx)
        pesos.pop(idx)
        selecionadas.append(escolhida)

    return selecionadas


def sortear_aleatorias(
    quantidade: int = 10, category: str = "Todas", difficulty: str = "Todas"
) -> list[dict]:
    """Sorteio puramente aleatório (Modo Aleatório)."""
    palavras = list_words("", category, difficulty)
    random.shuffle(palavras)
    return palavras[:quantidade]
