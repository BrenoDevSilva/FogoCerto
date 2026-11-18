"""As duas ferramentas do agente: consulta_risco (dados do Big Data) e busca_lei (base de leis)."""
import json
import os
import re
import urllib.request

from . import DADOS
from .busca import normalizar

FONTE_RISCO = "FOGOCERTO-risco"            # prefixo de todas as fontes de risco
ID_RANKING = f"{FONTE_RISCO}-ranking"
CAMPOS_RISCO = ["nome", "uf", "data", "nivel_risco", "pontos", "fatores", "focos_ontem",
                "umidade_min", "vento_max", "temp_max", "chuva_3d"]


def id_risco(municipio: str) -> str:
    """Identificador da fonte de risco de um município: 'Monte Alegre' -> 'FOGOCERTO-risco-monte-alegre'."""
    return f"{FONTE_RISCO}-{re.sub(r'[^a-z0-9]+', '-', normalizar(municipio)).strip('-')}"


def eh_fonte_risco(fonte_id: str) -> bool:
    return str(fonte_id).startswith(FONTE_RISCO)


def carregar_risco() -> list[dict]:
    """Lê o risco_atual.json exportado da camada Ouro.

    Padrão: a cópia salva em dados/ (deixa a avaliação reproduzível).
    Em produção: defina FOGOCERTO_RISCO_URL (site publicado) ou FOGOCERTO_RISCO_PATH.
    """
    url = os.getenv("FOGOCERTO_RISCO_URL")
    if url:
        with urllib.request.urlopen(url, timeout=10) as r:
            return json.load(r)
    caminho = os.getenv("FOGOCERTO_RISCO_PATH", str(DADOS / "risco_atual.json"))
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def consulta_risco(municipio: str) -> dict:
    """Risco de fogo mais recente de um município do recorte (nome ou código IBGE).
    Com municipio="todos", devolve a lista de todos, do maior para o menor risco."""
    try:
        dados = carregar_risco()
    except Exception:
        return {"encontrado": False, "erro": "dados de risco indisponíveis no momento"}
    alvo = normalizar(municipio)
    if alvo in ("todos", "todas", "ranking", "lista"):
        ordenados = sorted(dados, key=lambda d: (-d["pontos"], d["nome"]))
        return {"encontrado": True, "fonte_id": ID_RANKING, "data": ordenados[0]["data"],
                "municipios": [{"nome": d["nome"], "nivel_risco": d["nivel_risco"], "pontos": d["pontos"],
                                "focos_ontem": d["focos_ontem"]} for d in ordenados]}
    for d in dados:
        if alvo in (normalizar(d["nome"]), str(d["id_ibge"])):
            return {"encontrado": True, "fonte_id": id_risco(d["nome"]), **{k: d[k] for k in CAMPOS_RISCO},
                    "origem": "FogoCerto (INPE + Open-Meteo)",
                    "aviso": "O risco é informativo. Quem autoriza queima é o órgão ambiental competente."}
    return {"encontrado": False, "erro": "município fora da cobertura do FogoCerto: não consta",
            "municipios_disponiveis": [d["nome"] for d in dados]}


def criar_busca_lei(buscador, k: int = 3, limiar: float = 0.0, pergunta_original: str | None = None):
    """Devolve a função busca_lei ligada ao buscador, ao k e ao limiar escolhidos.

    A busca usa a consulta que o agente escreveu E a pergunta original do usuário (fica a maior nota de cada trecho):
    assim, uma consulta mal escrita pelo modelo não esconde o trecho que a própria pergunta acharia.
    A busca_lei só devolve trechos de lei e da regra de risco: o risco do dia o agente obtém pela consulta_risco.
    """

    def busca_lei(pergunta: str) -> dict:
        """Trechos de lei (e da regra de risco do FogoCerto) mais parecidos com a pergunta."""
        consultas = [str(pergunta)] + ([pergunta_original] if pergunta_original else [])
        notas = buscador._notas(consultas).max(axis=0)
        ordem = sorted(range(len(buscador.trechos)), key=lambda i: -notas[i])
        achados = [{**buscador.trechos[i], "nota": round(float(notas[i]), 4)} for i in ordem
                   if notas[i] >= limiar and not eh_fonte_risco(buscador.trechos[i]["id"])][:k]
        if not achados:
            return {"encontrado": False, "erro": "nenhum trecho da base trata disso: não consta"}
        return {"encontrado": True,
                "trechos": [{"fonte_id": t["id"], "referencia": t["referencia"], "nota": t["nota"], "texto": t["texto"]}
                            for t in achados]}

    return busca_lei


# Descrição das ferramentas no formato que o modelo recebe (padrão de "tools" do transformers).
DESCRICAO_FERRAMENTAS = [
    {"type": "function", "function": {
        "name": "consulta_risco",
        "description": "Consulta o risco de fogo mais recente de um município coberto pelo FogoCerto (nível, fatores, "
                       "focos de ontem e data do dado). Use sempre que a pergunta citar um município ou perguntar se "
                       "dá para queimar hoje. Use municipio='todos' para comparar municípios.",
        "parameters": {"type": "object",
                       "properties": {"municipio": {"type": "string", "description": "Nome do município, ou 'todos'"}},
                       "required": ["municipio"]}}},
    {"type": "function", "function": {
        "name": "busca_lei",
        "description": "Busca na base de leis o que a lei diz sobre uso do fogo, queima controlada, autorização, "
                       "suspensão da autorização, crimes e penas, e como o FogoCerto calcula o risco. Use também "
                       "quando a pergunta for se dá para queimar, para citar a regra da autorização.",
        "parameters": {"type": "object",
                       "properties": {"pergunta": {"type": "string", "description": "O que procurar na base"}},
                       "required": ["pergunta"]}}},
]
