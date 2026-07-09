"""
Celery tasks for the workbook pipeline.

Task chain for a new workbook run:
  run_workbook_pipeline → (async) design + review email

Approval path:
  approve_workbook → mark approved (the workbook is finished by hand in Canva)

Rejection path:
  reject_workbook → run_workbook_pipeline (with feedback, incremented iteration)
"""

import logging

from app.celery_app import celery
from app.config import settings
from app.database import SessionLocal
from app.models import JobStatus, WorkbookJob
from app.pipelines.workbook import design, generate, review

logger = logging.getLogger(__name__)


@celery.task(bind=True, max_retries=3)
def run_workbook_pipeline(
    self,
    job_id: str,
    reviewer_feedback: str | None = None,
) -> None:
    db = SessionLocal()
    try:
        job = db.get(WorkbookJob, job_id)
        if not job:
            logger.error("WorkbookJob %s not found", job_id)
            return

        job.status = JobStatus.generating
        db.commit()

        # learning_objectives stores "tema | obiettivi" — split on first pipe
        parts = job.learning_objectives.split(" | ", 1)
        tema = parts[0]
        obiettivi = parts[1] if len(parts) > 1 else parts[0]

        content = generate.generate_workbook_content(
            mese=job.module_title,
            tema_principale=tema,
            obiettivi=obiettivi,
            reviewer_feedback=reviewer_feedback,
        )

        design.create_workbook_design(job, content, db)

        review.send_review_email(
            job=job,
            db=db,
            base_url=settings.base_url,
            reviewer_email=settings.reviewer_email,
        )

    except Exception as exc:
        logger.exception("Pipeline failed for job %s", job_id)
        db.rollback()
        job = db.get(WorkbookJob, job_id)
        if job:
            job.status = JobStatus.failed
            job.error_message = str(exc)
            db.commit()
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()


@celery.task
def approve_workbook(job_id: str) -> None:
    db = SessionLocal()
    try:
        job = db.get(WorkbookJob, job_id)
        if not job:
            return
        # No downstream publish — the approved workbook is finished by hand in Canva.
        job.status = JobStatus.approved
        db.commit()
    finally:
        db.close()


@celery.task
def reject_workbook(job_id: str, feedback: str) -> None:
    db = SessionLocal()
    try:
        job = db.get(WorkbookJob, job_id)
        if not job:
            return

        if job.iteration >= settings.max_regeneration_iterations:
            logger.warning(
                "Job %s hit max regeneration iterations (%d)",
                job_id,
                settings.max_regeneration_iterations,
            )
            job.status = JobStatus.failed
            job.error_message = f"Max regeneration iterations ({settings.max_regeneration_iterations}) reached."
            db.commit()
            return

        job.iteration += 1
        job.status = JobStatus.changes_requested
        db.commit()

    finally:
        db.close()

    run_workbook_pipeline.delay(job_id, reviewer_feedback=feedback)
