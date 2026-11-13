import threading
from datetime import date
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from conftest import DADOS
from fonte import DadoInvalido, FonteIndisponivel, interpretar, ler_bruto

HOJE = date(2026, 11, 8)


def test_valido():
    ms, probs = interpretar((DADOS / "risco_valido.json").read_bytes(), HOJE)
    assert [m.nome for m in ms] == ["Monte Alegre", "Oriximiná", "Abaetetuba", "Castanhal"]
    assert probs == []
    assert ms[0].fatores[0] == "umidade minima de 39%"


def test_itens_com_problema_sao_ignorados_e_explicados():
    ms, probs = interpretar((DADOS / "risco_com_problemas.json").read_bytes(), HOJE)
    assert [m.nome for m in ms] == ["Monte Alegre"]
    texto = " | ".join(probs)
    for trecho in ("repetido", "nivel_risco desconhecido", "data futura", "id_ibge ausente", "focos_ontem inválido"):
        assert trecho in texto
    assert len(probs) == 5


@pytest.mark.parametrize("arquivo,trecho", [
    ("risco_quebrado.json", "JSON ilegível"),
    ("risco_vazio.json", "sem municípios"),
])
def test_arquivo_inteiro_invalido(arquivo, trecho):
    with pytest.raises(DadoInvalido, match=trecho):
        interpretar((DADOS / arquivo).read_bytes(), HOJE)


def test_formato_errado():
    with pytest.raises(DadoInvalido, match="lista"):
        interpretar(b'{"municipios": []}', HOJE)


def test_todos_invalidos():
    with pytest.raises(DadoInvalido, match="nenhum município válido"):
        interpretar(b'[{"id_ibge": 1, "nome": "X", "data": "2026-11-07", "nivel_risco": "?"}]', HOJE)


def test_arquivo_ausente_tenta_de_novo_e_desiste(tmp_path):
    with pytest.raises(FonteIndisponivel, match="não encontrado"):
        ler_bruto(str(tmp_path / "nao_existe.json"), tentativas=3, espera_s=0)


class _Servidor:
    """Servidor HTTP local que falha nas primeiras N chamadas (simula API fora do ar)."""

    def __init__(self, falhas, codigo=503, corpo=b"[]"):
        estado = {"chamadas": 0}

        class H(BaseHTTPRequestHandler):
            def do_GET(self):
                estado["chamadas"] += 1
                if estado["chamadas"] <= falhas:
                    self.send_response(codigo)
                    self.end_headers()
                    return
                self.send_response(200)
                self.end_headers()
                self.wfile.write(corpo)

            def log_message(self, *a):
                pass

        self.estado = estado
        self.srv = HTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.srv.server_port}/data/risco_atual.json"
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def fechar(self):
        self.srv.shutdown()


def test_api_instavel_recupera_na_terceira_tentativa():
    s = _Servidor(falhas=2, corpo=b"ok")
    try:
        assert ler_bruto(s.url, tentativas=3, espera_s=0) == b"ok"
        assert s.estado["chamadas"] == 3
    finally:
        s.fechar()


def test_api_fora_do_ar_desiste():
    s = _Servidor(falhas=99)
    try:
        with pytest.raises(FonteIndisponivel, match="HTTP 503"):
            ler_bruto(s.url, tentativas=3, espera_s=0)
        assert s.estado["chamadas"] == 3
    finally:
        s.fechar()


def test_404_nao_insiste():
    s = _Servidor(falhas=99, codigo=404)
    try:
        with pytest.raises(FonteIndisponivel, match="HTTP 404"):
            ler_bruto(s.url, tentativas=3, espera_s=0)
        assert s.estado["chamadas"] == 1
    finally:
        s.fechar()
