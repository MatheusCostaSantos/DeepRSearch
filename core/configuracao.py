from pydantic_settings import BaseSettings, SettingsConfigDict


class Configuracao(BaseSettings):
    openai_api_key: str
    serpapi_api_key: str
    openai_modelo: str = "gpt-4o-mini"

    # Lojas aceitas quando o usuário não pede lojas específicas.
    # A comparação ignora acentos e maiúsculas e aceita trechos
    # (ex: "amazon" aceita "Amazon.com.br"). Edite a lista como quiser.
    lojas_confiaveis: list[str] = [
        "amazon",
        "mercado livre",
        "magazine luiza",
        "magalu",
        "americanas",
        "casas bahia",
        "kabum",
        "ponto frio",
        "pontofrio",
        "submarino",
        "carrefour",
    ]

    max_resultados_ia: int = 40      # quantos resultados vão para a OpenAI avaliar
    max_ofertas_resposta: int = 5    # quantas ofertas aparecem na mensagem final

    # extra="ignore": sobras no .env (ex: TAVILY_API_KEY antiga) não causam erro
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


configuracao = Configuracao()
