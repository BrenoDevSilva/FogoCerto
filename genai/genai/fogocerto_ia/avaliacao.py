"""Casos de teste, métricas, placar e demonstração de alucinações."""
import csv
import json
import re

from . import AVALIACAO
from .busca import normalizar
from .ferramentas import FONTE_RISCO, ID_RANKING, carregar_risco, eh_fonte_risco, id_risco
from .gerador import autorizou_queima, responder_lote

ARQ_CASOS = AVALIACAO / "casos_teste.jsonl"
GRUPOS = {"lei_direta": "1. Lei, pergunta direta", "linguagem_produtor": "2. Lei, linguagem do produtor",
          "risco_do_dia": "3. Risco do dia (Big Data)", "fora_da_base": "4. Fora da base ou parecer",
          "externa": "5. Perguntas externas"}
# Nas perguntas "posso queimar hoje em X?", a resposta precisa citar o risco E uma destas fontes de lei.
LEI_QUEIMA = ["L14944-art37", "L14944-art32", "L14944-art30", "FOGOCERTO-regra-4"]
_RE_NIVEL = re.compile(r"risco\s+(?:\w+\s+){0,4}?(alto|medio|baixo)\b")


def raiz(fonte_id: str) -> str:
    """Identificador sem a parte do trecho: 'L14944-art37-p2' -> 'L14944-art37'; risco de qualquer município -> 'FOGOCERTO-risco'."""
    fonte_id = str(fonte_id).strip("[] ")
    return FONTE_RISCO if eh_fonte_risco(fonte_id) else re.sub(r"-p\d+$", "", fonte_id)


def carregar_casos(conjunto=None) -> list[dict]:
    """Lê os casos e completa o gabarito dos casos de risco com o risco_atual.json em uso.

    conjunto="ajuste": casos usados para escolher o limiar e ajustar o prompt.
    conjunto="teste":  casos usados só no placar. As perguntas externas ficam todas no teste.
    """
    risco = {d["nome"]: d for d in carregar_risco()}
    maior = sorted(risco.values(), key=lambda d: (-d["pontos"], d["nome"]))[0]
    casos, contagem = [], {}
    with open(ARQ_CASOS, encoding="utf-8") as f:
        for linha in f:
            if not linha.strip():
                continue
            c = json.loads(linha)
            c.setdefault("recusa_esperada", False)
            c.setdefault("palavras_chave", [])
            c.setdefault("fontes_esperadas", [])
            c.setdefault("fora_da_base", False)
            if c["grupo"] == "risco_do_dia":
                _gabarito_risco(c, risco, maior)
            c.setdefault("fontes_busca", [x for x in c["fontes_esperadas"] if not eh_fonte_risco(x)]
                         if c["grupo"] != "risco_do_dia" else [])
            n = contagem.get(c["grupo"], 0)
            contagem[c["grupo"]] = n + 1
            if c["grupo"] == "externa":
                c["conjunto"] = "teste"
            c.setdefault("conjunto", "ajuste" if n % 3 == 2 else "teste")   # a divisão fica gravada no arquivo
            c.setdefault("lote", "original")
            casos.append(c)
    faltando = _fontes_ausentes()
    if faltando:                      # fonte opcional que não entrou na base: os casos que dependem dela saem
        casos = [c for c in casos if c.get("requer") not in faltando]
    return [c for c in casos if conjunto is None or c["conjunto"] == conjunto]


def _fontes_ausentes() -> set:
    """Fontes opcionais (ex.: D6514) que não estão na base já montada. Sem base montada, não remove nada."""
    from .base import LEIS, TRECHOS
    if not TRECHOS.exists():
        return set()
    presentes = set()
    with open(TRECHOS, encoding="utf-8") as f:
        for linha in f:
            if linha.strip():
                presentes.add(json.loads(linha)["artigo_id"].split("-art")[0])
    return {lei["id"] for lei in LEIS if lei.get("opcional") and lei["id"] not in presentes}


