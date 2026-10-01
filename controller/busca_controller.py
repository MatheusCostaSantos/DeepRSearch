from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel

from service.busca_precos_service import BuscaPrecosService

router = APIRouter()


class RequisicaoBusca(BaseModel):
    mensagem: str      # o que o usuário pediu, ex: "PlayStation 5"
    responder_em: str  # URL do webhook do Discord (no console, qualquer texto)


def obter_service() -> BuscaPrecosService:
    raise NotImplementedError  # substituído no main.py


@router.post("/buscar", status_code=202)
async def buscar(
    requisicao: RequisicaoBusca,
    segundo_plano: BackgroundTasks,
    service: BuscaPrecosService = Depends(obter_service),
):
    segundo_plano.add_task(service.executar, requisicao.mensagem, requisicao.responder_em)
    return {"status": "processando"}
