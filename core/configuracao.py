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
    
    # Discord
    discord_public_key: str = ""         # Developer Portal > General Information > Public Key
    discord_canal_id: str = ""           # ID do canal permitido; vazio = qualquer canal
    discord_intervalo_segundos: float = 5  # intervalo mínimo entre buscas do mesmo usuário
    # usados apenas pelo script registrar_comandos.py
    discord_application_id: str = ""
    discord_bot_token: str = ""
    discord_servidor_id: str = ""
    
    # WhatsApp (API oficial da Meta)
    whatsapp_verify_token: str = ""      # texto que você inventa; igual ao digitado no painel da Meta
    whatsapp_app_secret: str = ""        # App settings > Basic > App secret
    whatsapp_access_token: str = ""      # WhatsApp > API Setup (o temporário expira em pouco tempo)
    whatsapp_phone_number_id: str = ""   # WhatsApp > API Setup > Phone number ID
    whatsapp_api_versao: str = "v23.0"   # versão da Graph API
    whatsapp_numeros_permitidos: str = ""  # números separados por vírgula; vazio = qualquer número
    whatsapp_intervalo_segundos: float = 5
    
    # Telegram
    telegram_bot_token: str = ""            # entregue pelo @BotFather ao criar o bot
    telegram_secret_token: str = ""         # você inventa (A-Z a-z 0-9 _ -); o Telegram o envia em toda chamada
    telegram_usuarios_permitidos: str = ""  # IDs numéricos separados por vírgula; vazio = recusa todos
    telegram_intervalo_segundos: float = 5

    # extra="ignore": sobras no .env (ex: TAVILY_API_KEY antiga) não causam erro
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


configuracao = Configuracao()
