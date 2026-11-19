from datetime import date

import pytest

from fonte import Municipio
from regras import FRASE_OBRIGATORIA, decidir, montar_mensagem

HOJE = date(2026, 11, 8)


def mun(nivel="alto", focos=10, data=date(2026, 11, 7), fatores=("umidade minima de 25%",)):
    return Municipio(1504802, "Monte Alegre", "PA", data, nivel, 6, list(fatores), focos)


@pytest.mark.parametrize("nivel,focos,alertar,motivo", [
    ("alto", 0, True, "risco_alto"),
    ("medio", 100, True, "risco_medio_muitos_focos"),
    ("medio", 99, False, "sem_alerta_risco_medio"),
    ("baixo", 500, False, "sem_alerta_risco_baixo"),
])
def test_decisao_por_nivel_e_focos(nivel, focos, alertar, motivo):
    d = decidir(mun(nivel, focos), HOJE)
    assert (d.alertar, d.motivo) == (alertar, motivo)


@pytest.mark.parametrize("data,alertar", [
    (date(2026, 11, 7), True),   # ontem: normal
    (date(2026, 11, 6), True),   # 2 dias: ainda aceito, com aviso
    (date(2026, 11, 5), False),  # 3 dias: retido
])
def test_regra_da_data(data, alertar):
    d = decidir(mun(data=data), HOJE, max_atraso_dias=2)
    assert d.alertar is alertar
    if not alertar:
        assert d.motivo == "retido_dado_atrasado"


def test_mensagem_de_risco_alto():
    m = mun()
    assunto, texto = montar_mensagem(m, decidir(m, HOJE))
    assert assunto == "FogoCerto · risco ALTO em Monte Alegre (PA)"
    assert "dados fechados de 07/11" in texto
    assert "Não faça queima" in texto and "199" in texto and "193" in texto
    assert texto.endswith(FRASE_OBRIGATORIA)
    assert "hoje há risco" not in texto.lower()
    assert "autoriz" not in texto.replace(FRASE_OBRIGATORIA, "").lower()


def test_mensagem_avisa_dado_atrasado():
    m = mun(data=date(2026, 11, 6))
    _, texto = montar_mensagem(m, decidir(m, HOJE))
    assert "dado mais recente disponível (06/11)" in texto


def test_mensagem_de_atencao_por_focos():
    m = mun("medio", 120, fatores=())
    assunto, texto = montar_mensagem(m, decidir(m, HOJE))
    assert "atenção" in assunto and "120 focos" in assunto
    assert "Evite queimar" in texto and FRASE_OBRIGATORIA in texto
