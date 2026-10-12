import asyncio
import html
import re

import httpx

from data.divisor_mensagem import dividir_mensagem
from domain.interfaces import NotificadorInterface

LIMITE_CARACTERES = 4000  # o Telegram aceita 4096 por mensagem


def _para_html(texto: str) -> str:
    # Escapa <, > e & e transforma **negrito** em <b>negrito</b>
    escapado = html.escape(texto, quote=False)
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escapado)


class NotificadorTelegram(NotificadorInterface):
    """Envia mensagens pelo bot do Telegram. `destino` é o chat_id de quem escreveu."""

    def __init__(self, bot_token: str):
        self.url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    async def enviar(self, destino: str, texto: str) -> None:
        partes = dividir_mensagem(texto, LIMITE_CARACTERES)

        async with httpx.AsyncClient(timeout=15) as http:
            for indice, parte in enumerate(partes):
                if indice:
                    await asyncio.sleep(1)
                corpo = {
                    "chat_id": destino,
                    "text": _para_html(parte),
                    "parse_mode": "HTML",
                    "link_preview_options": {"is_disabled": True},
                }
                resposta = await http.post(self.url, json=corpo)
                if resposta.status_code >= 400:
                    # Não usa raise_for_status: a mensagem de erro dele incluiria o token do bot
                    print(f"Telegram respondeu {resposta.status_code}: {resposta.text}")
                    raise RuntimeError(f"Telegram respondeu {resposta.status_code}")