"""Roda os cenários de teste exigidos (sucesso, decisão e falha) e guarda as evidências.

Uso (dentro de ``rpa/``)::

    python tests/gerar_evidencias.py

Cada cenário grava em ``tests/evidencias/<cenario>/``: o log, o resumo da execução
(JSON), a caixa de saída simulada e o ``alertas.json`` que o site leria. Nada é
enviado de verdade e os contatos são fictícios (``tests/dados/assinantes_teste.json``).
"""

import json
import shutil
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "src"))

from envio import Simulado  # noqa: E402
from executar import configuracao, executar  # noqa: E402

DADOS = AQUI / "dados"
SAIDA = AQUI / "evidencias"

CENARIOS = [
    ("01_sucesso_risco_alto", "risco_valido.json", {}, "risco alto e médio com muitos focos: alertas enviados"),
    ("02_decisao_sem_alerta", "risco_sem_alerta.json", {}, "só risco baixo/médio sem focos: nenhum alerta"),
    ("03_falha_fonte_ausente", "nao_existe.json", {}, "arquivo de risco ausente: 3 tentativas e aborta sem enviar"),
    ("04_falha_json_invalido", "risco_quebrado.json", {}, "JSON quebrado: aborta sem enviar"),
    ("05_dados_inconsistentes", "risco_com_problemas.json", {}, "itens repetidos/inválidos ignorados, o resto segue"),
    ("06_falha_de_envio", "risco_valido.json", {"falhar_para": {"111111111"}}, "um envio falha, os outros seguem"),
    ("07_duplicado_nao_reenvia", "risco_valido.json", {"repetir": True}, "segunda execução no mesmo dia não reenvia"),
]


def rodar(nome, fonte, opcoes, descricao):
    pasta = SAIDA / nome
    shutil.rmtree(pasta, ignore_errors=True)
    cfg = configuracao([
        "--fonte", str(DADOS / fonte),
        "--assinantes", str(DADOS / "assinantes_teste.json"),
        "--saida-mvp", str(pasta / "alertas.json"),
        "--pasta-logs", str(pasta),
        "--estado", str(pasta / "estado_enviados.json"),
        "--data-referencia", "2026-11-08",
        "--espera", "0.2",
        "--simular",
    ])
    canal = Simulado(pasta / "caixa_simulada.txt", falhar_para=opcoes.get("falhar_para"))
    canais = {"telegram": canal, "email": canal}
    codigo, resumo = executar(cfg, canais)
    if opcoes.get("repetir"):
        codigo, resumo = executar(cfg, canais)
    return {"cenario": nome, "descricao": descricao, "codigo_saida": codigo, "status": resumo["status"],
            "contagens": resumo["contagens"]}


if __name__ == "__main__":
    SAIDA.mkdir(exist_ok=True)
    resultados = [rodar(*c) for c in CENARIOS]
    (SAIDA / "resumo_cenarios.json").write_text(json.dumps(resultados, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\n=== Resumo ===")
    for r in resultados:
        print(f"{r['cenario']:28} saída={r['codigo_saida']} status={r['status']:30} {r['contagens']}")
