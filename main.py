from fastapi import FastAPI

from controller import busca_controller, discord_controller, whatsapp_controller
from controller.telegram import telegram_controller
from core.configuracao import configuracao
from data.agente_openai import AgenteOpenAI
from data.notificador_console import NotificadorConsole
from data.discord.notificador_discord_interacao import NotificadorDiscordInteracao
from data.telegram.notificador_telegram import NotificadorTelegram
from data.whatsapp.notificador_whatsapp import NotificadorWhatsApp
from data.pesquisa_serpapi import PesquisaSerpApi
from domain.interfaces import NotificadorInterface
from service.busca_precos_service import BuscaPrecosService
from domain.mercados import MERCADO_PADRAO, MERCADOS

agente = AgenteOpenAI(configuracao.openai_api_key, configuracao.openai_modelo)
pesquisa = PesquisaSerpApi(configuracao.serpapi_api_key)


def criar_service(notificador: NotificadorInterface) -> BuscaPrecosService:
    return BuscaPrecosService(
        filtro_entrada=agente,
        pesquisa=pesquisa,
        filtro_saida=agente,
        notificador=notificador,
        mercados=MERCADOS,
        mercado_padrao=MERCADO_PADRAO,
        max_resultados_ia=configuracao.max_resultados_ia,
        max_ofertas_resposta=configuracao.max_ofertas_resposta,
    )


notificador_whatsapp = NotificadorWhatsApp(
    configuracao.whatsapp_access_token,
    configuracao.whatsapp_phone_number_id,
    configuracao.whatsapp_api_versao,
)

notificador_telegram = NotificadorTelegram(configuracao.telegram_bot_token)

service_console = criar_service(NotificadorConsole())              # POST /buscar (testes)
service_discord = criar_service(NotificadorDiscordInteracao())     # POST /discord/interacoes
service_whatsapp = criar_service(notificador_whatsapp)             # POST /whatsapp/webhook
service_telegram = criar_service(notificador_telegram)             # POST /telegram/webhook

app = FastAPI(title="Busca de Preços")
app.dependency_overrides[busca_controller.obter_service] = lambda: service_console
app.dependency_overrides[discord_controller.obter_service_discord] = lambda: service_discord
app.dependency_overrides[whatsapp_controller.obter_service_whatsapp] = lambda: service_whatsapp
app.dependency_overrides[whatsapp_controller.obter_notificador_whatsapp] = lambda: notificador_whatsapp
app.dependency_overrides[telegram_controller.obter_service_telegram] = lambda: service_telegram
app.dependency_overrides[telegram_controller.obter_notificador_telegram] = lambda: notificador_telegram
app.include_router(busca_controller.router)
app.include_router(discord_controller.router)
app.include_router(whatsapp_controller.router)
app.include_router(telegram_controller.router)