# As matérias do FogoCerto, uma a uma

Visão geral de como cada disciplina se encaixa no mesmo produto. Cada matéria tem (ou terá) um guia próprio para quem for fazê-la; os links estão abaixo. Complementa `docs/PROJETO-FogoCerto.md`.

Entrega final de todas: **19/11/2026 às 23h55** (meta interna: 18/11). Nome completo e RM de todos os integrantes em cada relatório e no README. Sem isso, perde-se nota.

## A ideia em uma frase

Um sistema que diz ao produtor rural e à defesa civil, a cada manhã, se há risco de fogo na região e se é seguro (e permitido) fazer queima controlada. As sete matérias respondem à mesma pergunta: **"há risco hoje, e posso queimar?"**. O sistema **nunca autoriza queima**: informa o risco e encaminha ao órgão ambiental.

## Como as peças se ligam

```
INPE (focos) ─┐
              ├─> Airflow ─> chegada/ ─> Databricks: Bronze ─> Prata ─> Ouro ──> risco_atual.json
Open-Meteo ───┘                                                                        │
                                                                                       v
Robô (sensores) ──> API <── Visão (foto)       Assistente (GenAI) ──────────>   site (MVP)
                     │                                                                 │
                     └────────────────────────────> RPA (alertas) <────────────────────┘

DevOps: empacota, publica e vigia o site e a API.   Negócio: conta a história no vídeo de pitch.
```

O ponto de encontro entre todas é o arquivo **`site/public/data/risco_atual.json`** (gerado pelo Big Data) e, mais adiante, a API.

## Quadro-resumo

| Matéria | Pasta | Responde a | Estado hoje (08/11) | Guia |
|---|---|---|---|---|
| Big Data Architecture & Data Integration | [`bigdata/`](../bigdata/) | "qual o risco, e com que dados?" | Pipeline pronto; falta publicar o JSON atualizado | [`bigdata/README.md`](../bigdata/README.md) |
| MVP (site) | [`site/`](../site/) | "como o cidadão vê isso?" | Pronto e na `main`; falta publicar numa URL | [`site/README.md`](../site/README.md) |
| Generative AI for Engineering | [`genai/`](../genai/) | "posso queimar? o que diz a lei?" | Guia de integração feito; falta construir | [`genai/INTEGRACAO-BigData.md`](../genai/INTEGRACAO-BigData.md) |
| Applied Computer Vision | [`visao/`](../visao/) | "essa foto mostra fumaça ou fogo?" | Orientação feita; falta construir | [`visao/ORIENTACAO.md`](../visao/ORIENTACAO.md) |
| Robotic Process Automation | [`rpa/`](../rpa/) | "quem precisa ser avisado hoje?" | Só o esqueleto | [`rpa/ORIENTACAO.md`](../rpa/ORIENTACAO.md) |
| Secure DevOps & Cloud | [`devops/`](../devops/) | "como colocar no ar com segurança?" | Só o esqueleto | [`devops/ORIENTACAO.md`](../devops/ORIENTACAO.md) |
| Project-Based Maker Lab | [`maker/`](../maker/) | "o que se mede no local, agora?" | Só o esqueleto; hardware é o risco | [`maker/ORIENTACAO.md`](../maker/ORIENTACAO.md) |
| Business Intelligence & Startup | [`negocio/`](../negocio/) | "por que importa e como se sustenta?" | Só o guia | [`negocio/ORIENTACAO.md`](../negocio/ORIENTACAO.md) |

## 1. Big Data Architecture & Data Integration (Dados)

**Papel:** produzir o dado de risco. É a base de todo o resto.

**Entrega:** uma DAG diária no Airflow (INPE e Open-Meteo em paralelo, mais uma tarefa que confere a chegada); camadas Bronze (Auto Loader, sem duplicar), Prata (tipos, regras de qualidade, MERGE) e Ouro (um fato de risco por município e dia, dimensões, 5 consultas SQL com interpretação e um backtest); proteção de dado pessoal com hash.

**O que passa adiante:** a visão `vw_risco_atual` vira o `risco_atual.json`, que o site, a IA e a RPA leem. A coleta roda às 10:30 (Brasília) e traz o **dia anterior**, então a `data` do arquivo é sempre ontem.

**A regra de risco** (pontos por município e dia): umidade mínima abaixo de 30% (2) ou 40% (1); vento de 30 km/h ou mais (2) ou 20 km/h (1); menos de 1 mm de chuva em 3 dias (1); máxima de 35 °C ou mais (1); focos no dia anterior: 100 ou mais (3), 20 ou mais (2), pelo menos 1 (1). Nível: 0 a 2 baixo, 3 a 4 médio, 5 ou mais alto.

**Pendente:** rodar os notebooks com a coleta até ontem e abrir o PR do `risco_atual.json` novo (hoje a data ainda é 03/11).

## 2. MVP: o site

**Papel:** a tela que o cidadão usa. Não é uma disciplina separada, mas é o que o avaliador abre.

**Entrega:** Início (escolher o município e ver o cartão de risco com motivos e medidas), Panorama (os 15 municípios por risco), Como calculamos (a regra e as fontes) e espaços reservados para o assistente e a foto. Funciona sem internet e pode ser instalado no celular. Mostra a data a que o risco se refere e avisa se o dado estiver velho.

**Regras do produto:** nível sempre com cor, texto e ícone; aviso de que a autorização de queima é do órgão ambiental; em risco alto, recomenda não queimar e mostra a Defesa Civil (199) e os Bombeiros (193). Mapa do Pará pronto, mas só aparece quando o JSON trouxer `lat` e `lon`.

