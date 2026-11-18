"""Base de conhecimento: baixa o texto oficial das leis, corta por artigo e grava os trechos.

Cada trecho guarda de onde veio (lei, artigo, link), para a IA poder citar a fonte.
"""
import csv
import html
import json
import re
import urllib.request
from pathlib import Path

from . import BASE

ORIGINAIS = BASE / "originais"
TRECHOS = BASE / "trechos.jsonl"
FONTES = BASE / "fontes.csv"

# artigos=None significa "todos". Nas outras duas leis entram só os artigos ligados a fogo.
LEIS = [
    {
        "id": "L14944",
        "nome": "Lei 14.944/2024 (Política Nacional de Manejo Integrado do Fogo)",
        "arquivo": "L14944.html",
        "urls": [
            "https://www2.camara.leg.br/legin/fed/lei/2024/lei-14944-31-julho-2024-796016-normaatualizada-pl.html",
            "https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2024/lei/L14944.htm",
        ],
        "artigos": None,
    },
    {
        "id": "L12651",
        "nome": "Lei 12.651/2012 (Código Florestal), Capítulo IX: uso de fogo e incêndios",
        "arquivo": "L12651.html",
        "urls": [
            "https://www2.camara.leg.br/legin/fed/lei/2012/lei-12651-25-maio-2012-613076-normaatualizada-pl.html",
            "https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2012/lei/L12651.htm",
        ],
        "artigos": ["38", "39", "40"],
    },
    {
        "id": "L9605",
        "nome": "Lei 9.605/1998 (Crimes Ambientais), artigos ligados a fogo",
        "arquivo": "L9605.html",
        "urls": [
            "https://www2.camara.leg.br/legin/fed/lei/1998/lei-9605-12-fevereiro-1998-365397-normaatualizada-pl.html",
            "https://www.planalto.gov.br/ccivil_03/leis/L9605.htm",
        ],
        "artigos": ["2", "3", "14", "15", "38", "38-A", "41", "42", "48", "50", "53", "54", "70", "72"],
    },
    {
        "id": "D6514",
        "nome": "Decreto 6.514/2008 (infrações e multas ambientais), artigos sobre fogo",
        "arquivo": "D6514.html",
        "urls": [
            "https://www2.camara.leg.br/legin/fed/decret/2008/decreto-6514-22-julho-2008-578464-normaatualizada-pe.html",
            "https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2008/decreto/d6514.htm",
        ],
        "artigos": ["3", "58", "58-A", "58-B", "60"],
        "opcional": True,      # se o download falhar, a base segue sem ele e os casos que dependem dele saem da avaliação
    },
]
FALHAS: list[str] = []       # fontes opcionais que não puderam ser baixadas nesta execução
LICENCA_LEI = "Texto oficial de norma federal (não protegido por direito autoral, Lei 9.610/1998, art. 8º, IV)"

# Trechos escritos pelo próprio grupo: como o FogoCerto calcula o risco (mesma regra do Big Data).
REGRA_RISCO = [
    ("FOGOCERTO-regra-1", "Como o FogoCerto calcula o risco",
     "O FogoCerto calcula o risco de fogo de cada município por uma regra de pontos, uma vez por dia. "
     "Somam-se pontos para cinco fatores: umidade mínima do dia, vento máximo, chuva dos últimos 3 dias, "
     "temperatura máxima e focos de calor no município no dia anterior. O total vai de 0 a 9. "
     "De 0 a 2 pontos o risco é baixo, de 3 a 4 é médio e com 5 ou mais é alto."),
    ("FOGOCERTO-regra-2", "Pontos de cada fator do risco",
     "Pontos da regra de risco do FogoCerto: umidade mínima abaixo de 30% vale 2 pontos e abaixo de 40% vale 1 ponto. "
     "Vento máximo de 30 km/h ou mais vale 2 pontos e de 20 km/h ou mais vale 1 ponto. "
     "Menos de 1 mm de chuva somada nos últimos 3 dias vale 1 ponto. Temperatura máxima de 35 °C ou mais vale 1 ponto. "
     "Focos de calor no município no dia anterior: 100 ou mais valem 3 pontos, 20 ou mais valem 2 pontos e 1 ou mais vale 1 ponto."),
    ("FOGOCERTO-regra-3", "De onde vêm os dados do risco",
     "Os dados do risco do FogoCerto vêm de fontes abertas: os focos de calor são do INPE (Programa Queimadas) e o clima "
     "(umidade, vento, temperatura e chuva) é do Open-Meteo. O risco usa os focos do dia anterior, nunca os do próprio dia. "
     "A cobertura atual é de 15 municípios do Pará: Portel, Pacajá, Uruará, Almeirim, Monte Alegre, Prainha, Oriximiná, "
     "Santarém, Itaituba, Itupiranga, Tucuruí, Jacundá, Castanhal, Santana do Araguaia e Soure."),
    ("FOGOCERTO-regra-4", "O que o FogoCerto não faz",
     "O FogoCerto informa o risco de fogo e orienta, mas não autoriza queima e não substitui o órgão ambiental. "
     "A autorização de queima controlada é dada pelo órgão ambiental competente. Risco baixo não significa que a queima "
     "está liberada. Em caso de incêndio, a orientação é acionar o Corpo de Bombeiros (193) ou a Defesa Civil (199)."),
]


