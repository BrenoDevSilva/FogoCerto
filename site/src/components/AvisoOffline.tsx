import { IconeSemSinal } from './Icones'

/** Aparece quando o risco veio da última cópia salva no aparelho (sem internet). */
export function AvisoOffline() {
  return (
    <p className="aviso-data aviso-offline" role="status">
      <IconeSemSinal className="aviso-data__icone" />
      <span>
        <strong>Sem internet.</strong> Mostrando o último risco salvo neste aparelho. Confira a data abaixo: ela pode
        estar desatualizada.
      </span>
    </p>
  )
}
