import logging

from fastapi import FastAPI

from app.api import review, workbook
from app.database import init_db
from app.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Content Workflow Platform",
    description="AI-powered workbook generation and publishing pipeline",
    version="0.1.0",
)

app.include_router(workbook.router)
app.include_router(review.router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    start_scheduler()


@app.on_event("shutdown")
def on_shutdown() -> None:
    stop_scheduler()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
