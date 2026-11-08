# Orientação para a parte de Robotic Process Automation

Documento para quem fará a disciplina de RPA no FogoCerto. Pode ser lido por uma pessoa ou colado como contexto numa ferramenta de IA. Leia antes: `README.md` e `docs/PROJETO-FogoCerto.md` (seção 6.4).

## Contexto do projeto

FogoCerto avisa produtores rurais e defesa civil, a cada manhã, o risco de fogo no município (15 municípios do Pará). O risco vem de dados abertos (focos de calor do INPE e clima do Open-Meteo), processados em `bigdata/`. O produto **nunca autoriza queima**: informa o risco e encaminha ao órgão ambiental.

## Qual é o papel da RPA

O site mostra o risco para quem **abre** o site. A RPA cobre quem **não abriu**: um fluxo diário lê o risco de cada município, decide quem precisa ser avisado e envia o alerta. É o "avisa a cada manhã" do produto.

O fluxo é: **ler o risco → decidir por município → repetir para cada assinante → enviar → registrar o que aconteceu**.

## O que a disciplina exige (e o que vale nota)

Conferir o enunciado para a estrutura exata. Do que o projeto já levantou:

- Fluxo diário em **n8n ou Python** (não precisa ser os dois).
- Uma **decisão** (condição) por município e uma **repetição** (laço) para cada município assinante.
- Envio de alerta por **Telegram ou e-mail** (decisão do grupo ainda em aberto).
- **Tratamento de exceções:** API ou arquivo fora do ar, dado ausente ou inválido, dado duplicado.
- **Logs** com data e hora, itens processados, sucessos e falhas, sem dado sensível.
- **Integração verificável com o MVP:** dá para mostrar que o alerta veio do mesmo dado que o site mostra.
- **Testes** de sucesso, de decisão e de falha, com evidência.
- Fluxo desenhado em **BPMN**, relatório em **PDF** e **vídeo de até 3 minutos**.

## De onde o fluxo lê o risco

Hoje, o oficial é o arquivo **`site/public/data/risco_atual.json`**, gerado pelo Databricks (notebook `bigdata/databricks/04_exportar.py`), o mesmo que o site lê. Quando o site estiver publicado, o mesmo arquivo fica em `<URL do site>/data/risco_atual.json`. Quando a API existir, a leitura troca para `GET /risco?municipio_id=`.

Deixe o endereço **configurável** (variável de ambiente ou variável do n8n), para trocar do arquivo local para a URL do site sem mexer no fluxo.

Formato: uma lista com 1 item por município, do maior para o menor risco.

```json
{
  "id_ibge": 1504802,
  "nome": "Monte Alegre",
  "uf": "PA",
  "data": "2026-11-07",
  "nivel_risco": "alto",
  "pontos": 7,
  "fatores": "umidade minima de 39%; vento de ate 22 km/h; sem chuva nos ultimos 3 dias; calor de 36 C; 349 focos ontem no municipio",
  "focos_ontem": 349,
  "umidade_min": 39.0,
  "vento_max": 22.0,
  "temp_max": 35.8,
  "chuva_3d": 0.4,
  "atualizado_em": "2026-11-08T10:35:00"
}
```

| Campo | Para que serve no fluxo |
|---|---|
| `nivel_risco` | `baixo`, `medio` ou `alto` (sem acento). É a base da **decisão** |
| `fatores` | motivos em texto, separados por `;`. Ponha no alerta: "por que estou sendo avisado" |
| `focos_ontem` | focos no município no dia anterior. Pode entrar na decisão (ex.: alto **ou** muitos focos) |
| `data` | dia a que o risco se refere. Veja a regra abaixo |
| `id_ibge`, `nome` | identificam o município na lista de assinantes |

O arquivo **não traz distância de focos** em relação ao assinante. Se a decisão de vocês for "foco a menos de X km", é preciso um dado novo do Big Data; combine com ele antes. A decisão mais simples e honesta com o que existe é **`nivel_risco == "alto"`**, com `focos_ontem` como reforço.

## Regra da data (importante para a decisão)

O pipeline coleta o clima e os focos do **dia anterior** todo dia às 10:30 (horário de Brasília). Por isso o campo `data` é sempre o **último dia fechado: ontem**. Isso é o esperado, não é erro.

- `data` = ontem: segue o fluxo normal.
- `data` mais antiga que ontem: o dado está atrasado. Decida e registre no log. Sugestão: **não enviar alerta como se fosse atual**; enviar com a data ("risco calculado em DD/MM") ou segurar o envio.
- `data` futura: dado inválido. Não enviar, registrar como falha.

