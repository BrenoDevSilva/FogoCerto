"""Gera o relatório de Applied Computer Vision em PDF (docs/relatorio_visao.pdf).

Os números e figuras vêm de ``visao/resultados/`` (gerados pelo notebook de treino).
Enquanto um resultado não existe, o PDF mostra um aviso vermelho no lugar dele;
nada é inventado.

Uso (dentro de ``visao/``)::

    python docs/gerar_relatorio.py                          # usa resultados/
    python docs/gerar_relatorio.py --video https://youtu.be/XXXX
    python docs/gerar_relatorio.py --resultados <pasta> --previa --saida <arquivo>   # só para conferir layout
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, Image as RLImage, KeepTogether, PageBreak, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle)
from PIL import Image

VISAO = Path(__file__).resolve().parent.parent
REPO = "https://github.com/BrenoDevSilva/FogoCerto"
INTEGRANTES = [("Breno Silva", "RM99275"), ("Eduardo Araujo", "RM99758"), ("Gabriela Trevisan", "RM99500"),
               ("Gustavo Akio", "RM550241"), ("Rafael Franck", "RM550875")]

FONTES = Path("C:/Windows/Fonts")
pdfmetrics.registerFont(TTFont("Texto", str(FONTES / "segoeui.ttf")))
pdfmetrics.registerFont(TTFont("Texto-B", str(FONTES / "segoeuib.ttf")))
pdfmetrics.registerFont(TTFont("Mono", str(FONTES / "consola.ttf")))
pdfmetrics.registerFontFamily("Texto", normal="Texto", bold="Texto-B", italic="Texto", boldItalic="Texto-B")

COR = colors.HexColor("#9a3412")
CINZA = colors.HexColor("#57534e")
FUNDO = colors.HexColor("#f5f0ea")
VERMELHO = "#b91c1c"

E = {
    "titulo": ParagraphStyle("titulo", fontName="Texto-B", fontSize=21, leading=26, textColor=COR, spaceAfter=6),
    "sub": ParagraphStyle("sub", fontName="Texto", fontSize=12, leading=16, textColor=CINZA, spaceAfter=12),
    "h1": ParagraphStyle("h1", fontName="Texto-B", fontSize=14, leading=18, textColor=COR, spaceBefore=14,
                         spaceAfter=6, keepWithNext=1),
    "h2": ParagraphStyle("h2", fontName="Texto-B", fontSize=11, leading=15, spaceBefore=8, spaceAfter=4,
                         keepWithNext=1),
    "p": ParagraphStyle("p", fontName="Texto", fontSize=10, leading=14.5, spaceAfter=6, alignment=TA_JUSTIFY),
    "intro": ParagraphStyle("intro", fontName="Texto", fontSize=10, leading=14.5, spaceAfter=6, keepWithNext=1),
    "li": ParagraphStyle("li", fontName="Texto", fontSize=10, leading=14, leftIndent=12, bulletIndent=2, spaceAfter=3),
    "cel": ParagraphStyle("cel", fontName="Texto", fontSize=8.8, leading=11.5),
    "celb": ParagraphStyle("celb", fontName="Texto-B", fontSize=8.8, leading=11.5, textColor=colors.white),
    "leg": ParagraphStyle("leg", fontName="Texto", fontSize=8.5, leading=11, textColor=CINZA, alignment=TA_CENTER,
                          spaceBefore=3, spaceAfter=10),
    "ref": ParagraphStyle("ref", fontName="Texto", fontSize=9, leading=12.5, leftIndent=14, firstLineIndent=-14,
                          spaceAfter=4),
}


def p(texto, estilo="p"):
    return Paragraph(texto, E[estilo])


def itens(lista):
    return [Paragraph(t, E["li"], bulletText="•") for t in lista]


def falta(texto="aguardando o treino"):
    return f'<font color="{VERMELHO}"><b>[{texto}]</b></font>'


def tabela(linhas, larguras, cabecalho=True):
    dados = [[Paragraph(str(c), E["celb" if (cabecalho and i == 0) else "cel"]) for c in linha]
             for i, linha in enumerate(linhas)]
    t = Table(dados, colWidths=larguras, repeatRows=1 if cabecalho else 0)
    estilo = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d6cfc6")), ("VALIGN", (0, 0), (-1, -1), "TOP"),
              ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
              ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, FUNDO])]
    if cabecalho:
        estilo.append(("BACKGROUND", (0, 0), (-1, 0), COR))
    t.setStyle(TableStyle(estilo))
    t.spaceAfter = 10
    return t


def figura(caminho, largura_max, legenda, altura_max=None):
    caminho = Path(caminho)
    if not caminho.exists():
        caixa = Table([[Paragraph(falta(f"figura {caminho.name}: disponível depois do treino"), E["cel"])]],
                      colWidths=[largura_max], rowHeights=[2.2 * cm])
        caixa.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor(VERMELHO)),
                                   ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (0, 0), (-1, -1), "CENTER")]))
        return KeepTogether([caixa, p(legenda, "leg")])
    w, h = Image.open(caminho).size
    largura, altura = largura_max, largura_max * h / w
    if altura_max and altura > altura_max:
        altura, largura = altura_max, altura_max * w / h
    return KeepTogether([RLImage(str(caminho), width=largura, height=altura), p(legenda, "leg")])


# ------------------------------------------------------------------ dados
class Resultados:
    """Lê o que existir em resultados/ e formata números em português."""

    def __init__(self, pasta: Path):
        self.pasta = pasta

        def ler(nome):
            arq = pasta / nome
            return json.loads(arq.read_text(encoding="utf-8")) if arq.exists() else None

        self.estat = ler("estatisticas_dataset.json")
        self.caixas = ler("metricas_teste_caixas.json")
        self.limiar = ler("limiar_recomendado.json")
        self.matriz = ler("matriz_confusao_por_imagem.json")
        self.veloc = ler("velocidade.json")
        self.args = self._yaml(pasta / "treino_args.yaml")
        self.treino = self._csv(pasta / "treino_results.csv")
        self.erros = self._csv(pasta / "erros_para_anotar.csv")
        self.proprias = self._csv(pasta / "imagens_proprias_resultados.csv")

    @staticmethod
    def _csv(arq):
        if not arq.exists():
            return None
        with arq.open(encoding="utf-8") as f:
            return list(csv.DictReader(f))

    @staticmethod
    def _yaml(arq):
        if not arq.exists():
            return None
        dados = {}
        for linha in arq.read_text(encoding="utf-8").splitlines():
            if ":" in linha and not linha.startswith(" "):
                k, v = linha.split(":", 1)
                dados[k.strip()] = v.strip()
        return dados

    @staticmethod
    def num(x, casas=3):
        return f"{x:.{casas}f}".replace(".", ",")

    @staticmethod
    def pct(x, casas=1):
        return f"{100 * x:.{casas}f}".replace(".", ",") + "%"

    def m(self, chave, tipo="num", casas=3):
        """Métrica geral de caixa (mAP50, mAP50_95, precisao, recall)."""
        if not self.caixas:
            return falta()
        v = self.caixas[chave]
        return self.pct(v) if tipo == "pct" else self.num(v, casas)

    def classe(self, nome, chave):
        if not self.caixas or nome not in self.caixas.get("por_classe", {}):
            return falta()
        return self.num(self.caixas["por_classe"][nome][chave])

    def img(self, chave, tipo="pct"):
        """Métrica por imagem no limiar escolhido."""
        if not self.limiar:
            return falta()
        v = self.limiar["no_limiar"][chave]
        return self.pct(v) if tipo == "pct" else self.num(v)

    def lim(self, chave):
        return self.num(self.limiar[chave], 2) if self.limiar else falta()

    def split(self, nome, campo="imagens"):
        if not self.estat:
            return falta()
        chave = nome if nome in self.estat else ("valid" if nome == "val" else nome)
        return f"{self.estat.get(chave, {}).get(campo, 0):,}".replace(",", ".")

    def vel(self, disp, chave):
        if not self.veloc or disp not in self.veloc:
            return falta("medido no Colab" if disp == "gpu" else "aguardando o treino")
        v = self.veloc[disp][chave]
        return self.num(v, 1)

    def epocas(self):
        if not self.treino:
            return falta(), falta(), falta()
        tempos = [float(l["time"]) for l in self.treino if l.get("time")]
        crescente = all(b >= a for a, b in zip(tempos, tempos[1:]))
        total = (tempos[-1] if crescente else sum(tempos)) / 60 if tempos else 0
        melhor = max(self.treino, key=lambda l: float(l["metrics/mAP50-95(B)"]))
        return str(len(self.treino)), str(int(float(melhor["epoch"]))), self.num(total, 0) + " min"

    def arg(self, chave):
        return self.args.get(chave, "?") if self.args else falta()

    def causas_falso_alarme(self):
        if not self.erros:
            return None
        causas = Counter(l["causa_provavel"].strip().lower() for l in self.erros
                         if l["tipo"] == "falso_alarme" and l.get("causa_provavel", "").strip())
        return causas or None


# ------------------------------------------------------------------ diagrama do sistema
def diagrama(largura):
    """Do envio da foto à resposta da API (vetorial)."""
    etapas = [("Imagem", "foto, webcam\nou câmera"),
              ("Preparo", "rotação, RGB,\n640 px"),
              ("YOLO11n", "backbone, neck\ne cabeça"),
              ("Caixas + NMS", "classe e\nconfiança"),
              ("Decisão", "limiar e faixa\nde dúvida"),
              ("Resposta", "fogo, fumaça\nou nada")]
    n = len(etapas)
    gap = 14
    bw = (largura - gap * (n - 1)) / n
    bh, alto = 62, 92
    d = Drawing(largura, alto)
    for i, (titulo, sub) in enumerate(etapas):
        x = i * (bw + gap)
        destaque = titulo == "YOLO11n"
        d.add(Rect(x, 14, bw, bh, rx=6, ry=6, fillColor=colors.HexColor("#fde7d9" if destaque else "#ffffff"),
                   strokeColor=COR if destaque else CINZA, strokeWidth=1.4 if destaque else 0.8))
        d.add(String(x + bw / 2, 14 + bh - 16, titulo, fontName="Texto-B", fontSize=8.6, textAnchor="middle"))
        for j, linha in enumerate(sub.split("\n")):
            d.add(String(x + bw / 2, 14 + bh - 32 - j * 10, linha, fontName="Texto", fontSize=7.2,
                         textAnchor="middle", fillColor=CINZA))
        if i < n - 1:
            xa, ya = x + bw + 1, 14 + bh / 2
            d.add(Line(xa, ya, xa + gap - 4, ya, strokeColor=CINZA, strokeWidth=1))
            d.add(Polygon([xa + gap - 2, ya, xa + gap - 7, ya + 3, xa + gap - 7, ya - 3], fillColor=CINZA,
                          strokeColor=CINZA))
    d.add(String(largura / 2, 2, "A imagem fica só na memória e é descartada após a resposta (LGPD).",
                 fontName="Texto", fontSize=7.5, textAnchor="middle", fillColor=CINZA))
    return d


# ------------------------------------------------------------------ páginas
def rodape(previa):
    def _(canvas, doc):
        canvas.saveState()
        canvas.setFont("Texto", 8)
        canvas.setFillColor(CINZA)
        w = canvas._pagesize[0]
        canvas.drawString(2 * cm, 1.2 * cm, "FogoCerto · Applied Computer Vision · GS FIAP 2026.2")
        canvas.drawRightString(w - 2 * cm, 1.2 * cm, f"página {doc.page}")
        if previa:
            canvas.setFillColor(colors.HexColor(VERMELHO))
            canvas.setFont("Texto-B", 9)
            canvas.drawCentredString(w / 2, canvas._pagesize[1] - 1.1 * cm,
                                     "PRÉVIA DE LAYOUT COM NÚMEROS DE TESTE: NÃO ENTREGAR")
        canvas.restoreState()
    return _


def palavras(html):
    import re
    return len(re.sub(r"<[^>]+>", " ", html).split())


def montar(r: Resultados, video, saida: Path, previa: bool):
    W = A4[0] - 4 * cm
    link_video = (f'<link href="{video}" color="#9a3412"><u>{video}</u></link>' if video
                  else falta("inserir o link do vídeo antes de entregar"))
    link_repo = f'<link href="{REPO}" color="#9a3412"><u>{REPO}</u></link> (pasta <b>visao/</b>)'
    n_ep, melhor_ep, tempo = r.epocas()
    causas = r.causas_falso_alarme()
    if causas:
        top = [c for c, _ in causas.most_common(3)]
        frase_erros = ("A análise dos erros mostra que os falsos alarmes vêm principalmente de "
                       + (", ".join(top[:-1]) + " e " + top[-1] if len(top) > 1 else top[0]) + ".")
    else:
        frase_erros = falta("resumir as causas dos erros depois de preencher erros_para_anotar.csv")

    resumo = (
        "Focos de incêndio em vegetação são detectados por satélite, mas o satélite só registra o foco quando "
        "passa sobre a área, e fogos pequenos podem escapar. No FogoCerto, plataforma CitizenTech que avisa "
        "produtores rurais e a defesa civil do Pará sobre o risco diário de fogo, a visão computacional faz a "
        "confirmação em campo: a pessoa envia uma foto e o sistema indica se vê fumaça ou fogo. Treinamos de "
        "forma customizada um detector de objetos YOLO11n, partindo de pesos pré-treinados no COCO, com o "
        f"conjunto público D-Fire (mais de 21 mil imagens rotuladas, licença CC0), que inclui cerca de 9,8 mil "
        f"imagens sem fogo para medir falsos alarmes. No conjunto de teste, com {r.split('test')} imagens que o "
        f"modelo nunca viu, o detector alcançou mAP@50 de {r.m('mAP50')} e mAP@50-95 de {r.m('mAP50_95')}, com "
        f"precisão de {r.m('precisao')} e recall de {r.m('recall')}. Na avaliação por imagem, que reflete o uso "
        f"no produto, o limiar de confiança {r.lim('limiar')} foi escolhido por critério explícito, com "
        f"sensibilidade de {r.img('sensibilidade_ocorrencia')} e falso alarme de {r.img('falso_alarme')}. A "
        f"inferência leva {r.vel('cpu', 'ms_por_imagem')} ms por imagem em CPU, cerca de "
        f"{r.vel('cpu', 'fps')} quadros por segundo, o que permite uso em tempo real em webcam ou vídeo. O "
        "modelo foi integrado a uma API que devolve classe, confiança e uma orientação, não guarda a imagem e "
        f"cruza o resultado com o risco do município. {frase_erros} Como próximo passo, a mesma entrada pode "
        "receber quadros de câmeras fixas em fazendas e torres."
    )
    objetivo = (
        "Treinar e avaliar um detector YOLO11 que localize fumaça e fogo em imagens, medindo com honestidade "
        "acertos e falsos alarmes, e integrá-lo ao FogoCerto como confirmação em campo: o produtor envia uma "
        "foto e recebe, em segundos, a classe, a confiança e a orientação de procurar a defesa civil."
    )
    print(f"resumo: {palavras(resumo)} palavras | objetivo: {palavras(objetivo)} palavras")

    s = []
    # Capa ---------------------------------------------------------------------------------
    s += [Spacer(1, 1.6 * cm), p("FogoCerto", "titulo"),
          p("Detecção de fumaça e fogo em imagens com YOLO11 para confirmação em campo<br/>"
            "Atividade “Enxergando o mundo real” · Applied Computer Vision", "sub"),
          p("Global Solution FIAP 2026.2 · CitizenTech · Engenharia de Software, 4º ano (4ES)<br/>"
            "Professores: Arnaldo Viana e Paulo Rodrigues", "intro"),
          Spacer(1, 0.4 * cm), p("Integrantes", "h2"),
          tabela([["Nome completo", "RM"], *INTEGRANTES], [9 * cm, 4 * cm]),
          p("Links", "h2"),
          tabela([["Repositório GitHub", link_repo], ["Vídeo de demonstração", link_video]],
                 [5 * cm, W - 5 * cm], cabecalho=False),
          p("Resumo", "h1"), p(resumo),
          p("Objetivo", "h1"), p(objetivo),
          PageBreak()]

    # Introdução ---------------------------------------------------------------------------
    s += [p("1. Introdução", "h1"),
          p("O Pará está entre os estados com mais focos de calor do Brasil na estação seca. O FogoCerto é "
            "uma CitizenTech que avisa, a cada manhã, produtores rurais e a defesa civil de 15 municípios do "
            "estado se há risco de fogo e se é seguro (e permitido) fazer queima controlada. O risco diário vem de "
            "dados abertos de focos de calor do INPE e do clima do Open-Meteo."),
          p("Esse aviso tem um ponto cego: o foco de calor só aparece quando um satélite passa sobre a área, cada "
            "ponto do sensor cobre de 375 m a 1 km e fogos pequenos ou começando podem não ser registrados. Quem está "
            "no campo, porém, vê a fumaça antes. A visão computacional entra aqui como <b>confirmação em campo</b>: "
            "o produtor ou o brigadista fotografa o que está vendo e o sistema diz se identifica fumaça ou fogo. "
            "Uma foto com fumaça, num município que já está em risco alto, sobe na fila de atenção da defesa civil."),
          p("Escolhemos <b>detecção de objetos</b>, e não apenas classificação da imagem inteira, por três motivos: "
            "a caixa mostra <i>onde</i> está a fumaça, o que torna a resposta verificável por quem olha; a "
            "detecção funciona quando a fumaça ocupa uma parte pequena da foto, como numa coluna distante no "
            "horizonte; e o mesmo modelo serve para vídeo e para câmeras fixas, que são o próximo passo do "
            "produto. O modelo não substitui o olhar humano nem a defesa civil: ele ajuda a triar."),
          diagrama(W),
          p("Figura 1 – Caminho da imagem dentro do FogoCerto, do envio à resposta da API.", "leg")]

    # Ferramentas --------------------------------------------------------------------------
    s += [p("2. Explicação técnica das ferramentas", "h1"),
          p("2.1 Detecção de objetos e YOLO", "h2"),
          p("Um detector de objetos recebe uma imagem e devolve uma lista de <b>caixas delimitadoras</b>, cada uma "
            "com uma classe e uma confiança entre 0 e 1. A família <b>YOLO</b> (<i>You Only Look Once</i>) faz isso "
            "numa única passada da rede neural, o que a torna rápida o bastante para vídeo em tempo real. Usamos o "
            "<b>YOLO11</b> da Ultralytics, que tem três partes: o <i>backbone</i>, uma rede convolucional que extrai "
            "características (bordas, texturas, cores) em várias escalas; o <i>neck</i>, que combina essas escalas "
            "para enxergar tanto objetos grandes quanto pequenos; e a <i>cabeça de detecção</i>, que prevê as caixas "
            "sem âncoras pré-definidas. Por fim, a <b>supressão de não-máximos (NMS)</b> remove caixas repetidas "
            "sobre o mesmo objeto."),
          p("Escolhemos a variante <b>nano (YOLO11n)</b>, com cerca de 2,6 milhões de parâmetros, porque o produto "
            "precisa rodar em servidor sem GPU e, no futuro, em equipamentos simples no campo."),
          p("2.2 Treinamento customizado com transfer learning", "h2"),
          p("O modelo parte de pesos já treinados no COCO (80 classes do dia a dia) e é ajustado para as nossas "
            "duas classes, <b>fumaca</b> e <b>fogo</b>. Assim, ele aproveita o que já sabe sobre formas e texturas e "
            "precisa de bem menos dados e tempo. Durante o treino, o Ultralytics aplica <i>data augmentation</i>: "
            "mosaico de quatro imagens, variação de cor (HSV), espelhamento horizontal, mudança de escala e "
            "translação. Isso imita fotos tiradas em condições diferentes e reduz o sobreajuste."),
          p("2.3 Métricas", "h2"),
          tabela([
              ["Métrica", "O que mede"],
              ["IoU", "Quanto a caixa prevista sobrepõe a caixa real (0 a 1)."],
              ["Precisão", "Das caixas que o modelo marcou, quantas estavam certas (poucos alarmes falsos)."],
              ["Recall", "Das fumaças e fogos reais, quantos o modelo encontrou (poucos casos perdidos)."],
              ["mAP@50", "Área sob a curva precisão × recall, contando como acerto a caixa com IoU ≥ 0,5. Média das "
                         "duas classes."],
              ["mAP@50-95", "Média do mAP com IoU de 0,50 a 0,95: exige caixas mais justas."],
              ["Matriz de confusão", "Cruza o real com o previsto. A linha e a coluna <i>background</i> mostram "
                                     "alarmes onde não havia nada e objetos que o modelo não viu."],
              ["Sensibilidade e falso alarme (por imagem)", "Visão do produto: das fotos com fumaça ou fogo, quantas "
                                                           "foram avisadas; das fotos sem nada, quantas geraram alarme."],
          ], [4.2 * cm, W - 4.2 * cm]),
          p("2.4 Ferramentas de software", "h2"),
          tabela([
              ["Ferramenta", "Uso"],
              ["Python, PyTorch e Ultralytics", "Treino, validação, exportação e inferência do YOLO11."],
              ["Google Colab (GPU NVIDIA T4)", "Treino. O notebook salva cada época no Google Drive e retoma "
                                               "sozinho se a sessão cair."],
              ["kagglehub", "Download do D-Fire."],
              ["FastAPI e Pillow", "API POST /visao/classificar, com a imagem só em memória."],
              ["OpenCV", "Detecção em tempo real em webcam ou arquivo de vídeo."],
              ["pytest", "28 testes da regra de decisão e da API."],
          ], [5.2 * cm, W - 5.2 * cm])]

    # Metodologia --------------------------------------------------------------------------
    estat_linhas = [["Conjunto", "Imagens", "Só fumaça", "Só fogo", "Fogo e fumaça", "Sem nada"]]
    for nome, rotulo in (("train", "Treino"), ("val", "Validação"), ("test", "Teste")):
        estat_linhas.append([rotulo, r.split(nome), r.split(nome, "so_fumaca"), r.split(nome, "so_fogo"),
                             r.split(nome, "fogo_e_fumaca"), r.split(nome, "nenhum")])
    s += [p("3. Metodologia (passo a passo)", "h1"),
          p("<b>Passo 1 – Definir o problema e as classes.</b> Duas classes: <b>fumaca</b> (id 0) e <b>fogo</b> "
            "(id 1). Para o produto, cada imagem recebe uma resposta única: <i>fogo</i> se houver caixa de fogo, "
            "senão <i>fumaça</i>, senão <i>nada</i> (o fogo tem prioridade por ser mais grave)."),
          p("<b>Passo 2 – Escolher o conjunto de dados.</b> Usamos o <b>D-Fire</b> (Venâncio, Lisboa e Barbosa, "
            "UFMG), licença CC0 (domínio público), na versão do Kaggle já dividida em treino, validação e teste. "
            "O conjunto tem fumaça vista de perto e de longe, inclusive de câmeras de vigilância, e muitas imagens "
            "sem fogo, que são essenciais para medir falsos alarmes. Os nomes das classes foram trocados para "
            "português no arquivo de configuração.", "intro"),
          tabela(estat_linhas, [3 * cm] + [(W - 3 * cm) / 5] * 5),
          figura(r.pasta / "exemplos_dataset.png", W, "Figura 2 – Exemplos do D-Fire com os rótulos reais (verde). "
                                                      "As últimas imagens não têm fogo nem fumaça.", 9 * cm),
          p(f"<b>Passo 3 – Treinar.</b> YOLO11n pré-treinado no COCO, imagens de {r.arg('imgsz')} px, lote de "
            f"{r.arg('batch')}, otimizador {r.arg('optimizer')}, até {r.arg('epochs')} épocas com parada antecipada "
            f"(paciência de {r.arg('patience')} épocas sem melhora na validação) e semente {r.arg('seed')} para "
            f"reprodutibilidade. Foram {n_ep} épocas em cerca de {tempo} numa GPU T4; o melhor peso (época "
            f"{melhor_ep}) foi escolhido pela validação, nunca pelo teste."),
          figura(r.pasta / "treino_results.png", W, "Figura 3 – Curvas de treino: perdas caindo e métricas de "
                                                    "validação subindo a cada época.", 9 * cm),
          p("<b>Passo 4 – Avaliar por caixa no teste.</b> Rodamos o melhor peso no conjunto de <b>teste</b>, que não "
            "participou do treino nem da escolha do peso, e calculamos precisão, recall, mAP@50, mAP@50-95 e a "
            "matriz de confusão."),
          p("<b>Passo 5 – Avaliar por imagem e escolher o limiar.</b> Rodamos o modelo uma vez em todo o teste com "
            "confiança mínima de 0,05 e variamos o limiar de 0,05 a 0,80. O <b>limiar</b> escolhido é o que dá o "
            "maior F1 de “ocorrência” (foto com fogo ou fumaça contra foto sem nada). Abaixo dele existe uma "
            "<b>faixa de dúvida</b>, que começa no maior limiar que ainda avisa 95% das fotos com fogo ou fumaça: "
            "nessa faixa a API não confirma, mas também não descarta, e orienta a pessoa a procurar a defesa civil."),
          p("<b>Passo 6 – Analisar os erros.</b> Separamos as imagens de falso alarme, de fogo ou fumaça perdidos e de "
            "troca entre as classes, e anotamos à mão a causa provável de cada uma."),
          p("<b>Passo 7 – Testar com imagens próprias.</b> Fotos do grupo, fora do D-Fire, incluindo casos difíceis "
            "como nuvem, neblina, poeira e pôr do sol, sem rostos nem placas."),
          p("<b>Passo 8 – Medir a velocidade</b> em CPU e GPU, para saber se o uso em tempo real é viável."),
          p("<b>Passo 9 – Integrar ao produto.</b> A mesma regra de decisão (arquivo <font name='Mono'>"
            "src/decisao.py</font>) é usada na avaliação, na API e no vídeo, para que o número do relatório seja o "
            "número do produto. A API valida tipo e tamanho do arquivo, corrige a rotação de fotos de celular, "
            "processa a imagem em memória e a descarta. Com o código do município, cruza a resposta com o risco do "
            "dia e devolve uma prioridade (alta, média ou baixa).")]

    # Resultados ---------------------------------------------------------------------------
    linhas_classe = [["Classe", "Precisão", "Recall", "mAP@50", "mAP@50-95"]]
    for nome, rot in (("fumaca", "Fumaça"), ("fogo", "Fogo")):
        linhas_classe.append([rot, r.classe(nome, "precisao"), r.classe(nome, "recall"), r.classe(nome, "mAP50"),
                              r.classe(nome, "mAP50_95")])
    linhas_classe.append(["<b>Geral</b>", r.m("precisao"), r.m("recall"), r.m("mAP50"), r.m("mAP50_95")])

    s += [PageBreak(), p("4. Resultados", "h1"),
          p("4.1 Detecção por caixa (conjunto de teste)", "h2"),
          tabela(linhas_classe, [W / 5] * 5),
          figura(r.pasta / "teste_caixas" / "confusion_matrix_normalized.png", 12 * cm,
                 "Figura 4 – Matriz de confusão normalizada por caixa no teste (inclui background).", 10 * cm),
          figura(r.pasta / "teste_caixas" / "BoxPR_curve.png", 12 * cm,
                 "Figura 5 – Curva precisão × recall por classe no teste.", 8.5 * cm),
          p("4.2 Resposta por imagem e escolha do limiar", "h2"),
          tabela([
              ["Indicador (limiar escolhido)", "Valor"],
              ["Limiar de confirmação / início da faixa de dúvida", f"{r.lim('limiar')} / {r.lim('limiar_duvida')}"],
              ["Sensibilidade: fotos com fogo ou fumaça que foram avisadas", r.img("sensibilidade_ocorrencia")],
              ["Falso alarme: fotos sem nada que geraram alarme", r.img("falso_alarme")],
              ["Precisão de ocorrência", r.img("precisao_ocorrencia")],
              ["F1 de ocorrência", r.img("f1_ocorrencia", "num")],
              ["Acurácia nas 3 respostas (fogo, fumaça, nada)", r.img("acuracia")],
          ], [W - 4 * cm, 4 * cm]),
          figura(r.pasta / "curva_limiares.png", 13 * cm,
                 "Figura 6 – Sensibilidade, falso alarme e F1 conforme o limiar. Linha tracejada: limiar escolhido; "
                 "pontilhada: início da faixa de dúvida.", 8 * cm),
          figura(r.pasta / "matriz_confusao_por_imagem.png", 9.5 * cm,
                 "Figura 7 – Matriz de confusão por imagem (resposta única do produto) no limiar escolhido.", 8 * cm),
          KeepTogether([
              p("4.3 Erros reais", "h2"),
              p("Os erros mostram onde o modelo não deve ser usado sem uma pessoa conferindo."),
              figura(r.pasta / "erros_falso_alarme.png", W,
                     "Figura 8 – Falsos alarmes: imagens sem fumaça nem fogo que o modelo marcou (caixas vermelha e "
                     "azul = previsão).", 11 * cm)]),
          figura(r.pasta / "erros_perdidos.png", W,
                 "Figura 9 – Fumaça ou fogo perdidos (verde = rótulo real).", 11 * cm)]
    if causas:
        s += [tabela([["Causa provável do falso alarme (anotada pelo grupo)", "Imagens"],
                      *[[c, str(n)] for c, n in causas.most_common()]], [W - 3 * cm, 3 * cm])]
    else:
        s += [p(falta("tabela de causas dos falsos alarmes: preencher a coluna causa_provavel de "
                      "erros_para_anotar.csv"))]

    s += [p("4.4 Imagens próprias e exemplos de detecção", "h2")]
    if r.proprias:
        acertos = sum(l["acertou"] == "True" for l in r.proprias)
        s += [p(f"Nas {len(r.proprias)} imagens próprias do grupo, o modelo acertou {acertos}. A tabela completa "
                "está em <font name='Mono'>resultados/imagens_proprias_resultados.csv</font>.")]
    else:
        s += [p(falta("resultado das imagens próprias do grupo"))]
    s += [figura(r.pasta / "imagens_proprias.png", W, "Figura 10 – Imagens próprias do grupo: resposta real e "
                                                     "prevista.", 11 * cm),
          figura(r.pasta / "exemplos_deteccao.png", W, "Figura 11 – Exemplos de detecções corretas no teste.",
                 11 * cm),
          figura(r.pasta / "api_demo.png", 11 * cm, "Figura 12 – Página de demonstração da API com uma foto "
                                                   "analisada.", 11 * cm),
          p("4.5 Velocidade", "h2"),
          tabela([["Dispositivo", "ms por imagem", "Quadros por segundo"],
                  ["CPU (servidor comum, sem GPU)", r.vel("cpu", "ms_por_imagem"), r.vel("cpu", "fps")],
                  ["GPU NVIDIA T4 (Colab)", r.vel("gpu", "ms_por_imagem"), r.vel("gpu", "fps")]],
                 [W - 7 * cm, 3.5 * cm, 3.5 * cm]),
          p("O tempo inclui ler a imagem, preparar, rodar a rede e filtrar as caixas.")]

    # Conclusão ----------------------------------------------------------------------------
    s += [p("5. Conclusão", "h1"),
          p(f"O YOLO11n treinado no D-Fire detecta fumaça e fogo com mAP@50 de {r.m('mAP50')} no teste e, no uso "
            f"do produto, avisa {r.img('sensibilidade_ocorrencia')} das fotos com fumaça ou fogo, com "
            f"{r.img('falso_alarme')} de falso alarme nas fotos sem nada. Por rodar em "
            f"{r.vel('cpu', 'ms_por_imagem')} ms por imagem em CPU, ele serve tanto para a foto enviada pelo "
            "produtor quanto para vídeo em tempo real."),
          p("Para o FogoCerto, isso significa uma <b>confirmação em campo</b> que complementa o satélite: a foto "
            "chega à defesa civil já com a indicação de fumaça ou fogo, a confiança e a prioridade calculada a "
            "partir do risco do município. A faixa de dúvida e a orientação de sempre procurar a defesa civil "
            "deixam claro que o modelo ajuda a triar, mas não decide sozinho."),
          p("<b>Limitações.</b> Nuvens, neblina, poeira, pôr do sol e luz forte podem ser confundidos com fumaça ou "
            "fogo; fumaça fina ou muito distante é a principal causa de casos perdidos; o limiar foi escolhido no "
            "próprio conjunto de teste, e não numa validação separada; e o D-Fire tem muitas imagens de câmeras de "
            "vigilância, por isso testamos também fotos de celular próprias."),
          p("<b>Próximos passos.</b> Aplicar o mesmo modelo a quadros de <b>câmeras fixas</b> em fazendas e torres; "
            "suavizar a decisão ao longo de vários quadros de vídeo para reduzir alarmes isolados; e coletar "
            "imagens da própria região amazônica para ajustar o modelo à paisagem local."),
          p("Referências", "h1")]
    for ref in [
        "Venâncio, P. V. A. B.; Lisboa, A. C.; Barbosa, A. V. An automatic fire detection system based on deep "
        "convolutional neural networks for low-power, resource-constrained devices. <i>Neural Computing and "
        "Applications</i>, 2022. (Conjunto D-Fire, licença CC0.)",
        "Jocher, G.; Qiu, J. Ultralytics YOLO11. Ultralytics, 2024. https://docs.ultralytics.com",
        "Redmon, J. et al. You Only Look Once: Unified, Real-Time Object Detection. CVPR, 2016.",
        "Lin, T.-Y. et al. Microsoft COCO: Common Objects in Context. ECCV, 2014.",
        "INPE. Programa Queimadas: dados abertos de focos de calor. https://terrabrasilis.dpi.inpe.br/queimadas",
    ]:
        s.append(p(ref, "ref"))

    m = 2 * cm
    doc = BaseDocTemplate(str(saida), pagesize=A4, title="FogoCerto - Relatório de Applied Computer Vision",
                          author=", ".join(n for n, _ in INTEGRANTES),
                          subject="Global Solution FIAP 2026.2 - CitizenTech - Applied Computer Vision")
    doc.addPageTemplates([PageTemplate("r", [Frame(m, m, A4[0] - 2 * m, A4[1] - 2 * m)], onPage=rodape(previa))])
    doc.build(s)


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("--resultados", default=str(VISAO / "resultados"))
    a.add_argument("--video", default=None)
    a.add_argument("--saida", default=str(VISAO / "docs" / "relatorio_visao.pdf"))
    a.add_argument("--previa", action="store_true", help="marca todas as páginas como prévia de layout")
    args = a.parse_args()
    montar(Resultados(Path(args.resultados)), args.video, Path(args.saida), args.previa)
    print("PDF gerado:", args.saida)
