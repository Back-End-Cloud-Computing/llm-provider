# llm-provider no Kubernetes

Sobe três réplicas do llm-provider, com Service Discovery para
`authorization`. Não tem banco nem outra dependência própria - é o serviço
mais simples do GANJJ para essa demonstração.

```
Service llm-provider :8004
          |
   Service Discovery
          |
   +------+------+------+
   |             |      |
  Pod           Pod    Pod
   |             |      |
   +------+------+------+
          |
          | authorization:8081
          v
   Service authorization
```

## Subir

Depende de `authorization` já estar no cluster (repositório próprio):

```bash
kubectl apply -f k8s/llm-provider.yaml
```

```bash
kubectl wait --for=condition=ready pod -l app=llm-provider --timeout=120s
kubectl get pods
```

## Testar a comunicação interna

```bash
kubectl run teste --image=curlimages/curl:latest -it --rm -- sh
```

```sh
# sem token: 401
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://llm-provider:8004/generate \
  -H "Content-Type: application/json" -d '{"prompt":"teste"}'

T=$(curl -s -X POST http://authorization:8081/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@ganjj.com","password":"adminSegura123"}' \
  | sed 's/.*"accessToken":"\([^"]*\)".*/\1/')

# com token: 200 (modo mock, resposta offline sem chamar API externa)
curl -s -X POST http://llm-provider:8004/generate \
  -H "Authorization: Bearer $T" -H "Content-Type: application/json" \
  -d '{"prompt":"teste"}'
```

## Autorrecuperação

```bash
kubectl get pods -l app=llm-provider
kubectl delete pod <nome-de-um-pod>
kubectl get pods -l app=llm-provider
```

O manifesto declara `replicas: 3`. Ao perder um Pod, o Deployment cria outro
para voltar ao estado declarado, e o Service atualiza os endpoints sozinho.

## Escalar

```bash
kubectl apply -f k8s/llm-provider.yaml
```

## Acessar do host

```bash
kubectl port-forward service/llm-provider 8004:8004
```

## Sobre a imagem

Publicada em
[joao2006/llm-provider](https://hub.docker.com/r/joao2006/llm-provider).
Para publicar uma versão nova:

```bash
docker build -t joao2006/llm-provider:1.0.1 .
docker push joao2006/llm-provider:1.0.1
```

E atualize a tag em `image:` no `llm-provider.yaml`.