**Pendente:** publicar numa URL pública (DevOps) e ligar o assistente e a foto quando as APIs existirem.

## 3. Generative AI for Engineering (Inteligência)

**Papel:** responder perguntas de produtor e gestor sobre o uso do fogo, **com base na lei e citando a fonte**.

**Entrega:** casos de teste com gabarito (incluindo "não consta"); base de conhecimento em trechos com fonte (Lei 14.944/2024, Lei 12.651/2012, Lei 9.605/1998); busca medida por recall; três configurações comparadas em placar (modelo sem contexto, RAG simples e RAG com agente); 5 erros reais com causa e correção.

**O agente tem duas ferramentas:** `busca_lei(pergunta)` (a base de leis) e `consulta_risco(município)` (o `risco_atual.json`). Exemplo: "posso queimar em Portel?" junta o risco do dia com o que a lei diz sobre condições meteorológicas.

**Regra de produto:** orienta, **não dá parecer jurídico**, recusa o que a base não cobre e sempre encaminha ao órgão ambiental.

## 4. Applied Computer Vision (Visão)

**Papel:** **confirmar em campo.** O satélite só vê o foco quando passa e fogo pequeno escapa; a foto do produtor ajuda a triar.

**Entrega:** um modelo treinado de detecção ou classificação de fumaça e fogo, com métricas reais (mAP, precisão, recall, matriz de confusão), relatório em PDF, repositório e vídeo. O produto recebe a imagem e devolve classe e confiança, e **não guarda a foto**.

**Cuidado central:** nuvem, neblina e poeira confundem o modelo; o relatório precisa mostrar esses erros com honestidade. Câmeras fixas são **próximo passo**, não algo a construir agora.

## 5. Robotic Process Automation (Automação)

**Papel:** avisar quem **não abriu o site.** Um fluxo diário lê o risco, decide e envia o alerta.

**Entrega:** fluxo em n8n ou Python que **decide** por município (risco alto) e **repete** para cada município assinante, enviando por Telegram ou e-mail; tratamento de exceções (dado ausente, inválido ou duplicado); logs sem dado sensível; testes de sucesso, decisão e falha; fluxo em BPMN, PDF e vídeo de até 3 minutos.

**Ligação com o resto:** lê o mesmo `risco_atual.json` do site, o que torna a integração verificável.

## 6. Secure DevOps Tools & Cloud Computing (Produção)

**Papel:** colocar o produto no ar, com segurança e monitoramento. É o que faz o link do MVP existir.

**Entrega:** Docker (usuário não root, sem segredo na imagem), Terraform (sem `state` nem `.tfvars` no repositório, sem porta de administração aberta para o mundo), pipeline de GitHub Actions (build, Gitleaks, Semgrep, Trivy, deploy automático) com uma execução barrada e a corrigida; dashboard com as 4 métricas de ouro e um alerta disparado; Ficha Técnica, custo e LGPD.

**Decisão em aberto:** AWS ou Azure.

## 7. Project-Based Maker Lab (Físico)

**Papel:** dado **de campo, em tempo real**, que não depende do satélite.

**Entrega:** evolução do robô com sensor de temperatura e umidade e sensor de fumaça; **decide localmente** (alerta quando a combinação passa do limiar) e envia o evento à API; classificação de risco local (regra mais modelo leve); testes de operação e de falha (sem rede, leitura ruim). Só por GitHub, com vídeo de até 6 minutos e **nomes de todos no README** (sem eles, o grupo fica sem nota).

**Risco principal:** o carrinho não está disponível. Resolver o hardware vem antes de tudo.

## 8. Business Intelligence & Startup Development (Negócio e pitch)

**Papel:** **contar a história** e juntar as outras matérias numa demonstração.

**Entrega:** vídeo de até 5 minutos no YouTube (não listado), com a **demonstração do MVP real na URL pública**. Roteiro: problema com dado do INPE, solução, demo, modelo de negócio, indicadores e ODS, viabilidade e pedido.

**Cuidados:** o modelo de negócio são **hipóteses a validar** (prefeituras e defesas civis, cooperativas, seguradoras; o produtor usa de graça). Falta a evidência de campo (2 ou 3 conversas com usuários) e a fonte e o período do número de focos. ODS: 13 (clima), 2 (agricultura sustentável), 3 (saúde).

## Contratos entre os componentes

| Endereço | Quem fornece | Quem usa |
|---|---|---|
| `risco_atual.json` (hoje) / `GET /risco?municipio_id=` (depois) | Big Data | site, GenAI, RPA |
| `POST /sensor/eventos` | API | robô (Maker) |
| `POST /visao/classificar` | API | site (foto) |
| `POST /assistente/perguntar` | API | site (assistente) |

O dono de cada API é quem combina o formato exato com quem a consome. As APIs ainda não existem; o contrato acima vem de `docs/PROJETO-FogoCerto.md`.

## Regras que valem para todas

- **Nunca** autorizar queima. O sistema informa o risco e encaminha ao órgão ambiental.
- **Nunca** subir senha, token, chave ou dado pessoal. O `.gitignore` bloqueia o mais comum; confira antes de cada commit.
- **Nunca** subir dados grandes (CSV do INPE, modelos, vídeos).
- Uma **branch curta por tarefa** (`rpa/fluxo`, `devops/pipeline`...), pull request e **1 aprovação** antes de juntar na `main`.
- Prints legíveis e legendados; repositório **público** e no ar até uma semana após o encerramento.
- Uma contradição de pontuação do enunciado ainda precisa ser confirmada com os professores (semana de mentoria, 05 a 19/11).
