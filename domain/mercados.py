from domain.modelos import Mercado

MERCADO_PADRAO = "br"

# Países disponíveis. As listas de lojas são sugestões: confira o log "Lojas descartadas"
# depois das primeiras buscas e ajuste. A comparação ignora acentos e maiúsculas e aceita
# trechos (ex: "amazon" aceita "Amazon.com.br" e "Amazon.es").
_MERCADOS = [
    Mercado(
        codigo="br",
        nome="Brasil",
        google_domain="google.com.br",
        gl="br",
        hl="pt-br",
        formato_preco="R$ {valor}",
        separador_milhar=".",
        separador_decimal=",",
        lojas_confiaveis=[
            "amazon", "mercado livre", "magazine luiza", "magalu", "americanas",
            "casas bahia", "kabum", "fast shop", "ponto frio", "pontofrio",
            "submarino", "carrefour",
        ],
    ),
    Mercado(
        codigo="pt",
        nome="Portugal",
        google_domain="google.pt",
        gl="pt",
        hl="pt-pt",
        formato_preco="{valor} €",
        separador_milhar=".",
        separador_decimal=",",
        lojas_confiaveis=[
            "amazon", "worten", "fnac", "pcdiga", "radio popular", "mediamarkt",
            "el corte ingles", "continente", "chip7", "globaldata",
        ],
    ),
    Mercado(
        codigo="us",
        nome="Estados Unidos",
        google_domain="google.com",
        gl="us",
        hl="en",
        formato_preco="${valor}",
        separador_milhar=",",
        separador_decimal=".",
        lojas_confiaveis=[
            "amazon", "walmart", "best buy", "target", "newegg", "b&h",
            "costco", "gamestop",
        ],
    ),
    Mercado(
        codigo="gb",
        nome="Reino Unido",
        google_domain="google.co.uk",
        gl="uk",  # o Google (e o SerpApi) usam "uk" aqui
        hl="en",
        formato_preco="£{valor}",
        separador_milhar=",",
        separador_decimal=".",
        lojas_confiaveis=[
            "amazon", "argos", "currys", "john lewis", "ao.com", "very.co.uk", "game.co.uk",
        ],
    ),
]

MERCADOS: dict[str, Mercado] = {mercado.codigo: mercado for mercado in _MERCADOS}