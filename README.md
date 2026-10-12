# DeepR$earch

## O Que É?
O DeepRSearch é uma API criada para a busca de preços de produtos em lojas confiáveis, usando o Google Shopping como fonte de dados e uma IA para separar o que realmente é o produto pedido do que é acessório, versão errada ou anúncio duvidoso. O resultado, com os melhores preços ordenados, é enviado de volta ao canal de onde o pedido veio (Discord ou Telegram).
A API foi pensada para que o usuário converse de forma natural ("PS5", "iPhone 15 128GB", "Quero comprar um PS5 em Portugal") e receba uma lista curta e confiável, sem precisar abrir várias lojas e comparar preços manualmente.

## Funcionalidades
* Entende pedidos em linguagem natural e os transforma em um filtro de busca: produto, país, lojas pedidas, especificações obrigatórias, palavras a excluir (como "capa" e "película") e faixa de preço.
* Permite escolher o **país** da busca direto na mensagem. Cada país tem o seu Google Shopping, a sua lista de lojas confiáveis e a sua moeda. Sem país citado, a busca é feita no Brasil.
* Faz **uma única busca** no Google Shopping por pedido, o que mantém o custo previsível.
* Aplica regras em código, que não dependem da IA: descarta itens usados ou recondicionados, lojas fora da lista do país, palavras indesejadas, preços fora da faixa pedida e duplicados.
* Usa a IA como segundo filtro: ela recebe apenas identificador, título, loja e preço, e **devolve só os identificadores** dos resultados que são exatamente o produto. Como ela nunca escreve preços nem links, não tem como inventá-los.
* Remove preços suspeitos e ordena as ofertas por preço em código.
* Mostra, para cada oferta, o preço, a loja, a promoção (preço antigo e percentual de desconto), o parcelamento (quando o Google informa) e o link.

### Como a resposta é apresentada
```
Melhores preços para PlayStation 5 (Portugal):
1. 499,99 € - Worten.pt
   Consola PlayStation 5 Slim 1TB
   Promoção: de 549,99 € (-9%)
   Parcelado: 12x de 41,66 € sem juros
   Link: https://...
```
As linhas de promoção e de parcelamento só aparecem quando o dado existe. O "sem juros" é calculado: aparece quando a soma das parcelas é igual ao preço à vista. Se o total for maior, a linha mostra o total, para que a diferença fique visível.

## Ferramentas Usadas

**Backend**
* **FastAPI + uvicorn:** A API em Python que recebe os pedidos dos canais e orquestra o fluxo.
* **httpx:** Comunicação da API com os serviços externos (SerpApi, Discord e Telegram).

**Inteligência Artificial**
* **OpenAI:** Faz o papel de filtro de entrada (entende o pedido e cria o filtro de busca) e de filtro de saída (escolhe quais resultados são o produto pedido).

**Dados de preços**
* **SerpApi (Google Shopping):** Fonte dos preços, lojas, preços antigos e parcelamentos.

**Canais**
* **Discord:** Comandos por interações HTTP, sem bot conectado o tempo todo.
* **Telegram:** Bot por webhook.
* **WhatsApp (API oficial da Meta):** Preparado no código, mas não está em uso.

**Deploy**
* **Docker + Azure Container Apps:** Ambiente onde a API roda em produção, com endereço público HTTPS.

## Organização da API

### Arquitetura
A API foi desenvolvida utilizando a Arquitetura Limpa (Clean Architecture), organizando as funções em níveis de conhecimento. As camadas exteriores dependem das interiores, mas sem a necessidade de saber como elas funcionam, recebendo apenas o resultado final de cada uma. Cada parte foi feita pensando na modularização e em ajustes futuros da API.

O projeto foi organizado em:
* **Domain:** Modelos, contratos e interfaces, além da tabela de países.
* **Data:** Implementações concretas: agente da OpenAI, pesquisa no SerpApi e um notificador por canal.
* **Service:** Orquestração do fluxo de busca.
* **Controller:** A porta de entrada HTTP, com uma parte para cada canal.
* **Core:** Configurações.

