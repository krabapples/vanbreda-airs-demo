# Vanbreda Risk & Benefits – demo agent for Prisma AIRS PoC

![Vera demo agent: a normal question, then a prompt injection blocked by Prisma AIRS](docs/screenshot.png)

Small chat agent ("Vera") with Vanbreda branding. Every LLM call goes through the
**Prisma AIRS AI Gateway** endpoint you configure, so prompts, tool results and
responses are inspected by AI Runtime Security.

* Python / FastAPI, single container, no database
* Tool-calling agent loop with 4 mock back-office tools (policy, claim, HR benefits, knowledge base)
* Fictitious sensitive data (national numbers, IBANs) to trigger DLP / data-leak detections
* Built-in PoC prompt buttons: normal use, prompt injection, data leakage, harmful content, malicious URL/code
* Blocked requests are shown in the UI with the raw gateway response

## Run

```bash
cp .env.example .env      # set AI_GATEWAY_ENDPOINT and AI_GATEWAY_API_KEY
docker compose up --build
# open http://localhost:18080
```

## Configuration (.env)

| Variable | Meaning |
|---|---|
| `AI_GATEWAY_ENDPOINT` | Base URL of the OpenAI-compatible gateway; agent calls `<endpoint>/chat/completions` |
| `AI_GATEWAY_API_KEY` | API key for the gateway |
| `AI_GATEWAY_MODEL` | Model name behind the gateway |
| `AI_GATEWAY_AUTH_HEADER` | `Authorization` (Bearer, default) or a custom header name such as `x-pan-token` |
| `HOST_PORT` | Host port for the UI (default 18080) |
| `AI_GATEWAY_EXTRA_HEADERS` | Optional JSON object of extra headers, e.g. `{"x-portkey-provider":"google"}` |
| `VERIFY_TLS` | `false` for lab gateways with self-signed certs |

Any non-200 from the gateway is treated as a block and displayed as such.

## Branding

Colors/fonts taken from vanbreda.be (navy `#1a3d8f`, teal `#42a7bb`, magenta `#bc0062`).
`app/static/logo.svg` is a text placeholder; replace it with the official logo
(keep the filename) if the customer provides one.