# ---------- download e limpeza ----------

def _ler_bytes(dados: bytes) -> str:
    for cod in ("utf-8", "cp1252"):
        try:
            return dados.decode(cod)
        except UnicodeDecodeError:
            continue
    return dados.decode("utf-8", errors="ignore")


def baixar_lei(lei: dict, forcar: bool = False) -> Path:
    """Baixa o HTML oficial da lei para base/originais/. Se o arquivo já existe, usa o que está salvo."""
    ORIGINAIS.mkdir(parents=True, exist_ok=True)
    destino = ORIGINAIS / lei["arquivo"]
    if destino.exists() and destino.stat().st_size > 2000 and not forcar:
        return destino
    erros = []
    for url in lei["urls"]:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (FogoCerto; trabalho academico)"})
            with urllib.request.urlopen(req, timeout=40) as r:
                dados = r.read()
            if len(dados) > 2000 and b"Art" in dados:
                destino.write_bytes(dados)
                return destino
            erros.append(f"{url}: resposta sem o texto da lei")
        except Exception as e:  # rede, bloqueio, etc.
            erros.append(f"{url}: {e}")
    raise RuntimeError(
        f"Não consegui baixar {lei['nome']}.\n" + "\n".join(erros) +
        f"\nAbra um dos links no navegador, salve a página como HTML e coloque em {destino}."
    )


def html_para_texto(conteudo: str) -> str:
    """Tira as marcações do HTML e devolve o texto, uma linha por parágrafo."""
    t = re.sub(r"(?is)<(script|style|head)[^>]*>.*?</\1>", " ", conteudo)
    t = re.sub(r"\s+", " ", t)          # quebra de linha do código-fonte não é quebra de parágrafo
    t = re.sub(r"(?is)<(strike|s|del)\b[^>]*>.*?</\1>", " ", t)          # texto revogado (riscado no Planalto)
    t = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>|</h\d>|</li>", "\n", t)
    t = re.sub(r"(?s)<[^>]+>", " ", t)
    t = html.unescape(t).replace("\xa0", " ")
    linhas = [re.sub(r"\s+", " ", l).strip() for l in t.split("\n")]
    return "\n".join(l for l in linhas if l)


_RE_ART = re.compile(r"^Art\.?\s*(\d+)\s*[ºo°]?\s*(?:-\s*([A-Z])\b)?\s*\.?\s*(?=\S)")
_RE_TITULO = re.compile(r"^(CAP[ÍI]TULO|T[ÍI]TULO|Se[çc][ãa]o|SE[ÇC][ÃA]O|Subse[çc][ãa]o)\b")


def cortar_artigos(texto: str) -> list[dict]:
    """Corta o texto da lei em artigos. Devolve [{'artigo': '37', 'capitulo': ..., 'texto': ...}]."""
    artigos, atual, capitulo, pend_titulo, ultimo = [], None, "", [], 0
    for linha in texto.split("\n"):
        m = _RE_ART.match(linha)
        if m:
            num = int(m.group(1))
            # Só vale como artigo novo se a numeração avança. Artigo de outra lei citado
            # no meio do texto (numeração que volta) continua dentro do artigo atual.
            if num >= ultimo and num - ultimo <= 30:
                if atual:
                    artigos.append(atual)
                if pend_titulo:
                    capitulo, pend_titulo = " · ".join(pend_titulo), []
                rotulo = f"{num}-{m.group(2)}" if m.group(2) else str(num)
                atual = {"artigo": rotulo, "capitulo": capitulo, "texto": linha}
                ultimo = num
                continue
        if _RE_TITULO.match(linha) and len(linha) < 60:
            pend_titulo = [linha] if re.match(r"^(CAP|T[ÍI]T)", linha) else pend_titulo + [linha]
            continue
        if pend_titulo and atual and linha.isupper() and len(linha) < 120:   # nome do capítulo, em maiúsculas
            pend_titulo.append(linha)
            continue
        if pend_titulo and len(linha) < 90 and not re.match(r"^(§|Par[áa]grafo|[IVXL]+\s*[-–]|[a-z]\))", linha):
            pend_titulo.append(linha)                                         # nome da seção
            continue
        if atual:
            atual["texto"] += "\n" + linha
    if atual:
        artigos.append(atual)
    # o último artigo costuma trazer a assinatura; corta no fecho da lei
    if artigos:
        artigos[-1]["texto"] = re.split(r"\n(?:Bras[íi]lia,|Senado Federal,)", artigos[-1]["texto"])[0]
    return artigos


