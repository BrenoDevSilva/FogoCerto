# Databricks notebook source
# MAGIC %md
# MAGIC # FogoCerto - Exportacao para o MVP e para a IA
# MAGIC Gera `risco_atual.json` a partir da `vw_risco_atual` (Ouro). Rode depois do `03_ouro`.
# MAGIC Depois baixe o arquivo em Catalog > workspace > fogocerto > Volumes > exportacao
# MAGIC e coloque em `site/public/data/risco_atual.json` no repositorio (via pull request).
# MAGIC Nao tem dado pessoal: so municipio, risco e clima.

# COMMAND ----------

import json
import datetime
import decimal
from pyspark.sql import functions as F

P = "workspace.fogocerto"
spark.sql(f"CREATE VOLUME IF NOT EXISTS {P}.exportacao")

colunas = ["id_ibge", "nome", "uf", "lat", "lon", "data", "nivel_risco", "pontos", "fatores", "focos_ontem",
           "umidade_min", "vento_max", "temp_max", "chuva_3d", "atualizado_em"]
linhas = (spark.table(f"{P}.vw_risco_atual")
          .select(*[c for c in colunas if c != "atualizado_em"],
                  # o Databricks grava em UTC; o site mostra o horario como vem, entao exportamos em Brasilia
                  F.from_utc_timestamp("atualizado_em", "America/Sao_Paulo").alias("atualizado_em"))
          .orderBy(F.desc("pontos"), "nome")
          .collect())

def limpar(v):
    if isinstance(v, decimal.Decimal):
        return float(v)
    if isinstance(v, (datetime.date, datetime.datetime)):
        return v.isoformat()
    return v

dados = [{k: limpar(v) for k, v in r.asDict().items()} for r in linhas]
caminho = f"/Volumes/workspace/fogocerto/exportacao/risco_atual.json"
with open(caminho, "w", encoding="utf-8") as f:
    json.dump(dados, f, ensure_ascii=False, indent=2)

print(f"{len(dados)} municipios exportados para {caminho}")
display(spark.read.option("multiLine", "true").json(caminho))
