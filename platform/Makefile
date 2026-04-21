# Platform tasks: Python-first (uv). Prisma CLI still uses Node for schema/migrations; web uses npm.
UV ?= uv
BACKEND := backend

.PHONY: sync api seed test lint format
sync:
	cd $(BACKEND) && $(UV) sync --all-extras

api:
	cd $(BACKEND) && $(UV) run nims-api

seed:
	cd $(BACKEND) && $(UV) run nims-seed

test:
	cd $(BACKEND) && $(UV) run pytest -q

lint:
	cd $(BACKEND) && $(UV) run ruff check nims

format:
	cd $(BACKEND) && $(UV) run ruff format nims tests
