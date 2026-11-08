import { IconeAlerta, IconeRelogio } from './Icones'
import { fmtData } from '../lib/formato'
import { ontemISO, situacaoData } from '../lib/datas'

/**
 * Diz a que dia o risco se refere. O pipeline coleta o dia anterior todo dia às 10:30, então
 * o `data` esperado é sempre ONTEM (o último dia fechado):
 * - ontem: sem alerta, só uma linha informativa;
 * - mais antigo: aviso amarelo (a atualização mais recente não chegou).
 * Data futura nem chega aqui: o `getRiscoAtual()` a descarta como dado inválido.
 */
export function AvisoData({ data }: { data: string }) {
  if (situacaoData(data) === 'antigo') {
    return (
      <p className="aviso-data" role="status">
        <IconeAlerta className="aviso-data__icone" />
        <span>
          <strong>Dados de {fmtData(data, false)}.</strong> A atualização mais recente ainda não chegou.
        </span>
      </p>
    )
  }
  const ultimoDia = data.slice(0, 10) === ontemISO()
  return (
    <p className="info-data">
      <IconeRelogio className="info-data__icone" />
      <span>
        Risco calculado com os dados fechados de <strong>{fmtData(data, false)}</strong>
        {ultimoDia ? ', o último dia completo' : ''}. Atualizado uma vez por dia, pela manhã.
      </span>
    </p>
  )
}
