#!/usr/bin/env python3
"""Print each page's size in PDF points, for coordinate conversion.

Usage:
    python3 get_page_sizes.py <input.pdf>
"""
import sys

import pymupdf


def main() -> None:
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    doc = pymupdf.open(sys.argv[1])
    for i, page in enumerate(doc, start=1):
        r = page.rect
        print(f"page {i}: width={r.width} height={r.height}")


if __name__ == "__main__":
    main()