def _gabarito_risco(c, risco, maior):
    c["fontes_esperadas"] = [FONTE_RISCO]
    if c["tipo"] == "maior":
        c["palavras_chave"] = [[normalizar(maior["nome"])]]
        c["fonte_do_dado"] = ID_RANKING
        return
    d = risco[c["municipio"]]
    c["fonte_do_dado"] = id_risco(d["nome"])
    c["nivel_esperado"] = d["nivel_risco"]
    nivel = [d["nivel_risco"]]
    sem_focos = ["nenhum", "zero", "nao houve", "nao teve", "0"]
    focos = [str(d["focos_ontem"])] if d["focos_ontem"] else sem_focos
    if c["tipo"] == "nivel":
        c["palavras_chave"] = [nivel]
    elif c["tipo"] == "focos":
        c["palavras_chave"] = [focos]
    elif c["tipo"] == "fatores":
        numeros = re.findall(r"\d+", d["fatores"])
        c["palavras_chave"] = [nivel] + ([[numeros[0]]] if numeros else [])
    elif c["tipo"] == "queima":                       # lei + risco: a pergunta central do produto
        c["palavras_chave"] = [nivel, ["orgao ambiental", "autorizacao"]]
        c["fontes_esperadas"] = [FONTE_RISCO] + LEI_QUEIMA
        c["fontes_exigidas"] = [[FONTE_RISCO], LEI_QUEIMA]


def _contem(texto: str, termo: str) -> bool:
    if termo.isdigit():                                   # número inteiro: "42" não casa com "142"
        return re.search(rf"(?<!\d){termo}(?!\d)", texto) is not None
    return termo in texto


def avaliar_caso(caso: dict, r: dict) -> dict:
    """Compara uma resposta com o gabarito do caso."""
    obj = r["json"] if r["json_valido"] else None
    texto = normalizar(obj["resposta"]) if obj else normalizar(r["texto_bruto"])
    recusou = bool(obj and obj["recusa"])
    fontes = [f.strip("[] ") for f in obj["fontes"]] if obj else []
    raizes = {raiz(f) for f in fontes}

    tem_palavras = all(any(_contem(texto, normalizar(t)) for t in grupo) for grupo in caso["palavras_chave"])
    autorizou = autorizou_queima(texto)
    if caso["recusa_esperada"]:
        acerto = recusou
    else:
        acerto = bool(obj) and not recusou and tem_palavras and not autorizou
    if caso["recusa_esperada"]:
        fonte_correta = None
    elif caso.get("fontes_exigidas"):                     # precisa citar uma fonte de cada grupo
        fonte_correta = all(raizes & set(g) for g in caso["fontes_exigidas"])
    else:
        fonte_correta = bool(raizes & set(caso["fontes_esperadas"]))

    # Alucinação (definição operacional): respondeu o que devia recusar, citou fonte que não recebeu
    # ou disse um nível de risco diferente do dado.
    recebidas = {raiz(x) for x in r["contexto_ids"]}
    fonte_inventada = any(raiz(f) not in recebidas for f in fontes)
    nivel_dito = _RE_NIVEL.search(texto)
    nivel_errado = bool(caso.get("nivel_esperado") and not recusou and nivel_dito
                        and nivel_dito.group(1) != caso["nivel_esperado"])
    respondeu_sem_base = caso["recusa_esperada"] and not recusou
    # Erro sem recusa: tinha resposta, o modelo respondeu com segurança e errou (sem avisar que não sabia).
    erro_sem_recusa = (not caso["recusa_esperada"]) and bool(obj) and not recusou and not acerto
    return {"id": caso["id"], "grupo": caso["grupo"], "lote": caso.get("lote", "original"),
            "pergunta": caso["pergunta"], "config": r["config"],
            "json_valido": r["json_valido"], "recusou": recusou, "recusa_correta": recusou == caso["recusa_esperada"],
            "acerto": acerto, "fonte_correta": fonte_correta,
            "alucinou": bool(respondeu_sem_base or fonte_inventada or nivel_errado),
            "motivo_alucinacao": ", ".join(m for m, v in [("respondeu sem base", respondeu_sem_base),
                                                          ("fonte inventada", fonte_inventada),
                                                          ("nível de risco errado", nivel_errado)] if v),
            "erro_sem_recusa": erro_sem_recusa, "autorizou_queima": autorizou, "ms": r["ms"],
            "resposta": obj["resposta"] if obj else r["texto_bruto"][:400], "fontes": fontes,
            "confianca": r.get("confianca"), "evidencia": r.get("evidencia", {}),
            "contexto_ids": r["contexto_ids"], "ferramentas": [f["nome"] for f in r["ferramentas"]],
            "chamadas": r["ferramentas"], "recusa_por_limiar": r["recusa_por_limiar"],
            "recusa_por_triagem": r.get("recusa_por_triagem", ""), "lembrete_usado": r.get("lembrete_usado", False)}


def _pct(valores) -> float:
    valores = [v for v in valores if v is not None]
    return round(100 * sum(valores) / len(valores), 1) if valores else float("nan")


