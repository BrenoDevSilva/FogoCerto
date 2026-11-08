# Databricks notebook source
# MAGIC %md
# MAGIC # FogoCerto - Ouro
# MAGIC Tabelas finais, prontas para o app (MVP) e para as consultas.
# MAGIC - `dim_municipio`: os 15 municipios do recorte
# MAGIC - `dim_tempo`: os dias
# MAGIC - `fato_risco_municipio_dia`: 1 linha por municipio e dia, com o clima, os focos e o **nivel de risco**
# MAGIC - `assinantes_alerta`: quem recebe alerta, com contato protegido (hash e mascara) - LGPD
# MAGIC - `vw_risco_atual`: o que o MVP le (risco do dia mais recente)
# MAGIC
# MAGIC **Regra do risco (transparente, por pontos):**
# MAGIC | fator | pontos |
# MAGIC |---|---|
# MAGIC | umidade minima do dia < 30% (nivel de atencao da defesa civil) / < 40% | 2 / 1 |
# MAGIC | vento maximo >= 30 km/h / >= 20 km/h | 2 / 1 |
# MAGIC | menos de 1 mm de chuva nos ultimos 3 dias | 1 |
# MAGIC | temperatura maxima >= 35 C | 1 |
# MAGIC | focos no municipio **no dia anterior** >= 100 / >= 20 / >= 1 | 3 / 2 / 1 |
# MAGIC
# MAGIC Nivel: 0 a 2 = baixo, 3 a 4 = medio, 5 ou mais = alto.
# MAGIC O risco usa os focos de ONTEM, nunca os de hoje: assim da para testar se ele "acerta" os focos de hoje (backtest).

# COMMAND ----------

P = "workspace.fogocerto"

spark.sql(f"""
CREATE OR REPLACE TABLE {P}.dim_municipio AS
SELECT id_ibge, nome, uf, lat, lon, grupo_foco FROM {P}.ref_municipios
""")

spark.sql(f"""
CREATE OR REPLACE TABLE {P}.dim_tempo AS
SELECT data,
       year(data) AS ano, month(data) AS mes, day(data) AS dia,
       date_format(data, 'EEEE') AS dia_semana,
       CASE WHEN month(data) BETWEEN 6 AND 11 THEN 'seca' ELSE 'chuvosa' END AS periodo
FROM (SELECT DISTINCT data_local AS data FROM {P}.prata_clima_hora)
""")
print("dimensoes criadas")

# COMMAND ----------

# Fato: risco por municipio e dia
spark.sql(f"""
CREATE OR REPLACE TABLE {P}.fato_risco_municipio_dia AS
WITH clima AS (
  SELECT id_ibge, data_local AS data,
         MIN(umidade) AS umidade_min, MAX(temperatura) AS temp_max,
         MAX(vento_kmh) AS vento_max, SUM(chuva_mm) AS chuva_mm
  FROM {P}.prata_clima_hora GROUP BY id_ibge, data_local
),
focos AS (
  SELECT id_ibge, data_local AS data, COUNT(*) AS n_focos, ROUND(SUM(frp), 1) AS frp_total
  FROM {P}.prata_focos GROUP BY id_ibge, data_local
),
base AS (
  SELECT c.*, COALESCE(f.n_focos, 0) AS n_focos, f.frp_total
  FROM clima c LEFT JOIN focos f ON c.id_ibge = f.id_ibge AND c.data = f.data
),
janela AS (
  SELECT *,
         LAG(n_focos) OVER (PARTITION BY id_ibge ORDER BY data) AS focos_ontem,
         SUM(chuva_mm) OVER (PARTITION BY id_ibge ORDER BY data ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS chuva_3d
  FROM base
),
pontos AS (
  SELECT *,
    CASE WHEN umidade_min < 30 THEN 2 WHEN umidade_min < 40 THEN 1 ELSE 0 END AS p_umidade,
    CASE WHEN vento_max >= 30 THEN 2 WHEN vento_max >= 20 THEN 1 ELSE 0 END AS p_vento,
    CASE WHEN chuva_3d < 1 THEN 1 ELSE 0 END AS p_chuva,
    CASE WHEN temp_max >= 35 THEN 1 ELSE 0 END AS p_calor,
    CASE WHEN focos_ontem >= 100 THEN 3 WHEN focos_ontem >= 20 THEN 2 WHEN focos_ontem >= 1 THEN 1 ELSE 0 END AS p_focos
  FROM janela
)
SELECT id_ibge, data,
       n_focos, frp_total, focos_ontem,
       ROUND(umidade_min, 0) AS umidade_min, ROUND(temp_max, 1) AS temp_max,
       ROUND(vento_max, 1) AS vento_max, ROUND(chuva_mm, 1) AS chuva_mm, ROUND(chuva_3d, 1) AS chuva_3d,
       p_umidade + p_vento + p_chuva + p_calor + p_focos AS pontos,
       CASE WHEN p_umidade + p_vento + p_chuva + p_calor + p_focos >= 5 THEN 'alto'
            WHEN p_umidade + p_vento + p_chuva + p_calor + p_focos >= 3 THEN 'medio'
            ELSE 'baixo' END AS nivel_risco,
       concat_ws('; ',
         CASE WHEN p_umidade > 0 THEN concat('umidade minima de ', CAST(ROUND(umidade_min) AS INT), '%') END,
         CASE WHEN p_vento > 0 THEN concat('vento de ate ', CAST(ROUND(vento_max) AS INT), ' km/h') END,
         CASE WHEN p_chuva > 0 THEN 'sem chuva nos ultimos 3 dias' END,
         CASE WHEN p_calor > 0 THEN concat('calor de ', CAST(ROUND(temp_max) AS INT), ' C') END,
         CASE WHEN p_focos > 0 THEN concat(focos_ontem, ' focos ontem no municipio') END
       ) AS fatores,
       current_timestamp() AS atualizado_em
FROM pontos
""")
display(spark.table(f"{P}.fato_risco_municipio_dia").orderBy("data", "id_ibge"))

