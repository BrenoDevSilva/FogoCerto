"""Gera o relatório técnico de RPA em PDF (docs/relatorio_rpa.pdf).

Os números, trechos de log e mensagens vêm dos arquivos de evidência em
``tests/evidencias/`` e ``logs/amostras/``: rode ``python tests/gerar_evidencias.py``
antes, para o relatório refletir o código atual.

Uso (dentro de ``rpa/``)::

    python docs/gerar_relatorio.py --video https://youtu.be/XXXX
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from PIL import Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, Image as RLImage, KeepTogether, NextPageTemplate,
                                PageBreak, PageTemplate, Paragraph, Preformatted, Spacer, Table, TableStyle)

RPA = Path(__file__).resolve().parent.parent
EVID = RPA / "tests" / "evidencias"
TMP = RPA / "docs" / "_figuras_relatorio"
REPO = "https://github.com/BrenoDevSilva/FogoCerto"

INTEGRANTES = [("Breno Silva", "RM99275"), ("Eduardo Araujo", "RM99758"), ("Gabriela Trevisan", "RM99500"),
               ("Gustavo Akio", "RM550241"), ("Rafael Franck", "RM550875")]

# ------------------------------------------------------------------ fontes e estilos
FONTES = Path("C:/Windows/Fonts")
pdfmetrics.registerFont(TTFont("Texto", str(FONTES / "segoeui.ttf")))
pdfmetrics.registerFont(TTFont("Texto-B", str(FONTES / "segoeuib.ttf")))
pdfmetrics.registerFont(TTFont("Mono", str(FONTES / "consola.ttf")))
pdfmetrics.registerFontFamily("Texto", normal="Texto", bold="Texto-B", italic="Texto", boldItalic="Texto-B")

COR = colors.HexColor("#9a3412")
CINZA = colors.HexColor("#57534e")
FUNDO = colors.HexColor("#f5f0ea")

E = {
    "titulo": ParagraphStyle("titulo", fontName="Texto-B", fontSize=22, leading=27, textColor=COR, spaceAfter=6),
    "sub": ParagraphStyle("sub", fontName="Texto", fontSize=12, leading=16, textColor=CINZA, spaceAfter=14),
    "h1": ParagraphStyle("h1", fontName="Texto-B", fontSize=14, leading=18, textColor=COR, spaceBefore=14, spaceAfter=6,
                         keepWithNext=1),
    "h2": ParagraphStyle("h2", fontName="Texto-B", fontSize=11, leading=15, spaceBefore=8, spaceAfter=4,
                         keepWithNext=1),
    "p": ParagraphStyle("p", fontName="Texto", fontSize=10, leading=14.5, spaceAfter=6),
    "intro": ParagraphStyle("intro", fontName="Texto", fontSize=10, leading=14.5, spaceAfter=6, keepWithNext=1),
    "li": ParagraphStyle("li", fontName="Texto", fontSize=10, leading=14, leftIndent=12, bulletIndent=2, spaceAfter=3),
    "cel": ParagraphStyle("cel", fontName="Texto", fontSize=8.8, leading=11.5),
    "celb": ParagraphStyle("celb", fontName="Texto-B", fontSize=8.8, leading=11.5, textColor=colors.white),
    "leg": ParagraphStyle("leg", fontName="Texto", fontSize=8.5, leading=11, textColor=CINZA, alignment=TA_CENTER,
                          spaceBefore=3, spaceAfter=10),
    "mono": ParagraphStyle("mono", fontName="Mono", fontSize=7.2, leading=9.4, backColor=FUNDO, borderPadding=6,
                           spaceBefore=4, spaceAfter=10),
}


def p(texto, estilo="p"):
    return Paragraph(texto, E[estilo])


def itens(lista):
    return [Paragraph(t, E["li"], bulletText="•") for t in lista]


def tabela(linhas, larguras, cabecalho=True):
    dados = [[Paragraph(str(c), E["celb" if (cabecalho and i == 0) else "cel"]) for c in linha]
             for i, linha in enumerate(linhas)]
    t = Table(dados, colWidths=larguras, repeatRows=1 if cabecalho else 0)
    estilo = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d6cfc6")),
              ("VALIGN", (0, 0), (-1, -1), "TOP"),
              ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
              ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, FUNDO])]
    if cabecalho:
        estilo.append(("BACKGROUND", (0, 0), (-1, 0), COR))
    t.setStyle(TableStyle(estilo))
    t.spaceAfter = 10
    return t


def figura(caminho, largura_max, legenda, altura_max=None):
    w, h = Image.open(caminho).size
    largura = largura_max
    altura = largura * h / w
    if altura_max and altura > altura_max:
        altura, largura = altura_max, altura_max * w / h
    return KeepTogether([RLImage(str(caminho), width=largura, height=altura), p(legenda, "leg")])


def bloco(texto, largura=108):
    """Bloco monoespaçado; linhas longas continuam na linha de baixo, recuadas."""
    saida = []
    for linha in texto.splitlines():
        while len(linha) > largura:
            saida.append(linha[:largura])
            linha = "    " + linha[largura:]
        saida.append(linha)
    return KeepTogether([Preformatted("\n".join(saida), E["mono"])])  # não parte o bloco entre páginas


def linhas_log(arquivo, filtro=None, maximo=12, corte=400):
    linhas = Path(arquivo).read_text(encoding="utf-8").splitlines()
    if filtro:
        linhas = [l for l in linhas if re.search(filtro, l)]
    return "\n".join(l if len(l) <= corte else l[:corte - 1] + "…" for l in linhas[:maximo])


# ------------------------------------------------------------------ figuras do BPMN
def recortes_bpmn():
    """Divide o diagrama (muito largo) em: fluxo principal e laço de repetição."""
    TMP.mkdir(exist_ok=True)
    im = Image.open(RPA / "docs" / "fluxo_rpa.png").convert("RGB")
    k = im.width / 2728  # o SVG tem 2728 px de largura
    alto = int(560 * k)
    antes = im.crop((0, 0, int(890 * k), alto))
    depois = im.crop((int(2245 * k), 0, im.width, alto))
    juntas = Image.new("RGB", (antes.width + depois.width + int(60 * k), alto), "white")
    juntas.paste(antes, (0, 0))
    juntas.paste(depois, (antes.width + int(60 * k), 0))
    from PIL import ImageDraw, ImageFont
    d = ImageDraw.Draw(juntas)
    fonte = ImageFont.truetype(str(FONTES / "segoeuib.ttf"), int(11 * k))
    d.text((antes.width - int(30 * k), int(150 * k)), "laço (Figura 2)", fill="#9a3412", font=fonte)
    laco = im.crop((int(888 * k), 0, int(2250 * k), alto))
    juntas.save(TMP / "bpmn_principal.png")
    laco.save(TMP / "bpmn_laco.png")
    return TMP / "bpmn_principal.png", TMP / "bpmn_laco.png"


# ------------------------------------------------------------------ páginas
def rodape(canvas, doc):
    canvas.saveState()
    canvas.setFont("Texto", 8)
    canvas.setFillColor(CINZA)
    w = canvas._pagesize[0]  # muda nas páginas em paisagem
    canvas.drawString(2 * cm, 1.2 * cm, "FogoCerto · Robotic Process Automation · GS FIAP 2026.2")
    canvas.drawRightString(w - 2 * cm, 1.2 * cm, f"página {doc.page}")
    canvas.restoreState()


class Documento(BaseDocTemplate):
    def __init__(self, arquivo):
        super().__init__(str(arquivo), pagesize=A4, title="FogoCerto - Relatório técnico de RPA",
                         author="Breno Silva, Eduardo Araujo, Gabriela Trevisan, Gustavo Akio, Rafael Franck",
                         subject="Global Solution FIAP 2026.2 - CitizenTech - Robotic Process Automation")
        m = 2 * cm
        pw, ph = A4
        lw, lh = landscape(A4)
        self.addPageTemplates([
            PageTemplate("retrato", [Frame(m, m, pw - 2 * m, ph - 2 * m, id="r")], onPage=rodape, pagesize=A4),
            PageTemplate("paisagem", [Frame(m, m, lw - 2 * m, lh - 2 * m, id="p")], onPage=rodape,
                         pagesize=landscape(A4)),
        ])


def montar(video: str | None, saida: Path):
    resumo = json.loads((EVID / "resumo_cenarios.json").read_text(encoding="utf-8"))
    cen = {r["cenario"]: r for r in resumo}
    W = A4[0] - 4 * cm
    LW = landscape(A4)[0] - 4 * cm
    principal, laco = recortes_bpmn()
    link_video = (f'<link href="{video}" color="#9a3412"><u>{video}</u></link>' if video
                  else '<font color="#b91c1c"><b>[inserir o link do vídeo antes de entregar]</b></font>')
    link_repo = f'<link href="{REPO}" color="#9a3412"><u>{REPO}</u></link> (pasta <b>rpa/</b>)'

    s = []
    # Capa ------------------------------------------------------------------------------
    s += [Spacer(1, 2.2 * cm), p("FogoCerto", "titulo"),
          p("Relatório técnico · Robotic Process Automation<br/>"
            "Atividade: “Do Processo Manual à Automação Inteligente”", "sub"),
          p("Global Solution FIAP 2026.2 · CitizenTech · Engenharia de Software, 4º ano (4ES)<br/>"
            "Professores: Bruno Diniz e Cibele Ribeiro"),
          Spacer(1, 0.6 * cm), p("Integrantes", "h2"),
          tabela([["Nome completo", "RM"], *INTEGRANTES], [9 * cm, 4 * cm]),
          Spacer(1, 0.6 * cm), p("Links", "h2"),
          tabela([["Repositório GitHub", link_repo], ["Vídeo demonstrativo (até 3 min)", link_video]],
                 [5 * cm, W - 5 * cm], cabecalho=False),
          Spacer(1, 0.8 * cm),
          p("<b>Resumo.</b> O FogoCerto calcula, todo dia, o risco de fogo de 15 municípios do Pará com dados "
            "abertos do INPE e do Open-Meteo e mostra no site. A automação deste relatório leva esse risco a quem "
            "não abre o site: um robô em Python lê o mesmo arquivo de risco que o site usa, decide quais municípios "
            "precisam de alerta, repete o envio para cada assinante por Telegram ou e-mail, trata as falhas sem "
            "enviar aviso falso, registra tudo em log de auditoria sem dado pessoal e devolve ao site o que foi "
            "avisado. Foram 34 testes automáticos e 7 cenários com evidência (sucesso, decisão e falha)."),
          PageBreak()]

    # 1. CitizenTech e problema -------------------------------------------------------------
    s += [p("1. A CitizenTech e o problema resolvido", "h1"),
          p("<b>FogoCerto</b> avisa produtores rurais, brigadistas e a defesa civil se há risco de fogo no "
            "município e se é seguro (e permitido) fazer queima controlada. O risco sai de uma regra de pontos "
            "transparente (umidade, vento, chuva, calor e focos de calor do dia anterior), calculada no Databricks "
            "e publicada no arquivo <font name='Mono'>risco_atual.json</font>. O sistema <b>nunca autoriza "
            "queima</b>: informa o risco e encaminha ao órgão ambiental."),
          p("<b>O problema operacional.</b> O site só ajuda quem o abre. Para avisar os outros, alguém teria de, "
            "todo dia: abrir o arquivo de risco, conferir se o dado é recente, filtrar os municípios em risco, "
            "procurar quem mora em cada um, escrever e mandar as mensagens uma a uma e anotar o que foi feito. "
            "É um trabalho repetitivo, sujeito a esquecimento e a erro (mandar dado velho, avisar duas vezes, "
            "esquecer alguém), e que pesa mais justamente na época seca."),
          p("2. Objetivo da automação e benefício para o cidadão", "h1"),
          p("<b>Objetivo:</b> executar todo dia, sem intervenção humana, o processo “ler o risco → decidir por "
            "município → repetir para cada assinante → enviar → registrar → devolver ao site”, de forma confiável, "
            "auditável e respeitando a LGPD."),
          *itens([
              "<b>Cidadão:</b> o produtor ou o brigadista recebe no celular, de manhã, um aviso curto com o nível, "
              "os motivos e o que fazer (não queimar; telefones 199 e 193), sem precisar lembrar de abrir o site.",
              "<b>Defesa civil:</b> deixa de gastar tempo com uma tarefa manual e ganha um registro do que foi "
              "avisado, a quem (de forma anônima) e quando.",
              "<b>Confiança:</b> o robô não envia aviso com dado velho, inválido ou repetido, o que evita que as "
              "pessoas parem de ler os alertas.",
          ])]

    # 3. Processo e fluxo -----------------------------------------------------------------
    s += [p("3. Descrição do processo e desenho do fluxo", "h1"),
          p("O processo foi modelado em <b>BPMN 2.0</b> (arquivo <font name='Mono'>rpa/docs/fluxo_rpa.bpmn</font>, "
            "abre no Camunda Modeler ou em demo.bpmn.io). As figuras a seguir foram geradas a partir do mesmo "
            "modelo."),
          tabela([
              ["Elemento", "No FogoCerto"],
              ["Início", "Evento de tempo: todo dia às 13:00, depois da coleta do Big Data (10:30)."],
              ["Entradas", "risco_atual.json (o mesmo do site; arquivo local ou URL) e config/assinantes.json "
                           "(contatos, só na máquina que roda o robô)."],
              ["Etapas", "Ler com novas tentativas → validar o arquivo e cada município → carregar assinantes → "
                         "laço por município → laço por assinante → publicar alertas.json → gravar resumo."],
              ["Decisões", "Leitura ok? Arquivo válido? Assinantes ok? Dado atrasado? Risco alto ou médio com "
                           "100+ focos? Tem assinante? Já enviado? Enviou?"],
              ["Repetições", "Para cada município do arquivo; dentro dele, para cada assinante do município."],
              ["Exceções", "Fonte fora do ar, JSON inválido, item inconsistente, duplicado, falha de envio "
                           "(seção 6)."],
              ["Saídas", "Mensagens (Telegram/e-mail), log diário, resumo JSON por execução e alertas.json "
                         "para o site."],
          ], [3 * cm, W - 3 * cm]),
          NextPageTemplate("paisagem"), PageBreak(),
          figura(principal, LW, "Figura 1 – Fluxo principal: leitura, validação e tratamento de erro (esquerda); "
                                "publicação para o site e auditoria (direita). Entre as duas partes fica o laço "
                                "da Figura 2.", altura_max=13.5 * cm),
          PageBreak(),
          figura(laco, LW, "Figura 2 – Laço “para cada município” com as decisões e, dentro dele, o laço "
                           "“para cada assinante” com deduplicação e tratamento de falha de envio.",
                 altura_max=14 * cm),
          NextPageTemplate("retrato"), PageBreak()]

    # 4. Tecnologias ----------------------------------------------------------------------
    s += [p("4. Tecnologias utilizadas e justificativa", "h1"),
          tabela([
              ["Tecnologia", "Uso", "Por que"],
              ["Python 3 (só biblioteca padrão)", "Todo o robô",
               "Aceito pelo enunciado, versionado no GitHub e testável. Sem dependência externa: nada a instalar "
               "ou a quebrar, roda em qualquer máquina e agendador."],
              ["urllib / JSON", "Ler o risco (arquivo ou URL) e falar com a API do Telegram",
               "Mesma leitura funciona para o arquivo local hoje e para a URL do site ou a API amanhã."],
              ["API de bots do Telegram", "Canal principal de alerta",
               "Gratuito, chega no celular, funciona com rede fraca e é o canal mais usado no campo."],
              ["SMTP (smtplib)", "Canal de e-mail", "Alternativa para defesa civil e prefeituras."],
              ["pytest", "34 testes automáticos", "Prova sucesso, decisão e falha a cada mudança."],
              ["BPMN 2.0", "Desenho do processo", "Notação padrão de processos, exigida pela disciplina."],
              ["Agendador do Windows / cron", "Execução diária", "Já vem no sistema; não precisa de servidor."],
          ], [3.8 * cm, 4.5 * cm, W - 8.3 * cm]),
          p("UiPath e Power Automate foram descartados porque exigem licença ou conta e uma máquina Windows "
            "dedicada, e o fluxo deles não é tão simples de versionar e testar quanto código Python.")]

    # 5. Regras de negócio ----------------------------------------------------------------
    s += [p("5. Regras de negócio, decisões e processamento", "h1"),
          p("<b>Decisão por município</b> (arquivo <font name='Mono'>src/regras.py</font>; os limites mudam por "
            "variável de ambiente, sem mexer no código):"),
          tabela([
              ["Situação", "Decisão", "Justificativa"],
              ["data do dado com mais de 2 dias", "Retido, sem alerta",
               "A coleta traz o dia anterior, então o normal é data = ontem. Dado velho não pode virar aviso "
               "“atual”."],
              ["nivel_risco = alto", "Alerta: “Não faça queima”", "Mesmo nível em que o site recomenda não queimar."],
              ["nivel_risco = medio e focos_ontem ≥ 100", "Alerta de atenção: “Evite queimar”",
               "100 focos é onde a regra de risco do Big Data dá a nota máxima de focos: muito fogo em volta, "
               "mesmo com o tempo não crítico."],
              ["Demais casos", "Sem alerta", "Evita excesso de alertas, que faz as pessoas pararem de ler."],
          ], [4.3 * cm, 4 * cm, W - 8.3 * cm]),
          p("<b>Repetição.</b> Um laço percorre cada município do arquivo; dentro dele, outro percorre cada "
            "assinante daquele município. Para cada assinante, a chave <i>município + data do dado + assinante</i> "
            "impede reenvio: se já foi enviada, o robô registra “duplicado” e segue. O estado é gravado a cada "
            "envio, de forma atômica, para que uma queda no meio não cause reenvio."),
          p("<b>Mensagem.</b> Sempre traz a data do dado (nunca “hoje há risco”), os motivos calculados pelo Big "
            "Data, a orientação e a frase obrigatória sobre a autorização de queima. Exemplo real gerado no "
            "cenário de sucesso:", "intro"),
          bloco(Path(EVID / "01_sucesso_risco_alto" / "caixa_simulada.txt").read_text(encoding="utf-8")
                .split("\n\n")[0])]

    # 6. Exceções -------------------------------------------------------------------------
    s += [p("6. Tratamento de exceções e recuperação", "h1"),
          p("Nenhuma falha é silenciosa: toda exceção vira linha de log, entra no resumo da execução e muda o "
            "código de saída do programa (0 = ok, 1 = terminou com falha de envio, 2 = abortado), que o agendador "
            "pode monitorar."),
          tabela([
              ["Falha prevista", "Tratamento", "Saída"],
              ["Arquivo ausente, site ou API fora do ar, tempo esgotado",
               "3 tentativas com espera crescente (2 s, 4 s). Se não der, aborta sem enviar nada.", "2"],
              ["HTTP 4xx (endereço errado)", "Não insiste (repetir não resolve) e aborta.", "2"],
              ["JSON quebrado, vazio ou fora do formato", "Aborta sem enviar.", "2"],
              ["Item inconsistente: nível desconhecido, data futura, sem código, focos negativos",
               "Ignora só o item, registra o motivo e segue com os outros.", "0"],
              ["Município repetido no arquivo", "Mantém o primeiro e registra.", "0"],
              ["Arquivo de assinantes ausente ou ilegível", "Aborta sem enviar.", "2"],
              ["Assinante com canal ou destino inválido", "Ignora o assinante e registra.", "0"],
              ["Alerta já enviado (mesmo município e data)", "Não reenvia; registra “duplicado”.", "0"],
              ["Falha de envio (Telegram fora, chat bloqueado, SMTP)",
               "Telegram: até 3 tentativas. Registra e segue para o próximo; na próxima execução só o que "
               "falhou é tentado de novo.", "1"],
              ["Canal sem configuração", "Falham só os assinantes daquele canal.", "1"],
          ], [5.2 * cm, W - 6.6 * cm, 1.4 * cm])]

    # 7. Logs -----------------------------------------------------------------------------
    s += [p("7. Logs e evidências de auditoria", "h1"),
          *itens([
              "<font name='Mono'>logs/execucao/rpa_AAAA-MM-DD.log</font>: uma linha por evento, com data e hora, "
              "município, nível, focos, decisão, assinante (ref) e resultado.",
              "<font name='Mono'>logs/execucao/execucoes/&lt;id&gt;.json</font>: resumo de cada execução (início, "
              "fim, status, fonte, data do dado, contagens, itens com problema e erros).",
              "O assinante aparece só como <b>ref</b>, os 10 primeiros caracteres de um SHA-256: permite auditar "
              "sem expor o contato.",
          ]),
          p("Trecho real do log da execução com o arquivo oficial do site (modo simulado, 15 municípios):", "intro"),
          bloco(linhas_log(RPA / "logs" / "amostras" / "rpa_dado_oficial_simulado.log",
                           r"inicio|Almeirim|Prainha|Castanhal|fim status", 8)),
          p("Trecho do log de uma falha da fonte (cenário 03):", "intro"),
          bloco(linhas_log(EVID / "03_falha_fonte_ausente" / "rpa_2026-11-13.log", maximo=7))]

    # 8. Integração -----------------------------------------------------------------------
    s += [p("8. Integração com o MVP", "h1"),
          p("<b>Entrada:</b> o robô lê o <b>mesmo</b> <font name='Mono'>site/public/data/risco_atual.json</font> "
            "que o site mostra, gerado pela camada Ouro do Databricks. Com o site publicado, basta mudar a variável "
            "<font name='Mono'>RISCO_FONTE</font> para a URL do arquivo e, quando a API existir, para "
            "<font name='Mono'>GET /risco</font>."),
          p("<b>Saída consumida por outro componente:</b> o robô publica "
            "<font name='Mono'>site/public/data/alertas.json</font> (sem nenhum contato pessoal). O site lê esse "
            "arquivo (<font name='Mono'>site/src/data/alertas.ts</font>) e mostra no cartão do município: "
            "“Alerta automático enviado a N assinantes em DD/MM/AAAA às HH:MM”. Se o arquivo faltar ou vier "
            "quebrado, o site segue normal."),
          bloco(json.dumps(json.loads((EVID / "01_sucesso_risco_alto" / "alertas.json").read_text(encoding="utf-8"))
                           ["alertas"][0], ensure_ascii=False, indent=2)),
          figura(RPA / "assets" / "integracao_site_alerta.png", 6.5 * cm,
                 "Figura 3 – Site do FogoCerto (celular) mostrando, no cartão de Oriximiná, o alerta enviado pelo "
                 "robô. Execução em modo de teste, por isso “(envio de teste)”.", altura_max=13 * cm)]

    # 9. Testes ---------------------------------------------------------------------------
    linhas_cen = [["Cenário", "Tipo", "Resultado", "Saída"]]
    descricoes = {
        "01_sucesso_risco_alto": ("Sucesso", "2 municípios com alerta, {enviados} mensagens, alertas.json publicado"),
        "02_decisao_sem_alerta": ("Decisão", "risco baixo e médio sem focos: nenhuma mensagem"),
        "03_falha_fonte_ausente": ("Falha", "3 tentativas, abortado, nenhuma mensagem"),
        "04_falha_json_invalido": ("Falha", "abortado, nenhuma mensagem"),
        "05_dados_inconsistentes": ("Falha parcial", "{itens_invalidos} itens ruins ignorados com motivo; "
                                                     "o válido recebe {enviados} mensagens"),
        "06_falha_de_envio": ("Falha parcial", "{falhas_envio} envio falha, {enviados} saem normalmente"),
        "07_duplicado_nao_reenvia": ("Resiliência", "2ª execução: 0 enviados, {duplicados_nao_reenviados} "
                                                    "duplicados barrados"),
    }
    for nome, (tipo, modelo) in descricoes.items():
        r = cen[nome]
        linhas_cen.append([nome, tipo, modelo.format(**{"enviados": 0, **r["contagens"]}) + f" ({r['status']})",
                           str(r["codigo_saida"])])
    s += [p("9. Testes realizados", "h1"),
          p("Todos os testes rodam com o canal <b>simulado</b> (nada sai da máquina) e contatos fictícios. "
            "Os 7 cenários abaixo são gerados por <font name='Mono'>python tests/gerar_evidencias.py</font>; "
            "cada um guarda em <font name='Mono'>tests/evidencias/</font> o log, o resumo, a caixa de saída e o "
            "alertas.json."),
          tabela(linhas_cen, [4.6 * cm, 2.3 * cm, W - 8.3 * cm, 1.4 * cm]),
          p("Além disso, <b>34 testes automáticos</b> (<font name='Mono'>python -m pytest tests</font>) cobrem: "
            "cada regra de decisão e o limite exato de 100 focos; a regra da data (ontem, 2 dias, 3 dias); o texto "
            "obrigatório da mensagem; um servidor HTTP local que falha duas vezes e responde na terceira; HTTP 404 "
            "sem insistir; dado atrasado retido; data futura; canal sem configuração; reenvio só do que falhou; e "
            "uma checagem de LGPD que procura cada contato em todos os arquivos gravados (log, estado, resumo e "
            "alertas.json) e falha se encontrar algum.")]

    # 10. Segurança e LGPD ----------------------------------------------------------------
    s += [p("10. Segurança e LGPD", "h1"),
          *itens([
              "<b>Dado pessoal mínimo:</b> só o contato (chat_id do Telegram ou e-mail). Ele fica apenas em "
              "<font name='Mono'>config/assinantes.json</font>, na máquina que roda o robô, e não vai para o Git "
              "(.gitignore). No repositório só há contatos fictícios.",
              "<b>Pseudonimização:</b> logs, estado, resumo e alertas.json usam o ref (SHA-256 truncado). Um teste "
              "automático garante que nenhum contato vaze.",
              "<b>Segredos</b> (token do bot, senha SMTP) em .env ou variável de ambiente, nunca no código; o token "
              "é mascarado se aparecer numa mensagem de erro. O pipeline do repositório roda Gitleaks.",
              "<b>Consentimento e finalidade:</b> só recebe quem pediu, e só o alerta de risco. Na demonstração, "
              "apenas contas de teste do grupo.",
              "<b>Retenção:</b> o estado guarda 30 dias e o alertas.json, 14 dias.",
              "<b>Responsabilidade:</b> o alerta nunca autoriza queima e sempre encaminha ao órgão ambiental.",
          ]),
          p("11. Limitações e próximos passos", "h1"),
          *itens([
              "O arquivo oficial é atualizado por pull request do time de Big Data; se atrasar mais de 2 dias, o "
              "robô retém os alertas, de propósito.",
              "O alerta é por município, não pela distância do foco até a propriedade (o dado atual não traz a "
              "localização do assinante).",
              "Próximo passo: rodar no GitHub Actions agendado, com segredos em GitHub Secrets.",
          ]),
          KeepTogether([p("12. Links", "h1"),
                        tabela([["Repositório GitHub", link_repo], ["Vídeo demonstrativo", link_video]],
                               [5 * cm, W - 5 * cm], cabecalho=False)])]

    Documento(saida).build(s)


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("--video", default=None, help="link do vídeo no YouTube")
    a.add_argument("--saida", default=str(RPA / "docs" / "relatorio_rpa.pdf"))
    args = a.parse_args()
    montar(args.video, Path(args.saida))
    print("PDF gerado:", args.saida)
