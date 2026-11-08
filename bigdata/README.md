# FogoCerto · Big Data Architecture & Data Integration

Pipeline que coleta dados reais de focos de calor (INPE) e clima (Open-Meteo), trata em camadas Bronze, Prata e Ouro no Databricks e entrega ao MVP a tabela de risco de fogo por município e dia.

**Integrantes:** ver [README principal](../README.md#integrantes).

## Perguntas que o MVP responde

1. Qual o risco de fogo hoje no meu município, e por quê?
2. Quantos focos houve ontem perto de mim?
3. Quais municípios do recorte estão em risco alto hoje?

## Fontes

| Fonte | Origem | Formato | Frequência |
|---|---|---|---|
| Focos de calor | INPE, dados abertos (`dataserver-coids.inpe.br`, CSV diário; mensal para dias antigos) | CSV | diária |
| Clima por hora | Open-Meteo (`api.open-meteo.com`, sem chave): umidade, temperatura, vento e chuva | JSON | diária |
| Recorte | 15 municípios do Pará com código IBGE (`config/municipios.json`) | JSON | fixo |

## Arquitetura

```
INPE + Open-Meteo -> Airflow (gs_coleta) -> chegada/ -> upload manual em lotes -> Volume
  -> Bronze (Auto Loader) -> Prata (tipos, regras, MERGE) -> Ouro (fato + dimensões) -> MVP
```

O Databricks Free Edition não se conecta ao Airflow: os arquivos de `chegada/` sobem ao Volume pela interface, em lotes.

## Estrutura

```
dags/gs_coleta.py        DAG diária: focos e clima em paralelo, conferência da chegada, notificação
config/                  recorte de municípios e exemplo das Variables do Airflow
databricks/01_bronze.py  ingestão incremental com Auto Loader
databricks/02_prata.py   tipos, 3 regras de qualidade, tratamento de inválidos, MERGE
databricks/03_ouro.py    dim_municipio, dim_tempo, fato_risco_municipio_dia, LGPD, 5 consultas
amostras/                um pouco de cada fonte
docker-compose.yml       Airflow 3 local
```

## Como reproduzir

**1. Airflow (coleta)**

```bash
cd bigdata
cp config/variables.example.json config/variables.json
docker compose up -d
# espere ~2 min
docker compose exec airflow airflow variables import /opt/airflow/config/variables.json
docker compose exec airflow cat /opt/airflow/simple_auth_manager_passwords.json.generated
```

Acesse http://localhost:8080 (usuário `admin`, senha do comando acima), ative a DAG `gs_coleta`. Com `catchup`, ela baixa os dias desde `start_date`. Os arquivos aparecem em `chegada/focos/` e `chegada/clima/`.

**2. Databricks (lakehouse)**

1. Importe os 3 notebooks de `databricks/`.
2. Rode a célula 1 do `01_bronze` (cria schema e Volume).
3. Suba os arquivos de `chegada/focos` e `chegada/clima` para o Volume `workspace.fogocerto.chegada` (lote 1); rode o resto do `01_bronze`.
4. Rode `02_prata` e `03_ouro`.
5. Suba os arquivos novos (lote 2) e rode de novo os 3 notebooks: só os arquivos novos entram, nada duplica.

## Regras de qualidade (Prata)

- **R1:** foco sem campo obrigatório (id, data/hora, município, latitude, longitude) é barrado.
- **R2:** detecção repetida do mesmo fogo (mesmo id, ou vários satélites no mesmo lugar ~1 km na mesma hora) é barrada; fica 1 por fogo.
- **R3:** leitura de clima impossível (umidade fora de 0 a 100, vento ou chuva negativos, temperatura fora de -10 a 50 °C) é barrada.
- Tratamento: códigos negativos de "sem dado" do INPE (ex.: -999 em dias sem chuva) viram nulo.

## Regra de risco (Ouro)

Pontos por município e dia: umidade mínima < 30% (2) ou < 40% (1); vento ≥ 30 km/h (2) ou ≥ 20 km/h (1); menos de 1 mm de chuva em 3 dias (1); máxima ≥ 35 °C (1); focos no dia anterior ≥ 100 (3), ≥ 20 (2) ou ≥ 1 (1). Nível: 0 a 2 baixo, 3 a 4 médio, 5+ alto. O risco usa os focos de ontem, nunca os do próprio dia, para permitir o backtest.

## LGPD

A tabela `assinantes_alerta` guarda só o hash SHA-256 do e-mail e o telefone mascarado. Os dados atuais são **fictícios**. O MVP lê `vw_risco_atual`, que não tem dado pessoal.
