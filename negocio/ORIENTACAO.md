# Orientação para a parte de Business Intelligence & Startup Development

Documento para quem fará a disciplina de Negócio e Pitch no FogoCerto. Pode ser lido por uma pessoa ou colado como contexto numa ferramenta de IA. Leia antes: `README.md` e `docs/PROJETO-FogoCerto.md` (seções 3, 6.7 e 10).

## Contexto do projeto

FogoCerto avisa produtores rurais e defesa civil, a cada manhã, o risco de fogo no município (15 municípios do Pará) e orienta sobre queima controlada. O risco é uma **regra transparente de pontos** (umidade, vento, chuva, calor e focos do dia anterior), calculada com dados abertos do INPE e do Open-Meteo. O produto **nunca autoriza queima**: informa o risco e encaminha ao órgão ambiental.

## Qual é o papel desta disciplina

É a disciplina que **conta a história**: qual é o problema, para quem, por que a solução importa e como ela se sustenta. O vídeo de pitch é onde as outras seis matérias aparecem juntas, funcionando. Aqui, a nota depende de **clareza e de evidência**, não de promessa.

## O que a disciplina exige (e o que vale nota)

Conferir o enunciado para a estrutura exata. Do que o projeto já levantou:

- **Vídeo de até 5 minutos**, no **YouTube como "não listado"**.
- Com **demonstração do MVP real**, na **URL pública**. Nada de slides simulando tela.
- **Nome completo e RM de todos os integrantes** na entrega.
- Link do vídeo entregue na plataforma da disciplina.

Roteiro sugerido pelo projeto (cinco minutos passam rápido; ensaie):

1. **Problema**, com dado do INPE.
2. **Solução**, em uma frase.
3. **Demonstração** do site funcionando.
4. **Modelo de negócio.**
5. **Indicadores e ODS.**
6. **Viabilidade e pedido.**

## O problema e a evidência

O produto resolve isto: o fogo na vegetação é detectado por satélite, mas o produtor e o gestor local **não têm um aviso simples, diário e local** que una risco, regra legal e orientação do que fazer. Muitos não sabem se precisam de autorização, nem que tempo seco e ventoso pode tornar a queima proibida ou perigosa.

**O briefing exige "problema real com evidência".** O que existe e o que falta:

| Evidência | Situação |
|---|---|
| Número de focos de calor no recorte (INPE) | o grupo informou que o **Pará concentrou cerca de 66 mil dos 118 mil focos do Brasil**. **Antes de falar isso no vídeo, registre o período e a fonte exatos** (por exemplo, BDQueimadas, qual intervalo de datas). Número sem fonte enfraquece o pitch |
| Dados próprios do pipeline | o Big Data tem a contagem de focos por município e dia (`fato_risco_municipio_dia`). Dá para mostrar o ranking dos 15 municípios |
| **2 ou 3 conversas curtas** com produtores, brigadistas ou defesa civil | **ainda a fazer.** Sem isso, não afirme que "os produtores querem" o produto. Marque as conversas já |

A conversa com usuário real é a evidência que mais pesa e a que o grupo ainda não tem. Faça-a cedo.

## Modelo de negócio (são hipóteses, não fatos)

O projeto listou como **hipóteses a validar**, e é assim que devem aparecer no vídeo:

- **Prefeituras e defesas civis** (assinatura).
- **Cooperativas e sindicatos rurais.**
- **Seguradoras agrícolas.**
- O **produtor usa de graça.**

Não cite preço, mercado, quantidade de clientes ou receita que o grupo não tenha validado. Apresente como "quem poderia pagar e por quê", e diga o que falta para validar.

## Indicadores (BI)

O projeto sugeriu estes indicadores. Para cada um, diga **de onde o número vem**:

| Indicador | De onde vem |
|---|---|
| Municípios cobertos | `risco_atual.json` (hoje, 15) |
| Alertas enviados | logs da RPA |
| Consultas ao assistente | logs da GenAI |
| **Taxa de focos em dias de risco alto** (backtest) | consulta de impacto do Big Data |
| Tempo entre o risco e o aviso | fluxo da RPA (hora do dado até o envio) |

**O backtest é o indicador mais forte**, porque responde "a regra funciona?": dos focos que aconteceram, quantos caíram em dias que a regra marcou como risco alto. Peça o resultado ao Big Data e mostre o número real, mesmo que seja modesto. Honestidade vale mais que um número bonito.

## ODS

- **ODS 13**: ação contra a mudança do clima (prevenção de incêndios e redução de emissões).
- **ODS 2**: agricultura sustentável (manejo seguro do fogo na produção).
- **ODS 3**: saúde e bem-estar (fumaça e riscos à vida).

Ligue cada ODS a **um indicador do quadro acima**, em vez de só citar o número.

## O que mostrar na demonstração

O site já está pronto e testado. Um caminho de demo curto, que cabe em um minuto e meio:

1. **Início:** escolher um município e mostrar o cartão (nível, motivos, focos, umidade, vento, chuva). Aponte que o nível vem com cor, texto e ícone (acessibilidade).
2. **Orientação:** em risco alto, o site diz "Não faça queima" e mostra a Defesa Civil (199) e os Bombeiros (193).
3. **Panorama:** os 15 municípios do maior para o menor risco.
4. **Como calculamos:** a regra de pontos e as fontes, para mostrar que não é caixa-preta.
5. **Funciona sem internet** (opcional e impressiona): abrir uma vez, desligar a rede e mostrar o último risco salvo.
6. **Assistente, foto e alerta:** mostrar o que as outras matérias entregarem, **se estiver funcionando na URL pública**. O que estiver "em breve" no site, **não apresente como pronto**.

Atenção ao dado: o site mostra a **data a que o risco se refere**. O pipeline coleta o dia anterior, então a data é sempre **ontem**. Se aparecer o aviso amarelo "Dados de DD/MM", o arquivo está velho: peça ao Big Data o JSON atualizado **antes de gravar o vídeo**.

## IA responsável (vale citar no pitch)

- **Pessoa no circuito:** o sistema nunca autoriza queima; encaminha ao órgão competente.
- **Transparência:** cada alerta mostra por que foi emitido.
- **Dados mínimos (LGPD):** sem rosto ou placa, imagens não armazenadas, contato com hash.
- **Acessível e resiliente:** linguagem simples, contraste, teclado, leitor de tela, celular de entrada, rede ruim (a última informação fica visível).
- **Sem prometer "previsão por IA":** o risco é uma regra de pontos, validada por backtest.

## O que não fazer

- Não mostrar slide fingindo ser tela do produto.
- Não afirmar que o produto "autoriza" ou "libera" queima.
- Não apresentar hipótese de negócio como fato, nem inventar usuário, preço ou parceiro.
- Não citar número sem fonte e período.
- Não esquecer nome completo e RM de todos.
- Não passar de 5 minutos.

## Estrutura da pasta (sugestão)

```
negocio/
  README.md          link do vídeo, roteiro, nomes completos e RMs
  roteiro.md         texto do pitch, minuto a minuto
  evidencias/        fonte e período do número de focos, notas das conversas com usuários
  indicadores/       quadro de indicadores e de onde vêm os números
```

## Prazos

Entrega final: 19/11/2026 às 23h55 (link do vídeo no YouTube, com nome completo e RM de todos). Meta interna: 18/11. **A gravação do pitch precisa vir depois de: site publicado na URL pública, JSON de risco atualizado e funções das outras matérias funcionando.** Trabalhe em uma branch curta (`negocio/pitch`), abra pull request e peça 1 aprovação antes de juntar na `main`.
