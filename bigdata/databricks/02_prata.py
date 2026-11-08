# Databricks notebook source
# MAGIC %md
# MAGIC # FogoCerto - Prata
# MAGIC Pega a Bronze (dado cru) e deixa limpo: tipos certos, valores invalidos tratados,
# MAGIC so os 15 municipios do recorte, e grava com MERGE (rodar de novo nao duplica).
# MAGIC
# MAGIC **Regras de qualidade (linha que falha e barrada):**
# MAGIC - R1: foco sem campo obrigatorio (id, data/hora, municipio, latitude ou longitude)
# MAGIC - R2: deteccao repetida do mesmo fogo (mesmo id, ou mesma posicao ~1 km na mesma hora)
# MAGIC - R3: clima impossivel (umidade fora de 0-100, vento ou chuva negativos, temperatura fora de -10 a 50 C)
# MAGIC
# MAGIC **Tratamento (linha nao e barrada, so o valor vira nulo):** o INPE usa numeros negativos
# MAGIC como codigo de "sem dado" (ex.: -999 em dias sem chuva). Esses valores viram nulo.

# COMMAND ----------

# Celula 1 - configuracao e tabela do recorte (15 municipios)
from pyspark.sql import functions as F

P = "workspace.fogocerto"

def tc(col, tipo):
    """converte texto para o tipo; se nao der, vira nulo (em vez de quebrar)"""
    return F.expr(f"try_cast(trim({col}) AS {tipo})")

recorte = [
    (1505809, "Portel", -3.0655, -50.5757, "alto"),
    (1505486, "Pacajá", -3.6151, -50.5098, "alto"),
    (1508159, "Uruará", -3.3352, -54.0348, "alto"),
    (1500503, "Almeirim", -1.1768, -52.9294, "alto"),
    (1504802, "Monte Alegre", -1.5093, -54.2247, "alto"),
    (1506005, "Prainha", -2.3419, -53.7476, "alto"),
    (1505304, "Oriximiná", 0.6447, -55.9506, "alto"),
    (1506807, "Santarém", -2.7885, -54.5095, "alto"),
    (1503606, "Itaituba", -4.9311, -55.9300, "medio"),
    (1503705, "Itupiranga", -5.0422, -49.8844, "medio"),
    (1508100, "Tucuruí", -3.8459, -49.9149, "medio"),
    (1503804, "Jacundá", -4.4097, -49.1312, "medio"),
    (1502400, "Castanhal", -1.2484, -47.8975, "baixo"),
    (1506708, "Santana do Araguaia", -9.4296, -50.6708, "baixo"),
    (1507904, "Soure", -0.3219, -48.5364, "baixo"),
]
ref = (spark.createDataFrame(recorte, "id_ibge int, nome string, lat double, lon double, grupo_foco string")
       .withColumn("uf", F.lit("PA")))
ref.write.mode("overwrite").saveAsTable(f"{P}.ref_municipios")
ids_recorte = [r[0] for r in recorte]
print("recorte salvo:", len(ids_recorte), "municipios")

# COMMAND ----------

# Celula 2 - FOCOS: tipos, regras R1 e R2, tratamento dos codigos de "sem dado"
b = spark.table(f"{P}.bronze_focos")
total_bronze = b.count()

f = b.select(
    F.col("id").alias("id_foco"),
    tc("lat", "double").alias("lat"),
    tc("lon", "double").alias("lon"),
    F.expr("try_to_timestamp(trim(data_hora_gmt), 'yyyy-MM-dd HH:mm:ss')").alias("data_hora_utc"),
    F.col("satelite"),
    F.col("municipio"),
    F.col("estado"),
    tc("municipio_id", "int").alias("id_ibge"),
    tc("numero_dias_sem_chuva", "double").alias("dias_sem_chuva"),
    tc("precipitacao", "double").alias("precipitacao"),
    tc("risco_fogo", "double").alias("risco_fogo"),
    F.col("bioma"),
    tc("frp", "double").alias("frp"),
    F.col("_arquivo"),
)

# R1 - campo obrigatorio faltando
falta = (F.col("id_foco").isNull() | F.col("data_hora_utc").isNull() | F.col("id_ibge").isNull()
         | F.col("lat").isNull() | F.col("lon").isNull())
r1_barrados = f.filter(falta).count()
f = f.filter(~falta)

# R2 - deteccao repetida do mesmo fogo: mesmo id, ou varios satelites vendo o mesmo
# lugar (~1 km) na mesma hora. Fica 1 deteccao por fogo (a com maior potencia, frp).
from pyspark.sql.window import Window
antes_r2 = f.count()
f = f.dropDuplicates(["id_foco"])
f = (f.withColumn("_lat2", F.round("lat", 2))
      .withColumn("_lon2", F.round("lon", 2))
      .withColumn("_hora", F.date_trunc("hour", "data_hora_utc")))
w = Window.partitionBy("_lat2", "_lon2", "_hora").orderBy(F.col("frp").desc_nulls_last(), F.col("id_foco"))
f = (f.withColumn("_n", F.row_number().over(w))
      .filter(F.col("_n") == 1)
      .drop("_n", "_lat2", "_lon2", "_hora"))
r2_barrados = antes_r2 - f.count()

