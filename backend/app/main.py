from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import calcular, medicamento, parametros

app = FastAPI(
    title="FPRS API",
    description="Functional Pharmacotherapy Risk Score — Modelo 3 (sem interações)",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restringir em produção
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(calcular.router, tags=["FPRS"])
app.include_router(medicamento.router, tags=["Base"])
app.include_router(parametros.router, tags=["Config"])


@app.get("/health", tags=["Infra"])
def health():
    return {"status": "ok"}
