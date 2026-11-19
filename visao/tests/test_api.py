import io
import json

import pytest
from fastapi.testclient import TestClient
from PIL import Image

import api
from decisao import Deteccao


class DetectorFalso:
    def __init__(self, deteccoes):
        self.deteccoes = deteccoes
        self.chamadas = 0

    def detectar(self, imagem):
        assert isinstance(imagem, Image.Image) and imagem.mode == "RGB"
        self.chamadas += 1
        return self.deteccoes


def png(tamanho=(64, 48)):
    buf = io.BytesIO()
    Image.new("RGB", tamanho, (200, 120, 40)).save(buf, "PNG")
    return buf.getvalue()


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    risco = [{"id_ibge": 1504802, "nome": "Monte Alegre", "nivel_risco": "alto", "data": "2026-11-07"},
             {"id_ibge": 1500107, "nome": "Abaetetuba", "nivel_risco": "baixo", "data": "2026-11-07"}]
    arq = tmp_path / "risco.json"
    arq.write_text(json.dumps(risco), encoding="utf-8")
    monkeypatch.setenv("RISCO_FONTE", str(arq))
    monkeypatch.setenv("LIMIAR_CONFIANCA", "0.40")
    monkeypatch.setenv("LIMIAR_DUVIDA", "0.20")
    falso = DetectorFalso([Deteccao("fogo", 0.83, (1, 2, 30, 40))])
    api.app.dependency_overrides[api.detector_dependencia] = lambda: falso
    yield TestClient(api.app), falso
    api.app.dependency_overrides.clear()


def enviar(c, conteudo, tipo="image/png", **form):
    return c.post("/visao/classificar", files={"imagem": ("foto.png", conteudo, tipo)}, data=form)


def test_classifica_fogo_com_contrato(cliente):
    c, _ = cliente
    r = enviar(c, png())
    assert r.status_code == 200
    j = r.json()
    assert j["classe"] == "fogo" and j["confianca"] == 0.83 and j["duvida"] is False
    assert "193" in j["mensagem"]
    assert "prioridade" not in j


def test_cruza_com_risco_do_municipio(cliente):
    c, _ = cliente
    j = enviar(c, png(), municipio_id="1504802").json()
    assert j["risco_municipio"] == "alto" and j["prioridade"] == "alta"
    j = enviar(c, png(), municipio_id="1500107").json()
    assert j["risco_municipio"] == "baixo" and j["prioridade"] == "media"


def test_municipio_desconhecido_nao_quebra(cliente):
    c, _ = cliente
    j = enviar(c, png(), municipio_id="999").json()
    assert j["risco_municipio"] is None and j["prioridade"] == "media"


def test_arquivo_que_nao_e_imagem(cliente):
    c, falso = cliente
    r = enviar(c, b"isto nao e uma imagem")
    assert r.status_code == 400 and falso.chamadas == 0


def test_tipo_nao_aceito(cliente):
    c, _ = cliente
    assert enviar(c, b"%PDF-1.4", tipo="application/pdf").status_code == 415


def test_arquivo_grande(cliente, monkeypatch):
    c, _ = cliente
    monkeypatch.setattr(api, "TAM_MAX_BYTES", 100)
    assert enviar(c, png((400, 400))).status_code == 413


def test_vazio(cliente):
    c, _ = cliente
    assert enviar(c, b"").status_code == 400


def test_nao_grava_nada_em_disco(cliente, tmp_path, monkeypatch):
    c, _ = cliente
    monkeypatch.chdir(tmp_path)
    antes = set(tmp_path.rglob("*"))
    enviar(c, png())
    assert set(tmp_path.rglob("*")) == antes


def test_modelo_ausente_da_503(monkeypatch, tmp_path):
    monkeypatch.setenv("MODELO_PATH", str(tmp_path / "nao_existe.pt"))
    api.obter_detector.cache_clear()
    c = TestClient(api.app)
    assert enviar(c, png()).status_code == 503
    api.obter_detector.cache_clear()


def test_municipios_e_saude(cliente):
    c, _ = cliente
    nomes = [m["nome"] for m in c.get("/municipios").json()]
    assert nomes == ["Abaetetuba", "Monte Alegre"]
    s = c.get("/saude").json()
    assert s["limiar"] == 0.40 and s["limiar_duvida"] == 0.20


def test_pagina_demo(cliente):
    c, _ = cliente
    r = c.get("/")
    assert r.status_code == 200 and "Checar foto" in r.text
