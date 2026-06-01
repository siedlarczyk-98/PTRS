"""
Testes do motor de cálculo FPRS.
Cobertura: Exemplo_teste da planilha + casos de borda.
"""
import pytest
from app.calculator import calcular_fprs, PARAMETROS_PADRAO

# ---------------------------------------------------------------------------
# Base de dados simulada (subset do Exemplo_teste + medicamentos extras)
# ---------------------------------------------------------------------------

BASE_FAKE: dict[str, dict] = {
    "amitriptyline": {"pim_beers": 1, "afinidade_ac": "High",     "afinidade_sedativa": "High",     "peso_afinidade": 3},
    "losartan":      {"pim_beers": 0, "afinidade_ac": "No",       "afinidade_sedativa": "Low",      "peso_afinidade": 1},
    "metformin":     {"pim_beers": 0, "afinidade_ac": "No",       "afinidade_sedativa": "No",       "peso_afinidade": 0},
    "lorazepam":     {"pim_beers": 1, "afinidade_ac": "Low",      "afinidade_sedativa": "High",     "peso_afinidade": 3},
    "atorvastatin":  {"pim_beers": 0, "afinidade_ac": "No",       "afinidade_sedativa": "Low",      "peso_afinidade": 1},
    "paroxetine":    {"pim_beers": 1, "afinidade_ac": "Moderate", "afinidade_sedativa": "Moderate", "peso_afinidade": 2},
    # PIM sem afinidade (rede de captura)
    "aspirin":       {"pim_beers": 1, "afinidade_ac": "No",       "afinidade_sedativa": "No",       "peso_afinidade": 0},
    # sem contribuição
    "acetaminophen": {"pim_beers": 0, "afinidade_ac": "No",       "afinidade_sedativa": "No",       "peso_afinidade": 0},
}

ALIASES_FAKE: dict[str, str] = {
    "amitryptiline": "amitriptyline",  # grafia alternativa do Exemplo_teste
    "tylenol":       "acetaminophen",
    "aspirin":       "aspirin",
    "acetylsalicylic acid": "aspirin",
}


def lookup_fake(entrada: str):
    normalizado = entrada.strip().lower()
    if normalizado in ALIASES_FAKE:
        normalizado = ALIASES_FAKE[normalizado]
    registro = BASE_FAKE.get(normalizado)
    return normalizado, registro


# ---------------------------------------------------------------------------
# Exemplo_teste da planilha (6 medicamentos, FPRS esperado = 10.5)
# ---------------------------------------------------------------------------

EXEMPLO_ENTRADAS = [
    "Amitryptiline",  # alias → amitriptyline, peso 3
    "losartan",       # peso 1
    "metformin",      # peso 0
    "lorazepam",      # peso 3
    "atorvastatin",   # peso 1
    "paroxetine",     # peso 2
]


def test_exemplo_teste_planilha():
    res = calcular_fprs(EXEMPLO_ENTRADAS, lookup_fake)
    assert res.total_medicamentos == 6
    assert res.pontos_polifarmacia == 0.5   # polifarmácia 5–9
    assert res.label_polifarmacia == "Polifarmácia"
    assert res.carga_afinidade == 10.0      # 3+1+0+3+1+2
    assert res.pim_adicional == 0.0         # todos já pontuados por afinidade
    assert res.fprs == 10.5
    assert res.categoria == "Alto risco"


def test_alias_normalizado():
    res = calcular_fprs(["Amitryptiline"], lookup_fake)
    assert res.medicamentos[0].nome_normalizado == "amitriptyline"
    assert res.medicamentos[0].encontrado is True


def test_nao_encontrado_conta_medicamento_mas_contribuicao_zero():
    res = calcular_fprs(["medicamento_inexistente"], lookup_fake)
    assert res.total_medicamentos == 1
    assert res.medicamentos[0].encontrado is False
    assert res.medicamentos[0].contribuicao == 0.0
    assert "Revisar" in res.medicamentos[0].observacao


def test_duplicata_conta_uma_vez():
    res = calcular_fprs(["losartan", "losartan"], lookup_fake)
    assert res.total_medicamentos == 2
    contribs = [m.contribuicao for m in res.medicamentos]
    assert contribs == [1.0, 0.0]
    assert res.medicamentos[1].duplicata is True


