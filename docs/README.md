# `docs/` — specifications and GitHub Pages site

This folder holds **authoritative Markdown** (`architecture.md`, `design-llm-assistant.md`) and a **static documentation website** for GitHub Pages (`index.html`, `documentation.html`, `assets/`, `assets/screenshots/`, …).

- **Edit Markdown first** for long-form specs; the HTML pages summarize or mirror diagrams (e.g. architecture Mermaid figures) and link to the corresponding files on GitHub.
- **Styling:** `assets/site.css` matches the **IntentCenter operator console**—charcoal app chrome (`#0b0e14`), Signal Amber (`#e8b84e`), GitHub-style elevated panels, uppercase table headers, and Inter + JetBrains Mono.
- **Enable Pages:** Repository **Settings → Pages →** Branch `main`, folder **`/docs`**. The site publishes at `https://<user>.github.io/<repo>/` (for example `https://amne51ac.github.io/intentcenter/`).

Key entry points:

| Path | Role |
|------|------|
| `index.html` | Product landing (**About** — what / why / how), **in-app assistant & AI**; **in-app screenshots**; **live demo** at [https://demo.intentcenter.io](https://demo.intentcenter.io) |
| `documentation.html` | Doc hub and links to repo sources |
| `demo-database.md` | **AWS demo:** deploy / `deploy.sh` / ECS (entrypoint runs migrations); console & emergency Prisma notes |
| `platform.html` | Web console + REST summary (inventory, **copilot & LLM**, extensibility, auth, optional **MCP**) |
| `getting-started.html` | Local runbook (Postgres, API, optional **job worker**, env) |
| `deployment.html` / `deployment.md` | **OpenAPI** (`/docs/json`), Docker/K8s **deploy** examples, checklist |
| `environment-variables.md` | **Full** list of `AUTH_*`, `LLM_*`, `CONNECTOR_*`, `PG*`, seeds, etc. |
| `api.html` | REST/OpenAPI, authentication surfaces, v1 touchpoints |
| `architecture.md` / `architecture.html` | Target architecture (diagrams) |
| `design-auth-user-management.md` | **Sign-in & identity**: local email/password, **LDAP** / **Entra** / **OIDC** (at most one external), `AUTH_*` env vs DB, admin API, `GET /v1/auth/providers` |
| `design-api-token-authentication.md` | Bearer token authentication for automation |
| `design-llm-assistant.md` | In-app **copilot**: tool-grounded chat, page & chat–aware **next steps**, **skills**, import assist, triage; **§0** preview consent; **§18** extensibility, jobs, connectors |
| `design-mcp-server.md` | Optional **MCP** (`/mcp`, API-token auth, role-scoped tools) for external LLM clients |
| `design-extensibility-plugins-widgets.md` | Widget slots, placements, registry (Phase 0–1) |
| `assets/site.css`, `assets/github-mark.svg`, `assets/intentcenter-logo.svg`, `assets/favicon.svg` | Shared styles, GitHub mark for links, and marks |
| `assets/screenshots/*.png` | Product UI reference imagery for the static site; includes `ai-assistant-inventory-charts-maps.png` (copilot: Q&A, charts, maps) |
| `.nojekyll` | Disables Jekyll so static assets deploy cleanly |

### Custom domain

If you use a domain (e.g. **intentcenter.io**), add it under **Settings → Pages → Custom domain**, configure DNS per [GitHub Pages custom domains](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site), then enable **Enforce HTTPS**. For project sites, update root-relative paths in [`404.html`](404.html) if the repository name changes (`/intentcenter/...`).
