# Chart Helm — `llm-provider`

Mesmo desenho do [`k8s/`](../../k8s/README.md): Deployment `llm-provider` (3 réplicas, anotações do Prometheus),
Service `llm-provider:8004` e ConfigMap. Os valores que mudam entre ambientes estão em [`values.yaml`](values.yaml).
Sem Ingress e sem `host`: o serviço é interno, só o `product` o chama pelo Service.

A chave do OpenRouter fica fora do chart (nenhum `kind: Secret` no git), no Secret `llm-provider-secrets`, lido por
`envFrom` como **opcional**: sem ele o pod sobe e responde pelo provedor `mock`.

```bash
# só para LLM real:
kubectl create secret generic llm-provider-secrets --from-literal=OPENROUTER_API_KEY='<chave>'

helm lint helm/llm-provider
helm upgrade --install llm-provider helm/llm-provider                                   # mock
helm upgrade --install llm-provider helm/llm-provider --set config.LLM_PROVIDER=openrouter # OpenRouter
kubectl get pods -w
helm uninstall llm-provider
```

| Quero | Faço |
|---|---|
| Outra versão da imagem | `--set image.tag=1.1.1` |
| Mais réplicas | `--set replicaCount=5` |
| LLM real | Secret acima + `--set config.LLM_PROVIDER=openrouter` |
| Outro modelo | `--set config.LLM_MODEL=<modelo>` |
| Outro nome de Secret | `--set existingSecret=<nome>` |

Testado em 24/10/2026 num cluster `kind` limpo (Kubernetes 1.37, Helm 4.3): `helm lint` limpo; sem o Secret,
`helm install` sobe 3 pods `1/1` e `/generate` com token responde pelo `mock`; com o Secret e
`config.LLM_PROVIDER=openrouter`, a `OPENROUTER_API_KEY` chega ao pod. `/metrics` responde 200 pelo Service.
