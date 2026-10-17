#!/usr/bin/env python3
"""Add real AcroForm text-field widgets to a flat PDF at given coordinates.

Unlike stamping static text onto a page, this creates interactive form
fields a reader can tap/click and type into on desktop AND mobile PDF
viewers — including iOS's native Files/Quick Look/Mail viewer (Apple's
PDFKit), which needs more than a plain AcroForm widget to treat a field as
genuinely interactive; see the in-function comments for exactly what and
why, diagnosed against a real iPhone plus a known-working reference PDF.
Requires pymupdf: `pip install pymupdf`.

Usage:
    python3 add_form_fields.py <input.pdf> <fields.json> <output.pdf>

fields.json shape:
[
  {
    "page": 6,                          # 1-indexed
    "field_name": "sez1_ex1_line1",     # unique across the whole document
    "rect": [72.0, 380.5, 520.0, 402.0],# [x0, y0, x1, y1] in PyMuPDF page
                                         # space: origin top-left, y
                                         # increasing downward — NOT the
                                         # raw PDF-spec bottom-left-origin
                                         # convention. Matches what
                                         # page.get_text()/draw_line()/
                                         # Widget.rect all use natively.
    "font_size": 11                     # optional, default 11
  },
  ...
]
"""
import base64
import json
import os
import sys

import pymupdf


def add_form_fields(input_path: str, fields_path: str, output_path: str) -> int:
    with open(fields_path, encoding="utf-8") as f:
        fields = json.load(f)

    doc = pymupdf.open(input_path)
    seen_names = set()

    for spec in fields:
        page_number = spec["page"]
        name = spec["field_name"]
        if name in seen_names:
            raise ValueError(f"duplicate field_name {name!r} — field names must be unique")
        seen_names.add(name)

        if not (1 <= page_number <= doc.page_count):
            raise ValueError(f"field {name!r} targets page {page_number}, "
                              f"document has {doc.page_count} pages")
        page = doc[page_number - 1]

        x0, y0, x1, y1 = spec["rect"]
        rect = pymupdf.Rect(x0, y0, x1, y1)
        if rect.is_empty or rect.width <= 0 or rect.height <= 0:
            raise ValueError(f"field {name!r} has a degenerate rect {spec['rect']}")

        widget = pymupdf.Widget()
        widget.field_name = name
        widget.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
        widget.rect = rect
        widget.text_font = "helv"
        widget.text_fontsize = spec.get("font_size", 11)
        widget.border_color = None
        widget.fill_color = None
        widget.field_value = ""
        page.add_widget(widget)

        # Match the structural markers found on a known-working, iOS-fillable
        # PDF (produced by DocFly) that a plain pymupdf widget doesn't set by
        # default. Diagnosed from a real iPhone test: our first two builds
        # rendered fields fine in Acrobat/PyMuPDF but were completely
        # non-interactive in iOS's native Files/Quick Look viewer (PDFKit) —
        # tapping did nothing. DocFly's working file's widgets carry:
        #   - Ff = Multiline(4096) + DoNotSpellCheck(4194304) — ours were
        #     plain single-line (Ff 0). Multiline is also just correct here
        #     regardless of the iOS bug, since these fields are meant to hold
        #     wrapped multi-line answers, not one-line entries.
        #   - an explicit (if empty) /MK appearance-characteristics dict and
        #     /Border [0 0 0], instead of omitting them entirely.
        #   - a private Apple annotation extension key, /AAPL:AKExtras. This
        #     is namespaced to Apple and only appears on PDFKit-authored/
        #     targeted forms — its presence is the strongest candidate for
        #     why PDFKit treats one file as a real form and not the other.
        #     Its content (/PPKID, a per-field opaque token) doesn't look
        #     load-bearing, so a freshly generated placeholder is used here.
        w = next(cand for cand in page.widgets() if cand.field_name == name)
        doc.xref_set_key(w.xref, "Ff", "4198400")
        doc.xref_set_key(w.xref, "MK", "<<>>")
        doc.xref_set_key(w.xref, "Border", "[0 0 0]")
        ppkid = base64.b64encode(os.urandom(16)).decode()
        doc.xref_set_key(w.xref, "AAPL:AKExtras", f"<</PPKID ({ppkid})>>")

    # NeedAppearances=true matches the working reference file; PyMuPDF's own
    # per-field appearance streams are also correct and kept as a fallback
    # for viewers that honor /AP directly instead of regenerating.
    if doc.is_form_pdf and fields:
        first_widget = next(iter(doc[fields[0]["page"] - 1].widgets()))
        _, ap_ref = doc.xref_get_key(first_widget.xref, "AP")
        ap_n_xref = int(ap_ref.replace("<<", "").replace(">>", "")
                         .split("/N")[1].strip().split()[0])
        _, font_ref = doc.xref_get_key(ap_n_xref, "Resources")
        helv_xref = font_ref.split("/Helv")[1].strip().split()[0]

        # The AcroForm dict is stored inline on the catalog (not as its own
        # indirect object), so it has to be rewritten as a whole rather than
        # patched via a separate xref. Pull out the existing /Fields array
        # verbatim and rebuild the dict with /DR + /DA + /NeedAppearances.
        catalog_xref = doc.pdf_catalog()
        _, acro_val = doc.xref_get_key(catalog_xref, "AcroForm")
        fields_start = acro_val.index("/Fields[") + len("/Fields[")
        fields_end = acro_val.index("]", fields_start)
        fields_list = acro_val[fields_start:fields_end]

        new_acroform = (
            f"<</Fields[{fields_list}]"
            f"/DR<</Font<</Helv {helv_xref} 0 R>>>>"
            f"/DA(0 0 0 rg /Helv 10 Tf)"
            f"/NeedAppearances true>>"
        )
        doc.xref_set_key(catalog_xref, "AcroForm", new_acroform)

    doc.save(output_path)
    doc.close()
    return len(fields)


def main() -> None:
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)
    input_path, fields_path, output_path = sys.argv[1:4]
    count = add_form_fields(input_path, fields_path, output_path)
    print(f"Added {count} form field(s). Wrote {output_path}")


if __name__ == "__main__":
    main()
