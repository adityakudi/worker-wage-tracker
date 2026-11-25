import os
from pathlib import Path
import psycopg
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

async def database_unavailable(request, exception):
    # Do not disclose connection strings, hosts or driver internals to callers.
    return JSONResponse(status_code=503, content={"detail": "Database temporarily unavailable"})


def health():
    url = os.getenv("DATABASE_URL")
    if not url:
        return JSONResponse(status_code=503, content={"status": "unavailable", "database": "not_configured"})
    try:
        with psycopg.connect(url, connect_timeout=3) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                assert cursor.fetchone() == (1,)
        return {"status": "ok", "database": "connected"}
    except psycopg.Error:
        return JSONResponse(status_code=503, content={"status": "unavailable", "database": "unreachable"})

from backend.auth import router as auth_router
from backend.worksites import router as worksites_router
from backend.memberships import router as memberships_router


def create_app(frontend_dir: Path | None = None) -> FastAPI:
    application = FastAPI(title="Worker Attendance & Wage Tracker")
    application.add_exception_handler(psycopg.OperationalError, database_unavailable)
    application.add_api_route('/health', health, methods=['GET'])
    application.add_api_route('/api/health', health, methods=['GET'], include_in_schema=False)
    for router in (auth_router, worksites_router, memberships_router):
        # Keep existing development clients compatible; /api is the production origin.
        application.include_router(router)
        application.include_router(router, prefix='/api', include_in_schema=False)
    directory = frontend_dir if frontend_dir is not None else Path(__file__).resolve().parent.parent / 'frontend' / 'dist'
    if directory.is_dir():
        # Mount last so static files cannot shadow authentication or health routes.
        # The frontend uses #demo and #live; no catch-all HTML rewrite is needed.
        application.mount('/', StaticFiles(directory=directory, html=True), name='frontend')
    return application


app = create_app()
