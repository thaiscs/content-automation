"""
Canva design step for the workbook pipeline.

Takes a WorkbookContent, populates the brand template via Design Autofill,
and stores the design_id on the job. PDFs are exported on demand — never stored.
"""

from sqlalchemy.orm import Session

from app.integrations import canva_client
from app.models import WorkbookJob
from app.pipelines.workbook import backgrounds
from app.pipelines.workbook.generate import WorkbookContent, workbook_to_canva_fields


def create_workbook_design(
    job: WorkbookJob,
    content: WorkbookContent,
    db: Session,
) -> str:
    """
    Create a Canva design from the workbook content and save the design_id.
    Returns the design_id.
    """
    fields = workbook_to_canva_fields(content)

    # Pick this month's background photo(s) from the curated Canva folder, if set.
    image_fields = backgrounds.pick_background_fields(job.module_title)

    # Name the design after the edition so it's identifiable in Canva instead of
    # inheriting the brand template's name. Append the iteration on revisions.
    title = f"WB HDH {job.module_title}"
    if job.iteration > 1:
        title += f" (v{job.iteration})"

    design_id = canva_client.create_design_from_template(
        fields, image_fields=image_fields, title=title
    )

    job.canva_design_id = design_id
    db.commit()

    return design_id