O alerta nunca deve dizer "hoje há risco": diga "risco mais recente, com dados fechados de DD/MM".

## Assinantes e LGPD

No Big Data existe a tabela `assinantes_alerta`, com **dados fictícios**: só o hash SHA-256 do e-mail e o telefone mascarado. O contato original nunca é guardado. Para o fluxo de vocês:

- Para enviar por Telegram, o identificador é o `chat_id`. Trate-o como dado pessoal: **não vai para o repositório nem para o log**.
- Para a demonstração, use contas de teste do grupo. Nada de contato real de terceiros.
- No log, registre município, nível e resultado ("enviado", "falhou"), nunca o contato.

## Contrato com o resto do produto

- **Entrada:** o `risco_atual.json` (ou `GET /risco?municipio_id=`).
- **Saída:** mensagem curta por município, com nível, motivos (`fatores`), data do dado e a frase obrigatória.
- Frase obrigatória em todo alerta: **"O FogoCerto informa o risco. A autorização de queima é do órgão ambiental do seu estado."** Em risco alto, recomendar **não queimar** e procurar a defesa civil (199) ou os bombeiros (193).
- O alerta nunca autoriza queima.

Exemplo de mensagem:

```
FogoCerto · risco ALTO em Monte Alegre (PA)
Dados fechados de 07/11. Motivos: umidade mínima de 39%; vento de até 22 km/h; 349 focos no dia anterior.
Não faça queima. Se vir fogo ou fumaça, ligue para a Defesa Civil (199) ou os Bombeiros (193).
O FogoCerto informa o risco. A autorização de queima é do órgão ambiental do seu estado.
```

## Exceções que o fluxo precisa tratar

| Situação | O que fazer |
|---|---|
| Arquivo ou API fora do ar | tentar de novo algumas vezes; se falhar, registrar e **parar o envio** (não mandar alerta sem dado) |
| JSON vazio ou com formato errado | registrar como falha; não enviar |
| `nivel_risco` fora de `baixo`/`medio`/`alto` | ignorar o item e registrar |
| Município sem assinante | seguir para o próximo, sem erro |
| Alerta repetido (mesmo município e mesma `data`) | **não reenviar**; registrar "duplicado" |
| Falha de envio (Telegram/e-mail) | registrar e seguir para o próximo assinante |

## Testes (evidência para o relatório)

Um por tipo, com print ou log:

1. **Sucesso:** município de risco alto, alerta enviado.
2. **Decisão:** município de risco baixo, nenhum alerta enviado (a condição funcionou).
3. **Falha:** arquivo indisponível ou inválido, fluxo para e registra, sem alerta falso.

Para testar sem depender do dado do dia, aponte o fluxo para um JSON de teste **local**, fora do repositório oficial. Não edite `site/public/data/risco_atual.json` à mão: ele é atualizado pelo time de Big Data por pull request.

## Horário do fluxo

A coleta do Big Data roda às 10:30 (Brasília) e o arquivo oficial é atualizado por pull request, então o JSON publicado pode demorar a mudar. Agende o fluxo **depois** disso (por exemplo, no início da tarde) ou leia sempre a última versão publicada e confira a `data`.

## O que não fazer

- Não enviar alerta para contato real sem consentimento.
- Não subir `chat_id`, token de bot, senha de e-mail ou qualquer chave. Use variáveis de ambiente ou as credenciais do n8n (o `.gitignore` já bloqueia `.env`).
- Não dizer que o alerta "autoriza" ou "libera" a queima.
- Não prometer previsão. O risco é uma regra de pontos, não uma previsão por IA.
- Não subir logs com dados pessoais.

## Estrutura da pasta (já pedida pela disciplina)

```
rpa/
  src/               código Python (se usado)
  n8n/               exportação do fluxo (se usado; sem credenciais)
  docs/              fluxograma BPMN
  assets/            imagens e evidências
  logs/              amostras de logs sem dados sensíveis
  tests/             evidências dos testes (sucesso, decisão e falha)
  README.md          como reproduzir
```

## Prazos

Entrega final: 19/11/2026 às 23h55, no Teams da disciplina (PDF com links do repositório e do vídeo). Meta interna: 18/11. Trabalhe em uma branch curta (`rpa/fluxo`), abra pull request e peça 1 aprovação antes de juntar na `main`.
