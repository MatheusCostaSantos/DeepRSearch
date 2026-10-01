import re

import httpx

from domain.interfaces import PesquisaInterface
from domain.modelos import FiltroBusca, Oferta, _para_numero

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
    if valor is None:
        achado = re.search(r"R\$\s*([\d.]+,\d{2})", texto_preco)
        valor = _para_numero(achado.group(1)) if achado else None

    periodo = dado.get("period")
    parcelas = None
    if isinstance(periodo, int):
        parcelas = periodo
    elif isinstance(periodo, str) and re.search(r"\d+", periodo):
        parcelas = int(re.search(r"\d+", periodo).group())
    else:
        achado = re.search(r"(\d{1,2})\s*x", texto_preco, re.IGNORECASE)
        parcelas = int(achado.group(1)) if achado else None

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
    """Busca no Google Shopping (Brasil) via SerpApi. Cada pedido gasta 1 busca do plano."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def pesquisar(self, filtro: FiltroBusca) -> list[Oferta]:
        parametros = {
            "engine": "google_shopping",
            "q": " ".join([filtro.produto, *filtro.deve_conter]),
            "google_domain": "google.com.br",
            "gl": "br",
            "hl": "pt-br",
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