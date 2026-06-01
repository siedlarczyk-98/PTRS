from fastapi import APIRouter
from app.db import listar_parametros

router = APIRouter()


@router.get("/parametros", summary="Listar parâmetros configuráveis")
def get_parametros() -> dict[str, float]:
    return listar_parametros()
