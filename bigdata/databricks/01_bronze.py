# Databricks notebook source
# MAGIC %md
# MAGIC # FogoCerto - Bronze
# MAGIC Le os arquivos que subimos no Volume `chegada` e grava do jeito que vieram,
# MAGIC com o nome do arquivo e a hora da ingestao. Auto Loader so le arquivo novo:
# MAGIC rodar de novo nao duplica.

# COMMAND ----------

# Celula 1 - prepara o lugar (rode esta primeiro, antes de subir os arquivos)
CAT = "workspace"
SCH = "fogocerto"
VOL = f"/Volumes/{CAT}/{SCH}/chegada"
CK = f"/Volumes/{CAT}/{SCH}/checkpoints"

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CAT}.{SCH}")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {CAT}.{SCH}.chegada")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {CAT}.{SCH}.checkpoints")
dbutils.fs.mkdirs(f"{VOL}/focos")
dbutils.fs.mkdirs(f"{VOL}/clima")
print("Pronto. Suba os arquivos em", VOL + "/focos", "e", VOL + "/clima")

# COMMAND ----------

# Celula 2 - contagem ANTES
def contar(t):
    try:
        return spark.table(t).count()
    except Exception:
        return 0

T_FOCOS = f"{CAT}.{SCH}.bronze_focos"
T_CLIMA = f"{CAT}.{SCH}.bronze_clima"
antes = {"bronze_focos": contar(T_FOCOS), "bronze_clima": contar(T_CLIMA)}
print("ANTES:", antes)

# COMMAND ----------

# Celula 3 - ingestao com Auto Loader (so arquivos novos)
from pyspark.sql import functions as F

(spark.readStream.format("cloudFiles")
    .option("cloudFiles.format", "csv")
    .option("header", "true")
    .option("cloudFiles.schemaLocation", f"{CK}/focos_schema")
    .load(f"{VOL}/focos")
    .withColumn("_arquivo", F.col("_metadata.file_path"))
    .withColumn("_ingerido_em", F.current_timestamp())
    .writeStream
    .option("checkpointLocation", f"{CK}/focos")
    .trigger(availableNow=True)
    .toTable(T_FOCOS)
    .awaitTermination())

(spark.readStream.format("cloudFiles")
    .option("cloudFiles.format", "json")
    .option("multiLine", "true")
    .option("cloudFiles.schemaLocation", f"{CK}/clima_schema")
    .load(f"{VOL}/clima")
    .withColumn("_arquivo", F.col("_metadata.file_path"))
    .withColumn("_ingerido_em", F.current_timestamp())
    .writeStream
    .option("checkpointLocation", f"{CK}/clima")
    .trigger(availableNow=True)
    .toTable(T_CLIMA)
    .awaitTermination())

# COMMAND ----------

# Celula 4 - contagem DEPOIS (print disso vai pro relatorio)
depois = {"bronze_focos": contar(T_FOCOS), "bronze_clima": contar(T_CLIMA)}
print("ANTES:  ", antes)
print("DEPOIS: ", depois)

# COMMAND ----------

# Celula 5 - quantas linhas vieram de cada arquivo (prova que nao duplicou)
display(spark.table(T_FOCOS).groupBy("_arquivo").count().orderBy("_arquivo"))
display(spark.table(T_CLIMA).groupBy("_arquivo").count().orderBy("_arquivo"))
