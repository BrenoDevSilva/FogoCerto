"""Detecção em tempo real em webcam ou arquivo de vídeo (demonstração).

Exemplos (dentro de ``visao/``)::

    python src/detectar_video.py --fonte 0                       # webcam
    python src/detectar_video.py --fonte amostras/teste.mp4 --saida resultados/demo.mp4

Mostra as caixas, a decisão do FogoCerto para o quadro (mesma regra da API) e o
FPS. Tecla ``q`` encerra. Nenhum quadro é gravado, a não ser que ``--saida`` seja
informado (use só vídeo próprio ou de licença livre, sem rosto ou placa).
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import cv2  # noqa: E402  (vem com o ultralytics)

from api import carregar_limiares  # noqa: E402
from decisao import decidir  # noqa: E402
from modelo import Detector, converter  # noqa: E402

# BGR. Fumaça em azul (e não cinza) para a caixa aparecer em cima da própria fumaça.
COR = {"fogo": (28, 57, 224), "fumaca": (255, 170, 0)}
COR_FAIXA = {"fogo": (28, 57, 224), "fumaca": (170, 110, 20), "nada": (60, 107, 47)}
LARGURA_JANELA = 1280  # vídeos maiores (2K, 4K) são reduzidos só na janela, não na gravação
ROTULO = {"fogo": "FOGO", "fumaca": "FUMACA", "nada": "NADA"}
TITULO = "FogoCerto - visao (q para sair)"


def desenhar(quadro, deteccoes, decisao, fps: float) -> None:
    """Caixas, legendas com fundo e a faixa de resposta, em tamanho proporcional ao vídeo."""
    esc = max(1.0, quadro.shape[1] / 960)
    linha, fonte = max(2, round(2 * esc)), 0.6 * esc
    for d in deteccoes:
        x1, y1, x2, y2 = map(int, d.caixa)
        cv2.rectangle(quadro, (x1, y1), (x2, y2), COR[d.classe], linha)
    alt_faixa = int(36 * esc)
    for d in deteccoes:  # legendas depois das caixas, para nenhuma linha passar por cima
        x1, y1 = int(d.caixa[0]), int(d.caixa[1])
        texto = f"{ROTULO[d.classe]} {d.confianca:.0%}"
        (lt, at), base = cv2.getTextSize(texto, cv2.FONT_HERSHEY_SIMPLEX, fonte, linha)
        y = max(y1 - linha, alt_faixa + at + base)
        cv2.rectangle(quadro, (x1, y - at - base), (x1 + lt + 2 * linha, y + base), COR[d.classe], -1)
        cv2.putText(quadro, texto, (x1 + linha, y), cv2.FONT_HERSHEY_SIMPLEX, fonte, (255, 255, 255), linha)
    texto = ROTULO[decisao.classe] + (" (duvida)" if decisao.duvida else "")
    cv2.rectangle(quadro, (0, 0), (quadro.shape[1], alt_faixa), COR_FAIXA[decisao.classe], -1)
    cv2.putText(quadro, f"FogoCerto: {texto}   {fps:.1f} FPS", (int(10 * esc), int(25 * esc)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.75 * esc, (255, 255, 255), linha)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--fonte", default="0", help="0 para webcam ou caminho de vídeo")
    p.add_argument("--modelo", default=None, help="caminho do best.pt (padrão: visao/modelos/best.pt)")
    p.add_argument("--saida", default=None, help="grava o vídeo anotado neste arquivo .mp4")
    p.add_argument("--tam", type=int, default=640)
    p.add_argument("--sem-janela", action="store_true", help="não abre janela (só grava)")
    p.add_argument("--inicio", type=float, default=0.0, help="em vídeo, começa neste segundo")
    args = p.parse_args()

    limiares = carregar_limiares()
    det = Detector(args.modelo, tam_img=args.tam)
    fonte = int(args.fonte) if args.fonte.isdigit() else args.fonte
    cap = cv2.VideoCapture(fonte)
    if not cap.isOpened():
        sys.exit(f"Não foi possível abrir a fonte {args.fonte!r}.")
    if args.inicio > 0 and not isinstance(fonte, int):
        cap.set(cv2.CAP_PROP_POS_MSEC, args.inicio * 1000)

    gravador = None
    janela_criada = False
    fps_medio = 0.0
    while True:
        ok, quadro = cap.read()
        if not ok:
            break
        t0 = time.perf_counter()
        res = det.modelo.predict(quadro, imgsz=args.tam, conf=limiares["limiar_duvida"], verbose=False)[0]
        deteccoes = converter(res, det.nomes)
        decisao = decidir(deteccoes, limiares["limiar"], limiares["limiar_duvida"])
        dt = time.perf_counter() - t0
        fps_medio = 0.9 * fps_medio + 0.1 * (1 / dt) if fps_medio else 1 / dt

        desenhar(quadro, deteccoes, decisao, fps_medio)

        if args.saida:
            if gravador is None:
                Path(args.saida).parent.mkdir(parents=True, exist_ok=True)
                fps_video = cap.get(cv2.CAP_PROP_FPS) or 20
                gravador = cv2.VideoWriter(args.saida, cv2.VideoWriter_fourcc(*"mp4v"), fps_video,
                                           (quadro.shape[1], quadro.shape[0]))
            gravador.write(quadro)
        if not args.sem_janela:
            try:
                if not janela_criada:
                    cv2.namedWindow(TITULO, cv2.WINDOW_NORMAL)
                    largura = min(LARGURA_JANELA, quadro.shape[1])
                    cv2.resizeWindow(TITULO, largura, int(quadro.shape[0] * largura / quadro.shape[1]))
                    janela_criada = True
                cv2.imshow(TITULO, quadro)
            except cv2.error:
                # opencv "headless" (sem interface gráfica): segue só gravando
                print("Este OpenCV não abre janela. Instale 'opencv-python' ou use --saida para gravar o vídeo.")
                args.sem_janela = True
                if not args.saida:
                    break
                continue
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cap.release()
    if gravador:
        gravador.release()
    if not args.sem_janela:
        cv2.destroyAllWindows()
    print(f"FPS médio: {fps_medio:.1f}")


if __name__ == "__main__":
    main()
