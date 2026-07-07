"""
Teachable draft-upload step for the workbook pipeline.

Re-exports the PDF from Canva (design_id is the source of truth), creates a
DRAFT lesson in the allowlisted course, uploads the PDF, then sends a
notification email prompting the human to review and publish manually.

The pipeline never calls the Teachable publish endpoint.
"""

from sqlalchemy.orm import Session

from app.config import settings
from app.integrations import canva_client, sendgrid_client, teachable_client
from app.models import JobStatus, WorkbookJob

_DRAFT_READY_EMAIL = """
<html>
<body style="font-family:sans-serif;max-width:600px;margin:auto;padding:24px">
  <h2>Draft lesson ready in Teachable</h2>
  <p><strong>Module:</strong> {module_title}</p>
  <p>The workbook has been approved and uploaded as a <strong>draft lesson</strong>
     in your Teachable course.</p>
  <p>
    <a href="https://app.teachable.com/admin/courses/{course_id}/curriculum"
       style="background:#6366f1;color:#fff;padding:12px 24px;border-radius:6px;text-decoration:none">
      Review &amp; Publish in Teachable →
    </a>
  </p>
  <p style="color:#6b7280;font-size:13px;margin-top:24px">
    The lesson is in <strong>draft mode</strong> and not visible to students until
    you publish it manually inside Teachable admin.
  </p>
</body>
</html>
"""


def upload_draft_to_teachable(job: WorkbookJob, db: Session) -> None:
    job.status = JobStatus.uploading_draft
    db.commit()

    pdf_bytes = canva_client.export_design_pdf(job.canva_design_id)
    filename = f"{job.module_title.replace(' ', '_')}_workbook.pdf"

    lesson_id = teachable_client.create_draft_lesson(
        course_id=job.course_id,
        title=job.module_title,
    )
    teachable_client.upload_lesson_attachment(lesson_id, pdf_bytes, filename)

    job.teachable_lesson_id = lesson_id
    job.status = JobStatus.draft_uploaded
    db.commit()

    sendgrid_client.send_email(
        to=settings.reviewer_email,
        subject=f"[HDH] Draft ready to publish: {job.module_title}",
        html_body=_DRAFT_READY_EMAIL.format(
            module_title=job.module_title,
            course_id=job.course_id,
        ),
    )
