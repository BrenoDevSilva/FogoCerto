"""Regras de negócio do alerta: quem deve ser avisado e com que texto.

Decisão por município (documentada no relatório e no BPMN):

1. Dado com data futura: inválido (já barrado na leitura).
2. Dado mais velho que ``max_atraso_dias``: **retido**, não vira alerta.
   O pipeline coleta o dia anterior, então o normal é ``data = ontem`` (1 dia).
3. Risco ``alto``: alerta.
4. Risco ``medio`` com ``focos_ontem >= limiar_focos``: alerta de atenção
   (o tempo não está crítico, mas há muito fogo em volta).
5. Qualquer outro caso: sem alerta.

O alerta nunca autoriza queima.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from fonte import Municipio

FRASE_OBRIGATORIA = "O FogoCerto informa o risco. A autorização de queima é do órgão ambiental do seu estado."
NOME_NIVEL = {"baixo": "BAIXO", "medio": "MÉDIO", "alto": "ALTO"}


@dataclass(frozen=True)
class Decisao:
    alertar: bool
    motivo: str  # código curto, vai para o log e para o site
    dias_atraso: int


def decidir(m: Municipio, hoje: date, limiar_focos: int = 100, max_atraso_dias: int = 2) -> Decisao:
    atraso = (hoje - m.data).days
    if atraso > max_atraso_dias:
        return Decisao(False, "retido_dado_atrasado", atraso)
    if m.nivel_risco == "alto":
        return Decisao(True, "risco_alto", atraso)
    if m.nivel_risco == "medio" and m.focos_ontem >= limiar_focos:
        return Decisao(True, "risco_medio_muitos_focos", atraso)
    return Decisao(False, f"sem_alerta_risco_{m.nivel_risco}", atraso)


def montar_mensagem(m: Municipio, decisao: Decisao) -> tuple[str, str]:
    """Devolve (assunto, texto). Linguagem simples, sem prometer previsão."""
    local = f"{m.nome} ({m.uf})" if m.uf else m.nome
    dia = m.data.strftime("%d/%m")
    if decisao.motivo == "risco_alto":
        assunto = f"FogoCerto · risco ALTO em {local}"
        acao = "Não faça queima. Se vir fogo ou fumaça, ligue para a Defesa Civil (199) ou os Bombeiros (193)."
    else:
        assunto = f"FogoCerto · atenção em {local}: {m.focos_ontem} focos de calor"
        acao = (
            "Evite queimar: há muitos focos de calor na região. "
            "Se vir fogo ou fumaça, ligue para a Defesa Civil (199) ou os Bombeiros (193)."
        )

    motivos = "; ".join(m.fatores) if m.fatores else "sem detalhe dos fatores no dado"
    linhas = [
        assunto,
        f"Risco {NOME_NIVEL[m.nivel_risco]} com dados fechados de {dia}. Motivos: {motivos}.",
    ]
    if decisao.dias_atraso > 1:
        linhas.append(f"Atenção: é o dado mais recente disponível ({dia}); o de ontem ainda não chegou.")
    linhas += [acao, FRASE_OBRIGATORIA]
    return assunto, "\n".join(linhas)
