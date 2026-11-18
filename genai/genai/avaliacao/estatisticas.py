"""Recalcula, a partir das respostas salvas, as estatísticas citadas no README (seção 5.2).

Uso, dentro da pasta genai/:  python avaliacao/estatisticas.py
Só lê avaliacao/respostas_*.json; não precisa de GPU nem do modelo.

- Intervalo de confiança de 95% do acerto (Wilson).
- Teste de McNemar exato (binomial) nas perguntas em que uma configuração acertou e a outra errou.
- Alucinação de conteúdo: sem as respostas cuja única "fonte inventada" é um marcador do formato.
- Acerto sem os 12 casos em que a palavra-chave do gabarito já está na pergunta.
"""
import json
import math
from pathlib import Path

PASTA = Path(__file__).resolve().parent
R = {c: {r["id"]: r for r in json.loads((PASTA / f"respostas_{c}.json").read_text(encoding="utf-8"))}
     for c in ("sem_contexto", "rag", "agente")}
IDS = list(R["rag"])
MARCADORES = {"contexto", "município", "municipio", "fonte_id_1", "1", "terra_indigena", "identificador_municipio",
              "nível_risco", "motivo_risco", "fonte", "fogocerto"}
ECO = ["L17", "P02", "P04", "P05", "P13", "P16", "L32", "L34", "L38", "L40", "P24", "P30"]


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return 100 * (c - h), 100 * (c + h)


def mcnemar(a, b, ids, campo=lambda r: r["acerto"]):
    so_a = sum(1 for i in ids if campo(R[a][i]) and not campo(R[b][i]))
    so_b = sum(1 for i in ids if not campo(R[a][i]) and campo(R[b][i]))
    n, k = so_a + so_b, min(so_a, so_b)
    p = min(1.0, 2 * sum(math.comb(n, j) for j in range(k + 1)) / 2 ** n) if n else 1.0
    return so_a, so_b, p


def conteudo(r):
    if not r["alucinou"]:
        return False
    motivos = [m.strip() for m in r["motivo_alucinacao"].split(",") if m.strip()]
    return not (motivos == ["fonte inventada"] and all(f.strip().lower() in MARCADORES for f in r["fontes"]))


def grupo(*g):
    return [i for i in IDS if R["rag"][i]["grupo"] in g]


print("Acerto e IC 95% (Wilson):")
for c in R:
    k = sum(r["acerto"] for r in R[c].values())
    lo, hi = wilson(k, len(IDS))
    print(f"  {c:13s} {k}/{len(IDS)}  {lo:.1f}% a {hi:.1f}%")

print("\nMcNemar exato (só a 1ª acertou | só a 2ª acertou | p):")
for a, b, ids, nome in [("rag", "sem_contexto", IDS, "todas"), ("rag", "agente", IDS, "todas"),
                        ("rag", "agente", grupo("lei_direta", "linguagem_produtor"), "lei"),
                        ("agente", "rag", grupo("risco_do_dia"), "risco do dia")]:
    x, y, p = mcnemar(a, b, ids)
    print(f"  {a} x {b} ({nome}, n={len(ids)}): {x} | {y} | p={p:.4f}")

x, y, p = mcnemar("sem_contexto", "rag", IDS, lambda r: r["alucinou"])
print(f"\nAlucinação, sem contexto x RAG: {x} | {y} | p={p:.2e}")
print("Alucinação de conteúdo (sem marcadores do formato):",
      {c: sum(conteudo(r) for r in R[c].values()) for c in R})
x, y, p = mcnemar("sem_contexto", "rag", IDS, conteudo)
print(f"  sem contexto x RAG: {x} | {y} | p={p:.4f}")

resto = [i for i in IDS if i not in ECO]
print(f"\nAcerto sem os {len(ECO)} casos com a palavra-chave na pergunta (n={len(resto)}):",
      {c: f"{sum(R[c][i]['acerto'] for i in resto)}/{len(resto)}" for c in R})
