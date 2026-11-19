"""FogoCerto · RPA: alerta diário de risco de fogo aos assinantes.

Fluxo: ler o risco -> validar -> para cada município: decidir -> para cada
assinante: evitar duplicado -> enviar -> registrar -> publicar o resultado para o site.

Uso (dentro de ``rpa/``)::

    python src/executar.py                      # execução normal (agendada todo dia)
    python src/executar.py --simular            # não envia: grava em logs/execucao/caixa_simulada.txt
    python src/executar.py --data-referencia 2026-11-08 --simular

Códigos de saída: 0 = ok, 1 = terminou com falha de envio, 2 = abortado (sem dado ou sem assinantes).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from envio import AssinantesInvalidos, Email, EnvioFalhou, Simulado, Telegram, carregar_assinantes  # noqa: E402
from estado import Registro, gravar_json, publicar_alertas  # noqa: E402
from fonte import DadoInvalido, FonteIndisponivel, interpretar, ler_bruto  # noqa: E402
from regras import decidir, montar_mensagem  # noqa: E402

PASTA_RPA = Path(__file__).resolve().parent.parent
BRASILIA = timezone(timedelta(hours=-3))  # sem horário de verão desde 2019
log = logging.getLogger("fogocerto.rpa")

OK, COM_FALHAS, ABORTADO = 0, 1, 2


def carregar_env(arquivo: Path) -> None:
    """Lê um .env simples (CHAVE=valor) sem sobrescrever o ambiente. O .env não vai para o Git."""
    if not arquivo.exists():
        return
    for linha in arquivo.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if linha and not linha.startswith("#") and "=" in linha:
            chave, valor = linha.split("=", 1)
            os.environ.setdefault(chave.strip(), valor.strip().strip('"').strip("'"))


def configuracao(argv: list[str] | None = None) -> argparse.Namespace:
    carregar_env(PASTA_RPA / ".env")
    env = os.environ.get
    p = argparse.ArgumentParser(description="Alerta diário do FogoCerto")
    p.add_argument("--fonte", default=env("RISCO_FONTE", str(PASTA_RPA.parent / "site/public/data/risco_atual.json")),
                   help="arquivo ou URL do risco_atual.json")
    p.add_argument("--assinantes", default=env("ASSINANTES_ARQUIVO", str(PASTA_RPA / "config/assinantes.json")))
    p.add_argument("--saida-mvp", default=env("SAIDA_MVP", str(PASTA_RPA.parent / "site/public/data/alertas.json")),
                   help="alertas.json lido pelo site")
    p.add_argument("--pasta-logs", default=env("PASTA_LOGS", str(PASTA_RPA / "logs/execucao")))
    p.add_argument("--estado", default=env("ESTADO_ARQUIVO", str(PASTA_RPA / "estado/enviados.json")))
    p.add_argument("--limiar-focos", type=int, default=int(env("LIMIAR_FOCOS", "100")))
    p.add_argument("--max-atraso-dias", type=int, default=int(env("MAX_ATRASO_DIAS", "2")))
    p.add_argument("--tentativas", type=int, default=int(env("TENTATIVAS", "3")))
    p.add_argument("--espera", type=float, default=float(env("ESPERA_S", "2")), help="segundos antes da 2ª tentativa")
    p.add_argument("--data-referencia", type=date.fromisoformat, default=None,
                   help="'hoje' para a regra da data (AAAA-MM-DD); padrão: hoje em Brasília")
    p.add_argument("--simular", action="store_true", help="não envia de verdade; grava numa caixa local")
    p.add_argument("--sem-publicar", action="store_true", help="não atualiza o alertas.json do site")
    return p.parse_args(argv)


def preparar_log(pasta: Path, agora: datetime) -> Path:
    pasta.mkdir(parents=True, exist_ok=True)
    arquivo = pasta / f"rpa_{agora:%Y-%m-%d}.log"
    log.setLevel(logging.INFO)
    fechar_log()
    fmt = logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s", "%Y-%m-%d %H:%M:%S")
    for h in (logging.FileHandler(arquivo, encoding="utf-8"), logging.StreamHandler(sys.stdout)):
        h.setFormatter(fmt)
        log.addHandler(h)
    log.propagate = False
    return arquivo


def fechar_log() -> None:
    for h in list(log.handlers):
        h.close()
        log.removeHandler(h)


def criar_canais(cfg: argparse.Namespace, pasta_logs: Path) -> dict:
    """Um enviador por canal. Canal sem configuração vira erro na hora de enviar, não aborta tudo."""
    if cfg.simular:
        simulado = Simulado(pasta_logs / "caixa_simulada.txt")
        return {"telegram": simulado, "email": simulado}
    canais: dict = {}
    try:
        canais["telegram"] = Telegram(os.environ.get("TELEGRAM_BOT_TOKEN", ""), cfg.tentativas, cfg.espera)
    except ValueError as erro:
        canais["telegram"] = erro
    try:
        canais["email"] = Email(os.environ.get("SMTP_HOST", ""), int(os.environ.get("SMTP_PORTA", "587")),
                                os.environ.get("SMTP_USUARIO", ""), os.environ.get("SMTP_SENHA", ""),
                                os.environ.get("SMTP_REMETENTE", ""))
    except ValueError as erro:
        canais["email"] = erro
    return canais


def descrever_fonte(fonte: str) -> str:
    return fonte if fonte.startswith(("http://", "https://")) else Path(fonte).name


def executar(cfg: argparse.Namespace, canais: dict | None = None) -> tuple[int, dict]:
    agora = datetime.now(BRASILIA)
    hoje = cfg.data_referencia or agora.date()
    pasta_logs = Path(cfg.pasta_logs)
    arquivo_log = preparar_log(pasta_logs, agora)
    id_execucao = agora.strftime("%Y%m%dT%H%M%S")
    cont: Counter = Counter()
    resumo = {
        "id_execucao": id_execucao, "inicio": agora.isoformat(timespec="seconds"), "status": "em_andamento",
        "fonte": descrever_fonte(cfg.fonte), "data_referencia": hoje.isoformat(), "data_dado": None,
        "simulado": cfg.simular, "contagens": cont, "problemas_no_dado": [], "erros": [],
    }
    novos_alertas: list[dict] = []
    log.info("inicio execucao=%s fonte=%s hoje=%s simulado=%s", id_execucao, resumo["fonte"], hoje, cfg.simular)

    def encerrar(status: str, codigo: int) -> tuple[int, dict]:
        resumo["status"] = status
        resumo["fim"] = datetime.now(BRASILIA).isoformat(timespec="seconds")
        resumo["contagens"] = dict(cont)
        gravar_json(pasta_logs / "execucoes" / f"{id_execucao}.json", resumo)
        if not cfg.sem_publicar:
            try:
                publicar_alertas(Path(cfg.saida_mvp), novos_alertas, resumo, hoje)
                log.info("site atualizado: %s (%d alertas novos)", Path(cfg.saida_mvp).name, len(novos_alertas))
            except OSError as erro:
                log.error("falha ao publicar para o site: %s", erro)
                resumo["erros"].append(f"publicar: {erro}")
        log.info("fim status=%s contagens=%s log=%s", status, json.dumps(dict(cont), ensure_ascii=False), arquivo_log.name)
        fechar_log()
        return codigo, resumo

    # 1. Ler e validar o risco ------------------------------------------------------------
    try:
        bruto = ler_bruto(cfg.fonte, cfg.tentativas, cfg.espera)
        municipios, problemas = interpretar(bruto, hoje)
    except FonteIndisponivel as erro:
        log.error("ABORTADO: fonte indisponível (%s). Nenhum alerta enviado.", erro)
        resumo["erros"].append(f"fonte indisponível: {erro}")
        return encerrar("abortado_fonte_indisponivel", ABORTADO)
    except DadoInvalido as erro:
        log.error("ABORTADO: dado inválido (%s). Nenhum alerta enviado.", erro)
        resumo["erros"].append(f"dado inválido: {erro}")
        return encerrar("abortado_dado_invalido", ABORTADO)

    for prob in problemas:
        log.warning("item ignorado: %s", prob)
    resumo["problemas_no_dado"] = problemas
    cont["municipios_lidos"] = len(municipios)
    cont["itens_invalidos"] = len(problemas)
    resumo["data_dado"] = max(m.data for m in municipios).isoformat()

    # 2. Assinantes -------------------------------------------------------------------------
    try:
        assinantes = carregar_assinantes(cfg.assinantes)
    except AssinantesInvalidos as erro:
        log.error("ABORTADO: %s", erro)
        resumo["erros"].append(str(erro))
        return encerrar("abortado_assinantes", ABORTADO)
    log.info("assinantes carregados: %d em %d municípios",
             sum(len(v) for v in assinantes.values()), len(assinantes))

    canais = canais if canais is not None else criar_canais(cfg, pasta_logs)
    registro = Registro(cfg.estado)

    # 3. Repetição por município, decisão e repetição por assinante -------------------------
    for m in municipios:
        decisao = decidir(m, hoje, cfg.limiar_focos, cfg.max_atraso_dias)
        base = f"municipio={m.nome} id={m.id_ibge} nivel={m.nivel_risco} focos={m.focos_ontem} data={m.data}"
        if not decisao.alertar:
            cont["retidos_dado_atrasado" if decisao.motivo.startswith("retido") else "sem_alerta"] += 1
            log.info("%s decisao=%s", base, decisao.motivo)
            continue

        cont["municipios_com_alerta"] += 1
        lista = assinantes.get(m.id_ibge, [])
        if not lista:
            cont["sem_assinante"] += 1
            log.info("%s decisao=%s resultado=sem_assinante", base, decisao.motivo)
            continue

        assunto, texto = montar_mensagem(m, decisao)
        enviados = falhas = 0
        for a in lista:
            chave = registro.chave(m.id_ibge, m.data, a.ref)
            if registro.ja_enviado(chave):
                cont["duplicados_nao_reenviados"] += 1
                log.info("%s assinante=%s canal=%s resultado=duplicado", base, a.ref, a.canal)
                continue
            canal = canais.get(a.canal)
            try:
                if canal is None or isinstance(canal, Exception):
                    raise EnvioFalhou(f"canal {a.canal} não configurado ({canal})")
                canal.enviar(a, assunto, texto)
            except EnvioFalhou as erro:
                falhas += 1
                cont["falhas_envio"] += 1
                log.error("%s assinante=%s canal=%s resultado=falhou erro=%s", base, a.ref, a.canal, erro)
                resumo["erros"].append(f"envio {m.id_ibge}/{a.ref}: {erro}")
                continue
            enviados += 1
            cont["enviados"] += 1
            registro.marcar(chave, datetime.now(BRASILIA))
            registro.salvar(hoje)  # salva a cada envio: se cair no meio, não reenvia o que já foi
            log.info("%s decisao=%s assinante=%s canal=%s resultado=enviado", base, decisao.motivo, a.ref, a.canal)

        if enviados:
            novos_alertas.append({
                "id_ibge": m.id_ibge, "nome": m.nome, "uf": m.uf, "data_dado": m.data.isoformat(),
                "nivel_risco": m.nivel_risco, "motivo": decisao.motivo,
                "enviado_em": datetime.now(BRASILIA).isoformat(timespec="seconds"),
                "assinantes_avisados": enviados, "falhas": falhas, "simulado": cfg.simular,
            })

    registro.salvar(hoje)
    if cont["falhas_envio"]:
        return encerrar("concluido_com_falhas", COM_FALHAS)
    return encerrar("concluido", OK)


def main(argv: list[str] | None = None) -> int:
    codigo, _ = executar(configuracao(argv))
    return codigo


if __name__ == "__main__":
    sys.exit(main())
