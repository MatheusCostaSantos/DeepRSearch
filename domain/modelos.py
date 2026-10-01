import unicodedata

from pydantic import BaseModel, field_validator


def normalizar_texto(texto: str) -> str:
    """Minúsculas e sem acentos, para comparar nomes de lojas e palavras."""
    decomposto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in decomposto if not unicodedata.combining(c)).lower().strip()


def _para_lista(valor) -> list[str]:
    if valor is None or valor == "":
        return []
    if isinstance(valor, str):
        return [item.strip() for item in valor.split(",") if item.strip()]
    return valor


def _para_numero(valor) -> float | None:
    if valor is None or valor == "":
        return None
    if isinstance(valor, str):
        texto = valor.replace("R$", "").strip()
        if "," in texto:  # formato brasileiro: 4.299,00
            texto = texto.replace(".", "").replace(",", ".")
        try:
            return float(texto)
        except ValueError:
            return None
    return float(valor)


class FiltroBusca(BaseModel):
    produto: str
    lojas: list[str] = []             # só preenchido se o usuário pediu lojas específicas
    deve_conter: list[str] = []
    nao_deve_conter: list[str] = []   # ex: ["capa", "película"]
    preco_minimo: float | None = None
    preco_maximo: float | None = None

    @field_validator("lojas", "deve_conter", "nao_deve_conter", mode="before")
    @classmethod
    def normalizar_listas(cls, valor):
        return _para_lista(valor)

    @field_validator("preco_minimo", "preco_maximo", mode="before")
    @classmethod
    def normalizar_precos(cls, valor):
        return _para_numero(valor)


class Oferta(BaseModel):
    titulo: str
    loja: str
    url: str
    preco: float
    preco_original: float | None = None   # preço antigo (riscado), quando há promoção
    avaliacao: float | None = None
    usado: bool = False                   # usado ou recondicionado
    parcelas: int | None = None           # número de parcelas, se a loja informa
    valor_parcela: float | None = None

    @property
    def desconto_percentual(self) -> int | None:
        if self.preco_original and self.preco_original > self.preco:
            return round((1 - self.preco / self.preco_original) * 100)
        return None
