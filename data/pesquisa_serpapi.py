import re

import httpx

from domain.interfaces import PesquisaInterface
from domain.modelos import FiltroBusca, Mercado, Oferta, _para_numero

URL = "https://serpapi.com/search.json"


def _limpar_link(url: str) -> str:
    """Remove o parâmetro de rastreio do Google (srsltid) e deixa o link clicável."""
    url = re.sub(r"[?&]srsltid=[^&#]*", "", url)
    if "?" not in url and "&" in url:
        url = url.replace("&", "?", 1)
    # espaço e "|" aparecem nos links do Google e quebram o clique no terminal/Discord
    return url.replace(" ", "%20").replace("|", "%7C")


def _parcelamento(dado) -> tuple[int | None, float | None]:
    """Lê o bloco 'installment' do resultado. Devolve (parcelas, valor_da_parcela)."""
    if not isinstance(dado, dict) or dado.get("down_payment"):
        return None, None  # parcelamento com entrada: o cálculo ficaria enganoso

    texto_preco = str(dado.get("price") or "")
    valor = _para_numero(dado.get("extracted_price"))
    parcelas = None

    periodo = dado.get("period")
    if isinstance(periodo, int):
        parcelas = periodo
    elif isinstance(periodo, str) and re.search(r"\d+", periodo):
        parcelas = int(re.search(r"\d+", periodo).group())

    # Textos como "12x R$ 291,58" ou "12x de €41,66"
    achado = re.search(r"(\d{1,2})\s*x\D*(\d[\d.,]*)", texto_preco, re.IGNORECASE)
    if achado:
        if parcelas is None:
            parcelas = int(achado.group(1))
        if valor is None:
            valor = _para_numero(achado.group(2))
    elif valor is None:
        valor = _para_numero(texto_preco)  # texto só com o valor, ex: "R$ 291,58"

    if valor and parcelas and parcelas > 1:
        return parcelas, valor
    return None, None


def converter_item(item: dict) -> Oferta | None:
    preco = _para_numero(item.get("extracted_price") or item.get("price"))
    url = item.get("link") or item.get("product_link")
    if not preco or not url:
        return None

    parcelas, valor_parcela = _parcelamento(item.get("installment"))
    return Oferta(
        titulo=item.get("title", ""),
        loja=item.get("source") or "Loja desconhecida",
        url=_limpar_link(url),
        preco=preco,
        preco_original=_para_numero(item.get("extracted_old_price") or item.get("old_price")),
        avaliacao=_para_numero(item.get("rating")),
        usado=bool(item.get("second_hand_condition")),
        parcelas=parcelas,
        valor_parcela=valor_parcela,
    )


class PesquisaSerpApi(PesquisaInterface):
    """Busca no Google Shopping do país escolhido via SerpApi. Cada pedido gasta 1 busca do plano."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def pesquisar(self, filtro: FiltroBusca, mercado: Mercado) -> list[Oferta]:
        parametros = {
            "engine": "google_shopping",
            "q": " ".join([filtro.produto, *filtro.deve_conter]),
            "google_domain": mercado.google_domain,
            "gl": mercado.gl,
            "hl": mercado.hl,
            "api_key": self.api_key,
        }

        async with httpx.AsyncClient(timeout=60) as http:
            resposta = await http.get(URL, params=parametros)
            resposta.raise_for_status()

        dados = resposta.json()
        erro = dados.get("error")
        if erro:
            if "hasn't returned any results" in erro:
                return []
            raise RuntimeError(f"SerpApi: {erro}")

        ofertas = []
        for item in dados.get("shopping_results", []):
            oferta = converter_item(item)
            if oferta:
                ofertas.append(oferta)
        return ofertas