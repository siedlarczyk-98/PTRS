from pydantic import BaseModel, Field, field_validator
from typing import Optional


class CalcularRequest(BaseModel):
    medicamentos: list[str] = Field(..., description="Lista de medicamentos (máx. 25)")
    paciente_id: Optional[str] = Field(None, description="Identificador do paciente")
    idade: Optional[int] = Field(None, ge=0, le=150)
    data_avaliacao: Optional[str] = Field(None, description="Data no formato YYYY-MM-DD")
    observacao: Optional[str] = None

    @field_validator("medicamentos")
    @classmethod
    def valida_lista(cls, v: list[str]) -> list[str]:
        entradas = [e for e in v if e.strip()]
        if len(entradas) > 25:
            raise ValueError("Máximo de 25 medicamentos permitidos")
        return v


class MedicamentoDetalheResponse(BaseModel):
    entrada_original: str
    nome_normalizado: str
    encontrado: bool
    pim_beers: bool
    afinidade_ac: str
    afinidade_sedativa: str
    peso_afinidade: int
    contribuicao: float
    duplicata: bool
    observacao: str


class CalcularResponse(BaseModel):
    paciente_id: Optional[str]
    idade: Optional[int]
    data_avaliacao: Optional[str]
    observacao: Optional[str]
    medicamentos: list[MedicamentoDetalheResponse]
    total_medicamentos: int
    label_polifarmacia: str
    pontos_polifarmacia: float
    carga_afinidade: float
    pim_adicional: float
    fprs: float
    categoria: str
    alerta: str


class MedicamentoBaseResponse(BaseModel):
    nome_normalizado: str
    classe_observacao: str
    pim_beers: bool
    afinidade_ac: str
    afinidade_sedativa: str
    peso_afinidade: int
    fonte: str
