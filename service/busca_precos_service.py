import re
import statistics
from collections import Counter

from domain.interfaces import (
    FiltroEntradaInterface,
    FiltroSaidaInterface,
    NotificadorInterface,
    PesquisaInterface,
)
from domain.modelos import FiltroBusca, Oferta, normalizar_texto


class BuscaPrecosService:
    def __init__(
        self,
        filtro_entrada: FiltroEntradaInterface,
        pesquisa: PesquisaInterface,
        filtro_saida: FiltroSaidaInterface,
        notificador: NotificadorInterface,
        lojas_confiaveis: list[str],
        max_resultados_ia: int = 40,
        max_ofertas_resposta: int = 5,
    ):
        self.filtro_entrada = filtro_entrada
        self.pesquisa = pesquisa
        self.filtro_saida = filtro_saida
        self.notificador = notificador
        self.lojas_confiaveis = lojas_confiaveis
        self.max_resultados_ia = max_resultados_ia
        self.max_ofertas_resposta = max_ofertas_resposta

    async def executar(self, mensagem_usuario: str, destino: str) -> None:
        try:
            filtro = await self.filtro_entrada.criar_filtro(mensagem_usuario)
            print(f"Filtro criado: {filtro}")

            ofertas = await self.pesquisa.pesquisar(filtro)
            print(f"Resultados do Google Shopping: {len(ofertas)}")

            ofertas = self._filtrar_em_codigo(filtro, ofertas)
            print(f"Após filtros em código: {len(ofertas)}")

            ofertas = ofertas[: self.max_resultados_ia]
            ofertas = await self.filtro_saida.selecionar_relevantes(filtro, ofertas)
            print(f"Selecionadas pela IA: {len(ofertas)}")

            ofertas = self._remover_precos_suspeitos(ofertas)
            ofertas = sorted(ofertas, key=lambda oferta: oferta.preco)
            texto = self._formatar(filtro.produto, ofertas)
        except Exception as erro:
            print(f"Erro na busca: {erro}")
            texto = "Não consegui concluir a busca agora. Tente novamente em instantes."

        await self.notificador.enviar(destino, texto)

    # ---------- regras em código (não dependem da IA) ----------

    def _filtrar_em_codigo(self, filtro: FiltroBusca, ofertas: list[Oferta]) -> list[Oferta]:
        lojas_aceitas = [normalizar_texto(loja) for loja in (filtro.lojas or self.lojas_confiaveis)]
        palavras_excluidas = [normalizar_texto(p) for p in filtro.nao_deve_conter]

        vistos: set[tuple] = set()
        validas: list[Oferta] = []
        descartes: Counter = Counter()

        for oferta in ofertas:
            loja = normalizar_texto(oferta.loja)
            titulo = normalizar_texto(oferta.titulo)
            chave = (loja, titulo, oferta.preco)

            if oferta.usado:
                descartes["usado/recondicionado"] += 1
            elif not any(nome in loja for nome in lojas_aceitas):
                descartes["loja fora da lista"] += 1
            elif any(self._contem_palavra(titulo, p) for p in palavras_excluidas):
                descartes["palavra excluída no título"] += 1
            elif filtro.preco_minimo and oferta.preco < filtro.preco_minimo:
                descartes["abaixo do preço mínimo"] += 1
            elif filtro.preco_maximo and oferta.preco > filtro.preco_maximo:
                descartes["acima do preço máximo"] += 1
            elif chave in vistos:
                descartes["duplicada"] += 1
            else:
                vistos.add(chave)
                validas.append(oferta)

        if descartes:
            print(f"Descartadas em código: {dict(descartes)}")
        return validas

    @staticmethod
    def _contem_palavra(titulo: str, palavra: str) -> bool:
        # palavra inteira: "capa" não pode barrar "capacidade"
        return bool(palavra) and re.search(rf"\b{re.escape(palavra)}\b", titulo) is not None

    @staticmethod
    def _remover_precos_suspeitos(ofertas: list[Oferta]) -> list[Oferta]:
        if len(ofertas) < 3:
            return ofertas

        mediana = statistics.median(oferta.preco for oferta in ofertas)
        aceitas = []
        for oferta in ofertas:
            if oferta.preco < mediana * 0.5:
                print(f"Descartada (preço muito abaixo da mediana): {oferta.loja} - {oferta.preco}")
            else:
                aceitas.append(oferta)
        return aceitas

    # ---------- formatação ----------

    @staticmethod
    def _moeda(valor: float) -> str:
        texto = f"{valor:,.2f}"
        return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")

    def _formatar(self, produto: str, ofertas: list[Oferta]) -> str:
        if not ofertas:
            return f"Não encontrei ofertas de lojas confiáveis para **{produto}** desta vez."

        linhas = [f"**Melhores preços para {produto}:**"]
        for posicao, oferta in enumerate(ofertas[: self.max_ofertas_resposta], start=1):
            linhas.append(f"{posicao}. {self._moeda(oferta.preco)} - {oferta.loja}")
            linhas.append(f"   {oferta.titulo[:80]}")

            desconto = oferta.desconto_percentual
            if desconto:
                linhas.append(f"   Promoção: de {self._moeda(oferta.preco_original)} (-{desconto}%)")

            if oferta.parcelas and oferta.valor_parcela:
                total = oferta.parcelas * oferta.valor_parcela
                parcela = f"{oferta.parcelas}x de {self._moeda(oferta.valor_parcela)}"
                if total <= oferta.preco * 1.01:
                    linhas.append(f"   Parcelado: {parcela} sem juros")
                else:
                    linhas.append(f"   Parcelado: {parcela} (total {self._moeda(total)})")

            linhas.append(f"   Link: {oferta.url}")
        return "\n".join(linhas)