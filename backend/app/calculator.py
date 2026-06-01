"""
Motor de cálculo FPRS — módulo puro, sem I/O nem dependência de web.

Entrada : lista de nomes de medicamentos (strings) + dicionário de parâmetros
          + callable de lookup no banco (injetado para facilitar testes)
Saída   : FPRSResult com detalhamento completo
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional


# ---------------------------------------------------------------------------
# Tipos de dados
# ---------------------------------------------------------------------------

@dataclass
class MedicamentoDetalhe:
    entrada_original: str
    nome_normalizado: str
    encontrado: bool
    pim_beers: bool
    afinidade_ac: str       # No / Low / Moderate / High
    afinidade_sedativa: str
    peso_afinidade: int     # 0–3
    contribuicao: float     # valor efetivo somado ao FPRS
    duplicata: bool
    observacao: str


@dataclass
class FPRSResult:
    medicamentos: list[MedicamentoDetalhe] = field(default_factory=list)
    total_medicamentos: int = 0
    pontos_polifarmacia: float = 0.0
    carga_afinidade: float = 0.0
    pim_adicional: float = 0.0
    fprs: float = 0.0
    categoria: str = ""     # "Alto risco" | "Baixo risco"
    alerta: str = ""
    label_polifarmacia: str = ""  # "Sem polifarmácia" | "Polifarmácia" | "Superpolifarmácia"


# ---------------------------------------------------------------------------
# Parâmetros padrão (usados quando nenhum dict é passado)
# ---------------------------------------------------------------------------

PARAMETROS_PADRAO: dict[str, float] = {
    "poli_0_4":            0.0,
    "poli_5_9":            0.5,
    "poli_10_mais":        1.0,
    "afinidade_low":       1.0,
    "afinidade_moderate":  2.0,
    "afinidade_high":      3.0,
    "pim_beers_adicional": 0.5,
    "capacidade_max":      25.0,
    "corte_alto_risco":    1.5,
}

AFINIDADE_PESO = {"No": 0, "Low": 1, "Moderate": 2, "High": 3}


# ---------------------------------------------------------------------------
# Função principal
# ---------------------------------------------------------------------------

def calcular_fprs(
    entradas: list[str],
    lookup: Callable[[str], tuple[str, Optional[dict]]],
    params: Optional[dict[str, float]] = None,
) -> FPRSResult:
    """
    Parâmetros
    ----------
    entradas : lista de nomes brutos do paciente (máx. capacidade_max)
    lookup   : fn(entrada_bruta) -> (nome_normalizado, registro_ou_None)
               registro_ou_None: dict com chaves pim_beers, peso_afinidade,
               afinidade_ac, afinidade_sedativa — ou None se não encontrado
    params   : dict de parâmetros; usa PARAMETROS_PADRAO se None
    """
    p = {**PARAMETROS_PADRAO, **(params or {})}
    cap = int(p["capacidade_max"])
    result = FPRSResult()

    # Filtrar entradas não vazias e respeitar capacidade máxima
    entradas_validas = [e for e in entradas if e.strip()][:cap]
    result.total_medicamentos = len(entradas_validas)

    # RN-06 — Polifarmácia
    n = result.total_medicamentos
    if n >= 10:
        result.pontos_polifarmacia = p["poli_10_mais"]
        result.label_polifarmacia = "Superpolifarmácia"
    elif n >= 5:
        result.pontos_polifarmacia = p["poli_5_9"]
        result.label_polifarmacia = "Polifarmácia"
    else:
        result.pontos_polifarmacia = p["poli_0_4"]
        result.label_polifarmacia = "Sem polifarmácia"

    ja_pontuados: set[str] = set()
    carga_afinidade = 0.0
    pim_adicional = 0.0

    for entrada in entradas_validas:
        # RN-01 — Normalização + alias (delegado ao lookup)
        nome_norm, registro = lookup(entrada)

        # RN-02 — Não encontrado
        if registro is None:
            result.medicamentos.append(MedicamentoDetalhe(
                entrada_original=entrada,
                nome_normalizado=nome_norm,
                encontrado=False,
                pim_beers=False,
                afinidade_ac="No",
                afinidade_sedativa="No",
                peso_afinidade=0,
                contribuicao=0.0,
                duplicata=False,
                observacao="Revisar grafia/nome genérico ou inserir na Base_Fixa",
            ))
            continue

        # RN-04 — Deduplicação
        duplicata = nome_norm in ja_pontuados

        pim = bool(registro["pim_beers"])
        peso = int(registro["peso_afinidade"])
        ac = registro["afinidade_ac"]
        sed = registro["afinidade_sedativa"]

        if duplicata:
            contribuicao = 0.0
            obs = "Duplicata — não pontuada"
        elif peso > 0:
            # RN-03 / RN-05 hierarquia: afinidade tem prioridade
            contribuicao = float(peso)
            carga_afinidade += contribuicao
            obs = "Afinidade AC/sedativa"
        elif pim:
            # RN-05 — PIM como rede de captura
            contribuicao = p["pim_beers_adicional"]
            pim_adicional += contribuicao
            obs = "MPI/Beers (sem afinidade AC/sedativa)"
        else:
            contribuicao = 0.0
            obs = "Sem contribuição"

        if not duplicata:
            ja_pontuados.add(nome_norm)

        result.medicamentos.append(MedicamentoDetalhe(
            entrada_original=entrada,
            nome_normalizado=nome_norm,
            encontrado=True,
            pim_beers=pim,
            afinidade_ac=ac,
            afinidade_sedativa=sed,
            peso_afinidade=peso,
            contribuicao=contribuicao,
            duplicata=duplicata,
            observacao=obs,
        ))

    result.carga_afinidade = carga_afinidade
    result.pim_adicional = pim_adicional

    # RN-07 — FPRS final
    result.fprs = round(carga_afinidade + pim_adicional + result.pontos_polifarmacia, 4)

    # RN-08 — Classificação
    corte = p["corte_alto_risco"]
    if result.fprs > corte:
        result.categoria = "Alto risco"
        result.alerta = "Necessidade de revisão da farmacoterapia"
    else:
        result.categoria = "Baixo risco"
        result.alerta = "Sem indicação prioritária de revisão pelo FPRS"

    return result
