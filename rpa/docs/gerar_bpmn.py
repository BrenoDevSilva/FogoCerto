"""Gera o fluxo da automação em BPMN 2.0 (fluxo_rpa.bpmn) e uma figura (fluxo_rpa.svg).

O .bpmn abre no Camunda Modeler ou em https://demo.bpmn.io (arrastar o arquivo).
A figura usa o mesmo desenho, para o relatório em PDF.

Uso: python docs/gerar_bpmn.py
"""

from __future__ import annotations

from dataclasses import dataclass, field
from html import escape
from pathlib import Path

AQUI = Path(__file__).resolve().parent
TAM = {"evento": (36, 36), "tarefa": (150, 80), "gateway": (50, 50)}


@dataclass
class El:
    id: str
    tipo: str  # inicio, inicio_timer, fim, fim_erro, tarefa, gateway, sub
    nome: str
    cx: float
    cy: float
    pai: str | None = None
    w: float = 0
    h: float = 0
    multi: bool = False

    def __post_init__(self):
        if self.tipo != "sub":
            base = "evento" if self.tipo.startswith(("inicio", "fim")) else self.tipo
            self.w, self.h = TAM[base]

    @property
    def x(self):
        return self.cx - self.w / 2

    @property
    def y(self):
        return self.cy - self.h / 2


@dataclass
class Fluxo:
    id: str
    de: str
    para: str
    nome: str = ""
    pontos: list = field(default_factory=list)


ELS: dict[str, El] = {}
FLUXOS: list[Fluxo] = []


def el(id, tipo, nome, cx, cy, pai=None):
    ELS[id] = El(id, tipo, nome, cx, cy, pai)
    return ELS[id]


def sub(id, nome, x, y, w, h, pai=None):
    e = El(id, "sub", nome, x + w / 2, y + h / 2, pai, w, h, multi=True)
    ELS[id] = e
    return e


def fluxo(de, para, nome=""):
    FLUXOS.append(Fluxo(f"f_{de}_{para}", de, para, nome))


# ---------------------------------------------------------------- desenho
Y = 130      # linha principal
YB = 310     # linha de baixo (registros)
YF = 400     # fins da linha de baixo

el("inicio", "inicio_timer", "Todo dia, 13:00", 40, Y)
el("ler", "tarefa", "Ler risco_atual.json (até 3 tentativas)", 160, Y)
el("g_leu", "gateway", "Leitura ok?", 300, Y)
el("validar", "tarefa", "Validar JSON e cada município", 420, Y)
el("g_valido", "gateway", "Arquivo válido?", 560, Y)
el("assin", "tarefa", "Carregar assinantes", 680, Y)
el("g_assin", "gateway", "Assinantes ok?", 820, Y)
el("erro", "tarefa", "Registrar erro no log e no resumo (sem enviar)", 560, YB)
el("fim_erro", "fim_erro", "Abortado sem alerta", 560, YF + 20)

MX, MY = 900, 0
sub("mun", "Para cada município (repetição)", MX, MY, 1340, 535)
el("m_ini", "inicio", "", MX + 40, Y, "mun")
el("g_atraso", "gateway", "Dado com mais de 2 dias?", MX + 120, Y, "mun")
el("g_regra", "gateway", "Risco alto, ou médio com 100+ focos?", MX + 290, Y, "mun")
el("g_tem", "gateway", "Tem assinante?", MX + 460, Y, "mun")
el("retido", "tarefa", "Registrar 'retido: dado atrasado'", MX + 120, YB, "mun")
el("sem_alerta", "tarefa", "Registrar 'sem alerta'", MX + 290, YB, "mun")
el("sem_assin", "tarefa", "Registrar 'sem assinante'", MX + 460, YB, "mun")
el("m_fim1", "fim", "", MX + 120, YF + 20, "mun")
el("m_fim2", "fim", "", MX + 290, YF + 20, "mun")
el("m_fim3", "fim", "", MX + 460, YF + 20, "mun")

