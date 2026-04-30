# Environment variables (IntentCenter API & worker)

This is a **complete inventory** of variables used by the **Phase 1** stack (`platform/backend`, Prisma, `nims-worker`, and seed scripts). Values are read from the process environment and/or `platform/.env` (and `platform/backend/.env` if present), depending on how you start the process.

**Conventions:** Unless noted, unset variables fall back to code defaults. `AUTH_*` and `LLM_*` variables, when set, **override** values stored in the database for the org (admin UI shows those fields as read-only). **Secrets** should be supplied via a secret manager, Kubernetes `Secret`, or `env_file` never committed to git.

---

## Core API process

| Variable | Required | Default / notes |
|----------|----------|-----------------|
| `DATABASE_URL` | **Yes** (or RDS vars below) | SQLAlchemy URL, e.g. `postgresql+psycopg://user:pass@host:5432/nims` |
| `API_HOST` | No | `0.0.0.0` — bind address for `nims-api` / uvicorn |
| `API_PORT` | No | `8080` |
| `NIMS_RELOAD` | No | `true` in dev; `false` in Docker image / production |
| `NODE_ENV` | No | `development` / `production` — used by the app for environment hints |
| `LOG_LEVEL` | No | Listed in `platform/.env.example` for operators; **not** read by application code today—use with your process manager or future wiring |

### JWT and browser sessions

| Variable | Required | Default / notes |
|----------|----------|-----------------|
| `JWT_SECRET` | **Yes in production** | Signing key for session tokens (`POST /v1/auth/login`) |
| `JWT_EXPIRES_IN` | No | e.g. `12h` |

### Identity secrets at rest (optional separate key)

| Variable | Required | Default / notes |
|----------|----------|-----------------|
| `IDENTITY_ENCRYPTION_KEY` | No | If unset, `JWT_SECRET` is used to derive Fernet material for **encrypted IdP/LLM API secrets** in the database |

### PostgreSQL via split env (optional — Docker entrypoint & RDS)

When **`PGHOST`** is set, `platform/docker-entrypoint.sh` builds `DATABASE_URL` and optional `PRISMA_MIGRATE_URL` from:

| Variable | Required when using RDS style | Default / notes |
|----------|----------------------------------|-----------------|
| `PGHOST` | one of the set | Database hostname |
| `PGPORT` | No | `5432` |
| `PGUSER` | Yes | Username |
| `PGPASSWORD` | Yes | Password |
| `PGDATABASE` | No | `nims` |
| `PRISMA_MIGRATE_URL` | No | If set, used **only** for `prisma migrate deploy` in the entrypoint, then cleared |

---

## Model Context Protocol (MCP)

| Variable | Required | Default / notes |
|----------|----------|-----------------|
| `NIMS_MCP_ENABLED` | No | `0` / unset = disabled. `1` = mount Streamable HTTP MCP at **`/mcp`** (see `design-mcp-server.md`) |

---

## LLM and copilot

| Variable | Required | Default / notes |
|----------|----------|-----------------|
| `LLM_ENABLED` | No | When set, locks / drives org **enabled** flag (see `llm_config.py`) |
| `LLM_BASE_URL` | For copilot in env-only mode | OpenAI-compatible base, e.g. `https://api.openai.com/v1` or Azure resource URL |
| `LLM_API_KEY` | For copilot in env-only mode | API key; overrides org DB when set |
| `LLM_DEFAULT_MODEL` | No | e.g. `gpt-4.1-mini`; for Azure, use **deployment** name |
| `LLM_AZURE_API_VERSION` | No | e.g. `2024-02-15-preview` (Azure OpenAI) |
| `COPILOT_MAX_TOOL_ROUNDS` | No | Default `12`, max `64` — model↔tool rounds per user message |
| `NIMS_INTERNAL_LLM_KEY` | For `POST /v1/internal/llm/complete` | Shared secret header; leave unset to disable that route |

---

## Sign-in: local + at most one external directory

| Variable | Required | Notes |
|----------|----------|--------|
| `AUTH_LOCAL_ENABLED` | No | `1`/`0` — enable local email/password |
| `AUTH_EXTERNAL_PROVIDER` | No | `none` / `ldap` / `azure_ad` / `oidc` (env **wins** over admin UI) |
| `AUTH_LDAP_URL` | If LDAP | |
| `AUTH_LDAP_BIND_DN` | If LDAP | |
| `AUTH_LDAP_BIND_PASSWORD` | If LDAP | |
| `AUTH_LDAP_USER_SEARCH_BASE` | If LDAP | |
| `AUTH_LDAP_USER_SEARCH_FILTER` | If LDAP | e.g. `(sAMAccountName={username})` |
| `AUTH_AZURE_TENANT_ID` | If Entra | |
| `AUTH_AZURE_CLIENT_ID` | If Entra | |
| `AUTH_AZURE_CLIENT_SECRET` | If Entra | |
| `AUTH_OIDC_ISSUER` | If OIDC | |
| `AUTH_OIDC_CLIENT_ID` | If OIDC | |
| `AUTH_OIDC_CLIENT_SECRET` | If OIDC | |
| `AUTH_OIDC_REDIRECT_URI` | If OIDC | Callback URL registered with the IdP |

---

## Jobs: inline vs async worker

| Variable | Required | Default / notes |
|----------|----------|-----------------|
| `JOB_EXECUTION_MODE` | No | `inline` (default) or `async` — async queues `JobRun` for `nims-worker` |
| `JOB_WORKER_POLL_INTERVAL_SEC` | No | `2.0` |
| `JOB_WORKER_BATCH_SIZE` | No | `5` |

---

## Connectors (credentials + outbound HTTP)

| Variable | Required | Default / notes |
|----------|----------|-----------------|
| `CONNECTOR_SECRETS_FERNET_KEY` | **Recommended in production** | 44-byte url-safe base64 Fernet key; if unset, secrets may be stored as JSON (dev only) |
| `CONNECTOR_SECRETS_FERNET_KEY_PREVIOUS` | No | For key rotation; decrypt with old, re-encrypt with new |
| `CONNECTOR_SECRETS_KMS_KEY_ID` | No | **Reference / future**; not read by app logic today |
| `CONNECTOR_URL_BLOCK_PRIVATE_NETWORKS` | No | Default blocks RFC1918, loopback, etc. |
| `CONNECTOR_URL_ALLOWED_HOST_SUFFIXES` | No | Comma-separated allowlist; public IPs ignore suffix |
| `CONNECTOR_URL_HTTP_ALLOWED_SCHEMES` | No | e.g. `https` in production, `https,http` in dev |
| `CONNECTOR_HTTP_FOLLOW_REDIRECTS` | No | Default `0` / `false` |

---

## Seeding and demos (not used by running API in production)

| Variable | Notes |
|----------|--------|
| `SEED_ADMIN_EMAIL`, `SEED_ADMIN_PASSWORD` | `nims-seed` default admin |
| `PROVIDER_BULK_LITE`, `PROVIDER_BULK_CONFIRM`, `PROVIDER_BULK_PURGE`, `PROVIDER_BULK_ORG_SLUG` | Large synthetic dataset (see `seed_provider_bulk.py`) |
| `NUM_REGIONS`, `NUM_SITES_PER_REGION`, `RACKS_PER_SITE`, `DEVICES_PER_RACK` | Provider bulk scale knobs |
| `SEED_DEMO_FLEET` | `1` (default) vs `0` for demo comprehensive seed (`seed_demo_comprehensive.py`) |

For hosted demo **migrations and deploy**, see [demo-database.md](demo-database.md).
