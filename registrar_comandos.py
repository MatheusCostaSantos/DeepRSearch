"""Registra os comandos do bot no seu servidor. Rode uma vez: python registrar_comandos.py"""
import httpx

from core.configuracao import configuracao

COMANDOS = [
    {
        "name": "buscar",
        "type": 1,  # comando de barra
        "description": "Busca os melhores preços de um produto",
        "options": [
            {
                "type": 3,  # texto
                "name": "produto",
                "description": "Ex: PlayStation 5",
                "required": True,
            }
        ],
    },
    {
        "name": "Buscar preços",
        "type": 3,  # comando de mensagem (clique direito > Aplicativos)
    },
]


def main() -> None:
    necessarios = {
        "DISCORD_APPLICATION_ID": configuracao.discord_application_id,
        "DISCORD_BOT_TOKEN": configuracao.discord_bot_token,
        "DISCORD_SERVIDOR_ID": configuracao.discord_servidor_id,
    }
    faltando = [nome for nome, valor in necessarios.items() if not valor]
    if faltando:
        raise SystemExit(f"Faltam no .env: {', '.join(faltando)}")

    url = (
        f"https://discord.com/api/v10/applications/{configuracao.discord_application_id}"
        f"/guilds/{configuracao.discord_servidor_id}/commands"
    )
    cabecalhos = {"Authorization": f"Bot {configuracao.discord_bot_token}"}

    # PUT substitui todos os comandos do aplicativo neste servidor
    resposta = httpx.put(url, json=COMANDOS, headers=cabecalhos, timeout=30)
    print(f"Status: {resposta.status_code}")
    print(resposta.text)


if __name__ == "__main__":
    main()