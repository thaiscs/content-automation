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
oversized or undersized.

`cover_title`, `cover_subtitle`, `mantra_testo`, `intenzione_testo`, section
`titolo`/`citazione`, exercise titles/prompts, and the completion-sentence
starters are all naturally short/bounded by their nature — no explicit budget
needed for those.

## How the 34 Canva fields are assembled from the drafted JSON

Draft the JSON to the schema in `SKILL.md` first (34-field content: `sezioni`
with `corpo`/`esercizi`, `completamenti`, etc.). Then build the literal text for
each Canva `dataFieldLabel` as follows before filling (step 5):

**Direct 1:1 fields** — no assembly, just copy the value:
`cover_title`, `cover_subtitle`, `mantra_testo`, `intenzione_testo`,
`lettera_testo_1` = `lettera_corpo[0]`, `lettera_testo_2` = `lettera_corpo[1]`.

**Per section N (1–4):**
- `toc_N` = `sezioni[N].titolo` (the subtitle only — the template's own
  "SEZIONE N" heading is a separate, fixed element; don't prepend it)
- `sezN_titolo` = `sezioni[N].titolo` (same value as `toc_N`)
- `sezN_citazione` = `sezioni[N].citazione`
- `sezN_testo_1` = `sezioni[N].corpo[0]`, `sezN_testo_2` = `sezioni[N].corpo[1]`
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
  where `ANSWER_LINES` is **3 dotted lines**, each exactly `"." * 150`
  (150 period characters), separated by newlines — this is fixed scaffolding,
  always the same regardless of content. Each numbered block and its answer
  lines are separated by a blank line (double newline), matching the pattern
  above.

**`integrazione_testo_1`/`_2`** = `integrazione_corpo[0]`/`[1]` directly.

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

## Background photos (not currently wired up)

The template has three image autofill fields (`sfondo_cover`, `sfondo_pagina2`,
`sfondo_impressum`) for a monthly-rotating background photo from a curated Canva
folder. The old pipeline had this logic (`backgrounds.py`, deterministic photo
choice per edition) but it was never actually configured (no folder ID was ever
set), so in practice these three fields have always kept the template's default
image — nothing is lost by dropping this code. If you want monthly photo
rotation, it needs to be re-implemented (or just changed by hand in Canva each
month); it isn't currently part of the fill procedure.
