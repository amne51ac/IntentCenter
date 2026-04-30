# Platform implementation (`platform/`)

IntentCenter **Phase 1** stack: **FastAPI** (`backend/nims`), **PostgreSQL**, **Prisma** for migrations only, **React + Vite** (`web/`).

## Web console

- **Build**: from `platform/`, `npm run web:build` (or `npm run web:dev` for Vite only). Output is `web/dist`, which the API can serve under `/app/`.
- **Pinned pages**: stored in `User.preferences` (JSON), updated via `PATCH /v1/me` with `{ "preferences": { "pinnedPages": [ { "path": "/dcim/devices", "label": "Devices" } ] } }`.
- **Pin / Unpin** lives in the **page header** **⋯** menu (`ModelListPageHeader` + `PageActionsMenu`), not in the sidebar.
- **Sidebar**: pinned links first (below the brand), then global search, then **collapsible** nav sections (state in `localStorage` keys `nims.sidebar.*`).
- **List pages** use `ModelListPageHeader` for Add / bulk / pin; tables use `DataTable` + `RowOverflowMenu` (Copy, Archive, Delete) where applicable.

## Sign-in & identity (admin)

Identity settings are stored per **organization** in `Organization.identityConfig` (JSON) and merged with **environment variables** where set (env wins; those values are read-only in the UI).

| Option | Notes |
|--------|--------|
| **Local** | Email + password — optional; can be combined with one external directory. |
| **LDAP / AD** | At most one of LDAP, Entra, or OIDC. Interactive bind flows may still be partial; see design doc. |
| **Microsoft Entra ID** | App registration fields via admin UI or `AUTH_AZURE_*` env. |
| **OpenID Connect** | Issuer, client, redirect — `AUTH_OIDC_*` env or DB. |
| **SSO start** | `GET /v1/auth/sso/{provider}/start` may return **501** until redirect/callback wiring is complete. |

- **Admin UI (ADMIN only):** `/app/platform/admin/identity` — local checkbox + **at most one** external type; **Save** only when there are unsaved edits.
- **API:** `GET /v1/admin/identity`, `PATCH /v1/admin/identity`.
- **Public (unauthenticated):** `GET /v1/auth/providers` — effective provider catalog for the first organization.
- **Secrets:** IdP secrets in DB are encrypted at rest; never returned in plaintext to the browser.

Full variable list: [`docs/design-auth-user-management.md`](../docs/design-auth-user-management.md) and [`.env.example`](.env.example).

## Extensibility, plugins, and automation

| Area | What exists today |
|------|-------------------|
| **Plugin packages** | `PluginRegistration` per org (`GET /v1/plugins`); admin **Plugins & extensions** registers packages, **placements** (page + slot + widget key), and **connectors**. |
| **UI** | `GET /v1/ui/page-registry` (auth), `GET /v1/ui/placements`, `GET /v1/ui/navigation` (core + `manifest.navigation`), `GET /v1/ui/federation` (**builtin** only). Object view loads **slots** with macro-bound props. |
| **Connectors** | `GET/POST/PATCH/DELETE /v1/connectors` (admin for writes); optional **Fernet** for `credentialsEnc`; outbound HTTP uses **URL policy** (block private networks; optional host suffix allowlist). |
| **Jobs** | `GET/POST /v1/jobs`, `POST /v1/jobs/{key}/run`, `GET /v1/job-runs` — default **inline** execution; set **`JOB_EXECUTION_MODE=async`** and run **`nims-worker`** to process `JobRun` rows off the API hot path. |

Reserved / not yet implemented: `POST /v1/plugins/install` (**501**), remote module federation, full KMS for connector secrets. Summary: [§18 in `design-llm-assistant.md`](../docs/design-llm-assistant.md).

## API touchpoints for the UI