AX, AY = MX + 545, 25
sub("ass", "Para cada assinante do município (repetição)", AX, AY, 730, 470, "mun")
el("a_ini", "inicio", "", AX + 35, Y, "ass")
el("g_dup", "gateway", "Já enviado (município + data)?", AX + 110, Y, "ass")
el("enviar", "tarefa", "Montar mensagem e enviar (Telegram ou e-mail)", AX + 250, Y, "ass")
el("g_ok", "gateway", "Enviou?", AX + 400, Y, "ass")
el("marcar", "tarefa", "Marcar como enviado e registrar no log", AX + 540, Y, "ass")
el("a_fim", "fim", "", AX + 680, Y, "ass")
el("dup", "tarefa", "Registrar 'duplicado' (não reenvia)", AX + 110, YB, "ass")
el("falha_env", "tarefa", "Registrar falha (segue para o próximo)", AX + 400, YB, "ass")
el("a_fim2", "fim", "", AX + 110, YF + 20, "ass")
el("a_fim3", "fim", "", AX + 400, YF + 20, "ass")
el("m_fim", "fim", "", MX + 1305, Y, "mun")

el("publicar", "tarefa", "Publicar alertas.json para o site (MVP)", MX + 1340 + 110, Y)
el("resumo", "tarefa", "Gravar resumo da execução (auditoria)", MX + 1340 + 290, Y)
el("fim", "fim", "Concluído", MX + 1340 + 410, Y)

fluxo("inicio", "ler"); fluxo("ler", "g_leu"); fluxo("g_leu", "validar", "sim"); fluxo("g_leu", "erro", "não")
fluxo("validar", "g_valido"); fluxo("g_valido", "assin", "sim"); fluxo("g_valido", "erro", "não")
fluxo("assin", "g_assin"); fluxo("g_assin", "mun", "sim"); fluxo("g_assin", "erro", "não"); fluxo("erro", "fim_erro")
fluxo("m_ini", "g_atraso"); fluxo("g_atraso", "retido", "sim"); fluxo("g_atraso", "g_regra", "não")
fluxo("g_regra", "sem_alerta", "não"); fluxo("g_regra", "g_tem", "sim")
fluxo("g_tem", "sem_assin", "não"); fluxo("g_tem", "ass", "sim")
fluxo("retido", "m_fim1"); fluxo("sem_alerta", "m_fim2"); fluxo("sem_assin", "m_fim3"); fluxo("ass", "m_fim")
fluxo("a_ini", "g_dup"); fluxo("g_dup", "dup", "sim"); fluxo("g_dup", "enviar", "não")
fluxo("enviar", "g_ok"); fluxo("g_ok", "marcar", "sim"); fluxo("g_ok", "falha_env", "não"); fluxo("marcar", "a_fim")
fluxo("dup", "a_fim2"); fluxo("falha_env", "a_fim3")
fluxo("mun", "publicar"); fluxo("publicar", "resumo"); fluxo("resumo", "fim")


def rotear(f: Fluxo):
    a, b = ELS[f.de], ELS[f.para]
    if b.cy - b.h / 2 > a.cy + a.h / 2 - 1 and a.tipo != "sub":  # alvo abaixo
        x0, y0 = a.cx, a.cy + a.h / 2
        if b.x <= x0 <= b.x + b.w:
            return [(x0, y0), (x0, b.y)]
        borda = b.x if b.cx > x0 else b.x + b.w
        return [(x0, y0), (x0, b.cy), (borda, b.cy)]
    x0 = a.x + a.w
    y_saida = Y if a.tipo == "sub" else a.cy
    y_chegada = Y if b.tipo == "sub" else b.cy
    return [(x0, y_saida), (b.x, y_chegada)]


for f in FLUXOS:
    f.pontos = rotear(f)


# ---------------------------------------------------------------- BPMN XML
def filhos(pai):
    return [e for e in ELS.values() if e.pai == pai]


TAG = {"inicio": "startEvent", "inicio_timer": "startEvent", "fim": "endEvent", "fim_erro": "endEvent",
       "tarefa": "serviceTask", "gateway": "exclusiveGateway", "sub": "subProcess"}


