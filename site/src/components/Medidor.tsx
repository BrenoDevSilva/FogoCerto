import type { NivelRisco } from '../data/risco'
import { NIVEL, PONTOS_MAX } from '../lib/formato'

/**
 * Medidor semicircular no estilo das placas de "perigo de incêndio".
 * Faixas seguem a regra da Ouro: 0-2 baixo, 3-4 médio, 5-9 alto.
 */
const CX = 120
const CY = 118
const R = 92
const SLOTS = PONTOS_MAX + 1 // 0..9

function ponto(frac: number, raio = R) {
  const ang = Math.PI * (1 - frac)
  return [CX + raio * Math.cos(ang), CY - raio * Math.sin(ang)] as const
}

function arco(de: number, ate: number) {
  const [x0, y0] = ponto(de)
  const [x1, y1] = ponto(ate)
  return `M ${x0.toFixed(2)} ${y0.toFixed(2)} A ${R} ${R} 0 0 1 ${x1.toFixed(2)} ${y1.toFixed(2)}`
}

const FAIXAS: { nivel: NivelRisco; de: number; ate: number }[] = [
  { nivel: 'baixo', de: 0, ate: 3 / SLOTS },
  { nivel: 'medio', de: 3 / SLOTS, ate: 5 / SLOTS },
  { nivel: 'alto', de: 5 / SLOTS, ate: 1 },
]

export function Medidor({ nivel, pontos }: { nivel: NivelRisco; pontos: number }) {
  const p = Math.max(0, Math.min(PONTOS_MAX, pontos))
  const graus = ((p + 0.5) / SLOTS) * 180 - 90 // -90 = esquerda, +90 = direita
  return (
    <svg
      className="medidor"
      viewBox="0 0 240 140"
      role="img"
      aria-label={`${NIVEL[nivel].rotulo}: ${pontos} de ${PONTOS_MAX} pontos`}
    >
      {FAIXAS.map((f) => (
        <path
          key={f.nivel}
          d={arco(f.de + 0.006, f.ate - 0.006)}
          className={`medidor__faixa medidor__faixa--${f.nivel} ${f.nivel === nivel ? 'is-ativa' : ''}`}
          fill="none"
          strokeWidth="26"
        />
      ))}
      {Array.from({ length: SLOTS + 1 }, (_, i) => {
        const [x0, y0] = ponto(i / SLOTS, R - 19)
        const [x1, y1] = ponto(i / SLOTS, R - 13)
        return <line key={i} x1={x0} y1={y0} x2={x1} y2={y1} className="medidor__marca" />
      })}
      <g className="medidor__ponteiro" style={{ transform: `rotate(${graus}deg)` }}>
        <path d={`M ${CX - 5} ${CY} L ${CX} ${CY - R + 6} L ${CX + 5} ${CY} Z`} />
      </g>
      <circle cx={CX} cy={CY} r="11" className="medidor__eixo" />
      <circle cx={CX} cy={CY} r="4" className="medidor__eixo-miolo" />
    </svg>
  )
}
