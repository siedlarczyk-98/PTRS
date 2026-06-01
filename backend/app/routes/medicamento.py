from fastapi import APIRouter, HTTPException
from app.models import MedicamentoBaseResponse
from app.db import buscar_medicamento_completo

router = APIRouter()


@router.get(
    "/medicamento/{nome}",
    response_model=MedicamentoBaseResponse,
    summary="Consultar medicamento na base",
)
def consultar_medicamento(nome: str):
    nome_norm, registro = buscar_medicamento_completo(nome)
    if registro is None:
        raise HTTPException(
            status_code=404,
            detail=f"Medicamento '{nome}' não encontrado (normalizado: '{nome_norm}')",
        )
    return MedicamentoBaseResponse(
        nome_normalizado=registro["nome_normalizado"],
        classe_observacao=registro["classe_observacao"] or "",
        pim_beers=bool(registro["pim_beers"]),
        afinidade_ac=registro["afinidade_ac"],
        afinidade_sedativa=registro["afinidade_sedativa"],
        peso_afinidade=registro["peso_afinidade"],
        fonte=registro["fonte"] or "",
    )
