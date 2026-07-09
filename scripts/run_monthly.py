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
from app.integrations import canva_client  # noqa: E402
from app.pipelines.workbook import backgrounds, content_plan, notify  # noqa: E402
from app.pipelines.workbook.generate import (  # noqa: E402
    generate_workbook_content,
    workbook_to_canva_fields,
)


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
        notify.send_no_plan(edition_label=label, key=key)
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

    notify.send_ready(edition_label=edition.label, edit_url=edit_url, tema=edition.tema)
    print("✓ Notification sent (or skipped if email not configured).")


if __name__ == "__main__":
    main()
