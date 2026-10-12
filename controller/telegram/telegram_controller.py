import hmac
import json
import math
from collections import OrderedDict

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request

from controller.limitador import LimitadorPorUsuario
from core.configuracao import configuracao
from domain.interfaces import NotificadorInterface
from service.busca_precos_service import BuscaPrecosService

router = APIRouter()

TAMANHO_MAXIMO_PEDIDO = 200
MAXIMO_IDS_GUARDADOS = 1000
AJUDA = (
    "Olá! Envie o nome de um produto (por exemplo: PlayStation 5) "
    "e eu busco os melhores preços nas lojas confiáveis."
)

limitador = LimitadorPorUsuario(configuracao.telegram_intervalo_segundos)
_updates_processados: OrderedDict[int, None] = OrderedDict()


def obter_service_telegram() -> BuscaPrecosService:
    raise NotImplementedError  # substituído no main.py


def obter_notificador_telegram() -> NotificadorInterface:
    raise NotImplementedError  # substituído no main.py


def _usuarios_permitidos() -> set[str]:
    lista = configuracao.telegram_usuarios_permitidos.split(",")
    return {item.strip() for item in lista if item.strip()}


def _secret_valido(recebido: str) -> bool:
    esperado = configuracao.telegram_secret_token
    return bool(esperado) and hmac.compare_digest(recebido.encode(), esperado.encode())


def _ja_processado(update_id) -> bool:
    """O Telegram reenvia o update se não respondermos 200; o id evita buscar duas vezes."""
    if update_id is None:
        return False
    if update_id in _updates_processados:
        return True
    _updates_processados[update_id] = None
    if len(_updates_processados) > MAXIMO_IDS_GUARDADOS:
        _updates_processados.popitem(last=False)
    return False


def _tratar_mensagem(
    mensagem: dict,
    segundo_plano: BackgroundTasks,
    service: BuscaPrecosService,
    notificador: NotificadorInterface,
) -> None:
    remetente = mensagem.get("from") or {}
    usuario_id = str(remetente.get("id", ""))
    chat_id = (mensagem.get("chat") or {}).get("id")
    if remetente.get("is_bot") or not usuario_id or chat_id is None:
        return

    if usuario_id not in _usuarios_permitidos():
        print(
            f"Telegram: usuário {usuario_id} fora da lista; ignorado. "
            "Para liberar, inclua o ID em TELEGRAM_USUARIOS_PERMITIDOS."
        )
        return

    destino = str(chat_id)

    def avisar(texto: str) -> None:
        segundo_plano.add_task(notificador.enviar, destino, texto)

    espera = limitador.tentar(usuario_id)
    if espera > 0:
        avisar(f"Aguarde {max(1, math.ceil(espera))}s antes de fazer outra busca.")
        return

    texto = (mensagem.get("text") or "").strip()
    if not texto:
        avisar("Envie o nome do produto em texto. Exemplo: PlayStation 5")
        return
    if texto.startswith("/"):  # /start, /ajuda e qualquer outro comando
        avisar(AJUDA)
        return
    if len(texto) > TAMANHO_MAXIMO_PEDIDO:
        avisar(f"Pedido muito longo (máximo de {TAMANHO_MAXIMO_PEDIDO} caracteres).")
        return

    segundo_plano.add_task(service.executar, texto, destino)


@router.post("/telegram/webhook")
async def receber(
    request: Request,
    segundo_plano: BackgroundTasks,
    service: BuscaPrecosService = Depends(obter_service_telegram),
    notificador: NotificadorInterface = Depends(obter_notificador_telegram),
):
    if not _secret_valido(request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")):
        raise HTTPException(status_code=401, detail="Token secreto inválido")

    try:
        dados = json.loads(await request.body())
    except ValueError:
        raise HTTPException(status_code=400, detail="Corpo inválido")

    if _ja_processado(dados.get("update_id")):
        return {"ok": True}

    mensagem = dados.get("message")
    if mensagem:
        _tratar_mensagem(mensagem, segundo_plano, service, notificador)

    return {"ok": True}  # responder 200 rápido: senão o Telegram reenvia