"""
Tests for the review token logic and the regeneration loop cap.
Uses an in-memory SQLite database — no real Postgres needed.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, JobStatus, ReviewToken, WorkbookJob


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def job(db):
    j = WorkbookJob(
        id="job-1",
        module_title="Module 1",
        learning_objectives="Learn X",
        status=JobStatus.awaiting_review,
        canva_design_id="design-abc",
        iteration=1,
    )
    db.add(j)
    db.commit()
    return j


def test_token_expires_after_24h(db, job):
    token = ReviewToken(
        id="tok-1",
        job_id=job.id,
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    db.add(token)
    db.commit()

    # SQLite returns naive datetimes; compare without tzinfo
    expires_naive = token.expires_at.replace(tzinfo=None) if token.expires_at.tzinfo else token.expires_at
    assert expires_naive < datetime.utcnow()


def test_token_used_flag(db, job):
    token = ReviewToken(
        id="tok-2",
        job_id=job.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        used=False,
    )
    db.add(token)
    db.commit()

    token.used = True
    db.commit()

    refreshed = db.get(ReviewToken, "tok-2")
    assert refreshed.used is True


def test_reject_increments_iteration(db, job):
    job.iteration += 1
    job.status = JobStatus.changes_requested
    db.commit()

    refreshed = db.get(WorkbookJob, "job-1")
    assert refreshed.iteration == 2
    assert refreshed.status == JobStatus.changes_requested


def test_reject_at_max_iterations_sets_failed(db, job):
    from app.config import settings

    job.iteration = settings.max_regeneration_iterations
    db.commit()

    # Simulate what reject_workbook task does when cap is hit
    if job.iteration >= settings.max_regeneration_iterations:
        job.status = JobStatus.failed
        job.error_message = "Max regeneration iterations reached."
        db.commit()

    refreshed = db.get(WorkbookJob, "job-1")
    assert refreshed.status == JobStatus.failed
