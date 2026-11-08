import type { ReactNode } from 'react'
import { AvisoLegal } from '../components/AvisoLegal'

interface Props {
  titulo: string
  icone: ReactNode
  descricao: ReactNode
  previa: ReactNode
}

/** Casca das funções que ainda serão ligadas (assistente e foto). */
export function EmBreve({ titulo, icone, descricao, previa }: Props) {
  return (
    <>
      <h1 className="titulo-pagina" tabIndex={-1}>
        {titulo}
      </h1>
      <section className="em-breve">
        <p className="em-breve__selo">Em breve</p>
        <span className="em-breve__icone">{icone}</span>
        <div className="em-breve__texto">{descricao}</div>
        <div className="em-breve__previa" aria-hidden="true">
          {previa}
        </div>
      </section>
      <AvisoLegal compacto />
    </>
  )
}
