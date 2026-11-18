"""Sorteia a amostra da auditoria manual da métrica (avaliacao/auditoria_metrica.md).

Uso, na raiz do repositório:  python avaliacao/amostra_auditoria.py

População: respostas do RAG e do agente nas perguntas de lei (grupos lei_direta e
linguagem_produtor) do conjunto de teste que não foram recusadas. Sorteio de 20 com a semente 7.
Mostra o veredito da métrica para cada resposta; a leitura humana está na tabela da auditoria.
"""
import json
import random
from pathlib import Path

PASTA = Path(__file__).resolve().parent
GRUPOS_LEI = ("lei_direta", "linguagem_produtor")

populacao = []
for config in ("rag", "agente"):
    for r in json.loads((PASTA / f"respostas_{config}.json").read_text(encoding="utf-8")):
        if r["grupo"] in GRUPOS_LEI and not r["recusou"]:
            populacao.append((config, r))

amostra = random.Random(7).sample(populacao, 20)
print(f"População: {len(populacao)} respostas. Amostra: {len(amostra)}.\n")
for n, (config, r) in enumerate(amostra, 1):
    veredito = "acerto" if r["acerto"] else "erro"
    print(f"{n:2d}. {config:7s} {r['id']:4s} métrica: {veredito:6s} | {r['pergunta']}")
    print(f"    resposta: {r['resposta'][:300]}\n")
