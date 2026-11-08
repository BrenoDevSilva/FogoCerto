import type { NivelRisco, RiscoMunicipio } from '../data/risco'
import { BarrasNivel } from './SeloNivel'
import { NIVEL } from '../lib/formato'

/**
 * Mapa do Pará feito em SVG, sem biblioteca e sem servidor de mapas: funciona offline e pesa poucos bytes.
 *
 * Contorno: malha estadual do IBGE (API de malhas, qualidade mínima, estado 15), convertida uma vez em
 * um único caminho SVG. Projeção equiretangular com correção de cos(latitude média), enquadrada no
 * retângulo do estado. Os pontos usam a mesma projeção (constantes abaixo), então latitude e longitude
 * dos municípios caem no lugar certo.
 */
const CAIXA = { minLon: -58.8955, maxLat: 2.5837, k: 0.99799510, escala: 78.0861 }
const LARGURA = 1000
const ALTURA = 970
const MARGEM = 60

const CONTORNO_PARA =
  'M834 585L845 577L847 575L863 562L874 562L879 558L893 537L898 533L900 523L920 503L925 483L924 480L931 473L931 465L942 460L945 450L952 443L952 428L959 424L953 415L958 408L965 406L971 395L971 390L972 379L983 370L984 362L988 351L988 345L981 343L980 338L988 337L992 328L991 317L997 306L992 302L997 296L1000 288L998 281L990 286L989 271L979 282L968 282L966 270L964 276L955 277L956 264L943 270L940 260L931 269L928 257L922 264L920 254L915 261L913 254L907 252L897 249L894 253L890 248L889 259L881 247L880 256L878 257L878 249L868 249L856 246L851 255L845 253L838 261L836 266L826 274L817 272L812 270L810 260L815 234L820 225L816 219L791 221L778 220L758 212L741 217L737 212L743 204L740 197L722 196L717 190L722 183L733 176L726 169L702 177L680 175L680 171L690 160L688 152L676 147L661 153L646 182L643 185L635 192L617 198L606 209L599 211L588 225L582 239L569 253L562 264L561 285L555 291L546 293L540 290L529 297L528 291L511 289L505 284L502 267L498 269L499 257L496 247L487 247L483 241L484 226L465 213L461 199L452 187L446 172L448 155L451 149L427 129L424 113L426 105L419 107L418 98L390 92L390 88L375 85L372 76L352 64L343 65L335 62L323 63L323 48L318 43L322 30L314 12L307 0L296 5L290 2L279 5L274 13L265 11L248 14L248 14L231 4L222 19L215 25L222 28L228 39L233 54L226 59L214 54L207 55L192 49L180 53L169 51L164 57L154 51L148 53L141 44L128 50L124 46L114 53L113 61L103 70L86 67L86 70L71 72L69 84L60 85L57 80L45 79L41 86L30 88L34 95L31 103L14 101L13 107L5 110L0 106L0 181L0 203L2 208L2 229L13 236L12 250L18 258L36 271L36 282L45 291L50 290L58 298L67 287L72 293L70 306L73 311L92 319L95 326L102 325L120 337L128 334L141 341L146 352L159 359L167 359L166 372L173 375L180 372L185 369L193 372L208 362L218 360L210 372L195 380L189 392L194 394L166 455L163 462L154 480L151 487L120 553L81 639L49 707L36 718L32 731L36 741L44 747L56 763L58 775L59 776L65 779L78 801L83 823L98 844L94 858L98 868L102 886L115 888L115 894L132 898L145 912L143 919L148 923L162 924L167 936L173 933L204 936L213 937L236 938L304 944L334 946L373 949L414 952L449 955L489 958L517 960L592 965L627 967L676 970L686 946L690 927L696 923L704 911L705 910L718 893L725 892L734 879L740 869L744 859L749 856L754 842L757 827L758 815L759 810L744 800L743 796L742 787L751 777L757 764L756 758L756 752L755 743L765 736L768 733L783 729L797 722L800 709L800 708L810 698L820 697L815 686L819 682L827 678L823 671L831 666L826 658L828 649L836 648L838 639L824 631L820 624L815 624L803 625L790 619L814 601L833 586L834 585Z'

function projetar(lat: number, lon: number): [number, number] {
  return [(lon - CAIXA.minLon) * CAIXA.k * CAIXA.escala, (CAIXA.maxLat - lat) * CAIXA.escala]
}

// Tamanho do ponto também varia com o nível, para não depender só da cor.
const RAIO: Record<NivelRisco, number> = { alto: 40, medio: 32, baixo: 26 }