| Feature | Endpoint |
|--------|-----------|
| Search | `GET /v1/search?q=&limit=` |
| Me / preferences | `GET /v1/me`, `PATCH /v1/me` |
| Sign-in options (login page) | `GET /v1/auth/providers` |
| Identity config (admin) | `GET /v1/admin/identity`, `PATCH /v1/admin/identity` |
| UI extensibility | `GET /v1/ui/page-registry`, `GET /v1/ui/placements`, `GET /v1/ui/navigation`, `GET /v1/ui/federation` |
| Plugins / placements (admin) | `GET/POST/PATCH/DELETE /v1/admin/plugin-placements` |
| Connectors (admin writes) | `GET/POST/PATCH/DELETE /v1/connectors` |
| Jobs | `GET /v1/jobs`, `POST /v1/jobs/{key}/run` (optional `queued` if async), `GET /v1/job-runs` |
| LLM (admin) | `GET /v1/admin/llm`, `PATCH /v1/admin/llm`, `POST /v1/admin/llm/test`, `GET /v1/admin/llm/metrics` |
| Copilot (chat, next steps, skills) | `POST /v1/copilot/chat`, `POST /v1/copilot/chat/stream`, `POST /v1/copilot/suggest_next_steps`, `GET/POST/PATCH/DELETE /v1/copilot/skills` — see `copilot.py` / OpenAPI for assist & triage |
| Plugin install (reserved) | `POST /v1/plugins/install` → **501** until signing + store |
| Bulk CSV/JSON | `GET /v1/bulk/{resourceType}/export`, `POST /v1/bulk/{resourceType}/import/csv`, `POST /v1/bulk/{resourceType}/import/json` (core types + catalog types — see `bulk.py`) |
| Object view (UI) | `GET /v1/resource-view/{resourceType}/{id}` — item fields + graph |
| Graph only | `GET /v1/resource-graph/{resourceType}/{id}` — relationship graph JSON |

For full run instructions, database setup, and CI, see the repository root [`README.md`](../README.md).

**Hosted demo (AWS):** schema updates usually come from **deploying a new image** that includes the latest `prisma/migrations/`; `docker-entrypoint.sh` runs `prisma migrate deploy` on container start. Use your normal **`./deploy.sh` / AWS** flow, or the console to force a new ECS deployment—see [`docs/demo-database.md`](../docs/demo-database.md). For emergencies, `npm run db:migrate:deploy` from `platform/` with the demo `DATABASE_URL` is a fallback.

## AI assistant (copilot), LLM admin, and optional MCP

- **In-app panel:** the **Intent Center** copilot (slide-out) streams chat with **OpenAI-style tool calls** to inventory: search, view/graph, `inventory_stats`, `catalog_breakdown` / `catalog_list` (including pre-registered **catalog query** entries such as per-site or “without interface” device lists), `list_location_hierarchy`, and `propose_change_preview` (mutations are preview-gated as in the design spec). The UI renders **markdown**; object references in replies can be **linkified** to the catalog.
- **“Next steps”** chips: `POST /v1/copilot/suggest_next_steps` with page context and recent messages — **topic-aware** (heuristic + optional LLM) so suggestions follow the thread, not only generic org snapshots.
- **Admin (ADMIN only):** `GET/PATCH /v1/admin/llm`, `POST /v1/admin/llm/test`, `GET /v1/admin/llm/metrics` — org-level default model and base URL; **environment** `LLM_BASE_URL` / `LLM_API_KEY` / `LLM_DEFAULT_MODEL` (and optional `LLM_AZURE_API_VERSION`) **override** the admin UI for unattended deployments. When no LLM is enabled, the API still returns deterministic next-step and suggestion fallbacks.
- **Other copilot routes:** `POST /v1/copilot/chat` and `…/stream`, `POST /v1/copilot/assist/import-mapping`, `POST /v1/copilot/assist/ticket-triage`, `POST /v1/copilot/suggest_thread_title`, `GET /v1/copilot/suggestions` (static chips for empty state), and CRUD for org **skills** under `GET/POST/PATCH/DELETE /v1/copilot/skills`.
- **Internal extension LLM (optional):** `POST /v1/internal/llm/complete` (guarded with `NIMS_INTERNAL_LLM_KEY` header) for workers or plugins.
- **MCP (off by default):** set `NIMS_MCP_ENABLED=1` to mount **Streamable HTTP** MCP on **`/mcp`**, same host as the API, using **API tokens** as `Authorization: Bearer` (read/write/admin roles filter tools). See [`../docs/design-mcp-server.md`](../docs/design-mcp-server.md).

| Concern | Env / flag (see `.env.example`) |
|--------|----------------------------------|
| OpenAI-compatible LLM for copilot | `LLM_ENABLED`, `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_DEFAULT_MODEL` |
| Tool round limit | `COPILOT_MAX_TOOL_ROUNDS` |
| Expose MCP | `NIMS_MCP_ENABLED` |
| Internal LLM for extensions | `NIMS_INTERNAL_LLM_KEY` |

**Deployment:** the production image, OpenAPI contract (`/docs`, `/docs/json`), full **environment** inventory, and example **Docker Compose** and **Kubernetes** files live in [`../docs/deployment.md`](../docs/deployment.md), [`../docs/environment-variables.md`](../docs/environment-variables.md), and [`deploy/README.md`](deploy/README.md).
