"""FogoCerto - coleta diaria (INPE focos + Open-Meteo clima) para chegada/.

inicio -> [coletar_focos_inpe || coletar_clima_open_meteo] -> conferir_chegada -> notificar

Tudo que e configuracao/chave vem de Airflow Variables (config/variables.json).
Cada execucao busca o DIA ANTERIOR a data da execucao: o arquivo diario do INPE
do dia D so fica completo as ~09:05 de D+1.
"""
from __future__ import annotations

import csv
import json
import logging
import os

import pendulum
import requests
from airflow.exceptions import AirflowFailException
from airflow.providers.standard.operators.empty import EmptyOperator
from airflow.sdk import DAG, Variable, task

log = logging.getLogger(__name__)


def _alvo(data_interval_end) -> pendulum.Date:
    """Dia a coletar = dia anterior ao fim do intervalo da execucao."""
    return data_interval_end.subtract(days=1).date()


def _dir(sub: str) -> str:
    base = Variable.get("gs_chegada_dir")
    path = os.path.join(base, sub)
    os.makedirs(path, exist_ok=True)
    return path


def _path_focos(alvo) -> str:
    return os.path.join(_dir("focos"), f"focos_diario_br_{alvo:%Y%m%d}.csv")


def _path_clima(alvo) -> str:
    return os.path.join(_dir("clima"), f"clima_{alvo:%Y-%m-%d}.json")


def _baixar(url: str, destino: str) -> int:
    """Baixa url para destino sem deixar arquivo pela metade. Devolve o status HTTP."""
    with requests.get(url, stream=True, timeout=600) as r:
        if r.status_code != 200:
            return r.status_code
        tmp = f"{destino}.{os.getpid()}.tmp"
        with open(tmp, "wb") as f:
            for parte in r.iter_content(1 << 20):
                f.write(parte)
    if os.path.getsize(tmp) == 0:
        os.remove(tmp)
        return 204
    os.replace(tmp, destino)
    return 200


