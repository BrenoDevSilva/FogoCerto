"""Regra que transforma as detecções do modelo na resposta do FogoCerto.

O modelo (YOLO) devolve caixas com classe e confiança. O produto precisa de uma
resposta por imagem: ``fogo``, ``fumaca`` ou ``nada``. A regra é a mesma usada
na avaliação "por imagem" do notebook de treino, para que o número do relatório
seja o número do produto:

1. Descarta caixas abaixo de ``limiar_duvida``.
2. Se há caixa de fogo com confiança >= ``limiar``: resposta ``fogo``.
3. Senão, se há caixa de fumaça com confiança >= ``limiar``: resposta ``fumaca``.
   (Fogo tem prioridade porque é o caso mais grave.)
4. Senão, se sobrou alguma caixa entre ``limiar_duvida`` e ``limiar``: a resposta
   é a classe dessa caixa, marcada como dúvida.
5. Senão: ``nada``.

Este módulo não depende do Ultralytics para poder ser testado sem o modelo.
"""

from __future__ import annotations

from dataclasses import dataclass, field

CLASSES = ("fumaca", "fogo")  # mesma ordem dos ids do dataset (0 = fumaça, 1 = fogo)

MSG_FOGO = (
    "Possível fogo detectado. Afaste-se e ligue para os Bombeiros (193) "
    "ou a Defesa Civil (199)."
)
MSG_FUMACA = "Possível fumaça detectada. Procure a Defesa Civil (199) se houver perigo."
MSG_DUVIDA = (
    "Não foi possível confirmar fumaça ou fogo nesta imagem. "
    "Se houver perigo, procure a Defesa Civil (199)."
)
MSG_NADA = (
    "Nenhuma fumaça ou fogo identificado nesta imagem. "
    "Se houver perigo, procure a Defesa Civil (199)."
)
AVISO = "O FogoCerto ajuda a triar. A confirmação é de quem está no local e da Defesa Civil."


@dataclass(frozen=True)
class Deteccao:
    classe: str  # "fumaca" ou "fogo"
    confianca: float
    caixa: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)  # x1, y1, x2, y2 em pixels

    def __post_init__(self) -> None:
        if self.classe not in CLASSES:
            raise ValueError(f"classe desconhecida: {self.classe!r}")
        if not 0.0 <= self.confianca <= 1.0:
            raise ValueError(f"confiança fora de [0, 1]: {self.confianca}")


@dataclass
class Resultado:
    classe: str  # "fogo", "fumaca" ou "nada"
    confianca: float  # confiança da caixa que decidiu; em "nada", a maior encontrada (pode ser 0)
    duvida: bool
    mensagem: str
    deteccoes: list[Deteccao] = field(default_factory=list)

    def para_json(self) -> dict:
        return {
            "classe": self.classe,
            "confianca": round(self.confianca, 3),
            "duvida": self.duvida,
            "mensagem": self.mensagem,
            "aviso": AVISO,
            "deteccoes": [
                {
                    "classe": d.classe,
                    "confianca": round(d.confianca, 3),
                    "caixa": [round(v, 1) for v in d.caixa],
                }
                for d in self.deteccoes
            ],
        }


def classe_da_imagem(deteccoes: list[Deteccao], limiar: float) -> str:
    """Só a classe final (sem a faixa de dúvida). Usada na avaliação por imagem."""
    if any(d.classe == "fogo" and d.confianca >= limiar for d in deteccoes):
        return "fogo"
    if any(d.classe == "fumaca" and d.confianca >= limiar for d in deteccoes):
        return "fumaca"
    return "nada"


def decidir(deteccoes: list[Deteccao], limiar: float, limiar_duvida: float) -> Resultado:
    if not 0.0 < limiar_duvida <= limiar <= 1.0:
        raise ValueError("é preciso 0 < limiar_duvida <= limiar <= 1")

    uteis = sorted(
        (d for d in deteccoes if d.confianca >= limiar_duvida),
        key=lambda d: d.confianca,
        reverse=True,
    )
    classe = classe_da_imagem(uteis, limiar)

    if classe != "nada":
        melhor = max(d.confianca for d in uteis if d.classe == classe)
        msg = MSG_FOGO if classe == "fogo" else MSG_FUMACA
        return Resultado(classe, melhor, False, msg, uteis)

    if uteis:  # só caixas na faixa de dúvida
        topo = uteis[0]
        return Resultado(topo.classe, topo.confianca, True, MSG_DUVIDA, uteis)

    maior = max((d.confianca for d in deteccoes), default=0.0)
    return Resultado("nada", maior, False, MSG_NADA, [])


def prioridade(resultado: Resultado, nivel_risco: str | None) -> str:
    """Cruza a foto com o risco do município (orientação do projeto).

    Foto confirmada em município de risco alto sobe na fila de atenção.
    """
    confirmada = resultado.classe != "nada" and not resultado.duvida
    if confirmada and nivel_risco == "alto":
        return "alta"
    if confirmada or (resultado.duvida and nivel_risco == "alto"):
        return "media"
    return "baixa"
