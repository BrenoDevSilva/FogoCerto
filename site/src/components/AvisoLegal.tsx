import { IconeLei } from './Icones'
import { ORGAO_AMBIENTAL } from '../lib/estados'

/** Texto obrigatório: o FogoCerto nunca autoriza queima. */
export const TEXTO_AVISO_LEGAL =
  'O FogoCerto informa o risco. A autorização de queima é do órgão ambiental do seu estado.'

interface Props {
  compacto?: boolean
  /** UF do município em tela, para indicar o órgão certo quando conhecido. */
  uf?: string
}

export function AvisoLegal({ compacto = false, uf }: Props) {
  const orgao = uf ? ORGAO_AMBIENTAL[uf] : undefined
  return (
    <p className={compacto ? 'aviso-legal aviso-legal--compacto' : 'aviso-legal'}>
      <IconeLei className="aviso-legal__icone" />
      <span>
        <strong>{TEXTO_AVISO_LEGAL}</strong>
        {!compacto && (
          <>
            {' '}
            Procure {orgao ?? 'a secretaria estadual de meio ambiente'} ou a secretaria de meio ambiente do seu
            município.
          </>
        )}
      </span>
    </p>
  )
}
