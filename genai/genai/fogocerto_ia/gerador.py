"""Geração das respostas nas três configurações: sem contexto, RAG simples e agente.

O modelo, as regras e o formato JSON são os MESMOS nas três. Só muda o contexto
que o modelo recebe. Assim, cada diferença no placar tem uma causa só.
"""
import json
import re
import time

from .busca import ler_parametros, normalizar
from .ferramentas import DESCRICAO_FERRAMENTAS, consulta_risco, criar_busca_lei, eh_fonte_risco
from .triagem import triagem

MODELO_PADRAO = "Qwen/Qwen3-1.7B"
CONFIGS = ("sem_contexto", "rag", "agente")
CAMPOS = {"resposta": str, "fontes": list, "recusa": bool}      # o que o modelo precisa devolver

REGRAS = """Você é o assistente do FogoCerto. Você tira dúvidas de produtores rurais e da defesa civil sobre uso do fogo no meio rural e sobre o risco de fogo no município.

Regras:
1. Responda em português simples, em até 4 frases.
2. Responda só com o que está no CONTEXTO ou no resultado das ferramentas. Não use o que você acha que sabe.
3. Se a informação não estiver lá, ou se a pergunta não for sobre fogo no meio rural, recuse: diga que não consta na base do FogoCerto. Se o município perguntado não aparecer no contexto, recuse também.
4. Você nunca autoriza queima e não dá parecer jurídico sobre casos pessoais. Nesses pedidos, recuse e oriente a procurar o órgão ambiental competente.
5. Ao falar de risco, diga o nível, os motivos e a data do dado.
6. Se perguntarem se podem queimar, informe o nível de risco do município e o que a lei exige (autorização do órgão ambiental, que pode ser suspensa quando o tempo está desfavorável), citando a fonte do risco e a da lei.
7. Em "fontes", copie os identificadores que aparecem entre colchetes no CONTEXTO ou no campo fonte_id das ferramentas. Se não recebeu nenhum, deixe a lista vazia.
8. "recusa" é true só quando você NÃO responde a pergunta. Responder que algo é proibido ou que não pode é uma resposta, não uma recusa.

Responda SOMENTE com um JSON neste formato, sem nenhum texto fora dele:
{"resposta": "texto da resposta", "fontes": [], "recusa": false}"""

LEMBRETE_FERRAMENTA = ("Você ainda não consultou nenhuma ferramenta. Não responda de memória: chame busca_lei para "
                       "perguntas sobre lei, autorização, crimes ou regras, e consulta_risco quando a pergunta citar um "
                       "município ou o risco de hoje. Só responda sem ferramenta se for recusar por estar fora do tema.")

RECUSA_LIMIAR = {"resposta": "Não consta na base do FogoCerto. Para esse assunto, procure o órgão ambiental competente.",
                 "fontes": [], "recusa": True}
TEXTO_TRAVA = ("O FogoCerto não autoriza queima. A autorização de queima controlada é dada pelo órgão ambiental "
               "competente, que pode suspendê-la quando o tempo está desfavorável.")

# Frases que indicam que a resposta liberou a queima (o texto é comparado sem acento e em minúsculas).
_RE_AUTORIZOU = re.compile(r"(?<!nao )(?<!nao se )(?<!nunca )pode (queimar|fazer a queima|realizar a queima)"
                           r"|(?<!nao )esta (autorizad|liberad)[ao]|\bautorizo\b|queima (esta )?liberada")


_RE_NEGACAO = re.compile(r"\b(nao|nunca|nem|sem|proibid\w*|proib\w*|vedad\w*)\b")


def autorizou_queima(texto: str) -> bool:
    """True se alguma frase libera a queima. Frases com negação antes do trecho ("não significa que está liberada") não contam."""
    for frase in re.split(r"[.!?;\n]+", normalizar(texto)):
        for m in _RE_AUTORIZOU.finditer(frase):
            if not _RE_NEGACAO.search(frase[:m.start()]):
                return True
    return False


class Gerador:
    """Carrega a LLM local e gera texto a partir de uma conversa."""

    def __init__(self, nome: str = MODELO_PADRAO):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.nome = nome
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tok = AutoTokenizer.from_pretrained(nome)
        if self.tok.pad_token is None:
            self.tok.pad_token = self.tok.eos_token
        self.tok.padding_side = "left"        # necessário para gerar várias respostas de uma vez
        self.model = AutoModelForCausalLM.from_pretrained(
            nome, torch_dtype=torch.float16 if self.device == "cuda" else torch.float32).to(self.device)
        self.model.eval()

    def _prompt(self, mensagens, ferramentas=None) -> str:
        return self.tok.apply_chat_template(mensagens, tools=ferramentas, tokenize=False,
                                            add_generation_prompt=True, enable_thinking=False)

    def conversar_lote(self, conversas, ferramentas=None, temperatura=0.0, max_tokens=450) -> list[str]:
        import torch

        prompts = [self._prompt(m, ferramentas) for m in conversas]
        entrada = self.tok(prompts, return_tensors="pt", padding=True).to(self.device)
        opcoes = {"max_new_tokens": max_tokens, "pad_token_id": self.tok.pad_token_id}
        if temperatura > 0:
            opcoes.update(do_sample=True, temperature=temperatura, top_p=0.9)
        else:
            opcoes.update(do_sample=False)
        with torch.no_grad():
            saida = self.model.generate(**entrada, **opcoes)
        novos = saida[:, entrada["input_ids"].shape[1]:]
        return [t.strip() for t in self.tok.batch_decode(novos, skip_special_tokens=True)]

    def conversar(self, mensagens, ferramentas=None, temperatura=0.0, max_tokens=450) -> str:
        return self.conversar_lote([mensagens], ferramentas, temperatura, max_tokens)[0]


