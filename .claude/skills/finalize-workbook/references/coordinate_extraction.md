# Finding answer-line coordinates

`add_form_fields.py` needs a `fields.json` of `{page, field_name, rect}`,
`rect` in **PyMuPDF page space**: origin top-left, y increasing downward
(the same convention `page.get_text()`, `page.draw_line()`, and
`Widget.rect` all use — not the raw PDF-spec bottom-left-origin convention).
Since every script here is PyMuPDF end to end, coordinates never need
flipping between steps. This is how to build that file.

## Which pages have answer lines

Per `generate-workbook`'s template map (`references/canva_mcp_fill.md` in
that skill), the pages with hand-fill answer lines are the exercise pages —
6, 8, 10, 12 (`sez1_esercizi`..`sez4_esercizi`, 4 exercises each) — plus the
completions on 13 (`esercizio_finale`) and 14 (`completamenti`). Re-verify
against the live design rather than trusting this blindly; the template can
change.

## The answer lines are not separate Canva elements

Confirmed by reading the live design during the October 2026 fill: each
answer "line" is not its own element. Every `esercizi`/`completamenti`/
`esercizio_finale` field is **one single text box** whose content includes
one long unbroken run of dots per answer (e.g. `"." * 458`, no embedded
newlines — see `generate-workbook`'s `field_assembly.md`), which Canva's
text engine word-wraps into ~3 visual sub-lines on its own. There is no
Canva-side geometry to read for these — reading exact element positions via
`read-design` (what would otherwise be the first thing to try) doesn't
apply here, because there's nothing at the per-line granularity to read.
This may change if the template is ever restructured to use discrete line
elements per answer instead — worth re-checking `read-design` on one
exercise page first if a future run's dot count/format looks different from
what's documented here, before assuming this section still applies.

## Detecting answer positions in the exported flat PDF

Since the dots are real rendered text, their positions can be read directly
and reliably from the exported flat PDF — no guessing, no image-based
estimation needed. Use `scripts/detect_dotlines.py <flat.pdf>`: it finds
every line of text that's >90% period characters, then groups consecutive
dot-sublines (small vertical gap) into one bounding box per answer — that
grouped box is what one printed answer actually occupies, wrapped sub-lines
included.

Verify the output makes sense before building `fields.json`: the block
count per page should match the known content structure (4 answer blocks
on each of pages 6/8/10/12, 2 on page 13, 3 on page 14 — 21 total, as of
this template). Recompute the expected count from your own fields for the
edition you're finalizing rather than trusting "21" as a magic number if
the template or content schema ever changes.

## One field per answer, not one field per wrapped sub-line

Build `fields.json` with **one field per detected group** (i.e. per answer,
not per wrapped sub-line) — a single multiline field spanning the group's
full bounding box. This matches the source content's own structure: the
458-dot run is one continuous writing space that happens to wrap across
~3 printed lines, not three independent answer slots, so one merged
multiline field is both simpler and a better match for how someone
actually types an answer (no artificial break between "line 1" and "line
2" of what is really one flowing response).

## Field naming

Use a stable, descriptive scheme so a human glancing at `fields.json` can
tell what each one is: `sez<N>_ex<M>_line1` for exercise answers (e.g.
`sez2_ex3_line1` — always `_line1` since there's exactly one merged field
per exercise, not per wrapped sub-line), `esercizio_finale_line<L>` for the
`L`-th completion on that page, `completamenti_line<L>` likewise. Every
`field_name` must be unique across the whole document —
`add_form_fields.py` rejects duplicates. Map `detect_dotlines.py`'s
per-page groups to names in top-to-bottom order (the script already returns
them sorted by vertical position), using your own knowledge of which
exercise/completion appears at which position on that page.

## Validate before authoring

Run `python3 scripts/check_fields.py fields.json` before `add_form_fields.py`
— it flags duplicate field names, degenerate rects, and any two rects on
the same page that overlap, which is the most common way a coordinate pass
goes wrong. Fix everything it reports before proceeding.

## If a future template does have discrete per-line elements

If the template is ever rebuilt so each answer line is its own Canva
element (a deliberate, more robust design — see the note in `SKILL.md`),
that geometry can be read directly via `read-design` with an open
transaction, converting Canva's page-pixel coordinates to PDF points using
the ratio between the design's page dimensions (`page_metadata`) and the
exported PDF's actual page size (`scripts/get_page_sizes.py`). That path
wasn't available for the template as it exists today, so it isn't
documented in more detail here — write it up properly if and when it
becomes real, rather than trying to follow speculative steps.