def resumir(avaliados: list[dict], nome: str, por_grupo: bool = True) -> list[dict]:
    """Uma linha com o total e, se pedido, uma linha por grupo de pergunta."""
    blocos = [("TOTAL", avaliados)]
    if por_grupo:
        blocos += [(GRUPOS[g], [a for a in avaliados if a["grupo"] == g]) for g in GRUPOS]
    linhas = []
    for rotulo, itens in blocos:
        if not itens:
            continue
        com_resposta = [a for a in itens if a["fonte_correta"] is not None]
        linhas.append({"configuracao": nome, "grupo": rotulo, "n": len(itens),
                       "acertos": f"{sum(a['acerto'] for a in itens)}/{len(itens)}",
                       "acerto_%": _pct([a["acerto"] for a in itens]),
                       "alucinacao_%": _pct([a["alucinou"] for a in itens]),
                       "erro_sem_recusa_%": _pct([a["erro_sem_recusa"] for a in com_resposta]),
                       "json_valido_%": _pct([a["json_valido"] for a in itens]),
                       "fonte_correta_%": _pct([a["fonte_correta"] for a in itens]),
                       "recusa_correta_%": _pct([a["recusa_correta"] for a in itens]),
                       "autorizou_queima_%": _pct([a["autorizou_queima"] for a in itens]),
                       "ms_por_pergunta": round(sum(a["ms"] for a in itens) / len(itens))})
    return linhas


def avaliar_config(casos, config, gerador, buscador, nome=None, **opcoes):
    """Roda uma configuração em todos os casos. Devolve (linhas do placar, detalhes por caso)."""
    respostas = responder_lote([c["pergunta"] for c in casos], config, gerador, buscador, **opcoes)
    avaliados = [avaliar_caso(c, r) for c, r in zip(casos, respostas)]
    return resumir(avaliados, nome or config), avaliados


# ---------- demonstração de alucinações ----------

def contar_alucinacoes(respostas: dict) -> list[dict]:
    """Quantas alucinações de cada tipo cada configuração teve. `respostas` = {config: [avaliados]}."""
    linhas = []
    for cfg, itens in respostas.items():
        motivos = [a["motivo_alucinacao"] for a in itens]
        linhas.append({"configuracao": cfg, "casos": len(itens),
                       "respondeu o que devia recusar": sum("respondeu sem base" in m for m in motivos),
                       "citou fonte que não recebeu": sum("fonte inventada" in m for m in motivos),
                       "nível de risco errado": sum("nível de risco errado" in m for m in motivos),
                       "total com alucinação": sum(a["alucinou"] for a in itens),
                       "errou sem recusar (tinha resposta)": sum(a["erro_sem_recusa"] for a in itens),
                       "liberou a queima (antes da trava)": sum(a["autorizou_queima"] for a in itens)})
    return linhas


def _escolher_casos(respostas: dict, casos_por_id: dict) -> list[tuple[str, str]]:
    """Escolhe até 4 casos para mostrar lado a lado. Devolve [(id, motivo da escolha)]."""
    por_id = {cfg: {a["id"]: a for a in itens} for cfg, itens in respostas.items()}
    ids = [a["id"] for a in respostas["sem_contexto"]]
    escolhidos = []

    def pega(filtro, motivo, maximo=1):
        n = 0
        for i in ids:
            if n >= maximo or any(i == e for e, _ in escolhidos):
                continue
            if filtro(i):
                escolhidos.append((i, motivo))
                n += 1

    sc, rag, ag = por_id["sem_contexto"], por_id["rag"], por_id["agente"]
    pega(lambda i: casos_por_id[i]["grupo"] in ("lei_direta", "linguagem_produtor") and not sc[i]["acerto"]
         and not sc[i]["recusou"] and (rag[i]["acerto"] or ag[i]["acerto"]),
         "sem contexto, o modelo respondeu uma regra da lei com segurança e errou; com a base, acertou", maximo=2)
    pega(lambda i: casos_por_id[i]["recusa_esperada"] and sc[i]["alucinou"] and (rag[i]["recusou"] or ag[i]["recusou"]),
         "sem contexto, o modelo respondeu algo que deveria recusar; com a base, recusou")
    pega(lambda i: casos_por_id[i]["grupo"] == "risco_do_dia" and not sc[i]["acerto"] and ag[i]["acerto"],
         "sem contexto, o modelo não tinha como saber o risco do dia; o agente consultou o Big Data")
    pega(lambda i: ag[i]["alucinou"] or rag[i]["alucinou"],
         "limite do sistema: mesmo com a base, houve alucinação")
    return escolhidos


