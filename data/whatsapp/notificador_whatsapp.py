import asyncio
import re

import httpx

from data.divisor_mensagem import dividir_mensagem
from domain.interfaces import NotificadorInterface

LIMITE_CARACTERES = 4000  # o WhatsApp aceita 4096 por mensagem


def _para_formato_whatsapp(texto: str) -> str:
    # O texto do service usa **negrito**; o WhatsApp usa *negrito* (um asterisco)
    return re.sub(r"\*\*(.+?)\*\*", r"*\1*", texto)


class NotificadorWhatsApp(NotificadorInterface):
    """Envia mensagens de texto pela API de Nuvem do WhatsApp (Meta).

    `destino` é o número de quem escreveu (campo "from" do webhook). Dentro das 24 horas
    seguintes à mensagem do usuário, a resposta pode ser texto livre.
    """

    def __init__(self, access_token: str, phone_number_id: str, versao_api: str = "v23.0"):
        self.url = f"https://graph.facebook.com/{versao_api}/{phone_number_id}/messages"
        self.cabecalhos = {"Authorization": f"Bearer {access_token}"}

    async def enviar(self, destino: str, texto: str) -> None:
        partes = dividir_mensagem(_para_formato_whatsapp(texto), LIMITE_CARACTERES)

        async with httpx.AsyncClient(timeout=15, headers=self.cabecalhos) as http:
            for indice, parte in enumerate(partes):
                if indice:
                    await asyncio.sleep(0.5)
                corpo = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": destino,
                    "type": "text",
                    "text": {"preview_url": False, "body": parte},
                }
                resposta = await http.post(self.url, json=corpo)
                if resposta.status_code >= 400:
                    print(f"WhatsApp respondeu {resposta.status_code}: {resposta.text}")
                resposta.raise_for_status()