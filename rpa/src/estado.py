"""Memória entre execuções: evita reenviar o mesmo alerta e alimenta o site.

- ``estado/enviados.json``: chaves ``id_ibge|data|ref`` já enviadas (sem contato).
- ``alertas.json`` (saída para o MVP): histórico curto do que foi avisado, por
  município, que o site mostra no cartão de risco.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path


def gravar_json(caminho: Path, dados) -> None:
    """Grava de forma atômica: ou o arquivo novo inteiro, ou o antigo intacto."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=caminho.parent, prefix=caminho.name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        os.replace(tmp, caminho)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def _ler(caminho: Path, padrao):
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return padrao


class Registro:
    def __init__(self, caminho: str | Path, guardar_dias: int = 30):
        self.caminho = Path(caminho)
        self.guardar_dias = guardar_dias
        bruto = _ler(self.caminho, {})
        self.enviados: dict[str, str] = bruto.get("enviados", {}) if isinstance(bruto, dict) else {}

    @staticmethod
    def chave(id_ibge: int, data_dado: date, ref: str) -> str:
        return f"{id_ibge}|{data_dado.isoformat()}|{ref}"

    def ja_enviado(self, chave: str) -> bool:
        return chave in self.enviados

    def marcar(self, chave: str, quando: datetime) -> None:
        self.enviados[chave] = quando.isoformat(timespec="seconds")

    def salvar(self, hoje: date) -> None:
        corte = (hoje - timedelta(days=self.guardar_dias)).isoformat()
        self.enviados = {k: v for k, v in self.enviados.items() if k.split("|")[1] >= corte}
        gravar_json(self.caminho, {"enviados": self.enviados})


def publicar_alertas(caminho: str | Path, novos: list[dict], resumo: dict, hoje: date, guardar_dias: int = 14) -> None:
    """Acrescenta os alertas desta execução ao histórico lido pelo site."""
    caminho = Path(caminho)
    atual = _ler(caminho, {})
    historico = atual.get("alertas", []) if isinstance(atual, dict) else []
    corte = (hoje - timedelta(days=guardar_dias)).isoformat()
    historico = [a for a in historico if str(a.get("enviado_em", ""))[:10] >= corte]
    historico = novos + historico  # mais recente primeiro
    gravar_json(caminho, {
        "atualizado_em": resumo["fim"],
        "ultima_execucao": {k: resumo[k] for k in ("id_execucao", "status", "fim", "data_dado", "contagens")},
        "alertas": historico,
    })
