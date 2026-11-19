"""Testa o modelo nas imagens próprias do grupo, sem precisar do Colab.

Mesmo resultado da seção 8 do notebook: coloque as fotos em ``visao/imagens_proprias/``
com o nome começando pela resposta certa (``fogo_``, ``fumaca_`` ou ``nada_``) e rode:

    python src/avaliar_proprias.py

Gera ``resultados/imagens_proprias_resultados.csv`` e ``resultados/imagens_proprias.png``.
A pasta das fotos fica fora do Git (LGPD: sem rosto, placa ou endereço).
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

VISAO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from decisao import decidir  # noqa: E402

EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
COR = {"fogo": "red", "fumaca": "deepskyblue"}


def main() -> int:
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--pasta", default=str(VISAO / "imagens_proprias"))
    a.add_argument("--resultados", default=str(VISAO / "resultados"))
    a.add_argument("--modelo", default=str(VISAO / "modelos" / "best.pt"))
    args = a.parse_args()

    pasta, saida = Path(args.pasta), Path(args.resultados)
    fotos = sorted(p for p in pasta.glob("*") if p.suffix.lower() in EXT) if pasta.exists() else []
    if not fotos:
        print(f"Nenhuma foto em {pasta}. Coloque fotos com nome fogo_..., fumaca_... ou nada_...")
        return 1
    invalidas = [p.name for p in fotos if p.stem.split("_")[0].lower() not in ("fogo", "fumaca", "nada")]
    if invalidas:
        print("Estes nomes não começam com fogo_, fumaca_ ou nada_:", ", ".join(invalidas))
        return 1

    lim = json.loads((saida / "limiar_recomendado.json").read_text(encoding="utf-8"))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.patches as patches
    import matplotlib.pyplot as plt
    from PIL import Image, ImageOps

    from modelo import Detector

    det = Detector(args.modelo)
    linhas, itens = [], []
    for p in fotos:
        real = p.stem.split("_")[0].lower()
        img = ImageOps.exif_transpose(Image.open(p)).convert("RGB")
        dets = det.detectar(img)
        res = decidir(dets, lim["limiar"], lim["limiar_duvida"])
        previsto = "nada" if res.duvida else res.classe
        conf = max((d.confianca for d in dets), default=0.0)
        linhas.append({"arquivo": p.name, "real": real, "previsto": previsto, "duvida": res.duvida,
                       "maior_confianca": round(conf, 3), "acertou": real == previsto})
        itens.append((img, [d for d in dets if d.confianca >= lim["limiar_duvida"]],
                       f"{p.name}\nreal {real} · previsto {previsto}{' (dúvida)' if res.duvida else ''}"))

    with open(saida / "imagens_proprias_resultados.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)

    itens = itens[:16]
    colunas = min(4, len(itens))
    n_lin = (len(itens) + colunas - 1) // colunas
    fig, axs = plt.subplots(n_lin, colunas, figsize=(4 * colunas, 3.3 * n_lin), squeeze=False)
    for ax in axs.flat:
        ax.axis("off")
    for ax, (img, caixas, titulo) in zip(axs.flat, itens):
        ax.imshow(img)
        for d in caixas:
            x1, y1, x2, y2 = d.caixa
            ax.add_patch(patches.Rectangle((x1, y1), x2 - x1, y2 - y1, fill=False, ec=COR[d.classe], lw=2))
            ax.text(x1, y1, f"{d.classe} {d.confianca:.2f}", color="white", fontsize=7,
                    bbox=dict(facecolor=COR[d.classe], alpha=.7, pad=1, lw=0))
        ax.set_title(titulo, fontsize=8)
    fig.suptitle("Imagens próprias do grupo", fontsize=11)
    fig.tight_layout()
    fig.savefig(saida / "imagens_proprias.png", dpi=110)

    acertos = sum(l["acertou"] for l in linhas)
    print(f"acertos: {acertos}/{len(linhas)}")
    for l in linhas:
        print(f"  {l['arquivo']}: real {l['real']}, previsto {l['previsto']}"
              f"{' (dúvida)' if l['duvida'] else ''} -> {'ok' if l['acertou'] else 'ERRO'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
