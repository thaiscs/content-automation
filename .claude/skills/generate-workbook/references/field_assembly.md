# Field length budgets and text assembly

Ported from the old `app/pipelines/workbook/generate.py` (deleted along with the
rest of the Python pipeline — see the repo's git history if you ever need the
original code, e.g. `git log --all --full-history -- app/pipelines/workbook/generate.py`).
This is the load-bearing content logic that survives the deletion: it decides
how long each field must be to fill its Canva box, and how the raw JSON content
(step 3 of `SKILL.md`) turns into the exact text that goes into each of the 34
Canva fields.

## Character budgets (min, max) — inclusive

Calibrated from the template's box geometry. These are deliberately
approximate ranges, not hard limits — stay inside them so pages neither
overflow nor look sparse.

**Correction (2026-08):** the `sezN_testo_*` range below was originally ported
from `generate.py` as 480–720 chars, but that under-filled the actual template
box by roughly 30% (confirmed visually — see the August 2026 edition before/
after). These boxes auto-grow to fit their content, so there's no hard
overflow ceiling; the real failure mode is text that's too *short*, not too
long. Corrected range below is empirically validated (filled ~full page
height without visibly overflowing onto the next element) — treat 480–720 as
wrong if you see it referenced elsewhere (e.g. old commit messages).

| Field | Budget (chars) | ~Words |
|---|---|---|
| `sez1_testo_1`, `sez1_testo_2` | 750–870 | ~125–155 |
| `sez2_testo_1`, `sez2_testo_2` | 750–870 | ~125–155 |
| `sez3_testo_1`, `sez3_testo_2` | 750–870 | ~125–155 |
| `sez4_testo_1`, `sez4_testo_2` | 750–870 | ~125–155 |
| `lettera_testo_1` | 470–700 | ~85–110 |
| `lettera_testo_2` | 440–670 | ~85–110 |
| `integrazione_testo_1` | 250–440 | ~45–65 |
| `integrazione_testo_2` | 260–450 | ~45–65 |

Check these by counting characters/words yourself while drafting (no code
needed — a rough word count is enough; these are fill targets, not hard
limits). If a field lands outside its range, revise it — don't ship it
oversized or undersized. Budget counts include the paragraph-break and bold
markers described below — see "Paragraph rhythm & bold emphasis".

