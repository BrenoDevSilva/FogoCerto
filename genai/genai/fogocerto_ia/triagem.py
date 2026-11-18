"""Triagem de entrada: recusa por regra, antes do modelo, os pedidos que o assistente nunca deve atender.

É a mesma nas três configurações (sem contexto, RAG e agente), então não muda a comparação entre elas.
As regras são por categoria de pedido, não por pergunta: elas também são medidas nos casos novos,
escritos depois da rodada 1, para mostrar que não foram ajustadas às perguntas do teste.
"""
import re

from .busca import normalizar
from .ferramentas import carregar_risco

AVISO_ORGAO = "Procure o órgão ambiental competente do seu estado."

# Categorias de pedido (o texto é comparado sem acento e em minúsculas)
_PEDIDO_AUTORIZACAO = re.compile(
    r"\b(me|eu)\s+(autoriz\w*|liber\w*|aprov\w*)|\b(autoriz\w*|liber\w*|aprov\w*)\s+(eu|me|minha|meu|a minha|o meu)\b")
_PARECER = re.compile(
    r"minha defesa|\bdefesa (do|da|de|no|na) (meu|minha|auto|processo|multa)|escrev\w* (a |uma )?defesa|recurso contra"
    r"|vou ser (pres|conden|multad|process)|vai ser (pres|conden)|chance de (eu )?ganhar|ganhar o processo"
    r"|quanto (eu )?(ganho|recebo)|indeniza\w*|analis\w* (o )?meu caso|meu caso")
_BURLAR = re.compile(
    r"(fiscaliza\w*|ibama|policia|orgao|ninguem)\W+(\w+\W+){0,3}(perceb\w*|descobr\w*|flagr\w*|ver|saber)"
    r"|\bescond\w*|\bburl\w*|sem ser (pego|visto|descoberto)")
_INJECAO = re.compile(
    r"(ignore|esqueca|desconsidere)\W+(\w+\W+){0,3}(regras|instruc\w*|anteriores)|finja que|faca de conta")

# Município fora da cobertura: nome próprio depois de "em/de/no/na", numa pergunta sobre risco ou fogo
_TEMA_RISCO = re.compile(r"risco|foco|queim|fogo|incendi")
_LUGAR = re.compile(r"\b(?:em|de|no|na)\s+((?:[A-ZÁÉÍÓÚÂÊÔÃÕ][\wáéíóúâêôãõç]+)"
                    r"(?:\s+(?:do|da|de|dos|das)\s+[A-ZÁÉÍÓÚÂÊÔÃÕ][\wáéíóúâêôãõç]+|\s+[A-ZÁÉÍÓÚÂÊÔÃÕ][\wáéíóúâêôãõç]+)*)")
_NAO_SAO_MUNICIPIOS = {"para", "brasil", "lei", "ibama", "semas", "defesa civil", "codigo florestal", "sao joao",
                       "fogocerto", "inpe", "estado", "amazonia", "cerrado"}


def municipio_fora_da_cobertura(pergunta: str):
    """Devolve o nome do lugar citado se ele não for um dos municípios cobertos pelo FogoCerto."""
    if not _TEMA_RISCO.search(normalizar(pergunta)):
        return None
    cobertos = {normalizar(d["nome"]) for d in carregar_risco()}
    for m in _LUGAR.finditer(pergunta):
        nome = m.group(1).strip()
        n = normalizar(nome)
        if n in cobertos or n in _NAO_SAO_MUNICIPIOS or any(n.startswith(c) for c in cobertos):
            continue
        return nome
    return None


def triagem(pergunta: str):
    """None se a pergunta segue para o modelo; senão, (motivo, resposta de recusa)."""
    t = normalizar(pergunta)
    if _INJECAO.search(t):
        return ("tentativa de mudar as regras",
                "Não posso mudar as minhas regras. O FogoCerto não autoriza queima. " + AVISO_ORGAO)
    if _BURLAR.search(t):
        return ("pedido para burlar a fiscalização",
                "Não posso ajudar a esconder uma queima. Queimar sem autorização é infração ambiental. " + AVISO_ORGAO)
    if _PEDIDO_AUTORIZACAO.search(t):
        return ("pedido de autorização",
                "O FogoCerto não autoriza queima: a autorização é do órgão ambiental. " + AVISO_ORGAO)
    if _PARECER.search(t):
        return ("pedido de parecer jurídico",
                "Não dou parecer jurídico sobre casos pessoais. Procure um advogado ou a Defensoria Pública; "
                "sobre autorização de queima, " + AVISO_ORGAO.lower())
    lugar = municipio_fora_da_cobertura(pergunta)
    if lugar:
        nomes = ", ".join(sorted(d["nome"] for d in carregar_risco()))
        return ("município fora da cobertura",
                f"Não consta: o FogoCerto ainda não cobre {lugar}. Os municípios cobertos são: {nomes}.")
    return None