def xml_escopo(pai, nivel):
    ind = "  " * nivel
    ids = {e.id for e in filhos(pai)}
    out = []
    for e in filhos(pai):
        tag = TAG[e.tipo]
        out.append(f'{ind}<bpmn:{tag} id="{e.id}" name="{escape(e.nome)}">')
        for f in FLUXOS:
            if f.para == e.id:
                out.append(f"{ind}  <bpmn:incoming>{f.id}</bpmn:incoming>")
            if f.de == e.id:
                out.append(f"{ind}  <bpmn:outgoing>{f.id}</bpmn:outgoing>")
        if e.tipo == "inicio_timer":
            out.append(f'{ind}  <bpmn:timerEventDefinition id="{e.id}_timer"><bpmn:timeCycle xsi:type="bpmn:tFormalExpression">R/2026-11-14T13:00:00-03:00/P1D</bpmn:timeCycle></bpmn:timerEventDefinition>')
        if e.tipo == "fim_erro":
            out.append(f'{ind}  <bpmn:errorEventDefinition id="{e.id}_def" />')
        if e.tipo == "sub":
            out.append(f'{ind}  <bpmn:multiInstanceLoopCharacteristics isSequential="true" />')
            out += xml_escopo(e.id, nivel + 1)
        out.append(f"{ind}</bpmn:{tag}>")
    for f in FLUXOS:
        if f.de in ids:
            out.append(f'{ind}<bpmn:sequenceFlow id="{f.id}" name="{escape(f.nome)}" sourceRef="{f.de}" targetRef="{f.para}" />')
    return out


def xml():
    di = []
    for e in ELS.values():
        extra = ' isExpanded="true"' if e.tipo == "sub" else ""
        extra += ' isMarkerVisible="true"' if e.tipo == "gateway" else ""
        di.append(f'      <bpmndi:BPMNShape id="{e.id}_di" bpmnElement="{e.id}"{extra}>'
                  f'<dc:Bounds x="{e.x:.0f}" y="{e.y:.0f}" width="{e.w:.0f}" height="{e.h:.0f}" /></bpmndi:BPMNShape>')
    for f in FLUXOS:
        pts = "".join(f'<di:waypoint x="{x:.0f}" y="{y:.0f}" />' for x, y in f.pontos)
        di.append(f'      <bpmndi:BPMNEdge id="{f.id}_di" bpmnElement="{f.id}">{pts}</bpmndi:BPMNEdge>')
    return "\n".join([
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
        'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" '
        'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'id="fogocerto_rpa" targetNamespace="https://github.com/BrenoDevSilva/FogoCerto" exporter="gerar_bpmn.py">',
        '  <bpmn:process id="alerta_diario" name="FogoCerto - alerta diário de risco de fogo" isExecutable="false">',
        *xml_escopo(None, 2),
        "  </bpmn:process>",
        '  <bpmndi:BPMNDiagram id="diagrama">',
        '    <bpmndi:BPMNPlane id="plano" bpmnElement="alerta_diario">',
        *di,
        "    </bpmndi:BPMNPlane>",
        "  </bpmndi:BPMNDiagram>",
        "</bpmn:definitions>",
    ])


# ---------------------------------------------------------------- SVG
def quebrar(texto, largura_chars):
    linhas, atual = [], ""
    for p in texto.split():
        if len(atual) + len(p) + 1 > largura_chars and atual:
            linhas.append(atual)
            atual = p
        else:
            atual = f"{atual} {p}".strip()
    return linhas + ([atual] if atual else [])


def texto(x, y, linhas, tam=12, ancora="middle", peso="normal"):
    alt = tam * 1.25
    y0 = y - (len(linhas) - 1) * alt / 2
    spans = "".join(f'<tspan x="{x:.0f}" y="{y0 + i * alt + tam * 0.35:.0f}">{escape(l)}</tspan>' for i, l in enumerate(linhas))
    return f'<text font-size="{tam}" text-anchor="{ancora}" font-weight="{peso}">{spans}</text>'


