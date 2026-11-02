
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from interpretador import interpretar_solicitacao
from ranking import classificar_colaboradores
from pathlib import Path
from fastapi.responses import FileResponse

app = FastAPI(
    title="InHire API",
    description="Motor inteligente de busca de profissionais",
    version="1.0.0",
)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@app.get("/app", include_in_schema=False)
def pagina_web():
    return FileResponse(FRONTEND_DIR / "index.html")

class ConsultaRequest(BaseModel):
    texto: str = Field(min_length=1)


@app.get("/")
def inicio():
    return {
        "aplicacao": "InHire",
        "status": "online",
    }


@app.post("/buscar")
def buscar_profissionais(consulta: ConsultaRequest):
    try:
        filtros = interpretar_solicitacao(consulta.texto)

        skills = filtros["skills"]
        periodo = filtros["periodo"]
        percentual = filtros.get("percentual") or 0
        quantidade = filtros.get("quantidade_candidatos", 1)

        if not skills or not periodo:
            raise HTTPException(
                status_code=400,
                detail="Informe as competências e o período da busca.",
            )

        resultados = classificar_colaboradores(
            skills,
            percentual,
            periodo,
            senioridade=filtros.get("senioridade"),
            cargo=filtros.get("cargo"),
        )

        return {
            "filtros": filtros,
            "total_encontrado": len(resultados),
            "colaboradores": resultados[:quantidade],
        }

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Erro ao executar a busca de profissionais.",
        )
