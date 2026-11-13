"""Adaptador entre o Ultralytics YOLO e a regra de decisão.

Carrega o peso treinado (best.pt) uma única vez e converte a saída do modelo em
uma lista de ``Deteccao``. A imagem só existe em memória: nada é gravado em disco.
"""

from __future__ import annotations

import os
from pathlib import Path

from PIL import Image

from decisao import CLASSES, Deteccao

PASTA_VISAO = Path(__file__).resolve().parent.parent
MODELO_PADRAO = PASTA_VISAO / "modelos" / "best.pt"


class Detector:
    def __init__(self, caminho: str | os.PathLike | None = None, tam_img: int = 640):
        caminho = Path(caminho or os.environ.get("MODELO_PATH", MODELO_PADRAO))
        if not caminho.exists():
            raise FileNotFoundError(
                f"Modelo não encontrado em {caminho}. Baixe o best.pt (ver visao/README.md) "
                "ou aponte MODELO_PATH para ele."
            )
        # Sem isso o Ultralytics instala pacotes com pip em tempo de execução (ruim em servidor).
        os.environ.setdefault("YOLO_AUTOINSTALL", "false")
        from ultralytics import YOLO  # import tardio: os testes não precisam do Ultralytics

        self.modelo = YOLO(str(caminho))
        self.tam_img = tam_img
        nomes = {int(k): v for k, v in self.modelo.names.items()}
        # O notebook treina com os nomes em português; se o peso vier com os nomes
        # originais do D-Fire (smoke/fire), traduz pela posição.
        traducao = {"smoke": "fumaca", "fire": "fogo"}
        self.nomes = {k: traducao.get(v.lower(), v) for k, v in nomes.items()}
        if set(self.nomes.values()) != set(CLASSES):
            raise ValueError(f"o modelo tem classes inesperadas: {self.nomes}")

    def detectar(self, imagem: Image.Image, conf_minima: float = 0.05) -> list[Deteccao]:
        resultado = self.modelo.predict(
            imagem, imgsz=self.tam_img, conf=conf_minima, verbose=False
        )[0]
        return converter(resultado, self.nomes)


def converter(resultado, nomes: dict[int, str]) -> list[Deteccao]:
    """Converte um ``ultralytics.engine.results.Results`` em ``Deteccao``."""
    caixas = resultado.boxes
    if caixas is None or len(caixas) == 0:
        return []
    saida = []
    for cls, conf, xyxy in zip(
        caixas.cls.tolist(), caixas.conf.tolist(), caixas.xyxy.tolist()
    ):
        saida.append(Deteccao(nomes[int(cls)], float(conf), tuple(xyxy)))
    return saida
