import pytest

from decisao import Deteccao, classe_da_imagem, decidir, prioridade

L, LD = 0.40, 0.20


def d(classe, conf):
    return Deteccao(classe, conf, (0, 0, 10, 10))


def test_sem_deteccao_e_nada():
    r = decidir([], L, LD)
    assert (r.classe, r.duvida, r.confianca) == ("nada", False, 0.0)


def test_fogo_tem_prioridade_sobre_fumaca_mais_confiante():
    r = decidir([d("fumaca", 0.9), d("fogo", 0.5)], L, LD)
    assert r.classe == "fogo" and r.confianca == 0.5 and not r.duvida


def test_fumaca_confirmada():
    r = decidir([d("fumaca", 0.7), d("fogo", 0.3)], L, LD)
    assert r.classe == "fumaca" and r.confianca == 0.7 and not r.duvida


def test_faixa_de_duvida():
    r = decidir([d("fumaca", 0.3)], L, LD)
    assert r.classe == "fumaca" and r.duvida and "Não foi possível confirmar" in r.mensagem


def test_abaixo_da_duvida_e_nada_mas_informa_maior_confianca():
    r = decidir([d("fogo", 0.1)], L, LD)
    assert r.classe == "nada" and r.confianca == 0.1 and r.deteccoes == []


def test_limiar_exato_conta_como_confirmado():
    assert classe_da_imagem([d("fogo", 0.40)], 0.40) == "fogo"


def test_json_tem_contrato_e_aviso():
    j = decidir([d("fogo", 0.876543)], L, LD).para_json()
    assert set(j) >= {"classe", "confianca", "mensagem", "duvida", "deteccoes", "aviso"}
    assert j["confianca"] == 0.877


@pytest.mark.parametrize("ld,l", [(0.5, 0.4), (0.0, 0.4), (0.2, 1.1)])
def test_limiares_invalidos(ld, l):
    with pytest.raises(ValueError):
        decidir([], l, ld)


def test_classe_e_confianca_validadas():
    with pytest.raises(ValueError):
        Deteccao("nuvem", 0.5)
    with pytest.raises(ValueError):
        Deteccao("fogo", 1.5)


@pytest.mark.parametrize(
    "dets,nivel,esperado",
    [
        ([d("fogo", 0.9)], "alto", "alta"),
        ([d("fogo", 0.9)], "baixo", "media"),
        ([d("fumaca", 0.3)], "alto", "media"),
        ([d("fumaca", 0.3)], "baixo", "baixa"),
        ([], "alto", "baixa"),
        ([d("fogo", 0.9)], None, "media"),
    ],
)
def test_prioridade(dets, nivel, esperado):
    assert prioridade(decidir(dets, L, LD), nivel) == esperado