def dividir_longo(texto: str, max_chars: int) -> list[str]:
    """Divide um artigo longo em partes, quebrando só entre linhas (incisos e parágrafos)."""
    if not max_chars or len(texto) <= max_chars:
        return [texto]
    linhas = texto.split("\n")
    caput, partes, atual = linhas[0], [], []
    for linha in linhas[1:]:
        if atual and sum(len(x) + 1 for x in atual) + len(linha) > max_chars - len(caput):
            partes.append(atual)
            atual = []
        atual.append(linha)
    if atual:
        partes.append(atual)
    if not partes:
        return [texto]
    # o caput vai em todas as partes, para o trecho fazer sentido sozinho
    return [caput + "\n" + "\n".join(p) for p in partes]


# ---------- montagem ----------

def _data_br(iso: str) -> str:
    a, m, d = str(iso)[:10].split("-")
    return f"{d}/{m}/{a}"


def trechos_risco() -> list[dict]:
    """O risco do dia (cópia da camada Ouro do Big Data) em forma de texto: 1 trecho por município e 1 ranking.

    Assim o RAG simples recebe a MESMA informação que o agente consulta pela ferramenta consulta_risco.
    A comparação RAG x agente passa a medir só o jeito de obter o contexto (busca passiva x ferramenta).
    """
    from .ferramentas import ID_RANKING, carregar_risco, id_risco   # import aqui para evitar import circular

    dados = carregar_risco()
    data = _data_br(dados[0]["data"])
    fonte = f"FogoCerto: risco de fogo por município (Big Data, dados de {data})"
    url = "https://github.com/BrenoDevSilva/FogoCerto/tree/main/bigdata"
    saida = []
    for d in dados:
        motivos = d["fatores"] or "nenhum fator de risco somou pontos"
        texto = (f"Risco de fogo em {d['nome']} ({d['uf']}) no dia {_data_br(d['data'])}: nível {d['nivel_risco']} "
                 f"({d['pontos']} de 9 pontos). Motivos: {motivos}. Focos de calor no município no dia anterior: "
                 f"{d['focos_ontem']}. Umidade mínima de {d['umidade_min']:.0f}%, vento máximo de {d['vento_max']} km/h, "
                 f"temperatura máxima de {d['temp_max']} °C e {d['chuva_3d']} mm de chuva nos últimos 3 dias.")
        saida.append({"id": id_risco(d["nome"]), "artigo_id": id_risco(d["nome"]), "fonte": fonte,
                      "referencia": f"FogoCerto, risco de fogo em {d['nome']} ({data})", "capitulo": "Risco do dia",
                      "url": url, "texto": texto})
    ordenados = sorted(dados, key=lambda d: (-d["pontos"], d["nome"]))
    lista = "; ".join(f"{d['nome']} ({d['nivel_risco']}, {d['pontos']} pontos)" for d in ordenados)
    saida.append({"id": ID_RANKING, "artigo_id": ID_RANKING, "fonte": fonte,
                  "referencia": f"FogoCerto, ranking do risco de fogo ({data})", "capitulo": "Risco do dia", "url": url,
                  "texto": f"Ranking do risco de fogo nos {len(dados)} municípios cobertos pelo FogoCerto no dia {data}, "
                           f"do maior para o menor: {lista}."})
    return saida


