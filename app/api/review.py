from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import JobStatus, ReviewToken

router = APIRouter(prefix="/review", tags=["review"])


def _validate_token(token_id: str, db: Session) -> ReviewToken:
    token = db.get(ReviewToken, token_id)
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    if token.used:
        raise HTTPException(status_code=410, detail="Token already used")
    if token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Token expired")
    return token


@router.get("/{token_id}/approve", response_class=HTMLResponse)
def approve_workbook(token_id: str, db: Session = Depends(get_db)) -> HTMLResponse:
    token = _validate_token(token_id, db)
    token.used = True
    token.job.status = JobStatus.approved
    db.commit()

    return HTMLResponse(
        content="""
        <html><body style="font-family:sans-serif;max-width:600px;margin:auto;padding:48px;text-align:center">
          <h2 style="color:#16a34a">&#10003; Approvato!</h2>
          <p>Il workbook è approvato. Puoi finalizzarlo in Canva.</p>
        </body></html>
        """
    )


@router.get("/{token_id}/reject", response_class=HTMLResponse)
def reject_form(token_id: str, db: Session = Depends(get_db)) -> HTMLResponse:
    _validate_token(token_id, db)
    return HTMLResponse(
        content=f"""
        <html><body style="font-family:sans-serif;max-width:600px;margin:auto;padding:48px">
          <h2>Request Changes</h2>
          <form method="post" action="/review/{token_id}/reject">
            <label style="display:block;margin-bottom:8px;font-weight:600">
              Feedback for Claude:
            </label>
            <textarea name="feedback" rows="6" style="width:100%;padding:8px;font-size:14px"
              placeholder="Describe what needs to change..."></textarea>
            <button type="submit"
              style="margin-top:16px;background:#dc2626;color:#fff;padding:10px 24px;border:none;border-radius:6px;cursor:pointer;font-size:14px">
              Submit &amp; Regenerate
            </button>
          </form>
        </body></html>
        """
    )


@router.post("/{token_id}/reject", response_class=HTMLResponse)
def reject_workbook(
    token_id: str,
    feedback: str = Form(...),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    from app.tasks import reject_workbook as reject_task

    token = _validate_token(token_id, db)
    token.used = True
    token.feedback = feedback
    token.job.status = JobStatus.changes_requested
    db.commit()

    reject_task.delay(token.job_id, feedback)

    return HTMLResponse(
        content="""
        <html><body style="font-family:sans-serif;max-width:600px;margin:auto;padding:48px;text-align:center">
          <h2 style="color:#d97706">&#8635; Regenerating…</h2>
          <p>Feedback received. Claude is generating a revised workbook.
             You will receive a new review email shortly.</p>
        </body></html>
        """
    )
