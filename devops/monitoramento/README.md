# Monitoramento - FogoCerto

## 1. As 4 Métricas de Ouro
- **Latência:** Tempo de carregamento do PWA e requisição de `risco_atual.json`.
- **Tráfego:** Acessos por minuto ao sistema.
- **Erros:** Monitoramento de respostas `5xx` e erros `404` na busca do JSON.
- **Saturação:** Uso de CPU e RAM do contêiner Nginx.

## 2. Alerta de Negócio
- **Alerta Disparado:** *"Risco Atual Desatualizado"* (acionado se a data do `risco_atual.json` não for o dia anterior, indicando falha na atualização matinal).