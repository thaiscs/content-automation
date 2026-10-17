#!/usr/bin/env python3
"""Detect answer-line positions in a flat PDF by finding runs of dot glyphs.

For this template the printed "answer lines" are not separate Canva
elements — each is one long unbroken run of period characters (e.g. 458
dots) that word-wraps into several visual sub-lines. This script finds
those sub-lines in the exported flat PDF by inspecting actual rendered text
positions, then groups consecutive sub-lines that belong to the same answer
into one bounding box — this is what should become one fillable field.

Usage:
    python3 detect_dotlines.py <flat.pdf>
Prints, per page, one bounding box per detected answer block, grouped from
its wrapped dot sub-lines. Pipe through your own script (or edit this one)
to attach field names and write fields.json — field naming depends on your
content's page layout, which this script has no way to know.
"""
import json
import sys

import pymupdf


def is_dotline(text: str) -> bool:
    s = text.strip()
    if len(s) < 20:
        return False
    dots = sum(1 for c in s if c == ".")
    return dots / len(s) > 0.9


def find_dotline_groups(pdf_path: str, gap_threshold: float = 15.0):
    """Returns {page_number (1-indexed): [group_bbox, ...]} where each
    group_bbox is [x0, y0, x1, y1] in PyMuPDF page space (origin top-left,
    y increasing downward — the same convention add_form_fields.py expects,
    since both are pymupdf-native)."""
    doc = pymupdf.open(pdf_path)
    results = {}

    for pno in range(len(doc)):
        page = doc[pno]
        d = page.get_text("dict")
        dotlines = []
        for block in d["blocks"]:
            for line in block.get("lines", []):
                text = "".join(span["text"] for span in line["spans"])
                if is_dotline(text):
                    dotlines.append(line["bbox"])
        if not dotlines:
            continue

        dotlines.sort(key=lambda b: b[1])
        groups = [[dotlines[0]]]
        for b in dotlines[1:]:
            prev = groups[-1][-1]
            if b[1] - prev[3] < gap_threshold:
                groups[-1].append(b)
            else:
                groups.append([b])

        group_bboxes = []
        for g in groups:
            x0 = min(b[0] for b in g)
            y0 = min(b[1] for b in g)
            x1 = max(b[2] for b in g)
            y1 = max(b[3] for b in g)
            group_bboxes.append([round(x0, 1), round(y0, 1), round(x1, 1), round(y1, 1)])

        results[pno + 1] = group_bboxes

    return results


def main() -> None:
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    results = find_dotline_groups(sys.argv[1])
    for page, groups in results.items():
        print(f"page {page}: {len(groups)} answer block(s)")
        for bbox in groups:
            print("   ", bbox)
    print()
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
