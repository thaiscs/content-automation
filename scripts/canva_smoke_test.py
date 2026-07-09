"""
Canva autofill smoke test — isolated, no DB / Redis / Celery.

Fills the brand template (all 34 fields) with static sample content, runs one
Design Autofill job, and prints the resulting design's edit + view URLs so you
can open it in Canva and confirm every field populated.

No PDF export, no download.

Prerequisite: run `python scripts/canva_auth.py` first to authorize.

  python scripts/canva_smoke_test.py
"""

import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings  # noqa: E402
from app.integrations import canva_client  # noqa: E402
from app.pipelines.workbook.generate import (  # noqa: E402
    Esercizio,
    Sezione,
    WorkbookContent,
    workbook_to_canva_fields,
)

# A block of filler roughly sized to the body budgets, so the pages look filled
# and you can confirm the boxes hold the expected amount of text.
_FILLER = (
    "Questo è testo di prova per lo smoke test, scritto per riempire la casella "
    "e verificare che il campo autofill riceva il contenuto corretto e che il "
    "layout tenga la lunghezza prevista senza traboccare oltre i margini. "
)


def _sample_content() -> WorkbookContent:
    """Static sample matching the current 34-field model — recognizable markers."""
    sezioni = [
        Sezione(
            numero=n,
            titolo=f"[S{n}] Sottotitolo di prova",
            citazione=f"[S{n}] Citazione ispirazionale di prova.",
            corpo=[f"[S{n} col1] {_FILLER}", f"[S{n} col2] {_FILLER}"],
            esercizi_intro=f"Esercizi – Sezione {n} (prova)",
            esercizi=[
                Esercizio(
                    titolo=f"[S{n}] Esercizio {m} — titolo",
                    prompt=f"[S{n}] Esercizio {m} — prompt di riflessione?",
                )
                for m in range(1, 5)
            ],
        )
        for n in range(1, 5)
    ]

    return WorkbookContent(
        cover_title="SMOKE TEST — COVER TITLE",
        cover_subtitle="Sottotitolo di copertina di prova",
        mantra_testo="Mantra di prova per lo smoke test.",
        intenzione_testo="Intenzione di prova per lo smoke test.",
        lettera_corpo=[f"[lettera col1] {_FILLER}", f"[lettera col2] {_FILLER} Namaste,"],
        sezioni=sezioni,
        integrazione_corpo=[f"[integrazione col1] {_FILLER}", f"[integrazione col2] {_FILLER}"],
        esercizio_finale_titolo="Esercizio finale – prova",
        esercizio_finale_completamenti=[
            "Oggi scelgo di abitare di più...",
            "Sono pronta a lasciare andare...",
        ],
        completamenti=[
            "La mia femminilità per me ora è...",
            "La mia sensualità può diventare...",
            "Da oggi mi permetto di...",
        ],
        completamenti_chiusura="Sei pronta. Porta con te questa verità.",
    )


def main() -> None:
    if not settings.canva_template_id:
        sys.exit("CANVA_TEMPLATE_ID is not set in .env.")

    content = _sample_content()
    fields = workbook_to_canva_fields(content)
    print(f"Prepared {len(fields)} autofill fields (expected 34).")
    if len(fields) != 34:
        print("  ⚠️  Field count is not 34 — check workbook_to_canva_fields().")

    print(f"Running autofill on brand template {settings.canva_template_id} …")
    print("(polls every 2s; typically completes in 5–15s)")
    try:
        design_id = canva_client.create_design_from_template(
            data_fields=fields,
            title="SMOKE TEST — workbook autofill",
        )
    except httpx.HTTPStatusError as exc:
        # Canva returns a JSON body with the real reason (code + message).
        sys.exit(
            f"\n✗ Autofill failed: {exc.response.status_code} on {exc.request.url}\n"
            f"  body: {exc.response.text}\n"
        )
    except Exception as exc:  # surface any other raw error for debugging
        sys.exit(f"\n✗ Autofill failed: {type(exc).__name__}: {exc}")

    print("\n✓ Autofill succeeded.")
    print(f"  design_id: {design_id}")
    print(f"  Edit:  https://www.canva.com/design/{design_id}/edit")
    print(f"  View:  https://www.canva.com/design/{design_id}/view")
    print("\nOpen the Edit URL and confirm all 57 fields are populated with the")
    print("[Sezione N] / SMOKE TEST placeholder text.")


if __name__ == "__main__":
    main()
