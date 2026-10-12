import json
import math
import time

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request

from controller.discord.discord_assinatura import assinatura_valida
from core.configuracao import configuracao
from service.busca_precos_service import BuscaPrecosService

router = APIRouter()

TAMANHO_MAXIMO_PEDIDO = 200

# Códigos da API do Discord
INTERACAO_PING = 1
INTERACAO_COMANDO = 2
COMANDO_DE_MENSAGEM = 3      # menu "Aplicativos" ao clicar numa mensagem
RESPOSTA_PONG = 1
RESPOSTA_MENSAGEM = 4
RESPOSTA_ADIADA = 5          # "o bot está pensando..."
FLAG_SO_VOCE_VE = 64         # mensagem visível só para quem usou o comando


class LimitadorPorUsuario:
    """Permite uma busca por usuário a cada `intervalo` segundos."""

    def __init__(self, intervalo: float):
        self.intervalo = intervalo
        self._ultimo: dict[str, float] = {}

    def tentar(self, usuario: str) -> float:
        """Devolve 0 se liberado; senão, quantos segundos faltam."""
        agora = time.monotonic()
        ultimo = self._ultimo.get(usuario)
        if ultimo is not None and agora - ultimo < self.intervalo:
            return self.intervalo - (agora - ultimo)
        self._ultimo[usuario] = agora
        return 0.0


limitador = LimitadorPorUsuario(configuracao.discord_intervalo_segundos)


def obter_service_discord() -> BuscaPrecosService:
    raise NotImplementedError  # substituído no main.py


def _resposta_privada(texto: str) -> dict:
    return {"type": RESPOSTA_MENSAGEM, "data": {"content": texto, "flags": FLAG_SO_VOCE_VE}}


def _id_do_usuario(interacao: dict) -> str:
    membro = interacao.get("member") or {}
    usuario = membro.get("user") or interacao.get("user") or {}
    return str(usuario.get("id", ""))


def _extrair_pedido(interacao: dict) -> tuple[str | None, str | None]:
    """Devolve (texto_do_pedido, mensagem_de_erro)."""
    dados = interacao.get("data") or {}

    if dados.get("type") == COMANDO_DE_MENSAGEM:
        mensagens = (dados.get("resolved") or {}).get("messages") or {}
        alvo = mensagens.get(str(dados.get("target_id")), {})
        if alvo.get("webhook_id") or (alvo.get("author") or {}).get("bot"):
            return None, "Não busco preços a partir de mensagens de bots ou webhooks."
        texto = (alvo.get("content") or "").strip()
        if not texto:
            return None, "Não consegui ler o texto dessa mensagem. Use /buscar produto:..."
    else:
        opcoes = {o.get("name"): o.get("value") for o in dados.get("options") or []}
        texto = str(opcoes.get("produto") or "").strip()
        if not texto:
            return None, "Informe o produto. Exemplo: /buscar produto:PlayStation 5"

    if len(texto) > TAMANHO_MAXIMO_PEDIDO:
        return None, f"Pedido muito longo (máximo de {TAMANHO_MAXIMO_PEDIDO} caracteres)."
    return texto, None


@router.post("/discord/interacoes")
async def interacoes(
    request: Request,
    segundo_plano: BackgroundTasks,
    service: BuscaPrecosService = Depends(obter_service_discord),
):
    corpo = await request.body()
    if not assinatura_valida(
        configuracao.discord_public_key,
        request.headers.get("X-Signature-Ed25519", ""),
        request.headers.get("X-Signature-Timestamp", ""),
        corpo,
    ):
        raise HTTPException(status_code=401, detail="Assinatura inválida")

    interacao = json.loads(corpo)
    tipo = interacao.get("type")

    if tipo == INTERACAO_PING:
        return {"type": RESPOSTA_PONG}
    if tipo != INTERACAO_COMANDO:
        return _resposta_privada("Esse tipo de interação não é suportado.")

    canal_permitido = configuracao.discord_canal_id
    if canal_permitido and str(interacao.get("channel_id")) != canal_permitido:
        return _resposta_privada("Use este comando no canal de ofertas.")

    texto, erro = _extrair_pedido(interacao)
    if erro:
        return _resposta_privada(erro)

    espera = limitador.tentar(_id_do_usuario(interacao))
    if espera > 0:
        segundos = max(1, math.ceil(espera))
        return _resposta_privada(f"Aguarde {segundos}s antes de fazer outra busca.")

    # Responde "pensando..." dentro dos 3 segundos e faz a busca em segundo plano
    destino = (
        f"https://discord.com/api/v10/webhooks/"
        f"{interacao['application_id']}/{interacao['token']}"
    )
    segundo_plano.add_task(service.executar, texto, destino)
    return {"type": RESPOSTA_ADIADA}