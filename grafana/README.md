# Dashboard Grafana — `llm-provider`

[`llm-provider-dashboard.json`](llm-provider-dashboard.json): requisições, erros e latência do llm-provider, a partir do
`/metrics` (`prometheus-fastapi-instrumentator`). Mesmo layout dos dashboards dos outros serviços do GANJJ.

| Painel | O que mostra |
|---|---|
| Requisições/s, Erros 5xx, Latência p95, Réplicas no ar | Resumo em números |
| Requisições/s por rota | Tráfego por `método + rota` (`/generate`) |
| Respostas por status | `2xx`, `4xx` (inclui 401 sem token), `5xx` (falha do provedor externo vira 502) |
| Latência (p50, p95, p99) e p95 por rota | Com OpenRouter, a latência é quase toda do modelo externo, não do serviço |
| Taxa de erro 5xx por rota | Qual rota está falhando |

## Importar

Grafana → **Dashboards → New → Import** → enviar o JSON. Não precisa editar nada:

- **Prometheus** (variável `datasource`): escolha o datasource no topo do painel.
- **Filtro** (variável `filtro`, padrão `app="llm-provider"`): seletor que identifica os pods do llm-provider. É o label
  que o Prometheus cria a partir do label `app` do pod; se o seu scrape usar outro, troque no campo do topo.

Validado em 24/10/2026 com Prometheus 3.5 e Grafana 11.6 raspando o chart instalado num `kind`: import aceito e todas
as consultas dos painéis retornando dados.
