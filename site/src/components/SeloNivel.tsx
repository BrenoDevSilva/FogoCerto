import type { NivelRisco } from '../data/risco'
import { NIVEL } from '../lib/formato'

/** Barras crescentes (1, 2 ou 3 cheias): o nível fica legível sem depender da cor. */
export function BarrasNivel({ nivel, tamanho = 20 }: { nivel: NivelRisco; tamanho?: number }) {
  const cheias = NIVEL[nivel].barras
  return (
    <svg width={tamanho} height={tamanho} viewBox="0 0 20 20" aria-hidden="true" focusable="false" className="barras">
      {[0, 1, 2].map((i) => (
        <rect
          key={i}
          x={1 + i * 6.5}
          y={13 - i * 5}
          width="5"
          height={6 + i * 5}
          rx="1"
          fill={i < cheias ? 'currentColor' : 'none'}
          stroke="currentColor"
          strokeWidth="1.5"
        />
      ))}
    </svg>
  )
}

export function SeloNivel({ nivel, curto = false }: { nivel: NivelRisco; curto?: boolean }) {
  const n = NIVEL[nivel]
  return (
    <span className={`selo selo--${nivel}`}>
      <BarrasNivel nivel={nivel} tamanho={16} />
      {curto ? n.curto : n.rotulo}
    </span>
  )
}
