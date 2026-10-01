import httpx

from domain.interfaces import NotificadorInterface


class NotificadorDiscord(NotificadorInterface):
    async def enviar(self, destino: str, texto: str) -> None:
        # destino = URL do webhook do canal do Discord
        async with httpx.AsyncClient(timeout=15) as http:
            resposta = await http.post(destino, json={"content": texto[:2000]})
            resposta.raise_for_status()