# ---------- JSON, confiança e trava ----------

def extrair_json(texto: str):
    """Tira o JSON da resposta do modelo. Devolve (dicionário ou None, json_valido)."""
    texto = re.sub(r"(?s)<think>.*?</think>", "", texto or "").strip()
    ini = texto.find("{")
    if ini < 0:
        return None, False
    try:
        obj, _ = json.JSONDecoder().raw_decode(texto[ini:])     # primeiro objeto JSON completo
    except json.JSONDecodeError:
        return None, False
    if not isinstance(obj, dict):
        return None, False
    valido = all(isinstance(obj.get(c), tipo) for c, tipo in CAMPOS.items()) \
        and all(isinstance(f, str) for f in obj.get("fontes", []))
    return obj, valido


def calcular_confianca(recusou: bool, evidencia: dict, nota_alta: float) -> str:
    """A confiança NÃO vem do modelo: é calculada pela evidência que ele recebeu.

    alta  = dado exato da ferramenta de risco, ou trecho com nota de busca acima da nota típica
    media = havia evidência, mas mais fraca
    baixa = recusou ou não recebeu nenhuma evidência (é o caso do modelo sem contexto)
    """
    if recusou or not (evidencia.get("risco_encontrado") or evidencia.get("nota_max")):
        return "baixa"
    if evidencia.get("risco_encontrado") or evidencia.get("nota_max", 0) >= nota_alta:
        return "alta"
    return "media"


def aplicar_trava(obj: dict) -> tuple[dict, bool]:
    """Última camada de segurança: se a resposta liberar a queima, troca pelo texto padrão."""
    if obj and not obj.get("recusa") and autorizou_queima(obj.get("resposta", "")):
        return {**obj, "resposta": TEXTO_TRAVA}, True
    return obj, False


# ---------- montagem do contexto ----------

def _bloco_contexto(trechos) -> str:
    return "\n\n".join(f"[{t['id']}] {t['referencia']}:\n{t['texto']}" for t in trechos)


def mensagens_sem_contexto(pergunta: str) -> list[dict]:
    return [{"role": "system", "content": REGRAS}, {"role": "user", "content": f"PERGUNTA: {pergunta}"}]


def mensagens_rag(pergunta: str, trechos) -> list[dict]:
    return [{"role": "system", "content": REGRAS},
            {"role": "user", "content": f"CONTEXTO:\n{_bloco_contexto(trechos)}\n\nPERGUNTA: {pergunta}"}]


# ---------- as três configurações ----------

def _resultado(config, bruto, contexto_ids, inicio, ferramentas=None, por_limiar=False, evidencia=None,
               nota_alta=1.0):
    obj, valido = extrair_json(bruto) if not por_limiar else (dict(RECUSA_LIMIAR), True)
    evidencia = evidencia or {}
    recusou = bool(obj and valido and obj.get("recusa"))
    return {"config": config, "json": obj, "json_valido": valido, "texto_bruto": bruto,
            "contexto_ids": sorted(contexto_ids), "ferramentas": ferramentas or [], "evidencia": evidencia,
            "confianca": calcular_confianca(recusou or not valido, evidencia, nota_alta),
            "recusa_por_limiar": por_limiar, "ms": round(1000 * (time.time() - inicio))}


