#!/usr/bin/env python3
"""Render pages of a PDF to PNG, with any AcroForm widget rects drawn as
red outlines, so a human (or Claude, reading the image) can visually check
that each field actually sits on top of its intended answer line.

Usage:
    python3 render_with_fields.py <input.pdf> <output_dir> [page numbers...]

With no page numbers, renders every page that has at least one form field.
"""
import sys
from pathlib import Path

import pymupdf


def main() -> None:
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    input_path = sys.argv[1]
    out_dir = Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)
    requested_pages = {int(p) for p in sys.argv[3:]} if len(sys.argv) > 3 else None

    doc = pymupdf.open(input_path)
    zoom = 2.0
    matrix = pymupdf.Matrix(zoom, zoom)

    rendered = 0
    for i, page in enumerate(doc, start=1):
        widgets = list(page.widgets())
        if requested_pages is not None:
            if i not in requested_pages:
                continue
        elif not widgets:
            continue

        for w in widgets:
            page.draw_rect(w.rect, color=(1, 0, 0), width=1)

        pix = page.get_pixmap(matrix=matrix)
        out_path = out_dir / f"page_{i:02d}.png"
        pix.save(out_path)
        print(f"page {i}: {len(widgets)} field(s) -> {out_path}")
        rendered += 1

    if rendered == 0:
        print("No pages rendered (no fields found and no page numbers given).")


if __name__ == "__main__":
    main()
