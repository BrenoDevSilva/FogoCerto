import { IconeLei } from './Icones'

/** Texto obrigatório: o FogoCerto nunca autoriza queima. */
export const TEXTO_AVISO_LEGAL =
  'O FogoCerto informa o risco. A autorização de queima é do órgão ambiental do seu estado.'

export function AvisoLegal({ compacto = false }: { compacto?: boolean }) {
  return (
    <p className={compacto ? 'aviso-legal aviso-legal--compacto' : 'aviso-legal'}>
      <IconeLei className="aviso-legal__icone" />
      <span>
        <strong>{TEXTO_AVISO_LEGAL}</strong>
        {!compacto && <> No Pará, procure a SEMAS ou a secretaria de meio ambiente do seu município.</>}
      </span>
    </p>
  )
}
