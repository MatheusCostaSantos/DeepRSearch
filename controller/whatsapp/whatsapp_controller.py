import hmac
import json
import math
import re
from collections import OrderedDict

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from controller.limitador import LimitadorPorUsuario
from controller.whatsapp.whatsapp_assinatura import assinatura_valida
from core.configuracao import configuracao
from domain.interfaces import NotificadorInterface
from service.busca_precos_service import BuscaPrecosService

router = APIRouter()

TAMANHO_MAXIMO_PEDIDO = 200
MAXIMO_IDS_GUARDADOS = 1000

limitador = LimitadorPorUsuario(configuracao.whatsapp_intervalo_segundos)
_ids_processados: OrderedDict[str, None] = OrderedDict()


def obter_service_whatsapp() -> BuscaPrecosService:
    raise NotImplementedError  # substituído no main.py


def obter_notificador_whatsapp() -> NotificadorInterface:
    raise NotImplementedError  # substituído no main.py


def _canonico(numero: str) -> str:
    """Só dígitos; em números brasileiros ignora o 9 extra (a Meta pode enviar com ou sem ele)."""
    digitos = re.sub(r"\D", "", numero)
    if digitos.startswith("55") and len(digitos) == 13 and digitos[4] == "9":
        return digitos[:4] + digitos[5:]
    return digitos


def _numeros_permitidos() -> set[str]:
    lista = configuracao.whatsapp_numeros_permitidos.split(",")
    return {_canonico(n) for n in lista if n.strip()}


def _ja_processada(id_mensagem: str) -> bool:
    """A Meta reenvia o aviso se demorarmos; o id evita buscar duas vezes a mesma mensagem."""
    if id_mensagem in _ids_processados:
        return True
    _ids_processados[id_mensagem] = None
    if len(_ids_processados) > MAXIMO_IDS_GUARDADOS:
        _ids_processados.popitem(last=False)
    return False


def _mensagens_recebidas(dados: dict):
    for entrada in dados.get("entry") or []:
        for mudanca in entrada.get("changes") or []:
            valor = mudanca.get("value") or {}
            # avisos de entrega/leitura vêm em "statuses" e são ignorados
            for mensagem in valor.get("messages") or []:
                yield mensagem


def _tratar_mensagem(
    mensagem: dict,
    segundo_plano: BackgroundTasks,
    service: BuscaPrecosService,
    notificador: NotificadorInterface,
) -> None:
    numero = str(mensagem.get("from", ""))
    id_mensagem = str(mensagem.get("id", ""))
    if not numero or (id_mensagem and _ja_processada(id_mensagem)):
        return

    permitidos = _numeros_permitidos()
    if permitidos and _canonico(numero) not in permitidos:
        print(f"WhatsApp: número fora da lista ignorado (final {numero[-4:]})")
        return

    def avisar(texto: str) -> None:
        segundo_plano.add_task(notificador.enviar, numero, texto)

    espera = limitador.tentar(_canonico(numero))
    if espera > 0:
        avisar(f"Aguarde {max(1, math.ceil(espera))}s antes de fazer outra busca.")
        return

    if mensagem.get("type") != "text":
        avisar("Envie o nome do produto em texto. Exemplo: PlayStation 5")
        return

    texto = ((mensagem.get("text") or {}).get("body") or "").strip()
    if not texto:
        return
    if len(texto) > TAMANHO_MAXIMO_PEDIDO:
        avisar(f"Pedido muito longo (máximo de {TAMANHO_MAXIMO_PEDIDO} caracteres).")
        return

    segundo_plano.add_task(service.executar, texto, numero)


@router.get("/whatsapp/webhook")
async def verificar(
    modo: str | None = Query(default=None, alias="hub.mode"),
    token: str | None = Query(default=None, alias="hub.verify_token"),
    desafio: str | None = Query(default=None, alias="hub.challenge"),
):
    """Passo único de cadastro: a Meta confere se o endereço é nosso."""
    esperado = configuracao.whatsapp_verify_token
    if modo == "subscribe" and esperado and token and hmac.compare_digest(
        token.encode(), esperado.encode()
    ):
        return PlainTextResponse(desafio or "")
    raise HTTPException(status_code=403, detail="Token de verificação inválido")


@router.post("/whatsapp/webhook")
async def receber(
    request: Request,
    segundo_plano: BackgroundTasks,
    service: BuscaPrecosService = Depends(obter_service_whatsapp),
    notificador: NotificadorInterface = Depends(obter_notificador_whatsapp),
):
    corpo = await request.body()
    if not assinatura_valida(
        configuracao.whatsapp_app_secret,
        request.headers.get("X-Hub-Signature-256", ""),
        corpo,
    ):
        raise HTTPException(status_code=401, detail="Assinatura inválida")

    try:
        dados = json.loads(corpo)
    except ValueError:
        raise HTTPException(status_code=400, detail="Corpo inválido")

    for mensagem in _mensagens_recebidas(dados):
        _tratar_mensagem(mensagem, segundo_plano, service, notificador)

    return {"status": "ok"}  # responder rápido: a Meta reenvia se demorarmos