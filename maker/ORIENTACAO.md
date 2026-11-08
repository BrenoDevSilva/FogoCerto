# Orientação para a parte de Project-Based Maker Lab

Documento para quem fará a disciplina de Maker Lab no FogoCerto. Pode ser lido por uma pessoa ou colado como contexto numa ferramenta de IA. Leia antes: `README.md` e `docs/PROJETO-FogoCerto.md` (seção 6.6).

## Contexto do projeto

FogoCerto avisa produtores rurais e defesa civil, a cada manhã, o risco de fogo no município (15 municípios do Pará). O risco vem de dados abertos (focos de calor do INPE e clima do Open-Meteo), processados em `bigdata/`. O produto **nunca autoriza queima**: informa o risco e encaminha ao órgão ambiental.

## Qual é o papel do robô

O satélite e a previsão do tempo olham o município inteiro, de longe e uma vez por dia. O robô olha **um ponto, agora**: mede temperatura, umidade e fumaça no local e **decide ali mesmo** se a combinação passou do limiar. É a camada física do produto: dado de campo, em tempo real, que não depende do satélite passar.

Ele entra como **fonte extra de alerta local**: leitura ruim ou perigo no ponto vira um evento que o FogoCerto pode cruzar com o risco do município.

## Status e risco principal

O projeto marcou como pendência: **o carrinho não está disponível no momento.** É preciso descobrir quem está com ele ou o que falta comprar. **Este é o maior risco da disciplina**: sem robô funcionando não há vídeo nem testes. Resolva o hardware primeiro, antes de qualquer código.

Se faltar peça, o enunciado aceita **dado simulado, desde que a geração seja documentada e justificada**. Isso é um plano B, não o plano A: a nota é de um projeto físico.

## O que a disciplina exige (e o que vale nota)

Conferir o enunciado para a estrutura exata. Do que o projeto já levantou:

- **Evolução do robô** com sensor de **temperatura e umidade** e sensor de **fumaça**.
- **Decisão local:** o robô alerta quando a **combinação** de leituras passa do limiar, sem depender de comando manual nem de internet.
- **IA no robô:** classificação do nível de risco local, com **regra mais modelo leve**. Registre o que é regra e o que é modelo.
- **Envio do evento à API** quando há rede.
- **Testes de operação e de falha:** sem rede e com leitura ruim.
- **Entrega somente por GitHub** (ZIP, PDF e DOC **não** são aceitos).
- **Vídeo de até 6 minutos**, no README ou no YouTube.
- **Nomes completos de todos os integrantes no README.** Sem os nomes, o grupo fica **sem nota** na GS.

## Contrato com a API

`POST /sensor/eventos`, com o corpo:

```json
{
  "dispositivo_id": "robo-01",
  "horario": "2026-11-08T14:32:10-03:00",
  "temperatura": 38.5,
  "umidade": 22.0,
  "fumaca": 0.71
}
```

- `dispositivo_id`: identifica o robô. Um nome fixo, sem dado pessoal.
- `horario`: quando a leitura foi feita, com fuso (Brasília é UTC-3).
- `temperatura` em °C, `umidade` em %.
- `fumaca`: o valor da leitura do sensor. **Combine com o dono da API** se será valor bruto ou normalizado (0 a 1) e documente a unidade e a calibração.

A API ainda não existe; combine o formato exato com quem faz a API (Pessoa 4, segundo a divisão do projeto) antes de fixar o código do robô.

## Como pensar no limiar de alerta

Para o limiar local, reaproveite a lógica do produto para falar a mesma língua. O risco do município usa estes limites (vindos do `bigdata/README.md`):

| Sinal | Pontos |
|---|---|
| umidade mínima abaixo de 30% / abaixo de 40% | 2 / 1 |
| temperatura máxima de 35 °C ou mais | 1 |

(Os outros fatores, vento, chuva e focos, o robô não mede.) Uma combinação razoável para o robô: **umidade baixa + temperatura alta + fumaça acima de um valor**. **Justifique cada limiar** e mostre as leituras que o embasaram; limiar sem justificativa vale pouco.

Sugestão de estrutura em dois níveis, simples de explicar no vídeo:

1. **Regra:** `se fumaça acima do limite → alerta` (não depende de nada, funciona sempre).
2. **Modelo leve** (por exemplo, árvore de decisão pequena) que combina temperatura, umidade e fumaça e classifica `baixo`, `medio` ou `alto`. Compare com a regra e mostre onde diferem.

## Falhas que precisam ser tratadas e testadas

| Situação | O que o robô faz |
|---|---|
| **Sem rede** | decide localmente, guarda o evento e **reenvia quando a rede voltar** |
| **Leitura ruim** (sensor desconectado, valor impossível, como umidade acima de 100%) | descarta a leitura, **não dispara alerta falso**, registra o erro |
| API fora do ar | mesmo caminho de "sem rede" |
| Sensor de fumaça instável logo ao ligar | esperar o aquecimento antes de confiar na leitura |

Cada linha dessa tabela vira um teste com evidência (foto, log ou trecho do vídeo).

## Segurança nos testes

Teste com **fonte de fumaça segura e supervisionada**, sem fogo de verdade perto do equipamento. Fumaça de incenso ou de um palito, em ambiente aberto e com alguém acompanhando, basta para o sensor reagir. Registre no relatório como o teste foi feito de forma segura.

## O que não fazer

- Não promover o robô como se ele detectasse incêndio sozinho: ele **mede condições e fumaça** no ponto; a conclusão de "fogo" é de uma pessoa.
- Não citar usuários, mercado ou clientes que o grupo não validou.
- Não subir fotos com rosto ou placa de carro, nem dado pessoal.
- Não subir senha de Wi-Fi, token ou chave no código (use arquivo de configuração fora do repositório; o `.gitignore` já bloqueia `.env`).
- Não entregar em ZIP, PDF ou DOC: só link do GitHub.
- Não deixar o README sem os nomes completos.

## Estrutura da pasta (sugestão)

```
maker/
  README.md          nomes completos, vídeo, como montar e reproduzir
  firmware/          código do robô (leitura, decisão local, envio)
  modelo/            treino e exportação do modelo leve, com os dados usados
  docs/              esquema de ligação, justificativa dos limiares, evidências
  testes/            operação e falha (sem rede, leitura ruim), com logs
```

## Prazos

Entrega final: 19/11/2026 às 23h55, **somente o link do GitHub** (com o vídeo e os nomes no README). Meta interna: 18/11. Como o hardware é o gargalo, o primeiro marco é **ter o robô funcionando e lendo os sensores**, em poucos dias; o resto (modelo, API, testes) vem depois. Trabalhe em uma branch curta (`maker/sensores`, `maker/modelo`), abra pull request e peça 1 aprovação antes de juntar na `main`.
