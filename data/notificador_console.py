from domain.interfaces import NotificadorInterface


class NotificadorConsole(NotificadorInterface):
    async def enviar(self, destino: str, texto: str) -> None:
        print("\n===== RESULTADO =====")
        print(texto)
        print("=====================\n")