# COMMAND ----------

# LGPD - quem recebe alerta. DADOS FICTICIOS (o MVP ainda nao tem cadastro real).
# O contato original nunca e gravado: so o hash (para achar a pessoa) e a versao mascarada (para exibir).
from pyspark.sql import functions as F

ficticios = [
    (1, 1505809, "produtor", "produtor.portel@exemplo.com", "91988881234"),
    (2, 1505809, "defesa_civil", "defesacivil.portel@exemplo.com", "91977775678"),
    (3, 1508159, "produtor", "produtor.uruara@exemplo.com", "93966664321"),
    (4, 1506807, "defesa_civil", "defesacivil.santarem@exemplo.com", "93955558765"),
    (5, 1502400, "produtor", "produtor.castanhal@exemplo.com", "91944441111"),
]
a = spark.createDataFrame(ficticios, "id_assinante int, id_ibge int, perfil string, email string, telefone string")
a = (a.withColumn("email_hash", F.sha2(F.lower(F.trim("email")), 256))
      .withColumn("telefone_mascarado",
                  F.concat(F.lit("("), F.substring("telefone", 1, 2), F.lit(") *****-"), F.substring("telefone", -4, 4)))
      .drop("email", "telefone"))
a.write.mode("overwrite").saveAsTable(f"{P}.assinantes_alerta")
display(spark.table(f"{P}.assinantes_alerta"))

# COMMAND ----------

# Tabela que o MVP usa: risco do dia mais recente de cada municipio
spark.sql(f"""
CREATE OR REPLACE VIEW {P}.vw_risco_atual AS
SELECT m.id_ibge, m.nome, m.uf, f.data, f.nivel_risco, f.pontos, f.fatores,
       f.focos_ontem, f.umidade_min, f.vento_max, f.temp_max, f.chuva_3d, f.atualizado_em
FROM {P}.fato_risco_municipio_dia f
JOIN {P}.dim_municipio m ON m.id_ibge = f.id_ibge
WHERE f.data = (SELECT MAX(data) FROM {P}.fato_risco_municipio_dia)
""")
display(spark.table(f"{P}.vw_risco_atual").orderBy(F.desc("pontos")))

# COMMAND ----------

# MAGIC %md
# MAGIC ## As 5 consultas

# COMMAND ----------

# Consulta 1 - O que o app mostra hoje: risco de cada municipio no dia mais recente
display(spark.sql(f"""
SELECT nome, nivel_risco, pontos, fatores
FROM {P}.vw_risco_atual
ORDER BY pontos DESC, nome
"""))

# COMMAND ----------

# Consulta 2 - Ranking: municipios com mais focos (fogos unicos) no periodo
display(spark.sql(f"""
SELECT m.nome, m.grupo_foco, SUM(f.n_focos) AS focos_no_periodo, ROUND(SUM(f.frp_total), 0) AS potencia_total
FROM {P}.fato_risco_municipio_dia f JOIN {P}.dim_municipio m ON m.id_ibge = f.id_ibge
GROUP BY m.nome, m.grupo_foco
ORDER BY focos_no_periodo DESC
"""))

# COMMAND ----------

# Consulta 3 - Dia a dia no recorte: focos x umidade minima media
display(spark.sql(f"""
SELECT t.data, t.dia_semana,
       SUM(f.n_focos) AS focos,
       ROUND(AVG(f.umidade_min), 0) AS umidade_min_media,
       SUM(CASE WHEN f.nivel_risco = 'alto' THEN 1 ELSE 0 END) AS municipios_em_risco_alto
FROM {P}.fato_risco_municipio_dia f JOIN {P}.dim_tempo t ON t.data = f.data
GROUP BY t.data, t.dia_semana
ORDER BY t.data
"""))

# COMMAND ----------

# Consulta 4 - O clima explica o fogo? Focos medios por faixa de umidade minima
display(spark.sql(f"""
SELECT CASE WHEN umidade_min < 30 THEN '1) abaixo de 30%'
            WHEN umidade_min < 40 THEN '2) 30 a 40%'
            WHEN umidade_min < 50 THEN '3) 40 a 50%'
            ELSE '4) 50% ou mais' END AS faixa_umidade,
       COUNT(*) AS dias_municipio,
       ROUND(AVG(n_focos), 1) AS focos_medios_por_dia
FROM {P}.fato_risco_municipio_dia
GROUP BY 1 ORDER BY 1
"""))

# COMMAND ----------

# Consulta 5 - IMPACTO (backtest): o nivel de risco calculado de manha "acerta" onde houve fogo no dia?
# Ignora o 1o dia de cada municipio (sem "ontem" para comparar).
display(spark.sql(f"""
SELECT nivel_risco,
       COUNT(*) AS dias_municipio,
       ROUND(AVG(n_focos), 1) AS focos_medios_no_dia,
       ROUND(100 * AVG(CASE WHEN n_focos > 0 THEN 1 ELSE 0 END), 0) AS pct_dias_com_fogo
FROM {P}.fato_risco_municipio_dia
WHERE focos_ontem IS NOT NULL
GROUP BY nivel_risco
ORDER BY CASE nivel_risco WHEN 'alto' THEN 1 WHEN 'medio' THEN 2 ELSE 3 END
"""))
