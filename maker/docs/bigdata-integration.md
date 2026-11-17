# Integração Big Data

A fonte é a view `workspace.fogocerto.vw_risco_atual`, produzida no notebook Ouro.

O CSV precisa conter:
`id_ibge`, `nome`, `uf`, `data`, `nivel_risco`, `pontos`, `focos_ontem`, `umidade_min`, `vento_max`, `temp_max`, `chuva_3d`, `fatores`, `atualizado_em`.

Na raiz de `maker/`, execute:
```bash
python simulation/export_gold.py caminho/para/vw_risco_atual.csv
```

O script grava `firmware/gold_snapshot.h`. Preserve `id_ibge` como texto ao exportar. O snapshot é uma cópia estática; gere novamente quando houver novos dados Gold.