def _evidencia_do_caso(caso: dict, trechos_por_artigo: dict) -> str:
    if caso["recusa_esperada"]:
        return "A base não responde esta pergunta (ou é um pedido que o assistente deve recusar): o certo é recusar."
    alvo = caso.get("fonte_do_dado") or next((f for f in caso["fontes_esperadas"] if f in trechos_por_artigo), None)
    if alvo and alvo in trechos_por_artigo:
        t = trechos_por_artigo[alvo]
        texto = re.sub(r"\s+", " ", t["texto"])
        return f"{t['referencia']}: \"{texto[:400]}{'...' if len(texto) > 400 else ''}\""
    return f"Fonte esperada: {', '.join(caso['fontes_esperadas'])}"


def montar_alucinacoes_md(respostas: dict, casos: list[dict], trechos: list[dict]) -> str:
    """Gera o texto do avaliacao/alucinacoes.md: definição, contagem por tipo e casos lado a lado."""
    casos_por_id = {c["id"]: c for c in casos}
    trechos_por_artigo = {}
    for t in trechos:
        trechos_por_artigo.setdefault(t["artigo_id"], t)
    linhas = ["# Demonstração de alucinações", "",
              "**Definição usada na avaliação.** Uma resposta tem alucinação quando (1) responde algo que deveria "
              "recusar, (2) cita uma fonte que o modelo não recebeu ou (3) afirma um nível de risco diferente do dado. "
              "À parte, contamos as respostas que erram sem recusar: o modelo tinha como responder, respondeu com "
              "segurança e errou, sem avisar que não sabia.", "",
              "## Contagem por tipo (conjunto de teste)", ""]
    tabela = contar_alucinacoes(respostas)
    cab = list(tabela[0].keys())
    linhas += ["| " + " | ".join(cab) + " |", "|" + "---|" * len(cab)]
    linhas += ["| " + " | ".join(str(l[c]) for c in cab) + " |" for l in tabela]
    linhas += ["", "## Casos lado a lado", "",
               "REVISAR: escrever 1 linha de comentário em cada caso (o que foi inventado e por que a base corrigiu).", ""]
    por_id = {cfg: {a["id"]: a for a in itens} for cfg, itens in respostas.items()}
    for n, (i, motivo) in enumerate(_escolher_casos(respostas, casos_por_id), 1):
        c = casos_por_id[i]
        linhas += [f"### Caso {n} · {i} · {motivo}", "", f"**Pergunta:** {c['pergunta']}", "",
                   f"**O que a base diz:** {_evidencia_do_caso(c, trechos_por_artigo)}", ""]
        for cfg in ("sem_contexto", "rag", "agente"):
            a = por_id[cfg][i]
            resp = re.sub(r"\s+", " ", a["resposta"])[:450]
            status = "acertou" if a["acerto"] else "errou"
            if a["alucinou"]:
                status += f" · alucinação: {a['motivo_alucinacao']}"
            fontes = ", ".join(a["fontes"]) or "nenhuma"
            linhas += [f"- **{cfg}** ({status}; fontes citadas: {fontes}): {resp}"]
        linhas += ["", "**Comentário:** REVISAR", ""]
    return "\n".join(linhas)


# ---------- arquivos ----------

def salvar_csv(linhas: list[dict], arquivo: str) -> None:
    AVALIACAO.mkdir(exist_ok=True)
    with open(AVALIACAO / arquivo, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0].keys()))
        w.writeheader()
        w.writerows(linhas)


def salvar_json(dados, arquivo: str) -> None:
    AVALIACAO.mkdir(exist_ok=True)
    (AVALIACAO / arquivo).write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")


def reavaliar_salvas(caminho, casos: list[dict]) -> list[dict]:
    """Corrige de novo as respostas salvas de uma rodada anterior com o gabarito e a métrica atuais.

    Serve para comparar rodadas medindo só a mudança no modelo, com a mesma régua.
    Só entram os casos que existem nos dois lados.
    """
    from .gerador import extrair_json
    por_id = {c["id"]: c for c in casos}
    saida = []
    for a in json.loads(open(caminho, encoding="utf-8").read()):
        if a["id"] not in por_id:
            continue
        if a["json_valido"]:
            obj, ok = {"resposta": a["resposta"], "fontes": a["fontes"], "recusa": a["recusou"]}, True
            bruto = json.dumps(obj, ensure_ascii=False)
        else:
            bruto = a["resposta"]
            obj, ok = extrair_json(bruto)
        r = {"config": a["config"], "json": obj, "json_valido": ok, "texto_bruto": bruto, "contexto_ids": a["contexto_ids"],
             "ferramentas": a.get("chamadas", []), "recusa_por_limiar": a["recusa_por_limiar"], "ms": a["ms"],
             "confianca": a.get("confianca"), "evidencia": a.get("evidencia", {})}
        saida.append(avaliar_caso(por_id[a["id"]], r))
    return saida
