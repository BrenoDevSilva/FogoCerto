# Contexto: FogoCerto, componente Big Data (GS FIAP CitizenTech 2026.2)

Use este arquivo como ponto de partida do repositório. Entrega final: **19/11/2026 às 23h55** (meta interna: 18/11). Hoje é 07/11.

## Produto em uma frase
FogoCerto avisa, a cada manhã, produtores rurais e a defesa civil de um recorte de municípios se há risco de fogo hoje e se é seguro e permitido fazer queima controlada. O componente Big Data entrega ao MVP a tabela Ouro de risco por município e dia.

## Fontes (todas abertas, sem token)
- **INPE Queimadas:** focos de calor, CSV e GeoJSON das últimas 24 e 48 horas pela API de dados abertos, histórico em BDQueimadas desde 1998. Página: inpe.br/queimadas/dados-abertos. **A verificar:** URL exata do arquivo diário e as colunas reais do CSV. Pelo catálogo, cada foco traz data, satélite, município, estado, precipitação, dias sem chuva e risco de fogo.
- **Open-Meteo:** umidade, vento, temperatura e chuva (previsão e histórico), sem chave.
- **IBGE:** códigos e malha de municípios.
- Recorte: 10 a 20 municípios, **ainda a definir** (escolher onde há focos nos dias de teste).

## Requisitos da disciplina (resumo do enunciado)
1. Mínimo 2 fontes, ao menos 1 API ou dado aberto.
2. DAG Airflow agendada, baixa cada fonte e salva em `chegada/`, um arquivo por coleta com a data no nome.
3. Ao menos 2 tarefas em paralelo e 1 tarefa que confere a chegada dos arquivos. Chaves e configurações em Airflow Variables, nunca no código.
4. Enviar ao Volume do Databricks em pelo menos 2 lotes de dias de coleta diferentes (upload pela interface).
5. Bronze com Auto Loader ou COPY INTO: no 2º lote só entram arquivos novos, e rodar de novo não duplica. Registrar contagens antes e depois.
6. Prata: tipos corretos, nulos e inválidos tratados, MERGE pela chave e 3 regras de qualidade com o total barrado por cada uma.
7. Ouro: 1 tabela fato e ao menos 2 dimensões, mais 5 consultas SQL com interpretação (1 de impacto, o backtest).
8. Proteger dados pessoais na Ouro (máscara ou hash) e mostrar qual tabela da Ouro o MVP usa.
9. Repositório público com README (integrantes, arquitetura, passo a passo para reproduzir).

## Pontuação (nota 0 a 10)
Fontes 0,5 · DAG 1,0 · paralelismo, verificação e chaves 0,5 · 2 lotes 0,5 · Bronze 1,5 · Prata 2,0 · Ouro e 5 SQL 2,5 · LGPD e uso pelo MVP 1,0 · README 0,5.

## O que tira pontos
- Nome completo ou RM de integrante ausente no relatório: -0,5.
- Chaves, senhas ou dados pessoais reais no repositório: -1,0.
- Prints ilegíveis, sem legenda ou relatório fora de ordem: até -1,0.
- Repositório privado, vazio ou fora do ar na correção: itens dependentes valem zero.
- Exemplo do enunciado (Open-Meteo de temperatura e precipitação) entregue sem adaptar: itens 01 e 07 valem zero. Nossa fonte principal é o INPE e o clima entra como variável de risco; deixar isso explícito.

## Estrutura do repositório
```
dags/        DAGs do Airflow
databricks/  notebooks e SQL (Bronze, Prata, Ouro, consultas)
amostras/    um pouco de cada fonte
README.md    integrantes (nome completo e RM), arquitetura, como reproduzir
```

## Relatório em PDF (ordem fixa)
1 Nome e RM · 2 Produto em uma frase e perguntas que o MVP responde · 3 Diagrama do fluxo da fonte ao MVP · 4 Tabela de fontes (origem, formato, frequência) · 5 Requisitos 01 a 09, cada um com print e explicação curta · 6 Prints do Airflow (Graph e Grid com execuções concluídas) · 7 Contagens da Bronze antes e depois do 2º lote e da 2ª execução · 8 As 5 consultas SQL com resultado e interpretação · 9 Conclusão técnica e link do repositório.

## Design da DAG
- `schedule="@daily"`, `catchup=True` com `start_date` alguns dias atrás, para gerar várias execuções concluídas.
- Tarefas: `inicio` → [`coletar_focos_inpe`, `coletar_clima_open_meteo`] em paralelo → `conferir_chegada` (falha se faltar arquivo) → notificação.
- Variables: lista de municípios (id, nome, lat, lon), URLs, token de notificação (Telegram).
- Saída: `chegada/focos/focos_AAAA-MM-DD.csv` e `chegada/clima/clima_AAAA-MM-DD.json`.
- Observação: o Databricks Free Edition não conecta ao Airflow, então os arquivos sobem ao Volume manualmente, em lotes.

## Modelo Ouro (proposta)
- `fato_risco_municipio_dia`: município, data, nº de focos, umidade mínima, vento máximo, dias sem chuva, nível de risco.
- `dim_municipio` e `dim_tempo`.
- Dados pessoais (contato de quem recebe alerta, se existir) com hash.
- Consulta de impacto: quantos focos ocorreram em dias classificados como risco alto (backtest).

## Contrato com o MVP
`GET /risco?municipio_id=` devolve nível, fatores, focos nas últimas 24 horas e horário da atualização, lendo a tabela Ouro de risco.

## Cronograma
- 07 a 08/11: repositório, recorte, teste manual das fontes, Airflow local.
- 09/11: DAG coletando, lote 1 no Volume, Bronze.
- 10 a 11/11: Prata (MERGE, 3 regras). Lote 2 de outro dia.
- 12 a 15/11: Ouro, 5 consultas, mascaramento, contrato com a API.
- 16 a 18/11: README, prints legendados, PDF. Entregar com folga.

## Primeiras tarefas
1. Criar a estrutura do repositório e o README com nomes e RMs (pendente: lista da equipe).
2. Baixar à mão o CSV do INPE, registrar colunas reais em `amostras/` e definir a chave do MERGE.
3. Definir o recorte e gerar o arquivo de configuração de municípios (id, nome, lat, lon).
4. Subir o Airflow 3 em Docker compose e escrever a DAG `gs_coleta`.
5. Criar o schema e o Volume no Databricks e o notebook da Bronze.

## Pendências e riscos
- Recorte de municípios ainda não definido.
- URL e colunas do INPE a confirmar.
- Se o recorte não tiver focos nos dias de teste, usar o histórico do BDQueimadas para o backtest.
