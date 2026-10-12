import time


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