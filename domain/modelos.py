import re
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
    """Converte texto como "R$ 1.299,99", "€ 499,99" ou "$1,299.99" em número."""
    if valor is None or valor == "":
        return None
    if not isinstance(valor, str):
        return float(valor)

    achado = re.search(r"\d[\d.,]*", valor)
    if not achado:
        return None
    texto = achado.group().rstrip(".,")

    if "," in texto and "." in texto:
        # o último separador é o decimal; o outro é separador de milhar
        if texto.rfind(",") > texto.rfind("."):
            texto = texto.replace(".", "").replace(",", ".")
        else:
            texto = texto.replace(",", "")
    elif "," in texto:
        depois = texto.split(",")[-1]
        if texto.count(",") == 1 and len(depois) <= 2:
            texto = texto.replace(",", ".")  # 499,99
        else:
            texto = texto.replace(",", "")   # 1,299
    elif "." in texto:
        depois = texto.split(".")[-1]
        if texto.count(".") > 1 or len(depois) == 3:
            texto = texto.replace(".", "")   # 1.299 ou 1.299.000
    try:
        return float(texto)
    except ValueError:
        return None


ALIAS_PAISES = {"uk": "gb"}  # o Google usa "uk"; o código ISO é "gb"


def normalizar_pais(valor) -> str:
    codigo = str(valor or "").strip().lower()
    return ALIAS_PAISES.get(codigo, codigo)


class FiltroBusca(BaseModel):
    produto: str
    pais: str = ""                    # código do país (ex: "pt"); vazio = país padrão
    lojas: list[str] = []             # só preenchido se o usuário pediu lojas específicas
    deve_conter: list[str] = []
    nao_deve_conter: list[str] = []   # ex: ["capa", "película"]
    preco_minimo: float | None = None
    preco_maximo: float | None = None

    @field_validator("lojas", "deve_conter", "nao_deve_conter", mode="before")
    @classmethod
    def normalizar_listas(cls, valor):
        return _para_lista(valor)

    @field_validator("pais", mode="before")
    @classmethod
    def normalizar_codigo_do_pais(cls, valor):
        return normalizar_pais(valor)

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
    parcelas: int | None = None           # número de parcelas, se o Google informa
    valor_parcela: float | None = None

    @property
    def desconto_percentual(self) -> int | None:
        if self.preco_original and self.preco_original > self.preco:
            return round((1 - self.preco / self.preco_original) * 100)
        return None


class Mercado(BaseModel):
    """Um país onde a busca pode ser feita: parâmetros do Google, moeda e lojas confiáveis."""

    codigo: str                        # "br", "pt", "us"...
    nome: str                          # nome mostrado ao usuário
    google_domain: str                 # ex: "google.pt"
    gl: str                            # país do Google Shopping (SerpApi)
    hl: str                            # idioma do Google Shopping (SerpApi)
    formato_preco: str                 # ex: "R$ {valor}" ou "{valor} €"
    separador_milhar: str
    separador_decimal: str
    lojas_confiaveis: list[str]

    def formatar(self, valor: float) -> str:
        inteiro, decimal = f"{valor:,.2f}".rsplit(".", 1)  # "1,299" e "99"
        inteiro = inteiro.replace(",", self.separador_milhar)
        return self.formato_preco.format(valor=f"{inteiro}{self.separador_decimal}{decimal}")