`cover_title`, `cover_subtitle`, `mantra_testo`, `intenzione_testo`, section
`titolo`/`citazione`, exercise titles/prompts, and the completion-sentence
starters are all naturally short/bounded by their nature — no explicit budget
needed for those, and the paragraph/bold rules below don't apply to them
(they're single short lines, not body text).

## Paragraph rhythm & bold emphasis (body text fields)

Applies to every "wall of text" field: `lettera_testo_1`/`_2`, `sezN_testo_1`/
`_2` (all 4 sections), `integrazione_testo_1`/`_2`. Does NOT apply to the
fixed-scaffolding fields (`sezN_esercizi`, `esercizio_finale`,
`completamenti`) — those already get their own formatting treatment below.

**Current status: the paragraph-rhythm half of this convention ships every
run; the bold half does not.** Confirmed against the live Canva MCP tooling
(October 2026 fill) that partial-bold within a text box isn't achievable —
see "Filling" below for the specifics. Still draft the `**phrase**` markers
as described (they cost nothing and self-document intent if the tooling
ever adds range support), but the filling step strips them and ships plain
text — don't expect bold to actually render.

A page reads better — and fills its box more evenly — as short paragraphs
with a visible break between them, punctuated here and there (not
everywhere) by a bolded phrase anchoring a paragraph's core idea. Bold on
every single paragraph reads noisy and defeats its own purpose as emphasis —
so bold is a **page-level budget, not a per-paragraph requirement.** This is
a **drafting-time** decision (step 3 of `SKILL.md`), made the same way on
every run, not something patched in afterward:

1. **Write each `corpo`/`lettera_corpo`/`integrazione_corpo` string as 3
   paragraphs internally**, separated by a blank line (`\n\n`) inside the
   same string. Split roughly evenly across the field's word budget above —
   don't front-load one long paragraph and tack on a two-word fragment.
   - `integrazione_testo` is short (45–65 words total), so a 3-way split can
     get tight: if a 3-way split would leave any paragraph under ~12 words,
     fall back to 2 paragraphs instead; if even a 2-way split would leave a
     paragraph under ~15 words, keep it as one paragraph. Don't force an
     awkward break just for the pattern's sake.
   - Every paragraph gets this split treatment, whether or not it ends up
     bolded (step 2) — the paragraph rhythm and the bold emphasis are two
     separate decisions.
2. **Across the whole page, bold exactly 2 or 3 paragraphs total — never
   all of them.** A "page" here means the group of paragraphs that land on
   the same physical page: `lettera_testo_1` + `lettera_testo_2` together
   (up to 6 paragraphs), each section's `sezN_testo_1` + `sezN_testo_2`
   together (up to 6 paragraphs), and `integrazione_testo_1` +
   `integrazione_testo_2` together (up to 6, fewer if either fell back to
   2 or 1 paragraph per the rule above).
   - Pick the 2–3 paragraphs carrying the page's strongest turns — the
     reframe, the instruction, the emotional pivot — and leave the rest of
     that page's paragraphs plain, with no `**...**` marker at all.
   - Vary *which* paragraph(s) on the page you pick from run to run and
     section to section (don't mechanically always bold "testo_1's first
     paragraph") — otherwise the bolding reads as a fixed template pattern
     rather than genuine emphasis.
   - In each bolded paragraph, wrap exactly ONE short phrase — **3 to 5
     words**, a tight clause, never a generic connector, never a whole
     sentence, never a single word — in `**double asterisks**`. A paragraph
     either has one bold phrase or none; never two phrases in the same
     paragraph, and never bold the field's very first word. Two budgets
     stack here: max 2-3 bolded paragraphs per page, and within each of
     those, max 3-5 bolded words.
3. The `**` markers themselves are a drafting-time convention only — they
   never reach Canva as literal text (see Assembly below). When checking a
   field against its character budget, you can count them as written (they
   roughly proxy for the visual weight of a bold span) or strip them first;
   either way stay inside the budget range.

**Assembly (step 4):** for each of these fields, before filling Canva:
1. Find each `**phrase**` span in the drafted string (a field may have
   zero, one, or two — most fields on a page will have zero, per the
   2-or-3-per-page budget above); record its plain-text start/end character
   offset (0-indexed, counting the paragraph break as 2 characters) in the
   final field text, i.e. *after* stripping the `**` markers.
2. Strip the `**` markers to produce the plain text — this plain text (with
   its `\n\n` paragraph break intact) is what gets sent to `replace_text`.
3. Keep the `(field_name, start, end)` bold-span list per field for the
   Canva-filling step (an empty list for fields with no bolded paragraph on
   this page — that's expected, not a gap to fill).

**Filling (step 5):** for each of these body-text fields, after
`replace_text`:
1. First normalize the **whole element** to `font_weight: "normal"`,
   `font_style: "normal"`, `color: "#000000"` — all three, every time, on
   both the left and right box of every pair (`sezN_testo_1` AND
   `sezN_testo_2`, `lettera_testo_1` AND `_2`, `integrazione_testo_1` AND
   `_2`). The template's placeholder content can carry stray bold, italic,
   or off-color runs onto the new text — the same leak that hits the
   exercizi/completamenti fields below — and it's not just a bold problem:
   text has come back italic as well as fully bold on these boxes before
   this normalize step covered `font_style`. Do this unconditionally on
   every one of these fields, don't wait to notice a problem, and don't
   skip the second box of a pair because the first looked fine.
2. **Do not attempt the bold spans.** Confirmed against the live tooling in
   the October 2026 fill: `replace_text` does not parse `**markdown**` as
   rich text (it renders the literal asterisk characters), and
   `format_text`'s `formatting` object has no range/offset/length parameter
   anywhere in its schema — it can only style a whole element, never a
   sub-string. There is currently no way to bold a phrase within a text box
   through this Canva MCP surface. Strip the `**` markers and send the
   plain paragraph text only. Don't re-attempt the markdown trick expecting
   a different result, and don't invent a workaround (e.g. a separate
   bolded lead-in element) without checking with Giusi first, since that
   would mean editing the template itself.
3. Pull the page thumbnail and confirm: no box anywhere on the page reads
   italic or fully bold, and the paragraph break reads as an actual visual
   break (not a run-on line). Also compare the **font family** of the two
   columns against each other, not just their weight — `replace_text`
   inherits whichever old run's formatting happened to be first when it
   collapses a multi-run box, and that can carry a different font family
   per column even after normalize (see `canva_mcp_fill.md`'s font-family
   gotcha). `format_text` can't fix this; if the two columns visibly don't
   match, name the field in the final report rather than treating it as
   fixed.
4. **Verify-and-fix the fill itself, not just the formatting** — see
   "Verify-and-fix loop" below. Don't advance to the next page until both
   the formatting (this section) and the fill (below) check out on the
   thumbnail.
5. Note in the final report that body-text fields ship without deliberate
   bold emphasis, since the tooling doesn't support it — this is an
   expected, standing limitation, not a per-run failure to flag as new.

## Verify-and-fix loop for body-text pages

The character budgets in the table above are a fast offline estimate, not a
guarantee — actual fill depends on Canva's real font rendering, which the
word-count table can't see. Close the loop visually, per page, inside the
same open transaction, right after formatting that page's fields (previous
section):

1. Pull that page's thumbnail: `read-design` with
   `filter.fields: ["thumbnails"]`, `filter.page_indices: [<page>]`, same
   `transaction_id`.
2. Judge each box on the page against two failure modes:
   - **Overflow/clipped** — text is cut off, spills past the box edge, or
     the box has visibly grown into a neighboring element.
   - **Underfill** — a conspicuously empty lower portion of the box, text
     stopping well short of where the box actually ends.
3. If a box fails either way, don't just re-send the same text — revise the
   *drafted* content for that field (lengthen or shorten a paragraph,
   rebalance the two paragraphs) while staying inside the field's character
   budget and keeping the paragraph/bold rules intact, then redo
   `replace_text` and the formatting calls (normalize + any bold spans) for
   that field, and re-pull the thumbnail. Repeat until it looks right.
4. Only move on to the next page once every box on this one reads as
   genuinely filled — not overflowing, not sparse — and correctly
   formatted. If a field needs repeated correction to land in-budget, that's
   a signal the budget table itself may be stale for that field — note it
   in your final report rather than silently fighting it forever.

This applies to every body-text page: page 3 (lettera), each section's text
page (5, 7, 9, 11), and page 13 (integrazione).

## How the 34 Canva fields are assembled from the drafted JSON

Draft the JSON to the schema in `SKILL.md` first (34-field content: `sezioni`
with `corpo`/`esercizi`, `completamenti`, etc.). Then build the literal text for
each Canva `dataFieldLabel` as follows before filling (step 5):

**Direct 1:1 fields** — no assembly beyond the paragraph/bold-span
processing above, just copy the value: `cover_title`, `cover_subtitle`,
`mantra_testo`, `intenzione_testo`, `lettera_testo_1` = `lettera_corpo[0]`,
`lettera_testo_2` = `lettera_corpo[1]` (the latter two go through "Paragraph
rhythm & bold emphasis" above like any other body-text field).

**Per section N (1–4):**
- `toc_N` = `sezioni[N].titolo` (the subtitle only — the template's own
  "SEZIONE N" heading is a separate, fixed element; don't prepend it)
- `sezN_titolo` = `sezioni[N].titolo` (same value as `toc_N`)
- `sezN_citazione` = `sezioni[N].citazione`
- `sezN_testo_1` = `sezioni[N].corpo[0]`, `sezN_testo_2` = `sezioni[N].corpo[1]`
  (both go through "Paragraph rhythm & bold emphasis" above)
- `sezN_esercizi` = the exercises block, assembled as:
  ```
  {esercizi_intro}

  1. {esercizi[0].titolo}

  {esercizi[0].prompt}
  {ANSWER_LINES}

  2. {esercizi[1].titolo}

  {esercizi[1].prompt}
  {ANSWER_LINES}

  3. {esercizi[2].titolo}

  {esercizi[2].prompt}
  {ANSWER_LINES}

  4. {esercizi[3].titolo}

  {esercizi[3].prompt}
  {ANSWER_LINES}
  ```
  where `ANSWER_LINES` is **one unbroken line of `"." * 458`** (458 period
  characters, no embedded newlines) — the template's text box word-wraps
  this into ~3 visual lines on its own. (Confirmed against the live
  October 2026 fill — do not use 3 separate 150-dot lines joined by
  newlines; that was this doc's original guess and doesn't match what's
  actually in the template. Re-verify the dot count if the box width ever
  changes, since it's tuned to the current ~535px-wide exercise boxes.)
  This is fixed scaffolding, always the same regardless of content. Each
  numbered block and its answer line are separated by a blank line (double
  newline), matching the pattern above.
- **After every `replace_text` on an `esercizi`/`completamenti`/
  `esercizio_finale` field, immediately follow with a `format_text` call
  setting `font_weight: "normal"` (and usually `color: "#000000"`) on that
  same element.** These fields carry multi-run rich text in the template
  (bold numbered headers, differently-colored prompts) that `replace_text`
  collapses into a single run using the *first* run's formatting — in
  practice this means the whole block comes back bold and gold-colored,
  not just an occasional stray run. This isn't the rare edge case the
  older gotcha note below implies; it happens on essentially every one of
  these fields, every time. Normalizing to plain black after each fill is
  the reliable fix, not a "check and fix if you notice it" step.

**`integrazione_testo_1`/`_2`** = `integrazione_corpo[0]`/`[1]` directly
(through "Paragraph rhythm & bold emphasis" above like the other body-text
fields).

**`esercizio_finale`** — assembled as:
```
{esercizio_finale_titolo}

Completa senza pensarci troppo:

{esercizio_finale_completamenti[0]}
{ANSWER_LINES}

{esercizio_finale_completamenti[1]}
{ANSWER_LINES}
```

**`completamenti`** — assembled as:
```
{completamenti[0]}
{ANSWER_LINES}

{completamenti[1]}
{ANSWER_LINES}

{completamenti[2]}
{ANSWER_LINES}

Porta con te questo:

{completamenti_chiusura}
```

Note the literal connective text — `"Completa senza pensarci troppo:"` and
`"Porta con te questo:"` — is fixed template language, not something to
paraphrase; reproduce it verbatim, only the content around it changes.

## Background photos

The template has three image autofill fields (`sfondo_cover`, `sfondo_pagina2`,
`sfondo_impressum`) for a monthly-rotating background photo. The old Python
pipeline had this logic (`backgrounds.py`, deterministic photo choice per
edition) but it was never actually configured (no folder ID was ever set), so
in practice these three fields always kept the template's default image.

That's fixed now for two of the three: a curated Canva folder of Giusi's
photos exists ("For Claude", see `references/media_library.md`), and filling
`sfondo_cover` and `sfondo_impressum` is part of the routine procedure — see
`canva_mcp_fill.md` step 6. `sfondo_pagina2` is deliberately left alone
(keeps the template's default image) — only cover and impressum get a photo.
These are images, not text, so they're picked and placed directly via Canva
MCP (`update_fill`) — they're not part of the 34-field JSON content schema
above and need no drafting.
