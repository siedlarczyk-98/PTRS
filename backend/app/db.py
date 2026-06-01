"""
Camada de acesso ao SQLite. Todas as queries são parametrizadas.
O caminho do banco é resolvido via variável de ambiente DB_PATH ou
cai no padrão data/seed.db relativo ao diretório deste arquivo.
"""
import os
import sqlite3
from pathlib import Path
from typing import Optional

_DEFAULT_DB = Path(__file__).parent.parent / "data" / "seed.db"


def get_db_path() -> Path:
    env = os.environ.get("DB_PATH")
    return Path(env) if env else _DEFAULT_DB


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ---------------------------------------------------------------------------
# Tipos de retorno simples (dicts) — evita acoplamento com modelos Pydantic
# ---------------------------------------------------------------------------

def buscar_medicamento(nome_normalizado: str) -> Optional[dict]:
    """Retorna o registro de medicamentos_base ou None se não encontrado."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM medicamentos_base WHERE nome_normalizado = ?",
            (nome_normalizado,),
        ).fetchone()
    return dict(row) if row else None


def buscar_alias(entrada: str) -> Optional[str]:
    """Retorna o nome_normalizado para uma entrada aceita, ou None."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT nome_normalizado FROM aliases WHERE entrada_aceita = ?",
            (entrada,),
        ).fetchone()
    return row["nome_normalizado"] if row else None


def listar_parametros() -> dict[str, float]:
    """Retorna {chave: valor} de todos os parâmetros."""
    with _connect() as conn:
        rows = conn.execute("SELECT chave, valor FROM parametros").fetchall()
    return {r["chave"]: r["valor"] for r in rows}


def buscar_medicamento_completo(nome_raw: str) -> tuple[str, Optional[dict]]:
    """
    Recebe a entrada bruta, aplica normalização (lower+strip+alias) e
    devolve (nome_normalizado, registro_ou_None).
    """
    normalizado = nome_raw.strip().lower()
    alias = buscar_alias(normalizado)
    if alias:
        normalizado = alias
    return normalizado, buscar_medicamento(normalizado)