with DAG(
    dag_id="gs_coleta",
    description="Coleta diaria de focos (INPE) e clima (Open-Meteo) do recorte FogoCerto",
    # 13:30 UTC = 10:30 em Sao Paulo, depois da publicacao do arquivo do INPE (~09:05)
    schedule="30 13 * * *",
    start_date=pendulum.datetime(2026, 9, 1, tz="UTC"),
    catchup=True,
    max_active_runs=2,
    default_args={"retries": 2, "retry_delay": pendulum.duration(minutes=2)},
    tags=["fogocerto", "gs"],
) as dag:

    inicio = EmptyOperator(task_id="inicio")

    @task
    def coletar_focos_inpe(data_interval_end=None):
        """Baixa o CSV diario do INPE. O INPE so guarda os diarios recentes:
        se o diario nao existir mais (404), usa o arquivo MENSAL do INPE e separa so o dia."""
        alvo = _alvo(data_interval_end)
        destino = _path_focos(alvo)
        url = f"{Variable.get('gs_inpe_url_base')}/focos_diario_br_{alvo:%Y%m%d}.csv"
        log.info("GET %s", url)
        status = _baixar(url, destino)
        if status == 200:
            log.info("salvo %s", destino)
            return destino
        if status != 404:
            raise AirflowFailException(f"INPE respondeu {status} para {url}")

        # diario nao existe mais -> usa o mensal (baixado uma vez e guardado em _cache_mensal)
        mensal = os.path.join(_dir("_cache_mensal"), f"focos_mensal_br_{alvo:%Y%m}.csv")
        if not os.path.exists(mensal):
            url_m = f"{Variable.get('gs_inpe_url_mensal')}/focos_mensal_br_{alvo:%Y%m}.csv"
            log.info("diario indisponivel, baixando mensal %s", url_m)
            st = _baixar(url_m, mensal)
            if st != 200:
                raise AirflowFailException(f"INPE respondeu {st} para {url_m}")
        dia = f"{alvo:%Y-%m-%d}"
        tmp = f"{destino}.{os.getpid()}.tmp"
        n = 0
        with open(mensal, encoding="utf-8", newline="") as fi, open(tmp, "w", encoding="utf-8", newline="") as fo:
            cab = fi.readline()
            fo.write(cab)
            idx = cab.strip().split(",").index("data_hora_gmt")
            for linha in fi:
                if linha.split(",")[idx].startswith(dia):
                    fo.write(linha)
                    n += 1
        if n == 0:
            os.remove(tmp)
            raise AirflowFailException(f"nenhum foco de {dia} no arquivo mensal")
        os.replace(tmp, destino)
        log.info("salvo %s a partir do mensal (%d focos)", destino, n)
        return destino

    @task
    def coletar_clima_open_meteo(data_interval_end=None):
        alvo = _alvo(data_interval_end)
        muns = Variable.get("gs_municipios", deserialize_json=True)
        params = {
            "latitude": ",".join(str(m["lat"]) for m in muns),
            "longitude": ",".join(str(m["lon"]) for m in muns),
            "start_date": f"{alvo:%Y-%m-%d}",
            "end_date": f"{alvo:%Y-%m-%d}",
            "hourly": "relative_humidity_2m,temperature_2m,wind_speed_10m,precipitation",
            "timezone": "America/Sao_Paulo",
        }
        resp = requests.get(Variable.get("gs_open_meteo_url"), params=params, timeout=120)
        if resp.status_code != 200:
            raise AirflowFailException(f"Open-Meteo respondeu {resp.status_code}: {resp.text[:200]}")
        dados = resp.json()
        if isinstance(dados, dict):  # um unico ponto
            dados = [dados]
        if len(dados) != len(muns):
            raise AirflowFailException(f"esperava {len(muns)} pontos, veio {len(dados)}")
        saida = {
            "data": f"{alvo:%Y-%m-%d}",
            "municipios": [
                {"id_ibge": m["id_ibge"], "nome": m["nome"], "hourly": d["hourly"]}
                for m, d in zip(muns, dados)
            ],
        }
        destino = _path_clima(alvo)
        tmp = destino + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(saida, f, ensure_ascii=False)
        os.replace(tmp, destino)
        log.info("salvo %s (%d municipios)", destino, len(muns))
        return destino

    @task
    def conferir_chegada(data_interval_end=None):
        alvo = _alvo(data_interval_end)
        muns = Variable.get("gs_municipios", deserialize_json=True)
        focos, clima = _path_focos(alvo), _path_clima(alvo)
        for p in (focos, clima):
            if not os.path.exists(p) or os.path.getsize(p) == 0:
                raise AirflowFailException(f"arquivo ausente ou vazio: {p}")
        with open(focos, encoding="utf-8", errors="replace", newline="") as f:
            leitor = csv.reader(f)
            cab = next(leitor, [])
            n = sum(1 for _ in leitor)
        if "municipio_id" not in cab:
            raise AirflowFailException(f"CSV de focos sem coluna municipio_id: {cab}")
        with open(clima, encoding="utf-8") as f:
            c = json.load(f)
        if len(c.get("municipios", [])) != len(muns):
            raise AirflowFailException("clima com numero de municipios diferente do recorte")
        resumo = {"data": f"{alvo:%Y-%m-%d}", "linhas_focos": n, "municipios_clima": len(muns)}
        log.info("chegada ok: %s", resumo)
        return resumo

    @task
    def notificar(resumo):
        msg = (f"FogoCerto: coleta de {resumo['data']} ok. "
               f"{resumo['linhas_focos']} focos no Brasil, clima de {resumo['municipios_clima']} municipios.")
        log.info(msg)
        token = Variable.get("gs_telegram_token", default="")
        chat = Variable.get("gs_telegram_chat_id", default="")
        if token and chat:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          data={"chat_id": chat, "text": msg}, timeout=30)

    focos = coletar_focos_inpe()
    clima = coletar_clima_open_meteo()
    conferido = conferir_chegada()
    inicio >> [focos, clima] >> conferido
    notificar(conferido)
