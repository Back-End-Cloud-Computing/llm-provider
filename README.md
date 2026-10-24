# llm-provider

Microsserviço que abstrai o acesso a um provedor de LLM externo (inicialmente
OpenRouter), com um fallback offline determinístico (`MockLLMProvider`) para
desenvolvimento e testes.

## Escopo

- `POST /generate`: recebe um `prompt` pronto e devolve a resposta completa do modelo.
- `WS /generate/ws`: mesma geração, mas transmitindo a resposta em pedaços
  (streaming), usada exclusivamente pelo fluxo de geração de descrição do
  `product-service`.
- `GET /metrics`: métricas Prometheus (requisições, erros e latência por rota);
  sem token e sem rota fora do cluster.

**Este serviço não contém nenhum prompt de negócio.** Quem quiser gerar uma
descrição de produto, decidir uma estratégia de busca, etc., monta o prompt
do lado de lá (ex.: `product-service`) e manda o texto pronto para cá. Isso
permite trocar de modelo/provider sem tocar em regra de negócio.

## Configuração

Ver `.env.example`. `LLM_PROVIDER=openrouter` exige `OPENROUTER_API_KEY`; sem
isso (ou com `LLM_PROVIDER=mock`), usa o provedor mock.

## Rodando localmente

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/uvicorn app.main:app --reload --port 8004
```

Swagger em `http://localhost:8004/docs`.

## Rodando com Docker

A partir de um clone isolado deste repositório:

```bash
cp .env.example .env   # LLM_PROVIDER=openrouter e OPENROUTER_API_KEY para LLM real
docker compose up -d
```

O `docker-compose.yml` constrói o llm-provider do código local e sobe o
`authorization` (+ Oracle, construído direto do repositório no GitHub), que
emite os tokens. O primeiro `up` leva alguns minutos: o Oracle precisa
inicializar e o `authorization` é compilado.

- API: `http://localhost:8004`
- Tokens: `POST http://localhost:8081/auth/login` (admin padrão `admin@ganjj.com` / `adminSegura123`)

## Testes

```bash
.venv/bin/pytest
```