def montar_trechos(leis_ids=None, max_chars: int = 1200, incluir_regra: bool = True, baixar: bool = True,
                   incluir_risco: bool = True) -> list[dict]:
    """Monta a lista de trechos. `leis_ids` limita as leis (para o experimento de tamanho da base)."""
    trechos = []
    for lei in LEIS:
        if leis_ids is not None and lei["id"] not in leis_ids:
            continue
        try:
            caminho = baixar_lei(lei) if baixar else ORIGINAIS / lei["arquivo"]
            if not caminho.exists():
                raise FileNotFoundError(caminho)
        except Exception as e:
            if not lei.get("opcional"):
                raise
            if lei["id"] not in FALHAS:
                FALHAS.append(lei["id"])
                print(f"AVISO: não consegui baixar {lei['nome']}. A base segue sem ele. ({e})")
            continue
        artigos = cortar_artigos(html_para_texto(_ler_bytes(caminho.read_bytes())))
        for art in artigos:
            if lei["artigos"] is not None and art["artigo"] not in lei["artigos"]:
                continue
            partes = dividir_longo(art["texto"], max_chars)
            for i, parte in enumerate(partes, 1):
                artigo_id = f"{lei['id']}-art{art['artigo']}"
                trechos.append({
                    "id": artigo_id if len(partes) == 1 else f"{artigo_id}-p{i}",
                    "artigo_id": artigo_id,
                    "fonte": lei["nome"],
                    "referencia": f"{lei['nome'].split(' (')[0]}, art. {art['artigo']}"
                                  + (f" (parte {i} de {len(partes)})" if len(partes) > 1 else ""),
                    "capitulo": art["capitulo"],
                    "url": lei["urls"][0],
                    "texto": parte,
                })
    if incluir_regra:
        for id_, titulo, texto in REGRA_RISCO:
            trechos.append({"id": id_, "artigo_id": id_, "fonte": "FogoCerto: regra de risco (Big Data)",
                            "referencia": f"FogoCerto, {titulo}", "capitulo": "Regra de risco",
                            "url": "https://github.com/BrenoDevSilva/FogoCerto/tree/main/bigdata", "texto": texto})
    if incluir_risco:
        trechos += trechos_risco()
    return trechos


def salvar(trechos: list[dict]) -> None:
    BASE.mkdir(exist_ok=True)
    with open(TRECHOS, "w", encoding="utf-8") as f:
        for t in trechos:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")
    # tabela da base pedida no relatório: fonte, formato, licença e número de trechos
    contagem = {}
    for t in trechos:
        contagem[t["fonte"]] = contagem.get(t["fonte"], 0) + 1
    urls = {t["fonte"]: t["url"] for t in trechos}
    with open(FONTES, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["fonte", "formato", "licenca", "url", "n_trechos"])
        for fonte, n in contagem.items():
            if fonte.startswith(("Lei", "Decreto")):
                formato, licenca = "HTML (texto oficial)", LICENCA_LEI
            elif fonte.startswith("FogoCerto: risco"):
                formato = "JSON da camada Ouro (risco_atual.json), convertido em texto"
                licenca = "Derivado de dados abertos do INPE (focos de calor) e do Open-Meteo (CC BY 4.0)"
            else:
                formato, licenca = "Texto próprio do grupo", "Autoria do grupo (repositório público do projeto)"
            w.writerow([fonte, formato, licenca, urls[fonte], n])


def carregar() -> list[dict]:
    """Lê base/trechos.jsonl. Se ainda não existe, monta a base."""
    if not TRECHOS.exists():
        salvar(montar_trechos())
    with open(TRECHOS, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def conferir(trechos: list[dict]) -> list[str]:
    """Checagens simples da base. Devolve a lista de avisos (vazia = tudo certo)."""
    avisos = []
    por_lei = {}
    for t in trechos:
        por_lei.setdefault(t["artigo_id"].split("-art")[0], set()).add(t["artigo_id"])
    if "L14944" in por_lei and not 50 <= len(por_lei["L14944"]) <= 54:
        avisos.append(f"Lei 14.944: esperava cerca de 52 artigos, vieram {len(por_lei['L14944'])}.")
    for lei in LEIS:
        if lei["artigos"] and lei["id"] in por_lei:
            faltam = [a for a in lei["artigos"] if f"{lei['id']}-art{a}" not in por_lei[lei["id"]]]
            if faltam:
                avisos.append(f"{lei['id']}: não achei os artigos {faltam}.")
    for lei in LEIS:
        if lei["id"] not in por_lei:
            if lei.get("opcional"):
                avisos.append(f"{lei['nome']} (opcional): não entrou na base; os casos que dependem dele saem da avaliação.")
            else:
                avisos.append(f"{lei['nome']}: NENHUM artigo entrou na base. Confira o arquivo em base/originais/.")
    curtos = [t["id"] for t in trechos if len(t["texto"]) < 40]
    if curtos:
        avisos.append(f"Trechos muito curtos (conferir): {curtos[:8]}")
    return avisos
