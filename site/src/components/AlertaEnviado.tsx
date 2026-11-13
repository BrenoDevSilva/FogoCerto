import { useEffect, useState } from 'react'
import { alertaDoDia, getAlertas, type AlertaEnviado as Alerta } from '../data/alertas'
import { fmtDataHora } from '../lib/formato'
import { IconeSino } from './Icones'

/** Linha no cartão: "Alerta automático enviado aos assinantes em DD/MM/AAAA às HH:MM". */
export function AlertaEnviado({ idIbge, data }: { idIbge: number; data: string }) {
  const [alertas, setAlertas] = useState<Alerta[]>([])

  useEffect(() => {
    let ativo = true
    getAlertas().then((lista) => ativo && setAlertas(lista))
    return () => {
      ativo = false
    }
  }, [])

  const alerta = alertaDoDia(alertas, idIbge, data)
  if (!alerta) return null
  const pessoas = alerta.assinantes_avisados === 1 ? '1 assinante' : `${alerta.assinantes_avisados} assinantes`
  return (
    <p className="cartao__alerta" role="status">
      <IconeSino width={18} height={18} />
      <span>
        Alerta automático enviado a {pessoas} em {fmtDataHora(alerta.enviado_em)}
        {alerta.simulado ? ' (envio de teste)' : ''}.
      </span>
    </p>
  )
}
