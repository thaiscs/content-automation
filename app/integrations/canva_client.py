"""
Canva Connect API client.

Handles OAuth 2.0 client-credentials auth, Design Autofill (populate a branded
template with structured content), and PDF export. The design_id is the only
persistent reference stored — PDFs are always re-exported on demand.

Docs: https://www.canva.com/developers/docs/connect/
"""

import time

import httpx

from app.config import settings

_CANVA_API_BASE = "https://api.canva.com/rest/v1"
_token_cache: dict = {}


def _get_access_token() -> str:
    now = time.time()
    if _token_cache.get("expires_at", 0) > now + 60:
        return _token_cache["token"]

    resp = httpx.post(
        "https://api.canva.com/rest/v1/oauth/token",
        data={
            "grant_type": "client_credentials",
            "client_id": settings.canva_client_id,
            "client_secret": settings.canva_client_secret,
            "scope": "design:content:write design:content:read",
        },
    )
    resp.raise_for_status()
    data = resp.json()
    _token_cache["token"] = data["access_token"]
    _token_cache["expires_at"] = now + data.get("expires_in", 3600)
    return _token_cache["token"]


def _headers() -> dict:
    return {"Authorization": f"Bearer {_get_access_token()}"}


def create_design_from_template(
    data_fields: dict[str, str],
    image_fields: dict[str, str] | None = None,
    title: str | None = None,
) -> str:
    """
    Trigger a Design Autofill job using the configured template.
    `data_fields` maps text placeholder names to string values.
    `image_fields`, if given, maps image placeholder names to Canva asset IDs
    (the background photos live in the account and are referenced by asset_id).
    `title`, if given, names the resulting design (otherwise it inherits the
    brand template's name). Returns the new design_id.
    """
    data: dict = {k: {"type": "text", "text": v} for k, v in data_fields.items()}
    for label, asset_id in (image_fields or {}).items():
        if asset_id:
            data[label] = {"type": "image", "asset_id": asset_id}

    payload: dict = {
        "brand_template_id": settings.canva_template_id,
        "data": data,
    }
    if title:
        # Canva limits design titles to 255 characters.
        payload["title"] = title[:255]
    resp = httpx.post(
        f"{_CANVA_API_BASE}/autofills",
        json=payload,
        headers=_headers(),
    )
    resp.raise_for_status()
    job = resp.json()
    job_id = job["job"]["id"]

    # Poll until the autofill job completes
    for _ in range(30):
        time.sleep(2)
        status_resp = httpx.get(
            f"{_CANVA_API_BASE}/autofills/{job_id}",
            headers=_headers(),
        )
        status_resp.raise_for_status()
        result = status_resp.json()
        if result["job"]["status"] == "success":
            return result["job"]["result"]["design"]["id"]
        if result["job"]["status"] == "failed":
            raise RuntimeError(f"Canva autofill job failed: {result}")

    raise TimeoutError("Canva autofill job did not complete within timeout")


def export_design_pdf(design_id: str) -> bytes:
    """Export a design as PDF and return the raw bytes."""
    resp = httpx.post(
        f"{_CANVA_API_BASE}/exports",
        json={"design_id": design_id, "format": "pdf"},
        headers=_headers(),
    )
    resp.raise_for_status()
    job_id = resp.json()["job"]["id"]

    for _ in range(30):
        time.sleep(2)
        status_resp = httpx.get(
            f"{_CANVA_API_BASE}/exports/{job_id}",
            headers=_headers(),
        )
        status_resp.raise_for_status()
        result = status_resp.json()
        if result["job"]["status"] == "success":
            pdf_url = result["job"]["urls"][0]
            pdf_resp = httpx.get(pdf_url)
            pdf_resp.raise_for_status()
            return pdf_resp.content
        if result["job"]["status"] == "failed":
            raise RuntimeError(f"Canva export job failed: {result}")

    raise TimeoutError("Canva export job did not complete within timeout")


def list_folder_image_assets(folder_id: str) -> list[str]:
    """
    Return the asset IDs of the images stored in a Canva folder (paginated).

    Used to source the monthly background photos from a curated folder. Only
    image assets are returned; sub-folders and designs are ignored.
    """
    asset_ids: list[str] = []
    continuation: str | None = None
    for _ in range(20):  # safety bound on pagination
        params = {"continuation": continuation} if continuation else {}
        resp = httpx.get(
            f"{_CANVA_API_BASE}/folders/{folder_id}/items",
            params=params,
            headers=_headers(),
        )
        resp.raise_for_status()
        body = resp.json()
        for item in body.get("items", []):
            # Folder items nest the resource under a key matching their type;
            # image assets expose an `asset` (or `image`) object with an `id`.
            obj = item.get("asset") or item.get("image") or {}
            asset_id = obj.get("id") or obj.get("asset_id")
            if asset_id and item.get("type") in (None, "asset", "image"):
                asset_ids.append(asset_id)
        continuation = body.get("continuation")
        if not continuation:
            break
    return asset_ids


def get_design_share_url(design_id: str) -> str:
    """Return a read-only shareable view URL for the design."""
    resp = httpx.get(f"{_CANVA_API_BASE}/designs/{design_id}", headers=_headers())
    resp.raise_for_status()
    return resp.json()["design"]["urls"]["view_url"]


def get_design_edit_url(design_id: str) -> str:
    """
    Return the editable Canva URL for the design.

    Opening this lets the reviewer edit text and layout directly in Canva.
    Edits save in place against the same design_id, so the next PDF export
    (triggered on approval) automatically reflects them — no regeneration needed.
    The reviewer must be signed in to the Canva account that owns the design.
    """
    resp = httpx.get(f"{_CANVA_API_BASE}/designs/{design_id}", headers=_headers())
    resp.raise_for_status()
    return resp.json()["design"]["urls"]["edit_url"]
