"""Liga o webhook do Telegram. Rode na sua máquina, com o .env preenchido.

  python registrar_webhook_telegram.py https://SEU-APP.azurecontainerapps.io/telegram/webhook
  python registrar_webhook_telegram.py --info      (mostra o estado e o último erro)
  python registrar_webhook_telegram.py --remover   (desliga o webhook)
"""
import sys

import httpx

from core.configuracao import configuracao


def chamar(metodo: str, dados: dict | None = None) -> None:
    url = f"https://api.telegram.org/bot{configuracao.telegram_bot_token}/{metodo}"
    try:
        resposta = httpx.post(url, json=dados or {}, timeout=30)
    except httpx.HTTPError as erro:
        raise SystemExit(f"Falha de rede ao chamar {metodo}: {type(erro).__name__}")
    print(f"Status: {resposta.status_code}")
    print(resposta.text)


def main() -> None:
    if not configuracao.telegram_bot_token:
        raise SystemExit("Falta TELEGRAM_BOT_TOKEN no .env")
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)

    argumento = sys.argv[1]
    if argumento == "--info":
        chamar("getWebhookInfo")
    elif argumento == "--remover":
        chamar("deleteWebhook")
    elif argumento.startswith("https://"):
        if not configuracao.telegram_secret_token:
            raise SystemExit("Falta TELEGRAM_SECRET_TOKEN no .env")
        chamar(
            "setWebhook",
            {
                "url": argumento,
                "secret_token": configuracao.telegram_secret_token,
                "allowed_updates": ["message"],
            },
        )
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()