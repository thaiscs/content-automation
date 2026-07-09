"""
Monthly cron entrypoint: generate this month's workbook and email Giusi the link.

Flow (no DB / Redis / Celery / approval web service):
  1. Look up the current month's theme in content_plan.toml
  2. Claude generates the workbook content
  3. Canva autofills the brand template → finished design
  4. Email the Canva EDIT link to the reviewer so Giusi can finish it in Canva

If there's no plan entry for the current month, it emails a heads-up and stops
(never invents a theme). Designed to be run once a month from cron/launchd.

  python scripts/run_monthly.py            # uses today's month
  python scripts/run_monthly.py --month 2026-08   # force a specific month (testing)

Exit codes: 0 = success (or heads-up sent), 1 = failure (surfaces in cron mail/logs).
"""

import argparse
import sys
from datetime import date
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings  # noqa: E402
from app.integrations import canva_client, sendgrid_client  # noqa: E402
from app.pipelines.workbook import backgrounds, content_plan  # noqa: E402
from app.pipelines.workbook.generate import (  # noqa: E402
    generate_workbook_content,
    workbook_to_canva_fields,
)

_READY_EMAIL = """
<html><body style="font-family:sans-serif;max-width:600px;margin:auto;padding:24px">
  <h2>Il workbook di {label} è pronto ✨</h2>
  <p>Ho generato la bozza di questo mese in Canva. Aprila per rivederla,
     modificarla e finalizzarla.</p>
  <p style="margin:24px 0">
    <a href="{edit_url}"
       style="background:#6366f1;color:#fff;padding:12px 24px;border-radius:6px;text-decoration:none">
      ✏️ Apri e modifica in Canva
    </a>
  </p>
  <p style="color:#6b7280;font-size:13px">Tema del mese: {tema}</p>
</body></html>
"""

_NO_PLAN_EMAIL = """
<html><body style="font-family:sans-serif;max-width:600px;margin:auto;padding:24px">
  <h2>Nessun tema pianificato per {label}</h2>
  <p>Non ho trovato una voce per <strong>{key}</strong> in content_plan.toml,
     quindi non ho generato nessun workbook questo mese.</p>
  <p>Aggiungi il tema e gli obiettivi per {label} nel file di pianificazione,
     poi potrò rigenerarlo.</p>
</body></html>
"""


def _notify(subject: str, html: str) -> None:
    if settings.sendgrid_api_key and settings.reviewer_email:
        sendgrid_client.send_email(to=settings.reviewer_email, subject=subject, html_body=html)
    else:
        print(f"[email skipped — SENDGRID_API_KEY/REVIEWER_EMAIL not set]\n  subject: {subject}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Monthly workbook generation + notify")
    parser.add_argument("--month", help='Force month as "YYYY-MM" (default: today)')
    args = parser.parse_args()

    if args.month:
        y, m = args.month.split("-")
        target = date(int(y), int(m), 1)
    else:
        target = date.today()

    edition = content_plan.load_edition(target)

    # No theme planned → heads-up email, exit cleanly.
    if edition is None:
        label = content_plan.edition_label(target)
        key = f"{target.year:04d}-{target.month:02d}"
        print(f"No content-plan entry for {key}. Sending heads-up and stopping.")
        _notify(
            subject=f"[HDH] Nessun tema per {label}",
            html=_NO_PLAN_EMAIL.format(label=label, key=key),
        )
        return

    print(f"Generating workbook for «{edition.label}» — theme: {edition.tema}")
    try:
        content = generate_workbook_content(
            mese=edition.label,
            tema_principale=edition.tema,
            obiettivi=edition.obiettivi,
        )
    except Exception as exc:
        sys.exit(f"✗ Generation failed for {edition.label}: {type(exc).__name__}: {exc}")

    fields = workbook_to_canva_fields(content)
    image_fields = backgrounds.pick_background_fields(edition.label)

    print(f"Autofilling Canva template {settings.canva_template_id} ({len(fields)} fields)…")
    try:
        design_id = canva_client.create_design_from_template(
            fields, image_fields=image_fields, title=f"WB HDH {edition.label}"
        )
    except httpx.HTTPStatusError as exc:
        sys.exit(f"✗ Canva autofill failed: {exc.response.status_code} — {exc.response.text}")
    except Exception as exc:
        sys.exit(f"✗ Canva autofill failed: {type(exc).__name__}: {exc}")

    edit_url = f"https://www.canva.com/design/{design_id}/edit"
    print(f"✓ Design ready: {edit_url}")

    _notify(
        subject=f"[HDH] Workbook {edition.label} pronto",
        html=_READY_EMAIL.format(label=edition.label, edit_url=edit_url, tema=edition.tema),
    )
    print("✓ Notification sent (or skipped if email not configured).")


if __name__ == "__main__":
    main()
