# Platform implementation (`platform/`)

IntentCenter **Phase 1** stack: **FastAPI** (`backend/nims`), **PostgreSQL**, **Prisma** for migrations only, **React + Vite** (`web/`).

## Web console

- **Build**: from `platform/`, `npm run web:build` (or `npm run web:dev` for Vite only). Output is `web/dist`, which the API can serve under `/app/`.
- **Pinned pages**: stored in `User.preferences` (JSON), updated via `PATCH /v1/me` with `{ "preferences": { "pinnedPages": [ { "path": "/dcim/devices", "label": "Devices" } ] } }`.
- **Pin / Unpin** lives in the **page header** **⋯** menu (`ModelListPageHeader` + `PageActionsMenu`), not in the sidebar.
- **Sidebar**: pinned links first (below the brand), then global search, then **collapsible** nav sections (state in `localStorage` keys `nims.sidebar.*`).
- **List pages** use `ModelListPageHeader` for Add / bulk / pin; tables use `DataTable` + `RowOverflowMenu` (Copy, Archive, Delete) where applicable.

## API touchpoints for the UI

| Feature | Endpoint |
|--------|-----------|
| Search | `GET /v1/search?q=&limit=` |
| Me / preferences | `GET /v1/me`, `PATCH /v1/me` |
| Bulk CSV/JSON | `GET /v1/bulk/{resourceType}/export`, `POST /v1/bulk/{resourceType}/import/csv`, `POST /v1/bulk/{resourceType}/import/json` (core types + catalog types — see `bulk.py`) |
| Object view (UI) | `GET /v1/resource-view/{resourceType}/{id}` — item fields + graph |
| Graph only | `GET /v1/resource-graph/{resourceType}/{id}` — relationship graph JSON |

For full run instructions, database setup, and CI, see the repository root [`README.md`](../README.md).
