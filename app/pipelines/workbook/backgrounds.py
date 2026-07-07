"""
Monthly background-photo selection.

The three full-bleed background photos in the Canva template are tagged as image
autofill fields (`sfondo_cover`, `sfondo_pagina2`, `sfondo_impressum`). Each month
we pick a photo from a **curated Canva folder** (configured via
`CANVA_BACKGROUND_FOLDER_ID`) and pass its asset_id to the autofill call.

Selection is deterministic per edition label so that regenerating the same month
always yields the same background (idempotent). If no folder is configured or the
folder is empty, we return None and the template keeps its default photos.

Canva's Connect API cannot browse Canva's own stock library, so backgrounds must
live in the account (uploaded, or added to the folder) — that's what the curated
folder is for.
"""

import hashlib

from app.config import settings
from app.integrations import canva_client

# The image autofill field labels tagged in the template.
BACKGROUND_FIELDS = ("sfondo_cover", "sfondo_pagina2", "sfondo_impressum")


def _stable_index(seed: str, n: int) -> int:
    """A stable, non-salted index in [0, n) derived from `seed`."""
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()
    return int(digest, 16) % n


def pick_background_fields(edition: str) -> dict[str, str] | None:
    """
    Choose the month's background photo(s) from the curated folder.

    Returns a mapping of image-field label -> asset_id, or None if backgrounds
    aren't configured / the folder is empty (caller then keeps template defaults).

    Default strategy: one cohesive photo per edition, applied to all three
    background slots. To vary them independently, assign different indices below.
    """
    folder_id = settings.canva_background_folder_id
    if not folder_id:
        return None

    assets = canva_client.list_folder_image_assets(folder_id)
    if not assets:
        return None

    chosen = assets[_stable_index(edition, len(assets))]
    return {field: chosen for field in BACKGROUND_FIELDS}