Um bom exemplo dessa modularidade são os notificadores. Todos implementam a mesma interface, `NotificadorInterface`, com um único método `enviar`. O `Service` monta o texto e o entrega ao notificador, sem saber se o destino é um canal do Discord, um chat do Telegram ou o terminal. Isso permite adicionar um canal novo sem tocar no fluxo de busca.

### Países
Cada país disponível reúne os parâmetros do Google Shopping, a lista de lojas confiáveis e o formato da moeda (por exemplo `R$ 1.299,99`, `1.299,99 €` ou `$1,299.99`). Os países disponíveis são Brasil (padrão), Portugal, Estados Unidos e Reino Unido. Se o usuário pedir um país que não está na lista, a API responde com os países disponíveis, em vez de buscar em lojas desconhecidas. Os preços não são convertidos entre moedas.

## Como Funciona

### Fluxo de uma busca
1. O usuário envia o pedido pelo canal. A API confere a origem da chamada e responde na hora, deixando a busca para o segundo plano.
2. **Filtro de entrada (OpenAI):** transforma o texto em um filtro com produto, país, lojas, especificações, palavras a excluir e faixa de preço.
3. **Busca (SerpApi):** uma chamada ao Google Shopping do país escolhido devolve os resultados, com loja, preço, preço antigo e parcelamento.
4. **Filtros em código:** retiram usados, lojas fora da lista do país, palavras excluídas, preços fora da faixa e duplicados.
5. **Filtro de saída (OpenAI):** recebe os resultados restantes e devolve só os identificadores dos que são o produto pedido.
6. **Ordenação e formatação:** remove preços suspeitos, ordena por preço e monta o texto com as melhores ofertas.
7. **Envio:** o notificador do canal entrega a resposta.

Se qualquer etapa falhar, a API registra o erro e avisa o usuário no canal, em vez de ficar em silêncio.

### Canais
* **Discord:** o Discord chama a API quando alguém usa um comando. A API responde "o aplicativo está pensando..." na hora e entrega o resultado quando a busca termina. Como o Discord limita o tamanho das mensagens, respostas longas são divididas em mais de uma mensagem.
* **Telegram:** o Telegram envia cada mensagem à API. A conversa é natural: basta escrever o produto.
* **WhatsApp:** a integração com a API oficial da Meta está preparada no código, mas não está em uso.

### Segurança
Cada canal tem a sua forma de confirmar que a chamada realmente veio dele: assinatura digital no Discord, token secreto no Telegram e assinatura da Meta no WhatsApp. O acesso também é restrito: o Discord responde apenas no canal configurado, e o Telegram atende apenas usuários autorizados previamente pelos administradores.

## Como Usar
A API é usada diretamente pelos canais de mensagem, sem instalar nada. Como o acesso é restrito, é necessário que um dos administradores libere o usuário antes (no Telegram) e que o uso seja feito no canal definido (no Discord).

### Pelo Discord
1. Vá até o canal de ofertas.
2. Digite `/buscar` e informe o produto, por exemplo: `/buscar produto:PlayStation 5`.
3. Aparece a mensagem "o aplicativo está pensando...". Alguns segundos depois, ela é substituída pelo resultado.
4. Se preferir, escreva o produto como uma mensagem normal no canal e, com o botão direito sobre ela, escolha **Aplicativos → Buscar preços**.
5. Cada usuário pode fazer uma busca a cada 5 segundos.

### Pelo Telegram
1. Abra a conversa com o bot e toque em **Iniciar**.
2. Escreva o produto, como numa conversa normal. Exemplo: `PlayStation 5`.
3. Aguarde alguns segundos pela resposta com as melhores ofertas.
4. Se o bot não responder, o seu usuário ainda não foi liberado por um administrador.

### Dicas para fazer o pedido
* Cite o país quando quiser comprar fora do Brasil: `Quero comprar um PS5 em Portugal`.
* Inclua especificações: `iPhone 15 128GB`.
* Informe um limite de preço, na moeda do país: `Galaxy S24 até 3500 reais`.
* Peça uma loja específica: `PS5 só na Amazon`.