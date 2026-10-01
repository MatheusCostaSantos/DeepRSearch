from fastapi import FastAPI

from controller import busca_controller
from core.configuracao import configuracao
from data.agente_openai import AgenteOpenAI
from data.notificador_console import NotificadorConsole
# from data.notificador_discord import NotificadorDiscord
from data.pesquisa_serpapi import PesquisaSerpApi
from service.busca_precos_service import BuscaPrecosService

agente = AgenteOpenAI(configuracao.openai_api_key, configuracao.openai_modelo)

service = BuscaPrecosService(
    filtro_entrada=agente,
    pesquisa=PesquisaSerpApi(configuracao.serpapi_api_key),
    filtro_saida=agente,
    notificador=NotificadorConsole(),  # troque por NotificadorDiscord() ao ligar o Discord
    lojas_confiaveis=configuracao.lojas_confiaveis,
    max_resultados_ia=configuracao.max_resultados_ia,
    max_ofertas_resposta=configuracao.max_ofertas_resposta,
)

app = FastAPI(title="Busca de Preços")
app.dependency_overrides[busca_controller.obter_service] = lambda: service
app.include_router(busca_controller.router)