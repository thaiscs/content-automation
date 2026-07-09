import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import JobStatus, WorkbookJob

router = APIRouter(prefix="/workbooks", tags=["workbooks"])


class GenerateRequest(BaseModel):
    mese: str                  # e.g. "Giugno 2026"
    tema_principale: str       # e.g. "femminilità e sensualità come forza vitale"
    obiettivi: str             # learning objectives for this edition


class JobResponse(BaseModel):
    job_id: str
    status: str


@router.post("/generate", response_model=JobResponse, status_code=202)
def generate_workbook(body: GenerateRequest, db: Session = Depends(get_db)) -> JobResponse:
    from app.tasks import run_workbook_pipeline

    job = WorkbookJob(
        id=str(uuid.uuid4()),
        module_title=body.mese,
        learning_objectives=f"{body.tema_principale} | {body.obiettivi}",
        status=JobStatus.pending,
    )
    db.add(job)
    db.commit()

    run_workbook_pipeline.delay(job.id)
    return JobResponse(job_id=job.id, status=job.status.value)


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: str, db: Session = Depends(get_db)) -> JobResponse:
    job = db.get(WorkbookJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse(job_id=job.id, status=job.status.value)
