"""Testes de ponta a ponta do fluxo, com o canal simulado (nada sai da máquina)."""

import json
from pathlib import Path

from envio import Simulado
from executar import ABORTADO, COM_FALHAS, OK, executar
from conftest import DADOS

DESTINOS = [a["destino"] for a in json.loads((DADOS / "assinantes_teste.json").read_text(encoding="utf-8"))]


def canais_simulados(**kw):
    s = Simulado(**kw)
    return s, {"telegram": s, "email": s}


def todo_texto_gravado(raiz: Path) -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in raiz.rglob("*") if p.is_file())


def test_sucesso_envia_para_risco_alto_e_publica_no_site(cfg, tmp_path):
    s, canais = canais_simulados()
    codigo, resumo = executar(cfg(), canais)
    assert codigo == OK and resumo["status"] == "concluido"
    c = resumo["contagens"]
    assert c["enviados"] == 3 and c["municipios_com_alerta"] == 2 and c["sem_alerta"] == 2
    assuntos = [a for _, a, _ in s.enviadas]
    assert assuntos.count("FogoCerto · risco ALTO em Monte Alegre (PA)") == 2
    assert any("Oriximiná" in a for a in assuntos)

    site = json.loads((tmp_path / "site" / "alertas.json").read_text(encoding="utf-8"))
    assert {a["nome"] for a in site["alertas"]} == {"Monte Alegre", "Oriximiná"}
    monte = next(a for a in site["alertas"] if a["nome"] == "Monte Alegre")
    assert monte["assinantes_avisados"] == 2 and monte["data_dado"] == "2026-11-07"
    assert site["ultima_execucao"]["status"] == "concluido"


def test_decisao_risco_baixo_e_medio_sem_focos_nao_recebem(cfg):
    s, canais = canais_simulados()
    executar(cfg(), canais)
    textos = " ".join(t for _, _, t in s.enviadas)
    assert "Castanhal" not in textos and "Abaetetuba" not in textos


def test_falha_fonte_ausente_aborta_sem_enviar(cfg, tmp_path):
    s, canais = canais_simulados()
    codigo, resumo = executar(cfg(str(tmp_path / "sumiu.json")), canais)
    assert codigo == ABORTADO and resumo["status"] == "abortado_fonte_indisponivel"
    assert s.enviadas == []
    site = json.loads((tmp_path / "site" / "alertas.json").read_text(encoding="utf-8"))
    assert site["alertas"] == [] and site["ultima_execucao"]["status"] == "abortado_fonte_indisponivel"


def test_falha_json_quebrado_aborta_sem_enviar(cfg):
    s, canais = canais_simulados()
    codigo, resumo = executar(cfg("risco_quebrado.json"), canais)
    assert codigo == ABORTADO and resumo["status"] == "abortado_dado_invalido" and s.enviadas == []


def test_itens_ruins_sao_pulados_e_o_resto_segue(cfg):
    s, canais = canais_simulados()
    codigo, resumo = executar(cfg("risco_com_problemas.json"), canais)
    assert codigo == OK
    assert resumo["contagens"]["itens_invalidos"] == 5
    assert resumo["contagens"]["enviados"] == 2  # só Monte Alegre, uma vez por assinante


def test_segunda_execucao_nao_reenvia(cfg):
    s, canais = canais_simulados()
    executar(cfg(), canais)
    codigo, resumo = executar(cfg(), canais)
    assert codigo == OK
    assert resumo["contagens"].get("enviados", 0) == 0
    assert resumo["contagens"]["duplicados_nao_reenviados"] == 3
    assert len(s.enviadas) == 3


def test_dado_atrasado_e_retido(cfg):
    s, canais = canais_simulados()
    _, resumo = executar(cfg(hoje="2026-11-13"), canais)  # dado de 07/11 com 6 dias
    assert resumo["contagens"]["retidos_dado_atrasado"] == 4 and s.enviadas == []


def test_data_referencia_antes_do_dado_vira_data_futura(cfg):
    s, canais = canais_simulados()
    codigo, resumo = executar(cfg(hoje="2026-11-06"), canais)
    assert codigo == ABORTADO and "data futura" in " ".join(resumo["erros"])


def test_falha_de_um_envio_nao_para_os_outros(cfg):
    s, canais = canais_simulados(falhar_para={"111111111"})
    codigo, resumo = executar(cfg(), canais)
    assert codigo == COM_FALHAS and resumo["status"] == "concluido_com_falhas"
    assert resumo["contagens"]["falhas_envio"] == 1 and resumo["contagens"]["enviados"] == 2


def test_falha_reenviada_na_proxima_execucao(cfg):
    _, canais = canais_simulados(falhar_para={"111111111"})
    executar(cfg(), canais)
    s2, canais_ok = canais_simulados()
    _, resumo = executar(cfg(), canais_ok)
    assert resumo["contagens"]["enviados"] == 1  # só o que falhou antes
    assert resumo["contagens"]["duplicados_nao_reenviados"] == 2


def test_canal_sem_configuracao_falha_so_esse_assinante(cfg):
    s = Simulado()
    codigo, resumo = executar(cfg(), {"telegram": s, "email": ValueError("SMTP não configurado")})
    assert codigo == COM_FALHAS
    assert resumo["contagens"]["enviados"] == 2 and resumo["contagens"]["falhas_envio"] == 1


def test_assinantes_ausentes_aborta(cfg, tmp_path):
    c = cfg()
    c.assinantes = str(tmp_path / "nao_existe.json")
    s, canais = canais_simulados()
    codigo, resumo = executar(c, canais)
    assert codigo == ABORTADO and resumo["status"] == "abortado_assinantes" and s.enviadas == []


def test_lgpd_nenhum_contato_em_log_estado_ou_site(cfg, tmp_path):
    _, canais = canais_simulados(falhar_para={"222222222"})
    executar(cfg(), canais)
    executar(cfg(), canais)
    gravado = todo_texto_gravado(tmp_path)
    assert gravado  # há log, estado, resumo e alertas.json
    for destino in DESTINOS:
        assert destino not in gravado


def test_log_tem_data_hora_itens_e_resultado(cfg, tmp_path):
    _, canais = canais_simulados()
    executar(cfg(), canais)
    log = next((tmp_path / "logs").glob("rpa_*.log")).read_text(encoding="utf-8")
    assert "inicio execucao=" in log and "fim status=concluido" in log
    assert "municipio=Monte Alegre" in log and "resultado=enviado" in log
    assert "decisao=sem_alerta_risco_baixo" in log
    resumo = next((tmp_path / "logs" / "execucoes").glob("*.json"))
    assert json.loads(resumo.read_text(encoding="utf-8"))["contagens"]["enviados"] == 3