def test_pim_sem_afinidade_adiciona_0_5():
    res = calcular_fprs(["aspirin"], lookup_fake)
    assert res.pim_adicional == 0.5
    assert res.carga_afinidade == 0.0
    assert res.fprs == 0.5   # 0,5 PIM + 0 polifarmácia


def test_pim_com_afinidade_nao_duplica():
    # amitriptyline tem pim_beers=1 E peso=3; não deve somar 0,5 extra
    res = calcular_fprs(["amitriptyline"], lookup_fake)
    assert res.carga_afinidade == 3.0
    assert res.pim_adicional == 0.0
    assert res.fprs == 3.0


def test_lista_vazia():
    res = calcular_fprs([], lookup_fake)
    assert res.total_medicamentos == 0
    assert res.fprs == 0.0
    assert res.categoria == "Baixo risco"


def test_exatamente_5_medicamentos_polifarmacia():
    entradas = ["losartan", "metformin", "atorvastatin", "acetaminophen", "aspirin"]
    res = calcular_fprs(entradas, lookup_fake)
    assert res.total_medicamentos == 5
    assert res.pontos_polifarmacia == 0.5
    assert res.label_polifarmacia == "Polifarmácia"


def test_exatamente_10_medicamentos_superpolifarmacia():
    entradas = ["losartan"] * 10  # duplicatas contam para total mas não pontuam
    res = calcular_fprs(entradas, lookup_fake)
    assert res.total_medicamentos == 10
    assert res.pontos_polifarmacia == 1.0
    assert res.label_polifarmacia == "Superpolifarmácia"


def test_corte_exato_baixo_risco():
    # FPRS = exatamente 1,5 deve ser Baixo risco (> 1,5 é Alto)
    # 1 medicamento com peso 1 + polifarmácia 0,5
    entradas = ["losartan", "acetaminophen", "aspirin", "metformin", "acetaminophen2"]
    # acetaminophen2 não existe mas conta como medicamento
    res = calcular_fprs(entradas, lookup_fake)
    # losartan=1, aspirin=0.5 PIM, poli=0.5 → fprs=2.0 aqui, ajustar lookup
    # Vamos fazer um lookup customizado para fprs = 1.5 exato
    base_corte = {"med_low": {"pim_beers": 0, "afinidade_ac": "No", "afinidade_sedativa": "Low", "peso_afinidade": 1}}

    def lookup_corte(e):
        n = e.strip().lower()
        return n, base_corte.get(n)

    # 1 medicamento com peso 1 + 0 polifarmácia = fprs 1.0 → Baixo risco
    res2 = calcular_fprs(["med_low"], lookup_corte)
    assert res2.fprs == 1.0
    assert res2.categoria == "Baixo risco"

    # 5 medicamentos (med_low x5) → poli=0.5, contribuição só da 1a = 1.0 → fprs=1.5
    res3 = calcular_fprs(["med_low"] * 5, lookup_corte)
    assert res3.fprs == 1.5
    assert res3.categoria == "Baixo risco"  # 1.5 não é > 1.5


def test_corte_acima_alto_risco():
    base_corte = {"med_low": {"pim_beers": 0, "afinidade_ac": "No", "afinidade_sedativa": "Low", "peso_afinidade": 1}}

    def lookup_corte(e):
        n = e.strip().lower()
        return n, base_corte.get(n)

    # 5 medicamentos: fprs = 1.5, mas adicionar mais 1 PIM sem afinidade
    base_ext = {**base_corte, "pim_only": {"pim_beers": 1, "afinidade_ac": "No", "afinidade_sedativa": "No", "peso_afinidade": 0}}

    def lookup_ext(e):
        n = e.strip().lower()
        return n, base_ext.get(n)

    # med_low*5 + pim_only = 1 + 0.5(poli) + 0.5(pim) = 2.0
    res = calcular_fprs(["med_low"] * 5 + ["pim_only"], lookup_ext)
    assert res.fprs == 2.0
    assert res.categoria == "Alto risco"


def test_capacidade_maxima_respeitada():
    entradas = ["metformin"] * 30
    res = calcular_fprs(entradas, lookup_fake)
    assert res.total_medicamentos == 25  # capacidade_max=25
