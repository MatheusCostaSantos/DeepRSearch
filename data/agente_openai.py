import json

from openai import AsyncOpenAI

from domain.interfaces import FiltroEntradaInterface, FiltroSaidaInterface
from domain.modelos import FiltroBusca, Oferta

PROMPT_ENTRADA = """Você recebe o pedido de um usuário e devolve APENAS um JSON.

Regras:
- "produto": texto com o nome do produto, como se escreve numa busca (ex: "PlayStation 5").
- "lojas": LISTA de lojas SOMENTE se o usuário pediu lojas específicas (ex: ["Amazon"]).
  Caso contrário, deixe a lista vazia.
- "deve_conter": LISTA de textos com especificações pedidas pelo usuário (ex: ["128GB"]).
- "nao_deve_conter": LISTA de palavras para excluir acessórios e peças
  (ex: ["capa", "película", "carregador"]).
- "preco_minimo" e "preco_maximo": número ou null.
- Campos de lista devem ser SEMPRE listas JSON, mesmo com um só item ou vazios.

Exemplo de resposta:
{
  "produto": "iPhone 15",
  "lojas": [],
  "deve_conter": ["128GB"],
  "nao_deve_conter": ["capa", "película", "carregador"],
  "preco_minimo": null,
  "preco_maximo": null
}"""

PROMPT_SAIDA = """Você recebe o pedido do usuário e uma lista de resultados do Google Shopping,
cada um com id, titulo, loja e preco.

Devolva APENAS um JSON no formato {"relevantes": [ids]} com os ids dos resultados que são
EXATAMENTE o produto pedido, novo e completo.

Exclua:
- acessórios, peças, capas, películas, carregadores, cabos;
- jogos ou controles quando o produto pedido é um console;
- versões ou modelos diferentes do que foi pedido;
- kits de peças, anúncios de outro produto ou itens com título confuso.

Se o pedido não especifica versão (ex: "PlayStation 5"), aceite todas as versões do produto
(ex: Standard, Digital, Slim, Pro), desde que seja o produto em si.
Em caso de dúvida, exclua. Não altere preços nem títulos: devolva somente os ids."""


class AgenteOpenAI(FiltroEntradaInterface, FiltroSaidaInterface):
    def __init__(self, api_key: str, modelo: str):
        self.cliente = AsyncOpenAI(api_key=api_key)
        self.modelo = modelo

    async def _pedir_json(self, instrucao: str, conteudo: str) -> dict:
        resposta = await self.cliente.chat.completions.create(
            model=self.modelo,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": instrucao},
                {"role": "user", "content": conteudo},
            ],
        )
        return json.loads(resposta.choices[0].message.content)

    async def criar_filtro(self, mensagem_usuario: str) -> FiltroBusca:
        dados = await self._pedir_json(PROMPT_ENTRADA, mensagem_usuario)
        return FiltroBusca(**dados)

    async def selecionar_relevantes(
        self, filtro: FiltroBusca, ofertas: list[Oferta]
    ) -> list[Oferta]:
        if not ofertas:
            return []

        conteudo = json.dumps(
            {
                "pedido": filtro.model_dump(),
                "resultados": [
                    {"id": i, "titulo": o.titulo, "loja": o.loja, "preco": o.preco}
                    for i, o in enumerate(ofertas)
                ],
            },
            ensure_ascii=False,
        )
        dados = await self._pedir_json(PROMPT_SAIDA, conteudo)

        ids = set()
        for valor in dados.get("relevantes", []):
            try:
                ids.add(int(valor))
            except (TypeError, ValueError):
                continue

        # A IA só escolhe ids: preços e links vêm sempre dos dados originais.
        return [oferta for i, oferta in enumerate(ofertas) if i in ids]
