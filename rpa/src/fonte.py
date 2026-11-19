"""Leitura e validação do risco (``risco_atual.json``), o mesmo arquivo que o site usa.

A fonte pode ser um arquivo local ou uma URL (o site publicado serve
``/data/risco_atual.json``; mais adiante, a API ``GET /risco``).
"""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date
from pathlib import Path

log = logging.getLogger("fogocerto.rpa")

NIVEIS = ("baixo", "medio", "alto")


class FonteIndisponivel(Exception):
    """Arquivo ausente ou API/site fora do ar depois de todas as tentativas."""


class DadoInvalido(Exception):
    """A fonte respondeu, mas o conteúdo não serve (JSON quebrado, vazio, formato errado)."""


@dataclass(frozen=True)
class Municipio:
    id_ibge: int
    nome: str
    uf: str
    data: date
    nivel_risco: str
    pontos: int
    fatores: list[str]
    focos_ontem: int


def ler_bruto(fonte: str, tentativas: int = 3, espera_s: float = 2.0, timeout_s: float = 15.0) -> bytes:
    """Lê a fonte com novas tentativas (espera dobra a cada falha)."""
    ultima_falha = "sem tentativa"
    for n in range(1, tentativas + 1):
        try:
            if fonte.startswith(("http://", "https://")):
                req = urllib.request.Request(fonte, headers={"User-Agent": "FogoCerto-RPA/1.0"})
                with urllib.request.urlopen(req, timeout=timeout_s) as resp:  # noqa: S310 (URL configurada pelo time)
                    return resp.read()
            return Path(fonte).read_bytes()
        except FileNotFoundError:
            ultima_falha = "arquivo não encontrado"
        except urllib.error.HTTPError as erro:
            ultima_falha = f"HTTP {erro.code}"
            if 400 <= erro.code < 500 and erro.code != 429:
                break  # erro do pedido: tentar de novo não resolve
        except (urllib.error.URLError, TimeoutError, OSError) as erro:
            ultima_falha = f"{type(erro).__name__}: {getattr(erro, 'reason', erro)}"
        log.warning("leitura da fonte falhou (tentativa %d/%d): %s", n, tentativas, ultima_falha)
        if n < tentativas:
            time.sleep(espera_s * 2 ** (n - 1))
    raise FonteIndisponivel(ultima_falha)


def interpretar(bruto: bytes, hoje: date) -> tuple[list[Municipio], list[str]]:
    """Valida o JSON. Devolve os municípios aproveitáveis e a lista de problemas por item.

    Lança ``DadoInvalido`` quando o arquivo inteiro não serve.
    """
    try:
        dados = json.loads(bruto.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as erro:
        raise DadoInvalido(f"JSON ilegível: {erro}") from erro
    if not isinstance(dados, list):
        raise DadoInvalido("formato inesperado: era esperada uma lista de municípios")
    if not dados:
        raise DadoInvalido("arquivo sem municípios")

    validos: list[Municipio] = []
    problemas: list[str] = []
    vistos: set[int] = set()
    for i, item in enumerate(dados):
        try:
            m = _municipio(item, hoje)
        except ValueError as erro:
            problemas.append(f"item {i}: {erro}")
            continue
        if m.id_ibge in vistos:
            problemas.append(f"item {i}: município {m.id_ibge} repetido no arquivo (mantido o primeiro)")
            continue
        vistos.add(m.id_ibge)
        validos.append(m)

    if not validos:
        raise DadoInvalido("nenhum município válido no arquivo: " + "; ".join(problemas[:3]))
    return validos, problemas


def _municipio(item: object, hoje: date) -> Municipio:
    if not isinstance(item, dict):
        raise ValueError("não é um objeto")
    id_ibge = item.get("id_ibge")
    if not isinstance(id_ibge, int) or isinstance(id_ibge, bool):
        raise ValueError("id_ibge ausente ou não numérico")
    nome = item.get("nome")
    if not isinstance(nome, str) or not nome.strip():
        raise ValueError(f"município {id_ibge} sem nome")
    nivel = item.get("nivel_risco")
    if nivel not in NIVEIS:
        raise ValueError(f"município {id_ibge}: nivel_risco desconhecido {nivel!r}")
    try:
        data_ref = date.fromisoformat(str(item.get("data")))
    except ValueError as erro:
        raise ValueError(f"município {id_ibge}: data inválida {item.get('data')!r}") from erro
    if data_ref > hoje:
        raise ValueError(f"município {id_ibge}: data futura {data_ref.isoformat()}")
    focos = item.get("focos_ontem", 0)
    if not isinstance(focos, (int, float)) or isinstance(focos, bool) or focos < 0:
        raise ValueError(f"município {id_ibge}: focos_ontem inválido {focos!r}")
    pontos = item.get("pontos", 0)
    fatores = item.get("fatores") or ""
    return Municipio(
        id_ibge=id_ibge,
        nome=nome.strip(),
        uf=str(item.get("uf") or ""),
        data=data_ref,
        nivel_risco=nivel,
        pontos=int(pontos) if isinstance(pontos, (int, float)) else 0,
        fatores=[f.strip() for f in str(fatores).split(";") if f.strip()],
        focos_ontem=int(focos),
    )