# Tratamento: codigos negativos de "sem dado" viram nulo (a linha continua)
trat_dias = f.filter(F.col("dias_sem_chuva") < 0).count()
trat_risco = f.filter((F.col("risco_fogo") < 0) | (F.col("risco_fogo") > 1)).count()
trat_chuva = f.filter(F.col("precipitacao") < 0).count()
f = (f
     .withColumn("dias_sem_chuva", F.when(F.col("dias_sem_chuva") >= 0, F.col("dias_sem_chuva")))
     .withColumn("risco_fogo", F.when(F.col("risco_fogo").between(0, 1), F.col("risco_fogo")))
     .withColumn("precipitacao", F.when(F.col("precipitacao") >= 0, F.col("precipitacao")))
     .withColumn("data_local", F.to_date(F.from_utc_timestamp("data_hora_utc", "America/Sao_Paulo"))))

# So o recorte
antes_recorte = f.count()
f = f.filter(F.col("id_ibge").isin(ids_recorte))
fora_recorte = antes_recorte - f.count()

f.createOrReplaceTempView("novos_focos")
print("focos prontos para o MERGE:", f.count())

# COMMAND ----------

# Celula 3 - MERGE dos focos (chave: id_foco)
if not spark.catalog.tableExists(f"{P}.prata_focos"):
    f.limit(0).write.saveAsTable(f"{P}.prata_focos")

display(spark.sql(f"""
MERGE INTO {P}.prata_focos AS t
USING novos_focos AS s
ON t.id_foco = s.id_foco
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
"""))

# COMMAND ----------

# Celula 4 - CLIMA: abre o JSON (1 linha por municipio e hora) e regra R3
c = spark.table(f"{P}.bronze_clima")
# A Bronze guardou "municipios" como texto; aqui transformamos o texto em lista
schema_mun = ("array<struct<id_ibge:int, nome:string, hourly:struct<time:array<string>, "
              "relative_humidity_2m:array<double>, temperature_2m:array<double>, "
              "wind_speed_10m:array<double>, precipitation:array<double>>>>")
m = c.select("_arquivo", F.explode(F.from_json("municipios", schema_mun)).alias("m"))
h = m.select("_arquivo", "m", F.posexplode("m.hourly.time").alias("pos", "hora_txt"))
h = h.select(
    F.col("m.id_ibge").cast("int").alias("id_ibge"),
    F.expr("try_to_timestamp(hora_txt, \"yyyy-MM-dd'T'HH:mm\")").alias("data_hora_local"),
    F.expr("try_cast(m.hourly.relative_humidity_2m[pos] AS double)").alias("umidade"),
    F.expr("try_cast(m.hourly.temperature_2m[pos] AS double)").alias("temperatura"),
    F.expr("try_cast(m.hourly.wind_speed_10m[pos] AS double)").alias("vento_kmh"),
    F.expr("try_cast(m.hourly.precipitation[pos] AS double)").alias("chuva_mm"),
    "_arquivo",
)
h = h.withColumn("data_local", F.to_date("data_hora_local"))
h = h.dropDuplicates(["id_ibge", "data_hora_local"])

# R3 - leitura de clima impossivel ou faltando
ok = (F.col("umidade").between(0, 100) & (F.col("vento_kmh") >= 0) & (F.col("chuva_mm") >= 0)
      & F.col("temperatura").between(-10, 50) & F.col("data_hora_local").isNotNull())
ok = F.coalesce(ok, F.lit(False))
r3_barrados = h.filter(~ok).count()
h = h.filter(ok)
h.createOrReplaceTempView("novo_clima")
print("horas de clima prontas para o MERGE:", h.count())

# COMMAND ----------

# Celula 5 - MERGE do clima (chave: municipio + hora)
if not spark.catalog.tableExists(f"{P}.prata_clima_hora"):
    h.limit(0).write.saveAsTable(f"{P}.prata_clima_hora")

display(spark.sql(f"""
MERGE INTO {P}.prata_clima_hora AS t
USING novo_clima AS s
ON t.id_ibge = s.id_ibge AND t.data_hora_local = s.data_hora_local
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
"""))

# COMMAND ----------

# Celula 6 - RELATORIO DE QUALIDADE (print disso vai pro relatorio)
relatorio = spark.createDataFrame([
    ("Focos lidos da Bronze", total_bronze),
    ("R1 barrados: campo obrigatorio faltando", r1_barrados),
    ("R2 barrados: deteccao repetida do mesmo fogo", r2_barrados),
    ("R3 barrados: clima impossivel", r3_barrados),
    ("Tratados: dias sem chuva com codigo negativo -> nulo", trat_dias),
    ("Tratados: risco de fogo fora de 0-1 -> nulo", trat_risco),
    ("Tratados: precipitacao negativa -> nulo", trat_chuva),
    ("Fora do recorte (outros municipios do Brasil)", fora_recorte),
    ("Total na prata_focos", spark.table(f"{P}.prata_focos").count()),
    ("Total na prata_clima_hora", spark.table(f"{P}.prata_clima_hora").count()),
], "item string, quantidade long")
display(relatorio)
(relatorio.withColumn("executado_em", F.current_timestamp())
 .write.mode("append").saveAsTable(f"{P}.log_qualidade"))
