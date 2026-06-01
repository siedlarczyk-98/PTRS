from fastapi import APIRouter, HTTPException
from app.models import CalcularRequest, CalcularResponse, MedicamentoDetalheResponse
from app.calculator import calcular_fprs
from app.db import buscar_medicamento_completo, listar_parametros

router = APIRouter()


@router.post("/calcular", response_model=CalcularResponse, summary="Calcular FPRS")
def calcular(req: CalcularRequest):
    params = listar_parametros()
    result = calcular_fprs(req.medicamentos, buscar_medicamento_completo, params)

    return CalcularResponse(
        paciente_id=req.paciente_id,
        idade=req.idade,
        data_avaliacao=req.data_avaliacao,
        observacao=req.observacao,
        medicamentos=[
            MedicamentoDetalheResponse(**m.__dict__) for m in result.medicamentos
        ],
        total_medicamentos=result.total_medicamentos,
        label_polifarmacia=result.label_polifarmacia,
        pontos_polifarmacia=result.pontos_polifarmacia,
        carga_afinidade=result.carga_afinidade,
        pim_adicional=result.pim_adicional,
        fprs=result.fprs,
        categoria=result.categoria,
        alerta=result.alerta,
    )
