import os
from fastapi import FastAPI
from db import init_db, close_db, run_migrations

app = FastAPI()


@app.on_event("startup")
async def startup():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL no definida")

    await init_db(database_url)
    await run_migrations()


@app.on_event("shutdown")
async def shutdown():
    await close_db()


@app.get("/")
async def root():
    return {"status": "ok"}