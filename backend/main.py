import os
import psycopg
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="Worker Attendance & Wage Tracker")

@app.get("/health")
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

from backend.auth import router
app.include_router(router)
from backend.worksites import router as worksites_router
app.include_router(worksites_router)
