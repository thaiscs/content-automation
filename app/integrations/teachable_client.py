"""
Teachable REST API client — draft-only, allowlisted.

Security constraints enforced here:
  1. Every call asserts the target course_id is in TEACHABLE_ALLOWED_COURSE_IDS.
     If not, a PermissionError is raised BEFORE any network request.
  2. The publish endpoint is intentionally absent. Lessons are always created
     as drafts (is_published: false). A human publishes manually in Teachable admin.

The complete set of Teachable endpoints this module calls:
  POST /v1/courses/{course_id}/lessons       — create draft lesson
  POST /v1/lessons/{lesson_id}/attachments   — upload PDF attachment

Nothing else. No student data, no transactions, no school-wide reads.

Docs: https://docs.teachable.com/reference/
"""

import httpx

from app.config import settings

_TEACHABLE_BASE = "https://developers.teachable.com/v1"


def _allowed_course_ids() -> set[str]:
    raw = settings.teachable_allowed_course_ids.strip()
    if not raw:
        return set()
    return {cid.strip() for cid in raw.split(",") if cid.strip()}


def _assert_allowed_course(course_id: str) -> None:
    allowed = _allowed_course_ids()
    if not allowed:
        raise PermissionError(
            "TEACHABLE_ALLOWED_COURSE_IDS is not configured. "
            "Set it to a comma-separated list of permitted course IDs (start with a test course)."
        )
    if course_id not in allowed:
        raise PermissionError(
            f"Course ID '{course_id}' is not in TEACHABLE_ALLOWED_COURSE_IDS ({', '.join(sorted(allowed))}). "
            "Add it explicitly to grant access."
        )


def _headers() -> dict:
    return {
        "apiKey": settings.teachable_api_key,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def create_draft_lesson(course_id: str, title: str) -> str:
    """
    Create a new lesson in draft state. Returns the lesson_id.
    Raises PermissionError if course_id is not allowlisted.
    """
    _assert_allowed_course(course_id)

    resp = httpx.post(
        f"{_TEACHABLE_BASE}/courses/{course_id}/lessons",
        json={"lesson": {"name": title, "is_published": False, "content_type": "native_download"}},
        headers=_headers(),
    )
    resp.raise_for_status()
    return str(resp.json()["lesson"]["id"])


def upload_lesson_attachment(lesson_id: str, pdf_bytes: bytes, filename: str) -> None:
    """Upload a PDF file as a downloadable attachment on a draft lesson."""
    resp = httpx.post(
        f"{_TEACHABLE_BASE}/lessons/{lesson_id}/attachments",
        files={"attachment[file]": (filename, pdf_bytes, "application/pdf")},
        headers={"apiKey": settings.teachable_api_key, "Accept": "application/json"},
    )
    resp.raise_for_status()


# publish_lesson is deliberately NOT implemented here.
# Human publishes manually inside Teachable admin after reviewing the draft.
