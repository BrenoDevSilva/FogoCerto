"""API de Visão do FogoCerto: ``POST /visao/classificar``.

Recebe uma imagem (foto do produtor hoje; quadro de câmera fixa no futuro),
devolve classe, confiança e mensagem. A imagem é processada em memória e
descartada: não é gravada em disco nem em log (LGPD).

Rodar (dentro de ``visao/``)::

    uvicorn api:app --app-dir src --port 8001

Variáveis de ambiente (todas opcionais):

- ``MODELO_PATH``: caminho do best.pt (padrão ``visao/modelos/best.pt``)
- ``LIMIAR_CONFIANCA`` / ``LIMIAR_DUVIDA``: se ausentes, lê
  ``visao/resultados/limiar_recomendado.json`` (gerado no notebook)
- ``RISCO_FONTE``: arquivo ou URL do ``risco_atual.json``
- ``CORS_ORIGENS``: origens permitidas, separadas por vírgula
"""

from __future__ import annotations

import io
import json
import logging
import os
import urllib.request
from functools import lru_cache
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from PIL import Image, ImageOps, UnidentifiedImageError

from decisao import decidir, prioridade

PASTA_VISAO = Path(__file__).resolve().parent.parent
PASTA_ESTATICOS = Path(__file__).resolve().parent / "static"
RISCO_PADRAO = PASTA_VISAO.parent / "site" / "public" / "data" / "risco_atual.json"
LIMIARES_PADRAO = {"limiar": 0.40, "limiar_duvida": 0.20}  # trocados pelo valor medido no notebook
TAM_MAX_BYTES = int(float(os.environ.get("TAM_MAX_MB", "10")) * 1024 * 1024)
TIPOS_ACEITOS = {"image/jpeg", "image/png", "image/webp"}

Image.MAX_IMAGE_PIXELS = 40_000_000  # barra "bomba de descompressão"

log = logging.getLogger("fogocerto.visao")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def carregar_limiares() -> dict:
    limiares = dict(LIMIARES_PADRAO)
    arquivo = PASTA_VISAO / "resultados" / "limiar_recomendado.json"
    if arquivo.exists():
        dados = json.loads(arquivo.read_text(encoding="utf-8"))
        limiares.update({k: float(dados[k]) for k in limiares if k in dados})
    if "LIMIAR_CONFIANCA" in os.environ:
        limiares["limiar"] = float(os.environ["LIMIAR_CONFIANCA"])
    if "LIMIAR_DUVIDA" in os.environ:
        limiares["limiar_duvida"] = float(os.environ["LIMIAR_DUVIDA"])
    return limiares


@lru_cache(maxsize=1)
def obter_detector():
    from modelo import Detector

    return Detector()


def detector_dependencia():
    try:
        return obter_detector()
    except FileNotFoundError as erro:
        log.error("modelo indisponível: %s", erro)
        raise HTTPException(503, "Modelo de visão indisponível no servidor.") from erro


def ler_risco() -> list[dict]:
    """Lê o risco do dia no mesmo arquivo que o site usa. Falha aqui não derruba a foto."""
    fonte = os.environ.get("RISCO_FONTE", str(RISCO_PADRAO))
    try:
        if fonte.startswith(("http://", "https://")):
            with urllib.request.urlopen(fonte, timeout=5) as resp:  # noqa: S310 (URL configurada pelo time)
                dados = json.load(resp)
        else:
            dados = json.loads(Path(fonte).read_text(encoding="utf-8"))
    except (OSError, ValueError) as erro:
        log.warning("risco indisponível (%s): %s", fonte, erro)
        return []
    return [i for i in dados if isinstance(i, dict)] if isinstance(dados, list) else []


def nivel_do_municipio(municipio_id: int) -> str | None:
    for item in ler_risco():
        if item.get("id_ibge") == municipio_id:
            return item.get("nivel_risco")
    return None


def abrir_imagem(conteudo: bytes) -> Image.Image:
    try:
        imagem = Image.open(io.BytesIO(conteudo))
        imagem.load()
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError) as erro:
        raise HTTPException(400, "Arquivo não é uma imagem válida.") from erro
    return ImageOps.exif_transpose(imagem).convert("RGB")  # foto de celular vem girada no EXIF


app = FastAPI(title="FogoCerto · Visão", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.environ.get("CORS_ORIGENS", "*").split(",") if o.strip()],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
def pagina_demo():
    return FileResponse(PASTA_ESTATICOS / "index.html")


@app.get("/saude")
def saude():
    return {"status": "ok", **carregar_limiares()}


@app.get("/municipios")
def municipios():
    itens = [
        {"id_ibge": i.get("id_ibge"), "nome": i.get("nome"), "nivel_risco": i.get("nivel_risco"), "data": i.get("data")}
        for i in ler_risco()
    ]
    return sorted(itens, key=lambda i: str(i["nome"]))


@app.post("/visao/classificar")
async def classificar(
    imagem: UploadFile = File(..., description="Foto JPEG, PNG ou WebP"),
    municipio_id: int | None = Form(None, description="Código IBGE do município (opcional)"),
    detector=Depends(detector_dependencia),
):
    if imagem.content_type not in TIPOS_ACEITOS:
        raise HTTPException(415, "Envie uma foto JPEG, PNG ou WebP.")
    conteudo = await imagem.read(TAM_MAX_BYTES + 1)
    if len(conteudo) > TAM_MAX_BYTES:
        raise HTTPException(413, f"Imagem maior que {TAM_MAX_BYTES // (1024 * 1024)} MB.")
    if not conteudo:
        raise HTTPException(400, "Arquivo vazio.")

    foto = abrir_imagem(conteudo)
    del conteudo  # não guardamos a imagem

    limiares = carregar_limiares()
    resultado = decidir(detector.detectar(foto), limiares["limiar"], limiares["limiar_duvida"])
    resposta = resultado.para_json()

    if municipio_id is not None:
        nivel = nivel_do_municipio(municipio_id)
        resposta["municipio_id"] = municipio_id
        resposta["risco_municipio"] = nivel
        resposta["prioridade"] = prioridade(resultado, nivel)

    # Log sem a imagem e sem dado pessoal: só o que a auditoria precisa.
    log.info(
        "classificacao classe=%s confianca=%.3f duvida=%s municipio=%s",
        resultado.classe, resultado.confianca, resultado.duvida, municipio_id,
    )
    return resposta
