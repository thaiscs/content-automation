"""
Human review step for the workbook pipeline.

Sends a review email with three options:
  - "Modifica in Canva" → editable Canva link; reviewer edits text/layout in place.
    Edits save against the same design_id, so the approval re-export captures them.
  - "Approva e carica"  → re-exports the CURRENT design state (including any manual
    Canva edits) and uploads the draft to Teachable.
  - "Chiedi a Claude"   → fallback: regenerate the whole workbook with free-text feedback.

Because the approval path always re-exports fresh from Canva, manual edits made in
the Canva editor before approving are picked up automatically — no regeneration needed.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.integrations import canva_client, sendgrid_client
from app.models import JobStatus, ReviewToken, WorkbookJob


_REVIEW_EMAIL_TEMPLATE = """
<html>
<body style="font-family:sans-serif;max-width:600px;margin:auto;padding:24px">
  <h2>Workbook pronto per la revisione</h2>
  <p><strong>Edizione:</strong> {module_title}</p>
  <p>Il workbook è stato generato. Puoi rivederlo, modificarlo direttamente in Canva,
     e poi approvarlo.</p>

  <p style="margin-top:24px">
    <a href="{edit_url}"
       style="background:#6366f1;color:#fff;padding:12px 24px;border-radius:6px;text-decoration:none">
      ✏️ Modifica in Canva
    </a>
  </p>
  <p style="color:#6b7280;font-size:13px;margin-top:4px">
    Apri il design, modifica testo e layout liberamente. Le modifiche si salvano in Canva.
    Quando hai finito, torna a questa email e clicca "Approva e carica".
  </p>

  <hr style="border:none;border-top:1px solid #e5e7eb;margin:28px 0">

  <p>
    <a href="{approve_url}"
       style="background:#16a34a;color:#fff;padding:12px 24px;border-radius:6px;text-decoration:none;margin-right:12px">
      ✓ Approva e carica
    </a>
    <a href="{reject_url}"
       style="background:#dc2626;color:#fff;padding:12px 24px;border-radius:6px;text-decoration:none">
      ↻ Chiedi a Claude di rivedere
    </a>
  </p>
  <p style="color:#6b7280;font-size:13px;margin-top:8px">
    <strong>Approva e carica</strong>: esporta il design attuale (incluse le tue modifiche)
    e lo carica come bozza su Teachable.<br>
    <strong>Chiedi a Claude</strong>: rigenera l'intero workbook in base al tuo feedback.
  </p>

  <p style="color:#9ca3af;font-size:12px;margin-top:28px">
    Questo link scade tra 24 ore.
  </p>
</body>
</html>
"""


def send_review_email(job: WorkbookJob, db: Session, base_url: str, reviewer_email: str) -> None:
    token = ReviewToken(
        job_id=job.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db.add(token)
    db.commit()
    db.refresh(token)

    edit_url = canva_client.get_design_edit_url(job.canva_design_id)
    approve_url = f"{base_url}/review/{token.id}/approve"
    reject_url = f"{base_url}/review/{token.id}/reject"

    html = _REVIEW_EMAIL_TEMPLATE.format(
        module_title=job.module_title,
        edit_url=edit_url,
        approve_url=approve_url,
        reject_url=reject_url,
    )

    sendgrid_client.send_email(
        to=reviewer_email,
        subject=f"[Review] Workbook: {job.module_title}",
        html_body=html,
    )

    job.status = JobStatus.awaiting_review
    db.commit()
