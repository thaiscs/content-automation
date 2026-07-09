"""
Full local end-to-end run: Claude generation → Canva autofill → finished design.

No DB / Redis / Celery / email — just the content core. Proves that
Claude produces a valid workbook and Canva renders it, before any hosting work.

Prerequisites:
  - ANTHROPIC_API_KEY set in .env
  - Canva authorized (scripts/canva_auth.py already run)
  - CANVA_TEMPLATE_ID set

Usage:
  python scripts/run_local.py
  python scripts/run_local.py --mese "Luglio 2026" \
      --tema "il coraggio di scegliere se stesse" \
      --obiettivi "riconoscere i propri desideri e agire con intenzione"
"""

import argparse
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings  # noqa: E402
from app.integrations import canva_client  # noqa: E402
from app.pipelines.workbook import backgrounds  # noqa: E402
from app.pipelines.workbook.generate import (  # noqa: E402
    check_budgets,
    generate_workbook_content,
    workbook_to_canva_fields,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Local generate → Canva autofill test")
    parser.add_argument("--mese", default="Luglio 2026", help="Edition label")
    parser.add_argument(
        "--tema",
        default="la femminilità e la sensualità come forza vitale",
        help="Core theme",
    )
    parser.add_argument(
        "--obiettivi",
        default="riconnettersi al proprio corpo e alla propria energia femminile",
        help="Learning objectives",
    )
    args = parser.parse_args()

    if not settings.anthropic_api_key:
        sys.exit("ANTHROPIC_API_KEY is not set in .env — generation can't run.")
    if not settings.canva_template_id:
        sys.exit("CANVA_TEMPLATE_ID is not set in .env.")

    print(f"1/3  Generating content with Claude for «{args.mese}» …")
    print("     (this includes up to 2 length-fix passes; ~20-40s)")
    try:
        content = generate_workbook_content(
            mese=args.mese,
            tema_principale=args.tema,
            obiettivi=args.obiettivi,
        )
    except Exception as exc:
        sys.exit(f"\n✗ Generation failed: {type(exc).__name__}: {exc}")

    fields = workbook_to_canva_fields(content)
    print(f"     ✓ Generated {len(fields)} fields. Cover: «{content.cover_title}»")

    # Report page-fill status (informational — doesn't block)
    violations = check_budgets(fields)
    if violations:
        print(f"     ⚠️  {len(violations)} body field(s) outside length budget:")
        for field, length, lo, hi in violations:
            print(f"        - {field}: {length} chars (target {lo}-{hi})")
    else:
        print("     ✓ All body fields within their length budgets.")

    print("2/3  Selecting background photo(s) …")
    image_fields = backgrounds.pick_background_fields(args.mese)
    if image_fields:
        print(f"     ✓ Using curated background asset for {len(image_fields)} slots.")
    else:
        print("     · No background folder configured — keeping template defaults.")

    print(f"3/3  Running Canva autofill on template {settings.canva_template_id} …")
    title = f"WB HDH {args.mese}"
    try:
        design_id = canva_client.create_design_from_template(
            fields, image_fields=image_fields, title=title
        )
    except httpx.HTTPStatusError as exc:
        sys.exit(
            f"\n✗ Autofill failed: {exc.response.status_code} on {exc.request.url}\n"
            f"  body: {exc.response.text}\n"
        )
    except Exception as exc:
        sys.exit(f"\n✗ Autofill failed: {type(exc).__name__}: {exc}")

    print("\n✓ Done — full workbook generated and rendered in Canva.")
    print(f"  design_id: {design_id}")
    print(f"  Edit:  https://www.canva.com/design/{design_id}/edit")
    print(f"  View:  https://www.canva.com/design/{design_id}/view")
    print("\nOpen the Edit URL and review the real generated content in the layout.")


if __name__ == "__main__":
    main()
