from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from nims.graphql_api import graphql_router
from nims.routers.health import router as health_router
from nims.routers.v1.auth import router as auth_router
from nims.routers.v1.automation import router as automation_router
from nims.routers.v1.bulk import router as bulk_router
from nims.routers.v1.catalog import router as catalog_router
from nims.routers.v1.circuits import router as circuits_router
from nims.routers.v1.connectors import router as connectors_router
from nims.routers.v1.core import router as core_router
from nims.routers.v1.dcim import router as dcim_router
from nims.routers.v1.extensions_admin import router as extensions_admin_router
from nims.routers.v1.identity_admin import router as identity_admin_router
from nims.routers.v1.ipam import router as ipam_router
from nims.routers.v1.reconciliation import router as reconciliation_router
from nims.routers.v1.resource_graph import router as resource_graph_router
from nims.routers.v1.resource_view import router as resource_view_router
from nims.routers.v1.search import router as search_router
from nims.routers.v1.templates import router as templates_router
from nims.routers.v1.ui import router as ui_router
from nims.routers.v1.users_admin import router as users_admin_router
from nims.swagger_html import SWAGGER_DOCS_HTML


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield


app = FastAPI(
    title="IntentCenter API",
    description="IntentCenter — DCIM, IPAM, circuits, automation, and closed-loop inventory (clean-room derived). Read-only GraphQL at /graphql.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def close_graphql_db_session(request: Request, call_next):
    response = await call_next(request)
    db = getattr(request.state, "graphql_db", None)
    if db is not None:
        db.close()
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router, prefix="/v1")
app.include_router(core_router, prefix="/v1")
app.include_router(ui_router, prefix="/v1")
app.include_router(users_admin_router, prefix="/v1")
app.include_router(identity_admin_router, prefix="/v1")
app.include_router(dcim_router, prefix="/v1")
app.include_router(ipam_router, prefix="/v1")
app.include_router(circuits_router, prefix="/v1")
app.include_router(automation_router, prefix="/v1")
app.include_router(reconciliation_router, prefix="/v1")
app.include_router(templates_router, prefix="/v1")
app.include_router(search_router, prefix="/v1")
app.include_router(resource_graph_router, prefix="/v1")
app.include_router(resource_view_router, prefix="/v1")
app.include_router(bulk_router, prefix="/v1")
app.include_router(catalog_router, prefix="/v1")
app.include_router(connectors_router, prefix="/v1")
app.include_router(extensions_admin_router, prefix="/v1")

app.include_router(graphql_router, prefix="/graphql")


@app.get("/docs/json", include_in_schema=False)
def docs_json() -> JSONResponse:
    return JSONResponse(app.openapi())


@app.get("/docs", include_in_schema=False)
@app.get("/docs/", include_in_schema=False)
def docs_page() -> JSONResponse:
    return JSONResponse(content=SWAGGER_DOCS_HTML, media_type="text/html; charset=utf-8")


_here = Path(__file__).resolve().parent
_web_dist = _here.parent.parent / "web" / "dist"
if (_web_dist / "index.html").is_file():
    assets_dir = _web_dist / "assets"
    if assets_dir.is_dir():
        app.mount("/app/assets", StaticFiles(directory=assets_dir), name="web-assets")

    @app.get("/app")
    async def redirect_app() -> RedirectResponse:
        return RedirectResponse("/app/", status_code=302)

    @app.get("/")
    async def redirect_root() -> RedirectResponse:
        return RedirectResponse("/app/", status_code=302)

    @app.get("/app/")
    async def app_index() -> FileResponse:
        return FileResponse(_web_dist / "index.html")

    @app.get("/app/{full_path:path}", response_model=None)
    async def app_spa(full_path: str) -> FileResponse | JSONResponse:
        if full_path.startswith("assets/"):
            return JSONResponse({"error": "Not Found"}, status_code=404)
        candidate = _web_dist / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_web_dist / "index.html")
