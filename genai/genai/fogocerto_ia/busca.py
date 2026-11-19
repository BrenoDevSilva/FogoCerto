"""Busca de trechos por semelhança, com recall@k e escolha do limiar de recusa."""
import json
import unicodedata

import numpy as np

from . import AVALIACAO

MODELO_EMBEDDING = "intfloat/multilingual-e5-small"
ARQ_LIMIAR = AVALIACAO / "limiar.json"


def normalizar(txt: str) -> str:
    """minúsculas e sem acento: 'Oriximiná' -> 'oriximina'."""
    txt = unicodedata.normalize("NFKD", str(txt)).encode("ascii", "ignore").decode()
    return " ".join(txt.lower().split())


class Buscador:
    """Guarda os trechos e devolve os mais parecidos com a pergunta.

    tipo="e5"    -> embeddings multilíngues (padrão; usa GPU se houver)
    tipo="tfidf" -> contagem de palavras (comparação simples; roda em qualquer máquina)
    """

    def __init__(self, trechos: list[dict], tipo: str = "e5", modelo: str = MODELO_EMBEDDING):
        self.trechos, self.tipo = trechos, tipo
        textos = [f"{t['referencia']}. {t['texto']}" for t in trechos]
        if tipo == "e5":
            from sentence_transformers import SentenceTransformer
            self._modelo = SentenceTransformer(modelo)
            self._matriz = self._modelo.encode([f"passage: {x}" for x in textos],
                                               normalize_embeddings=True, show_progress_bar=False)
        elif tipo == "tfidf":
            from sklearn.feature_extraction.text import TfidfVectorizer
            self._vet = TfidfVectorizer(preprocessor=normalizar, ngram_range=(1, 2), sublinear_tf=True)
            self._matriz = self._vet.fit_transform(textos)
        else:
            raise ValueError("tipo deve ser 'e5' ou 'tfidf'")

    def _notas(self, perguntas: list[str]) -> np.ndarray:
        if self.tipo == "e5":
            q = self._modelo.encode([f"query: {p}" for p in perguntas],
                                    normalize_embeddings=True, show_progress_bar=False)
            return q @ self._matriz.T
        return (self._vet.transform(perguntas) @ self._matriz.T).toarray()

    def buscar(self, pergunta: str, k: int = 3, limiar: float = 0.0) -> list[dict]:
        """Os k trechos mais parecidos, com a nota. Trechos abaixo do limiar ficam de fora."""
        return self.buscar_varias([pergunta], k, limiar)[0]

    def buscar_varias(self, perguntas: list[str], k: int = 3, limiar: float = 0.0) -> list[list[dict]]:
        notas = self._notas(perguntas)
        saida = []
        for linha in notas:
            ordem = np.argsort(-linha)[:k]
            saida.append([{**self.trechos[i], "nota": round(float(linha[i]), 4)} for i in ordem if linha[i] >= limiar])
        return saida


def recall_em_k(buscador: Buscador, casos: list[dict], ks=(1, 3, 5)) -> dict:
    """recall@k: em quantas perguntas um dos artigos do gabarito aparece entre os k primeiros.

    Só entram os casos que têm `fontes_esperadas` na base de trechos (leis e regra de risco).
    """
    casos = [c for c in casos if c.get("fontes_busca")]
    achados = buscador.buscar_varias([c["pergunta"] for c in casos], k=max(ks))
    res = {"n": len(casos)}
    for k in ks:
        ok = sum(any(t["artigo_id"] in c["fontes_busca"] for t in ach[:k]) for c, ach in zip(casos, achados))
        res[f"recall@{k}"] = round(100 * ok / max(len(casos), 1), 1)
    res["detalhes"] = [{"id": c["id"], "pergunta": c["pergunta"], "esperado": c["fontes_busca"],
                        "achados": [t["artigo_id"] for t in ach], "nota_top1": ach[0]["nota"] if ach else 0.0,
                        "acertou@3": any(t["artigo_id"] in c["fontes_busca"] for t in ach[:3])}
                       for c, ach in zip(casos, achados)]
    return res


def curva_limiar(buscador: Buscador, casos: list[dict], passos=None) -> list[dict]:
    """Para cada limiar: % de perguntas da base que continuam respondidas e % de perguntas
    de fora da base que são recusadas. Usa a nota do trecho mais parecido (top 1)."""
    dentro = [c["pergunta"] for c in casos if c.get("fontes_busca")]
    fora = [c["pergunta"] for c in casos if c.get("fora_da_base")]
    n_dentro = buscador._notas(dentro).max(axis=1)
    n_fora = buscador._notas(fora).max(axis=1)
    if passos is None:
        todas = np.concatenate([n_dentro, n_fora])
        passos = np.round(np.linspace(todas.min() - 0.01, todas.max() + 0.01, 41), 4)
    curva = []
    for t in passos:
        mantidas = 100 * float((n_dentro >= t).mean())
        recusadas = 100 * float((n_fora < t).mean())
        curva.append({"limiar": float(t), "base_respondida_%": round(mantidas, 1),
                      "fora_recusada_%": round(recusadas, 1), "equilibrio_%": round((mantidas + recusadas) / 2, 1)})
    return curva


MINIMO_BASE = 95.0     # % das perguntas da base que a busca não pode barrar

REGRA_LIMIAR = (f"o maior limiar que ainda deixa passar pelo menos {MINIMO_BASE:.0f}% das perguntas que a base "
                "responde (medido no conjunto de ajuste). A busca é a primeira camada de recusa e não pode barrar o que "
                "a base sabe responder; as perguntas parecidas com o tema, mas fora da base, ficam para a segunda camada "
                "(o modelo lendo o contexto) e para a trava contra 'pode queimar'.")


def escolher_limiar(curva: list[dict], minimo_base: float = MINIMO_BASE) -> dict:
    """Maior limiar que mantém pelo menos `minimo_base`% das perguntas da base respondidas.

    Entre os limiares que cumprem essa condição, o maior é o que mais recusa perguntas de fora da base.
    """
    validos = [c for c in curva if c["base_respondida_%"] >= minimo_base]
    if not validos:                                   # não deve acontecer: o menor limiar mantém 100%
        melhor = max(c["equilibrio_%"] for c in curva)
        validos = [c for c in curva if c["equilibrio_%"] == melhor]
    return max(validos, key=lambda c: c["limiar"])


def nota_tipica(buscador, casos) -> float:
    """Mediana da nota do melhor trecho nas perguntas que a base responde. Acima dela, a evidência é 'alta'."""
    dentro = [c["pergunta"] for c in casos if c.get("fontes_busca")]
    return round(float(np.median(buscador._notas(dentro).max(axis=1))), 4)


def salvar_limiar(valor: float, tipo: str, detalhes: dict) -> None:
    ARQ_LIMIAR.write_text(json.dumps({"limiar": valor, "buscador": tipo, "regra": REGRA_LIMIAR, **detalhes},
                                     ensure_ascii=False, indent=2), encoding="utf-8")


def ler_parametros(padrao: float = 0.80) -> dict:
    """Limiar de recusa e nota de evidência alta salvos na etapa do limiar."""
    if ARQ_LIMIAR.exists():
        d = json.loads(ARQ_LIMIAR.read_text(encoding="utf-8"))
        return {"limiar": d["limiar"], "nota_alta": d.get("nota_alta", d["limiar"] + 0.05)}
    return {"limiar": padrao, "nota_alta": padrao + 0.05}


def ler_limiar(padrao: float = 0.80) -> float:
    return ler_parametros(padrao)["limiar"]
