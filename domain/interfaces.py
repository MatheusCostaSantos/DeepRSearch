from abc import ABC, abstractmethod

from .modelos import FiltroBusca, Mercado, Oferta


class FiltroEntradaInterface(ABC):
    @abstractmethod
    async def criar_filtro(self, mensagem_usuario: str) -> FiltroBusca: ...


class PesquisaInterface(ABC):
    @abstractmethod
    async def pesquisar(self, filtro: FiltroBusca, mercado: Mercado) -> list[Oferta]: ...


class FiltroSaidaInterface(ABC):
    @abstractmethod
    async def selecionar_relevantes(
        self, filtro: FiltroBusca, ofertas: list[Oferta]
    ) -> list[Oferta]: ...


class NotificadorInterface(ABC):
    @abstractmethod
    async def enviar(self, destino: str, texto: str) -> None: ...
