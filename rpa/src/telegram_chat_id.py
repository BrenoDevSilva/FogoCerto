"""Mostra o chat_id de quem mandou mensagem para o bot (para montar config/assinantes.json).

1. Crie o bot com o @BotFather e coloque o token em rpa/.env (TELEGRAM_BOT_TOKEN=...).
2. Do celular de teste, abra o bot e envie /start.
3. Rode: python src/telegram_chat_id.py

O chat_id é dado pessoal: só aparece aqui no terminal. Não cole em issue, log ou commit.
"""

import json
import os
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from executar import PASTA_RPA, carregar_env  # noqa: E402

carregar_env(PASTA_RPA / ".env")
token = os.environ.get("TELEGRAM_BOT_TOKEN")
if not token:
    sys.exit("Defina TELEGRAM_BOT_TOKEN em rpa/.env")
try:
    with urllib.request.urlopen(f"https://api.telegram.org/bot{token}/getUpdates", timeout=15) as r:  # noqa: S310
        dados = json.load(r)
except OSError as erro:
    sys.exit(f"Falha ao falar com o Telegram: {type(erro).__name__}")
chats = {}
for u in dados.get("result", []):
    chat = (u.get("message") or u.get("my_chat_member") or {}).get("chat")
    if chat:
        chats[chat["id"]] = chat.get("first_name") or chat.get("title") or ""
if not chats:
    print("Nenhuma mensagem recebida. Envie /start para o bot e rode de novo.")
for cid, nome in chats.items():
    print(f"chat_id={cid}  ({nome})")
