"""API do assistente do FogoCerto.

    uvicorn api.main:app --host 0.0.0.0 --port 8000      (rodar de dentro da pasta genai/)

POST /assistente/perguntar  {"pergunta": "...", "municipio": "Portel"}
  -> {"resposta", "fontes": [{"id", "referencia", "url"}], "recusa", "confianca", "aviso"}
"""
import os
from functools import lru_cache

from fastapi import FastAPI
from pydantic import BaseModel, Field

from fogocerto_ia import base, busca, gerador
from fogocerto_ia.ferramentas import eh_fonte_risco

AVISO = ("O FogoCerto informa e orienta. Ele não autoriza queima e não substitui o órgão ambiental competente. "
         "Em caso de incêndio, ligue 193 (Bombeiros) ou 199 (Defesa Civil).")
RESPOSTA_FALHA = "Não consegui responder agora. Tente de novo ou procure o órgão ambiental competente."

app = FastAPI(title="FogoCerto - Assistente", version="1.1")


class Pergunta(BaseModel):
    pergunta: str = Field(min_length=3, max_length=500)
    municipio: str | None = Field(default=None, max_length=80)


@lru_cache(maxsize=1)
def _recursos():
    """Carrega a base, o buscador e o modelo uma vez só, no primeiro pedido."""
    trechos = base.carregar()
    buscador = busca.Buscador(trechos, tipo=os.getenv("FOGOCERTO_BUSCADOR", "e5"))
    modelo = gerador.Gerador(os.getenv("FOGOCERTO_MODELO", gerador.MODELO_PADRAO))
    return {t["id"]: t for t in trechos}, buscador, modelo


def _fontes(ids, por_id):
    saida = []
    for i in ids:
        if i in por_id:
            saida.append({"id": i, "referencia": por_id[i]["referencia"], "url": por_id[i]["url"]})
        elif eh_fonte_risco(i):
            saida.append({"id": i, "referencia": "FogoCerto: risco de fogo por município (INPE + Open-Meteo)",
                          "url": None})
    return saida


@app.get("/saude")
def saude():
    return {"status": "ok"}


@app.post("/assistente/perguntar")
def perguntar(p: Pergunta):
    por_id, buscador, modelo = _recursos()
    texto = p.pergunta.strip()
    if p.municipio and p.municipio.lower() not in texto.lower():
        texto += f" (município: {p.municipio.strip()})"
    params = busca.ler_parametros()
    r = gerador.responder(texto, "agente", modelo, buscador, k=3, limiar=params["limiar"], nota_alta=params["nota_alta"])
    if not r["json_valido"]:                       # o modelo não devolveu o JSON combinado
        return {"resposta": RESPOSTA_FALHA, "fontes": [], "recusa": True, "confianca": "baixa", "aviso": AVISO}
    j, _ = gerador.aplicar_trava(r["json"])         # última camada: nunca liberar queima
    # só devolve fonte que o modelo realmente recebeu (nunca uma fonte inventada)
    recebidas = set(r["contexto_ids"])
    ids = [f for f in (x.strip("[] ") for x in j["fontes"]) if f in recebidas]
    # a pergunta não é guardada: nada de dado pessoal em log (LGPD)
    return {"resposta": j["resposta"], "fontes": _fontes(ids, por_id), "recusa": j["recusa"],
            "confianca": r["confianca"], "aviso": AVISO}
