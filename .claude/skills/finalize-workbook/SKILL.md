---
name: finalize-workbook
description: Turn an already-approved HDH workbook Canva design into a fillable PDF — real form fields a reader can type into on desktop or mobile, laid over the answer lines. Use when Giusi says a workbook is approved/finalized and asks to make it fillable, or when the user runs /finalize-workbook. Never run this on a design that hasn't been explicitly approved — this is a separate, later step from /generate-workbook, triggered by a human decision, not by content generation finishing.
---

# Finalize the HDH workbook into a fillable PDF

This is **step two** of the workbook pipeline, and it is gated on a human
decision: `generate-workbook` drafts content and fills the Canva template,
then hands Giusi a Canva edit URL to review and finalize by hand. Only
once she has approved that design does this skill run — turning the
approved design into a PDF with real AcroForm text fields over its answer
lines, so the person using the workbook can type into it on their phone or
laptop instead of needing to print and handwrite.

**Never run this unprompted.** If you generated a workbook earlier in this
conversation, that is not approval — wait for an explicit "this is
approved" / "make it fillable" / `/finalize-workbook` from Giusi before
touching it.

## Inputs

You need a specific Canva design to work from. Giusi will give you one of:
- A Canva edit/view URL (e.g. `https://www.canva.com/design/<design_id>/edit`), or
- A `design_id` directly, or
- Just a month — in which case **ask her for the Canva URL**; there is no
  stored record of which design_id belongs to which month (each
  `generate-workbook` run is a fresh, unlinked session), so guessing is not
  safe here.

If she gives a bare month with no URL and can't produce one, stop and ask —
do not search Canva designs by title as a substitute; get it wrong here and
you ship the wrong month's PDF as fillable.

## Steps

1. **Confirm before acting.** State back which design (title + URL) you're
   about to export and finalize, and confirm this is the approved version —
   a one-line check, not a big ceremony. This step is irreversible in the
   sense that it produces a deliverable meant to go out to workbook users;
   catch a wrong-design mistake here, not after.

2. **Export the flat PDF.** `mcp__Canva__get-export-formats` to confirm PDF
   is supported for this design, then `mcp__Canva__export-design` with
   `format.type: "pdf"`. Download the result locally (e.g. into
   `out/workbook-<YYYY-MM>-flat.pdf`, or the scratchpad if this run doesn't
   need it kept).

3. **Get answer-line coordinates.** Follow
   `references/coordinate_extraction.md` in full. For this template, the
   answer lines aren't separate Canva elements — they're one long dot-run
   per answer that word-wraps — so the real method is
   `scripts/detect_dotlines.py <flat.pdf>`, which finds those dot-runs
   directly in the exported PDF and groups each answer's wrapped sub-lines
   into one bounding box. Build a `fields.json` (see that script's
   docstring in `scripts/add_form_fields.py` for the exact shape) with one
   *merged* field per answer (not per wrapped sub-line), named per the
   convention in that reference doc.

4. **Validate the field map.** `python3 scripts/check_fields.py
   fields.json`. Fix everything it reports (duplicate names, degenerate or
   overlapping rects) before continuing — don't hand-wave past a reported
   overlap.

5. **Author the fields.**
   ```
   pip install pymupdf   # if not already available in this session
   python3 scripts/add_form_fields.py <flat.pdf> fields.json <fillable.pdf>
   ```
   This creates real AcroForm text-field widgets (not XFA, not static
   annotations) — the kind Acrobat, Preview, Chrome/Edge's built-in
   viewers, and mobile Adobe Reader all render as tappable/typeable.

6. **Verify visually.** `python3 scripts/render_with_fields.py <fillable.pdf>
   <out_dir>` renders every page that has fields, with each field's rect
   drawn as a red outline, and prints the per-page field count. Read those
   images (the `Read` tool handles PNGs directly) and check every field
   sits on its line, none overlap the prompt text above it, and the page
   count of fields matches what you expect (4 lines × 4 exercises × 4
   sections, plus the completions pages — recompute the exact expected
   count from the actual field map you built, don't assume a fixed number
   blindly). If anything's off, fix `fields.json` and redo steps 4–6 rather
   than shipping a visibly wrong overlay.

7. **Deliver.** Send the fillable PDF back in this session
   (`SendUserFile`, status `normal` since this follows a direct request).
   Report: how many fields, on which pages, and which coordinate tier
   (Canva geometry vs. detected lines vs. visual estimate) you used — so
   Giusi knows how much to spot-check on her own device before it goes
   out. Nothing is archived automatically; this session's file card is the
   deliverable.

## Notes

- This skill has no relationship to Canva's own export formats — Canva
  does not support exporting interactive/fillable PDFs (its `pdf` export
  is always flat); the fillable layer is always added afterward, locally,
  by `add_form_fields.py`.
- Coordinates are expected to be stable release-to-release, since the
  template layout is fixed — but re-derive them (don't hardcode a
  months-old `fields.json`) each time, since a template edit in Canva
  would silently desync a cached coordinate file from the real answer-line
  positions.
- **A plain AcroForm widget is not enough to be tappable in iOS's native
  PDF viewer (Files/Quick Look/Mail — Apple's PDFKit).** This was found the
  hard way: the first two builds of this pipeline rendered fields correctly
  in Acrobat and PyMuPDF but were completely inert on a real iPhone —
  visible, but tapping did nothing. Diagnosed by comparing against a
  known-working, iOS-fillable reference PDF (produced by DocFly) field by
  field. `add_form_fields.py` now reproduces the markers that turned out to
  matter: the `Multiline` field flag, an explicit `/MK` + `/Border` on each
  widget, `NeedAppearances: true` plus a proper top-level `/DR`/`/DA` on the
  AcroForm dict, and — the key one — a private Apple annotation extension
  key, `/AAPL:AKExtras`, that only appears on PDFKit-authored/targeted
  forms. None of this is exotic or fragile; it's just what a real
  interactive PDF form needs to carry for Apple's viewer specifically, and
  it's now baked into the script — nothing more to do here on future runs
  unless Apple changes what PDFKit expects. If a future run produces a PDF
  that again renders but doesn't respond to taps on iOS, re-run this same
  diff-against-a-working-reference approach rather than guessing from
  scratch — get a fillable PDF known to work on the affected device and
  compare its widget dict against `add_form_fields.py`'s output.