def svg():
    largura = max(e.x + e.w for e in ELS.values()) + 40
    altura = max(e.y + e.h for e in ELS.values()) + 70
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{largura:.0f}" height="{altura:.0f}" '
         f'viewBox="-10 -10 {largura + 10:.0f} {altura + 10:.0f}" font-family="Segoe UI, Arial, sans-serif">',
         '<defs><marker id="seta" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="8" markerHeight="8" orient="auto">'
         '<path d="M0,0 L10,5 L0,10 z" fill="#333"/></marker></defs>',
         f'<rect x="-10" y="-10" width="{largura + 10:.0f}" height="{altura + 10:.0f}" fill="#fff"/>']
    for e in sorted(ELS.values(), key=lambda e: e.tipo != "sub"):  # subprocessos atrás
        if e.tipo == "sub":
            fundo = "#fbf7f2" if e.pai is None else "#f3ede4"
            s.append(f'<rect x="{e.x}" y="{e.y}" width="{e.w}" height="{e.h}" rx="14" fill="{fundo}" stroke="#7a5a3a" stroke-width="1.5"/>')
            s.append(texto(e.x + 14, e.y + 20, [e.nome], 13, "start", "bold"))
            mx, my = e.cx, e.y + e.h - 18
            for dx in (-6, 0, 6):
                s.append(f'<line x1="{mx + dx}" y1="{my}" x2="{mx + dx}" y2="{my + 12}" stroke="#333" stroke-width="2"/>')
        elif e.tipo == "tarefa":
            s.append(f'<rect x="{e.x}" y="{e.y}" width="{e.w}" height="{e.h}" rx="10" fill="#fff" stroke="#333" stroke-width="1.5"/>')
            s.append(texto(e.cx, e.cy, quebrar(e.nome, 21), 12))
        elif e.tipo == "gateway":
            r = e.w / 2
            s.append(f'<polygon points="{e.cx},{e.cy - r} {e.cx + r},{e.cy} {e.cx},{e.cy + r} {e.cx - r},{e.cy}" fill="#fff8d6" stroke="#333" stroke-width="1.5"/>')
            k = 9
            s.append(f'<path d="M{e.cx - k},{e.cy - k} L{e.cx + k},{e.cy + k} M{e.cx + k},{e.cy - k} L{e.cx - k},{e.cy + k}" stroke="#333" stroke-width="2.5"/>')
            s.append(texto(e.cx, e.y - 22, quebrar(e.nome, 22), 11))
        else:
            r = e.w / 2
            grossa = e.tipo.startswith("fim")
            cor = "#fde4e1" if e.tipo == "fim_erro" else "#e7f5e9" if e.tipo.startswith("inicio") else "#fff"
            s.append(f'<circle cx="{e.cx}" cy="{e.cy}" r="{r}" fill="{cor}" stroke="#333" stroke-width="{4 if grossa else 1.5}"/>')
            if e.tipo == "inicio_timer":
                s.append(f'<circle cx="{e.cx}" cy="{e.cy}" r="{r - 6}" fill="#fff" stroke="#333" stroke-width="1.2"/>'
                         f'<path d="M{e.cx},{e.cy - 8} L{e.cx},{e.cy} L{e.cx + 6},{e.cy + 3}" stroke="#333" stroke-width="1.5" fill="none"/>')
            if e.tipo == "fim_erro":
                s.append(f'<path d="M{e.cx - 7},{e.cy + 7} L{e.cx - 3},{e.cy - 7} L{e.cx + 2},{e.cy + 2} L{e.cx + 7},{e.cy - 7}" stroke="#333" stroke-width="2" fill="none"/>')
            if e.nome:
                s.append(texto(e.cx, e.cy + r + 18, quebrar(e.nome, 22), 11))
    for f in FLUXOS:
        pts = " ".join(f"{x:.0f},{y:.0f}" for x, y in f.pontos)
        s.append(f'<polyline points="{pts}" fill="none" stroke="#333" stroke-width="1.5" marker-end="url(#seta)"/>')
        if f.nome:
            (x0, y0), (x1, y1) = f.pontos[0], f.pontos[1]
            if abs(y0 - y1) < 1:
                s.append(texto(x0 + 3, y0 - 9, [f.nome], 10, "start", "bold"))
            else:
                s.append(texto(x0 + 6, y0 + 14, [f.nome], 11, "start", "bold"))
    s.append(texto(10, altura - 30, ["FogoCerto · RPA · alerta diário de risco de fogo (BPMN 2.0, fonte: docs/fluxo_rpa.bpmn)"], 12, "start"))
    s.append("</svg>")
    return "\n".join(s)


if __name__ == "__main__":
    (AQUI / "fluxo_rpa.bpmn").write_text(xml(), encoding="utf-8")
    (AQUI / "fluxo_rpa.svg").write_text(svg(), encoding="utf-8")
    print("ok:", len(ELS), "elementos,", len(FLUXOS), "fluxos")
