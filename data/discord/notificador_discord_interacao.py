import asyncio
import re

import httpx

from domain.interfaces import NotificadorInterface

LIMITE_CARACTERES = 1900  # o Discord aceita 2000; sobra margem para os "<>" dos links


def dividir_mensagem(texto: str, limite: int = LIMITE_CARACTERES) -> list[str]:
    """Divide o texto em mensagens, sem partir uma oferta no meio."""
    blocos = re.split(r"\n(?=\d+\. )", texto)  # cabeçalho + um bloco por oferta
    partes: list[str] = []
    atual = ""

    for bloco in blocos:
        bloco = bloco.strip("\n")
        while len(bloco) > limite:  # bloco gigante: corta no limite
            if atual:
                partes.append(atual)
                atual = ""
            partes.append(bloco[:limite])
            bloco = bloco[limite:]
        if not atual:
            atual = bloco
        elif len(atual) + 1 + len(bloco) <= limite:
            atual += "\n" + bloco
        else:
            partes.append(atual)
            atual = bloco

    if atual:
        partes.append(atual)
    return partes or [texto[:limite]]


def _sem_previa_de_link(texto: str) -> str:
    # <link> faz o Discord não montar a prévia grande de cada endereço
    return re.sub(r"(https?://\S+)", r"<\1>", texto)


class NotificadorDiscordInteracao(NotificadorInterface):
    """Responde a uma interação do Discord.

    `destino` é o endereço https://discord.com/api/v10/webhooks/{application_id}/{token}
    montado pelo controller. A 1ª mensagem substitui o "pensando..."; as demais vão como
    mensagens extras. O token da interação vale por 15 minutos.
    """

    async def enviar(self, destino: str, texto: str) -> None:
        partes = [_sem_previa_de_link(p) for p in dividir_mensagem(texto)]
        sem_mencoes = {"parse": []}  # um título com "@everyone" não pode marcar ninguém

        async with httpx.AsyncClient(timeout=15) as http:
            resposta = await http.patch(
                f"{destino}/messages/@original",
                json={"content": partes[0], "allowed_mentions": sem_mencoes},
            )
            resposta.raise_for_status()

            for parte in partes[1:]:
                await asyncio.sleep(0.5)
                resposta = await http.post(
                    destino, json={"content": parte, "allowed_mentions": sem_mencoes}
                )
                resposta.raise_for_status()