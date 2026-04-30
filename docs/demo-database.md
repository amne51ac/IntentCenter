# Hosted demo — database schema (Prisma migrations)

The public demo (e.g. **demo.intentcenter.io** on **AWS**) must use the same **PostgreSQL schema** as this repo: files under `platform/prisma/migrations/` need to be applied to the **RDS** (or equivalent) database the running API uses.

In normal operation you **do not** hand-run SQL from a laptop. Schema updates land when you **ship a build that includes the new migration folders** and the API process starts.

## How migrations actually run in production

`platform/docker-entrypoint.sh` runs:

```bash
npx prisma migrate deploy
```

**before** the main process. So a deploy that **starts a new container/task** with an image built from a commit that contains the new migrations is usually enough: the first boot applies any **pending** migrations, then the server starts.

If you use **RDS env** (`PGHOST`, etc.), the same script can set `PRISMA_MIGRATE_URL` for the CLI (see `docker-entrypoint.sh`).

---

## Preferred: deploy the way you already do (e.g. `./deploy.sh`, AWS)

1. **Merge** migrations on `main` and **build** an image (or artifact) that includes `platform/prisma/migrations/`.
2. **Deploy to AWS** using your usual path — for example the repo/infra script you run from this project (**`./deploy.sh`** or your CI), which should roll **ECS** (or EKS) to a new task definition / service revision.
3. New tasks start → **entrypoint runs `prisma migrate deploy`** → schema matches code.

That is the same “deployment and update” you already use; the schema follows automatically **as long as** the image has the latest migration files and the app is allowed to connect to the DB with DDL-capable permissions.

## Using the AWS console

If you are not doing a full pipeline run, you can still get migrations applied by **starting new service work** with an image that already contains the new migrations, for example:

- **ECS:** “Update service” → **Force new deployment**, or push a new task definition that points at the new image digest.
- Ensure the service actually **replaces** running tasks (new containers run the entrypoint once).

For **one-off** or debugging, your team might use **ECS Exec**, **SSM** into a runner, or a **bastion** + `DATABASE_URL` — that is environment-specific. The important part is still: run `prisma migrate deploy` with credentials that hit the **same** database the demo app uses, or rely on the **entrypoint** on a fresh deploy.

## Fallback: run Prisma from your machine (emergency / ops)

If you must apply migrations without a full deploy (rare), from the directory that contains **`prisma/`** (this repo’s `platform/` folder):

```bash
cd platform
export DATABASE_URL="postgresql://…"   # demo RDS URL, same DB the service uses
npx prisma migrate deploy
# or: npm run db:migrate:deploy
```

Use a URL Prisma accepts (often `postgresql://…`, not `postgresql+psycopg://…`). Restart the service afterward if the API was up with a stale pool.

## Optional: re-seed

Only if you intentionally want to refresh demo data:

`npm run db:seed` (with `DATABASE_URL` set). Not required for schema-only changes; idempotency depends on the seed.

## Troubleshooting

| Symptom | What to check |
|--------|----------------|
| **Deployed but still schema errors** | Image was built from a commit **without** the new `prisma/migrations/*` folder, or old tasks are still running. **Force a new deployment** with the correct image. |
| **`P3009` / failed migration** | A migration half-applied. Fix DB state or use `prisma migrate resolve` only after you understand the failure ([Prisma troubleshooting](https://www.prisma.io/docs/guides/migrate/troubleshooting-development)). |
| **App and CLI disagree** | Confirm `DATABASE_URL` points at the **same** RDS instance the ECS task uses (same cluster/env). |

## Related

- Migrations: [`platform/prisma/migrations/`](../platform/prisma/migrations/)
- Local dev: `npm run db:migrate` → `prisma migrate **dev**` (creates dev migrations). **Demo/prod** use **`migrate deploy`**, which the container entrypoint runs automatically.
