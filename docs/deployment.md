# Deployment and API access

This document covers how to **access the API specification**, how to **run and deploy** IntentCenter (Docker, Compose, Kubernetes-style patterns), and points to the **authoritative environment variable list**: [environment-variables.md](environment-variables.md).

---

## 1. API specification (OpenAPI / Swagger)

The FastAPI app exposes a **live OpenAPI 3** schema and an HTML **Swagger-like** page:

| What | URL (replace host) |
|------|---------------------|
| **OpenAPI JSON** (for codegen, contract tests) | `GET https://<your-api-host>/docs/json` |
| **API browser** (human-friendly; loads JSON client-side) | `GET https://<your-api-host>/docs` or `/docs/` |
| **ReDoc** | Not installed by default; use `/docs/json` with an external ReDoc or Postman import |

**Local (default `make api` / port 8080):**

- `http://localhost:8080/docs/json`
- `http://localhost:8080/docs`

**Versioning:** All REST v1 resources are under **`/v1/...`**. The OpenAPI `info.version` tracks the app bundle; breaking changes are communicated via [Repository README](https://github.com/amne51ac/intentcenter/blob/main/README.md) and API changelog practices.

**GraphQL (read):** `POST /graphql` — GraphiQL at `GET /graphql` when enabled; same process as REST.

**Health:** `GET` health routes are mounted from `nims/routers/health` (see running instance or OpenAPI for exact paths used in your build).

**Optional MCP:** When `NIMS_MCP_ENABLED=1`, the Model Context Protocol is mounted at **`/mcp`** (same origin and TLS as the API; bearer API tokens). See [design-mcp-server.md](design-mcp-server.md).

---

## 2. What you ship (single container image)

The [Dockerfile](../platform/Dockerfile) builds a **single image** that:

1. **Installs** Python + uv, Node/Prisma CLI, and production Python deps.
2. **Builds** the React app (`web/dist`) and **runs** `prisma migrate deploy` on startup.
3. Starts **uvicorn** for `nims.main:app` on port **8080** with **`--proxy-headers`**, so you can run behind a reverse proxy or load balancer that sets `X-Forwarded-*` (e.g. AWS ALB).

**Image defaults (see Dockerfile `ENV`):**

- `NIMS_RELOAD=false`, `API_HOST=0.0.0.0`, `API_PORT=8080`, `NODE_ENV=production`

**Runtime secrets and config** are always injected with **environment variables** or a mounted `.env` file (e.g. ECS task definition, Kubernetes `Secret` + `ConfigMap`).

---

## 3. Local and simple Docker Compose (database only)

For **day-one development**, `platform/docker-compose.yml` runs only **Postgres** on `localhost:5433`. The API is started on the host with `make api` and `DATABASE_URL` pointing at that port.

A **full stack** example (Postgres + API + optional worker) lives under **`platform/deploy/docker-compose.app.example.yml`**. Copy it, set secrets, and run with Compose v2.

```bash
cd platform
# Copy and edit: DATABASE_URL, JWT_SECRET, and any optional settings from environment-variables.md
cp deploy/docker-compose.app.example.yml deploy/docker-compose.app.yml
docker compose -f deploy/docker-compose.app.yml up -d
```

---

## 4. Production-style deployment: RDS / split PG env

If you deploy to **AWS RDS** (or any managed Postgres) and your platform **injects** the standard variables `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, and optionally `PGDATABASE`, the **`docker-entrypoint.sh` script** will:

1. Compose `DATABASE_URL` and optional `PRISMA_MIGRATE_URL` for Prisma.
2. Runs **`npx prisma migrate deploy`**.
3. Starts the API with the same `DATABASE_URL`.

You do **not** need a separate migration Job if every new version runs this entrypoint once. See [demo-database.md](demo-database.md) for the hosted-demo workflow and emergency Prisma notes.

---

## 5. Background job worker (optional)

When `JOB_EXECUTION_MODE=async`, the API enqueues work; a **second process** must run the worker against the same database:

```bash
# Same DATABASE_URL / PG* as the API
uv run --directory backend nims-worker
```

In containers, use a second **Deployment** or a **sidecar** pattern with the same image and command override (see [platform/deploy](../platform/deploy) Kubernetes example).

---

## 6. Kubernetes (example manifests)

Example manifests (namespace, service, deployment, config placeholder, **optional** worker) are in **`platform/deploy/kubernetes/`**. They are **not** a turn-key product chart—they illustrate:

- Probes, resource limits, and **envFrom** a `ConfigMap` / `Secret`
- Exposing the web UI and API on port **8080** through a `Service` (`type: LoadBalancer` or your ingress controller)
- A separate `Deployment` for `nims-worker` when using async jobs

**Before apply:** create secrets with `JWT_SECRET`, `DATABASE_URL` (or `PG*`), and any `LLM_*` / `AUTH_*` you need, then update references in the YAML to match your secret names and namespaces.

---

## 7. Checklist (production)

| Item | Note |
|------|------|
| `JWT_SECRET` | Strong, unique per environment |
| `DATABASE_URL` or `PG*` + entrypoint | Migrations on boot |
| TLS | Terminate at load balancer or ingress; image expects forwarded headers for HTTPS links |
| `LLM_*` or admin UI | Only if you use the copilot |
| `NIMS_MCP_ENABLED` | Keep `0` unless you intend to expose `/mcp` to trusted clients |
| `CONNECTOR_SECRETS_FERNET_KEY` | Set before production connector use |
| Worker | `JOB_EXECUTION_MODE=async` + `nims-worker` if you use async jobs |

For every variable, see [environment-variables.md](environment-variables.md).
