#!/usr/bin/env python3
"""Sanity-check a fields.json before running add_form_fields.py.

Flags: degenerate/inverted rects, and any two rects on the same page that
overlap (the most common way a coordinate-extraction pass goes wrong).

Usage:
    python3 check_fields.py <fields.json>
Exits non-zero if any problem is found.
"""
import json
import sys


def rects_intersect(a, b):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    disjoint_horizontal = ax0 >= bx1 or ax1 <= bx0
    disjoint_vertical = ay0 >= by1 or ay1 <= by0
    return not (disjoint_horizontal or disjoint_vertical)


def check(fields_path: str) -> int:
    with open(fields_path, encoding="utf-8") as f:
        fields = json.load(f)

    problems = []
    seen_names = set()

    for spec in fields:
        name = spec.get("field_name", "<unnamed>")
        if name in seen_names:
            problems.append(f"duplicate field_name {name!r}")
        seen_names.add(name)

        x0, y0, x1, y1 = spec["rect"]
        if x1 <= x0 or y1 <= y0:
            problems.append(f"{name!r}: degenerate/inverted rect {spec['rect']}")

    by_page = {}
    for spec in fields:
        by_page.setdefault(spec["page"], []).append(spec)

    for page, page_fields in by_page.items():
        for i, a in enumerate(page_fields):
            for b in page_fields[i + 1:]:
                if rects_intersect(a["rect"], b["rect"]):
                    problems.append(
                        f"page {page}: {a['field_name']!r} {a['rect']} overlaps "
                        f"{b['field_name']!r} {b['rect']}"
                    )

    print(f"Checked {len(fields)} field(s) across {len(by_page)} page(s).")
    if problems:
        print(f"{len(problems)} problem(s):")
        for p in problems:
            print(f"  FAILURE: {p}")
        return 1
    print("No problems found.")
    return 0


def main() -> None:
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    sys.exit(check(sys.argv[1]))


if __name__ == "__main__":
    main()
