"""Assinantes e canais de envio (Telegram, e-mail e simulado).

LGPD: o contato (``chat_id`` ou e-mail) só existe no arquivo local de assinantes
(fora do Git) e na chamada de envio. Logs, estado e saída para o site usam apenas
``ref``, um resumo SHA-256 truncado que não permite recuperar o contato.
"""

from __future__ import annotations

import hashlib
import json
import logging
import smtplib
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path

log = logging.getLogger("fogocerto.rpa")

CANAIS = ("telegram", "email")


class EnvioFalhou(Exception):
    pass


class AssinantesInvalidos(Exception):
    pass


@dataclass(frozen=True)
class Assinante:
    municipio_id: int
    canal: str
    destino: str  # dado pessoal: nunca logar

    @property
    def ref(self) -> str:
        return hashlib.sha256(f"{self.canal}:{self.destino}".encode()).hexdigest()[:10]

    def __repr__(self) -> str:  # evita vazar o contato num print ou traceback
        return f"Assinante(municipio_id={self.municipio_id}, canal={self.canal!r}, ref={self.ref!r})"


def carregar_assinantes(caminho: str | Path) -> dict[int, list[Assinante]]:
    """Lê o arquivo de assinantes e agrupa por município. Itens ruins são ignorados e registrados."""
    caminho = Path(caminho)
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as erro:
        raise AssinantesInvalidos(f"arquivo de assinantes não encontrado: {caminho.name}") from erro
    except json.JSONDecodeError as erro:
        raise AssinantesInvalidos(f"arquivo de assinantes ilegível: {erro.msg} (linha {erro.lineno})") from erro
    if not isinstance(dados, list):
        raise AssinantesInvalidos("arquivo de assinantes deve ser uma lista")

    por_municipio: dict[int, list[Assinante]] = {}
    vistos: set[tuple[int, str]] = set()
    for i, item in enumerate(dados):
        if not isinstance(item, dict):
            log.warning("assinante %d ignorado: não é um objeto", i)
            continue
        mid, canal, destino = item.get("municipio_id"), item.get("canal"), str(item.get("destino") or "").strip()
        if not isinstance(mid, int) or canal not in CANAIS or not destino:
            log.warning("assinante %d ignorado: municipio_id, canal (telegram/email) ou destino inválido", i)
            continue
        a = Assinante(mid, canal, destino)
        if (mid, a.ref) in vistos:
            log.warning("assinante %d ignorado: repetido (ref=%s)", i, a.ref)
            continue
        vistos.add((mid, a.ref))
        por_municipio.setdefault(mid, []).append(a)
    return por_municipio


class Telegram:
    URL = "https://api.telegram.org/bot{token}/sendMessage"

    def __init__(self, token: str, tentativas: int = 3, espera_s: float = 2.0):
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN não configurado")
        self._token = token
        self.tentativas, self.espera_s = tentativas, espera_s

    def _limpo(self, texto: str) -> str:
        return texto.replace(self._token, "***")

    def enviar(self, assinante: Assinante, assunto: str, texto: str) -> None:
        corpo = urllib.parse.urlencode({"chat_id": assinante.destino, "text": texto}).encode()
        motivo = ""
        for n in range(1, self.tentativas + 1):
            try:
                req = urllib.request.Request(self.URL.format(token=self._token), data=corpo, method="POST")
                with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310
                    if json.load(resp).get("ok"):
                        return
                    motivo = "Telegram respondeu ok=false"
            except urllib.error.HTTPError as erro:
                motivo = f"HTTP {erro.code}"
                try:
                    motivo += f" ({json.load(erro).get('description', '')})"
                except Exception:  # noqa: BLE001 (corpo do erro é opcional)
                    pass
                if erro.code in (400, 401, 403, 404):
                    break  # chat inexistente, bot bloqueado ou token errado: repetir não resolve
            except (urllib.error.URLError, TimeoutError, OSError) as erro:
                motivo = f"{type(erro).__name__}: {getattr(erro, 'reason', erro)}"
            if n < self.tentativas:
                time.sleep(self.espera_s * 2 ** (n - 1))
        raise EnvioFalhou(self._limpo(motivo))


class Email:
    def __init__(self, host: str, porta: int, usuario: str, senha: str, remetente: str):
        if not (host and usuario and senha):
            raise ValueError("SMTP_HOST, SMTP_USUARIO e SMTP_SENHA são obrigatórios para e-mail")
        self.host, self.porta, self.usuario, self._senha = host, porta, usuario, senha
        self.remetente = remetente or usuario

    def enviar(self, assinante: Assinante, assunto: str, texto: str) -> None:
        msg = EmailMessage()
        msg["From"], msg["To"], msg["Subject"] = self.remetente, assinante.destino, assunto
        msg.set_content(texto)
        try:
            contexto = ssl.create_default_context()
            if self.porta == 465:
                with smtplib.SMTP_SSL(self.host, self.porta, context=contexto, timeout=20) as s:
                    s.login(self.usuario, self._senha)
                    s.send_message(msg)
            else:
                with smtplib.SMTP(self.host, self.porta, timeout=20) as s:
                    s.starttls(context=contexto)
                    s.login(self.usuario, self._senha)
                    s.send_message(msg)
        except (smtplib.SMTPException, OSError) as erro:
            raise EnvioFalhou(f"{type(erro).__name__}") from erro


class Simulado:
    """Não envia nada: grava a mensagem numa caixa de saída local (demonstração e testes)."""

    def __init__(self, caixa: str | Path | None = None, falhar_para: set[str] | None = None):
        self.caixa = Path(caixa) if caixa else None
        self.falhar_para = falhar_para or set()  # destinos que simulam falha de envio (teste)
        self.enviadas: list[tuple[str, str, str]] = []  # (ref, assunto, texto)

    def enviar(self, assinante: Assinante, assunto: str, texto: str) -> None:
        if assinante.destino in self.falhar_para:
            raise EnvioFalhou("falha simulada")
        self.enviadas.append((assinante.ref, assunto, texto))
        if self.caixa:
            self.caixa.parent.mkdir(parents=True, exist_ok=True)
            with self.caixa.open("a", encoding="utf-8") as f:
                f.write(f"--- {assinante.canal} para assinante ref={assinante.ref} ---\n{texto}\n\n")