const LARGURA_LETRA = 25 // largura média de uma letra do nome, em unidades do mapa
const ALTURA_NOME = 28 // meia altura do texto

/**
 * Nome só nos municípios de risco alto. Fica à direita do ponto; se ali bater em outro ponto
 * (ou sair do mapa), vai para a esquerda.
 */
function posicionarRotulos(pontos: { m: RiscoMunicipio; x: number; y: number }[]) {
  const bate = (caixa: [number, number], y: number, ignorar: number) =>
    pontos.some((o) => {
      if (o.m.id_ibge === ignorar) return false
      const r = RAIO[o.m.nivel_risco]
      const dx = Math.max(caixa[0] - o.x, 0, o.x - caixa[1])
      const dy = Math.max(y - ALTURA_NOME - o.y, 0, o.y - (y + ALTURA_NOME))
      return Math.hypot(dx, dy) < r
    })
  return pontos
    .filter((p) => p.m.nivel_risco === 'alto')
    .map(({ m, x, y }) => {
      const raio = RAIO.alto
      const largura = m.nome.length * LARGURA_LETRA
      const dir: [number, number] = [x + raio + 10, x + raio + 10 + largura]
      const esq: [number, number] = [x - raio - 10 - largura, x - raio - 10]
      const cabeNaDireita = dir[1] <= LARGURA + MARGEM
      const usarEsquerda = (!cabeNaDireita || bate(dir, y, m.id_ibge)) && esq[0] >= -MARGEM && !bate(esq, y, m.id_ibge)
      return usarEsquerda
        ? { id: m.id_ibge, nome: m.nome, x: x - raio - 10, y, ancora: 'end' as const }
        : { id: m.id_ibge, nome: m.nome, x: x + raio + 10, y, ancora: 'start' as const }
    })
}

interface Props {
  /** Municípios já ordenados do maior para o menor risco (a posição vira o número do ponto). */
  lista: RiscoMunicipio[]
  onAbrir: (id: number) => void
}

export function MapaPara({ lista, onAbrir }: Props) {
  const pontos = lista
    .map((m, i) => ({ m, pos: i + 1 }))
    .filter((p) => p.m.lat !== null && p.m.lon !== null)
    .map(({ m, pos }) => {
      const [x, y] = projetar(m.lat as number, m.lon as number)
      return { m, pos, x, y }
    })

  if (pontos.length === 0) return null

  // Maiores por baixo, menores por cima: se dois pontos se sobrepuserem, o menor não some.
  const desenho = [...pontos].sort((a, b) => RAIO[b.m.nivel_risco] - RAIO[a.m.nivel_risco])

  const rotulos = posicionarRotulos(desenho)

  return (
    <figure className="mapa">
      <svg
        viewBox={`${-MARGEM} ${-MARGEM} ${LARGURA + MARGEM * 2} ${ALTURA + MARGEM * 2}`}
        role="group"
        aria-label="Mapa do Pará com os municípios acompanhados"
      >
        <path d={CONTORNO_PARA} className="mapa__estado" />
        {desenho.map(({ m, pos, x, y }) => {
          const raio = RAIO[m.nivel_risco]
          const rotulo = `${m.nome}, ${NIVEL[m.nivel_risco].rotulo.toLowerCase()}, ${m.pontos} de 9 pontos`
          return (
            <a
              key={m.id_ibge}
              href="#/"
              aria-label={rotulo}
              className={`mapa__ponto mapa__ponto--${m.nivel_risco}`}
              onClick={(e) => {
                e.preventDefault()
                onAbrir(m.id_ibge)
              }}
            >
              <circle cx={x} cy={y} r={raio + 12} className="mapa__toque" />
              <circle cx={x} cy={y} r={raio} className="mapa__bolinha" />
              <text x={x} y={y} className="mapa__numero" textAnchor="middle" dominantBaseline="central">
                {pos}
              </text>
            </a>
          )
        })}
        {rotulos.map((r) => (
          <text
            key={r.id}
            x={r.x}
            y={r.y}
            className="mapa__nome"
            textAnchor={r.ancora}
            dominantBaseline="central"
          >
            {r.nome}
          </text>
        ))}
      </svg>
      <figcaption className="mapa__legenda">
        <span className="mapa__legenda-titulo">Cor e tamanho mostram o nível. O número é a posição na lista abaixo.</span>
        <ul>
          {(['alto', 'medio', 'baixo'] as NivelRisco[]).map((n) => (
            <li key={n} className={`mapa__legenda-item mapa__legenda-item--${n}`}>
              <BarrasNivel nivel={n} tamanho={18} />
              {NIVEL[n].curto}
            </li>
          ))}
        </ul>
      </figcaption>
    </figure>
  )
}
