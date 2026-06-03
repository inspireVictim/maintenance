"""Точка входа FastAPI-приложения «Учёт заявок на ТО»."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .database import init_schema, seed_data
from .routers import (
    equipment_router,
    parts_router,
    reference_router,
    requests_router,
)

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"

app = FastAPI(
    title="Учёт заявок на ТО — REST API",
    description="ВКР. Система учёта заявок на техническое обслуживание оборудования.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_schema()
    seed_data()


app.include_router(reference_router.router)
app.include_router(equipment_router.router)
app.include_router(parts_router.router)
app.include_router(requests_router.router)

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
def root_index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")