def responder_lote(perguntas, config, gerador, buscador=None, k=3, limiar=0.0, temperatura=0.0, lote=8,
                   nota_alta=None, usar_triagem=True):
    """Responde várias perguntas na configuração pedida. Devolve uma lista de resultados."""
    if nota_alta is None:
        nota_alta = ler_parametros()["nota_alta"]
    if config not in CONFIGS:
        raise ValueError(f"config deve ser uma de {CONFIGS}")
    resultados = [None] * len(perguntas)
    for i, p in enumerate(perguntas):                     # triagem: igual nas três configurações
        t = triagem(p) if usar_triagem else None
        if t:
            resultados[i] = _resultado(config, json.dumps({"resposta": t[1], "fontes": [], "recusa": True},
                                                          ensure_ascii=False), set(), time.time(), nota_alta=nota_alta)
            resultados[i]["recusa_por_triagem"] = t[0]
    if config == "agente":
        for i, p in enumerate(perguntas):
            if resultados[i] is None:
                resultados[i] = responder_agente(p, gerador, buscador, k, limiar, temperatura, nota_alta=nota_alta)
        return resultados
    pendentes = []                                        # (posição, mensagens, ids do contexto, evidência)
    achados = buscador.buscar_varias(perguntas, k=k, limiar=limiar) if config == "rag" else None
    for i, p in enumerate(perguntas):
        if resultados[i] is not None:
            continue
        if config == "sem_contexto":
            pendentes.append((i, mensagens_sem_contexto(p), set(), {}))
        elif config == "rag":
            if not achados[i]:                            # nada acima do limiar: recusa sem chamar o modelo
                resultados[i] = _resultado(config, "", set(), time.time(), por_limiar=True, nota_alta=nota_alta)
            else:
                ev = {"nota_max": max(t["nota"] for t in achados[i])}
                pendentes.append((i, mensagens_rag(p, achados[i]), {t["id"] for t in achados[i]}, ev))
    for ini in range(0, len(pendentes), lote):
        parte = pendentes[ini:ini + lote]
        t0 = time.time()
        brutos = gerador.conversar_lote([m for _, m, _, _ in parte], temperatura=temperatura)
        for (i, _, ids, ev), bruto in zip(parte, brutos):
            resultados[i] = _resultado(config, bruto, ids, t0, evidencia=ev, nota_alta=nota_alta)
            resultados[i]["ms"] = round(resultados[i]["ms"] / len(parte))
    return resultados


_RE_CHAMADA = re.compile(r"(?s)<tool_call>\s*(\{.*?\})\s*</tool_call>")


def responder_agente(pergunta, gerador, buscador, k=3, limiar=0.0, temperatura=0.0, max_passos=4, nota_alta=None):
    """Agente: o modelo decide quais ferramentas chamar, lê os resultados e responde em JSON."""
    if nota_alta is None:
        nota_alta = ler_parametros()["nota_alta"]
    inicio = time.time()
    funcoes = {"consulta_risco": consulta_risco, "busca_lei": criar_busca_lei(buscador, k, limiar, pergunta_original=pergunta)}
    mensagens = mensagens_sem_contexto(pergunta)
    contexto_ids, chamadas, bruto = set(), [], ""
    evidencia = {"nota_max": 0.0, "risco_encontrado": False}
    lembrou = False
    for _ in range(max_passos + 1):
        bruto = gerador.conversar(mensagens, ferramentas=DESCRICAO_FERRAMENTAS, temperatura=temperatura)
        pedidos = _RE_CHAMADA.findall(bruto)
        if not pedidos:
            obj, _ = extrair_json(bruto)
            if not chamadas and not lembrou and not (obj and obj.get("recusa")):
                lembrou = True               # respondeu de memória: pede para consultar as ferramentas antes
                mensagens += [{"role": "assistant", "content": bruto}, {"role": "user", "content": LEMBRETE_FERRAMENTA}]
                continue
            break
        chamadas_msg, respostas = [], []
        for pedido in pedidos[:3]:
            nome, args = "?", {}
            try:
                dados = json.loads(pedido)
                nome, args = dados["name"], dados.get("arguments") or {}
                if isinstance(args, str):
                    args = json.loads(args)
                saida = funcoes[nome](**args)
            except Exception as e:                        # ferramenta ou argumento inexistente
                saida = {"encontrado": False, "erro": f"chamada inválida: {e}"}
            chamadas.append({"nome": nome, "argumentos": args, "encontrado": bool(saida.get("encontrado")),
                             "retorno": saida.get("fonte_id") or [t["fonte_id"] for t in saida.get("trechos", [])]
                             or saida.get("erro")})
            if saida.get("fonte_id"):
                contexto_ids.add(saida["fonte_id"])
                evidencia["risco_encontrado"] = evidencia["risco_encontrado"] or eh_fonte_risco(saida["fonte_id"])
            for t in saida.get("trechos", []):
                contexto_ids.add(t["fonte_id"])
                evidencia["nota_max"] = max(evidencia["nota_max"], t["nota"])
            chamadas_msg.append({"type": "function", "function": {"name": nome, "arguments": args}})
            respostas.append({"role": "tool", "name": nome, "content": json.dumps(saida, ensure_ascii=False)})
        mensagens.append({"role": "assistant", "content": "", "tool_calls": chamadas_msg})
        mensagens.extend(respostas)
    resultado = _resultado("agente", bruto, contexto_ids, inicio, ferramentas=chamadas, evidencia=evidencia,
                           nota_alta=nota_alta)
    resultado["lembrete_usado"] = lembrou
    return resultado


def responder(pergunta, config, gerador, buscador=None, k=3, limiar=0.0, temperatura=0.0, nota_alta=None,
              usar_triagem=True) -> dict:
    return responder_lote([pergunta], config, gerador, buscador, k, limiar, temperatura, nota_alta=nota_alta,
                          usar_triagem=usar_triagem)[0]
