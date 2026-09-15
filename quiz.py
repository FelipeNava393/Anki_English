"""
quiz.py
-------
Geração automática de perguntas a partir do banco de vocabulário.

Tipos suportados:
- Múltipla escolha  (Inglês -> Português  ou  Português -> Inglês)
- Digitar a resposta (Inglês -> Português  ou  Português -> Inglês)
- Identificar a tradução correta (múltipla escolha com distratores)
"""

from __future__ import annotations

import random
import unicodedata

from database import list_words
from models import QuizQuestion, QuizResult

TIPOS_QUIZ = [
    "Misto",
    "Inglês → Português",
    "Português → Inglês",
    "Múltipla escolha",
    "Digitar a resposta",
]


# ---------------------------------------------------------------------------
# Helpers de comparação de texto
# ---------------------------------------------------------------------------
def normalizar(texto: str) -> str:
    """Remove acentos, espaços extras e caixa para comparar respostas digitadas."""
    texto = (texto or "").strip().lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return " ".join(texto.split())


def resposta_correta(digitada: str, esperada: str) -> bool:
    """Aceita a resposta se bater com o texto todo ou com uma das alternativas
    separadas por vírgula/barra (ex.: 'casa, lar')."""
    alvo = normalizar(digitada)
    if not alvo:
        return False
    opcoes = [normalizar(p) for p in esperada.replace("/", ",").split(",")]
    return alvo in opcoes or alvo == normalizar(esperada)


# ---------------------------------------------------------------------------
# Geração de perguntas
# ---------------------------------------------------------------------------
def _distratores(palavras: list[dict], correta: dict, campo: str, n: int = 3) -> list[str]:
    """Sorteia alternativas erradas plausíveis (mesma categoria quando possível)."""
    mesma_categoria = [
        w for w in palavras
        if w["id"] != correta["id"] and w["category"] == correta["category"]
    ]
    outras = [w for w in palavras if w["id"] != correta["id"]]
    fonte = mesma_categoria if len(mesma_categoria) >= n else outras
    random.shuffle(fonte)

    vistos, escolhidos = {normalizar(correta[campo])}, []
    for w in fonte:
        if normalizar(w[campo]) not in vistos:
            vistos.add(normalizar(w[campo]))
            escolhidos.append(w[campo])
        if len(escolhidos) == n:
            break
    return escolhidos


def gerar_pergunta(palavra: dict, palavras: list[dict], tipo: str) -> QuizQuestion:
    """Cria uma pergunta para uma palavra específica."""
    # Define direção e formato conforme o tipo escolhido pelo usuário
    if tipo == "Inglês → Português":
        direcao, formato = "en_pt", random.choice(["multipla_escolha", "digitar"])
    elif tipo == "Português → Inglês":
        direcao, formato = "pt_en", random.choice(["multipla_escolha", "digitar"])
    elif tipo == "Múltipla escolha":
        direcao, formato = random.choice(["en_pt", "pt_en"]), "multipla_escolha"
    elif tipo == "Digitar a resposta":
        direcao, formato = random.choice(["en_pt", "pt_en"]), "digitar"
    else:  # Misto
        direcao = random.choice(["en_pt", "pt_en"])
        formato = random.choice(["multipla_escolha", "digitar"])

    if direcao == "en_pt":
        enunciado = f"Qual a tradução de **{palavra['english']}**?"
        resposta, campo = palavra["portuguese"], "portuguese"
    else:
        enunciado = f"Como se diz **{palavra['portuguese']}** em inglês?"
        resposta, campo = palavra["english"], "english"

    opcoes: list[str] = []
    if formato == "multipla_escolha":
        opcoes = _distratores(palavras, palavra, campo) + [resposta]
        # Se o banco for pequeno demais, cai para "digitar"
        if len(opcoes) < 2:
            formato, opcoes = "digitar", []
        else:
            random.shuffle(opcoes)

    return QuizQuestion(
        word_id=int(palavra["id"]),
        tipo=formato,
        direcao=direcao,
        enunciado=enunciado,
        resposta=resposta,
        opcoes=opcoes,
        dica=palavra.get("example") or palavra.get("definition") or "",
    )


def gerar_quiz(
    quantidade: int = 10,
    tipo: str = "Misto",
    category: str = "Todas",
    difficulty: str = "Todas",
    palavras: list[dict] | None = None,
) -> list[QuizQuestion]:
    """Monta uma lista de perguntas prontas para a sessão de quiz."""
    banco = palavras if palavras is not None else list_words("", category, difficulty)
    if not banco:
        return []

    selecionadas = random.sample(banco, k=min(quantidade, len(banco)))
    return [gerar_pergunta(p, banco, tipo) for p in selecionadas]


def consolidar_resultado(respostas: list[dict]) -> QuizResult:
    """Recebe a lista de respostas da sessão e devolve o resumo final.

    Cada item deve ter: {'correct': bool, 'english': str}
    """
    resultado = QuizResult(total=len(respostas))
    for r in respostas:
        if r["correct"]:
            resultado.acertos += 1
        else:
            resultado.erros += 1
            resultado.revisar.append(r["english"])
    return resultado
