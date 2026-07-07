# Workbook Layout Spec — HDH monthly workbook

Goal: a **uniform, page-filling** layout so (a) page numbers never need adjusting again,
and (b) generated text and exercises reliably fill each page.

This is achieved with two levers:

1. **Uniform template geometry** → every section is exactly **2 pages** with identical box
   structure, so the page sequence is fixed forever and the page numbers are baked in once.
2. **Fixed font size + calibrated text length** → autofill drops text into fixed boxes at a
   fixed size (body = 12). "Fills the page" is then purely a function of how much text we
   generate, so the code targets a length budget per field and **auto-regenerates** anything
   that comes back too short or too long.

> The template restructuring (adding/moving/splitting boxes) is manual in Canva — the connector
> API can format and tag boxes but cannot create or move them. Once you've built the layout
> below, I inspect the finished template, measure each box, compute the exact length budgets,
> and wire up the code.

---

## Fixed page map

| Page | Purpose | Dynamic fields | Fixed (never autofilled) |
|------|---------|----------------|--------------------------|
| 1 | Cover | `cover_title` | photo, GIUSI VALENTINI, HAPPY DAILY HOME |
| 2 | Cover subtitle | `cover_subtitle` | photo, brand text |
| 3 | Mantra & Intenzione | `mantra_testo`, `intenzione_testo` | MANTRA / INTENZIONE labels |
| 4 | Cara Homie (letter) | `lettera_testo_1`, `lettera_testo_2` | "Cara Homie," greeting, "Giusi" signature, photo |
| 5 | Contenuti (TOC) | `toc_1`–`toc_4` (subtitles only) | "Contenuti", "SEZIONE N" labels |
| 6 | Sezione 1 — Intro | `sez1_titolo`, `sez1_citazione`, `sez1_testo_1`, `sez1_testo_2` | "Sezione 1" label, page number |
| 7 | Sezione 1 — Esercizi | `sez1_esercizi` | page number |
| 8 | Sezione 2 — Intro | `sez2_titolo`, `sez2_citazione`, `sez2_testo_1`, `sez2_testo_2` | "Sezione 2" label, page number |
| 9 | Sezione 2 — Esercizi | `sez2_esercizi` | page number |
| 10 | Sezione 3 — Intro | `sez3_titolo`, `sez3_citazione`, `sez3_testo_1`, `sez3_testo_2` | "Sezione 3" label, page number |
| 11 | Sezione 3 — Esercizi | `sez3_esercizi` | page number |
| 12 | Sezione 4 — Intro | `sez4_titolo`, `sez4_citazione`, `sez4_testo_1`, `sez4_testo_2` | "Sezione 4" label, page number |
| 13 | Sezione 4 — Esercizi | `sez4_esercizi` | page number |
| 14 | Integrazione finale | `integrazione_testo`, `esercizio_finale` | "Integrazione finale" label |
| 15 | Completamenti | `completamenti` | photo |
| 16 | Impressum | — | all fixed |

Net change vs the old template: each section drops from a variable 2–3 pages to a fixed 2, while
the intro page keeps its **two-column** body (as in the current template). Once this is in
place, the page numbers printed on each page are correct permanently.

---

## Per-page rules

### Section intro page (pages 6, 8, 10, 12)
- **Two columns** for the body (`sezN_testo_1`, `sezN_testo_2`), as in the current template —
  sized to span the page's text area below the title/quote.
- `sezN_titolo` (section subtitle) and `sezN_citazione` (quote) keep their own styles.
- "Sezione N" label and page number are fixed.
- Combined body length across both columns is calibrated to **fill the page** at size 12, and
  the split between the two columns is balanced.

### Section exercises page (pages 7, 9, 11, 13)
- One combined exercises text box (`sezN_esercizi`), structured as:
  - Header: `Esercizi – [tema della sezione]`
  - **4 exercises**, each:
    - `N. [titolo esercizio]`
    - `[prompt riflessivo]`
    - **3 answer lines** (dotted) — fixed scaffolding added by the code
- Claude writes only the header, the 4 titles and the 4 prompts; the code assembles the block
  with the numbering and the 3 dotted answer lines per exercise (`ANSWER_LINES = 3`,
  `DOTTED_LINE = "." * 150`).
- Template note: the exercise boxes (and the completion blocks on p14–15) are set to **font 12
  with line spacing 1.9** so that 4 exercises × 3 answer lines fit the page without overflowing
  at their original (larger) size.

### Cara Homie (page 4)
- Two columns (`lettera_testo_1`, `lettera_testo_2`), both size 12, calibrated to fill.

---

## Build method (fastest in Canva)

1. Build **one** canonical intro page and **one** canonical exercises page exactly as above
   (two-column body; 4-exercise block with 3 answer lines each).
2. **Duplicate the page pair** three more times (Canva: right-click page → Duplicate).
3. On each copy, update only the fixed "Sezione N" label so it reads 1 / 2 / 3 / 4.
4. Leave the dynamic boxes empty-ish or with placeholder text — I'll tag them afterward.
5. Save / publish the brand template, then tell me.

Because you duplicate rather than rebuild, every section page is pixel-identical, which is what
makes the calibration consistent.

---

## What I implement after the template is built

1. **Inspect & measure** every dynamic box's width/height.
2. **Compute length budgets** (min/max characters) per field from box size at font 12.
3. **Update `generate.py`:**
   - New `SECTION_LAYOUT`: 2 body columns + 1 exercises block per section (uniform across all 4);
     4 exercises × 1 prompt; `ANSWER_LINES = 3`.
   - `toc_N` becomes the subtitle only (drops the `"SEZIONE N\n\n"` prefix).
   - A `FIELD_BUDGETS` table and a **validation + auto-regeneration loop**: after each
     generation, any field outside its budget triggers a targeted "expand/trim field X to ~N
     words" instruction and one more generation pass (bounded by a max-iterations cap), reusing
     the existing reviewer-feedback mechanism.
4. **Re-tag** the template's dynamic boxes to match the new field names.
5. **Update the tests** and run the suite.

---

## Background photos (monthly rotation)

Three full-bleed photos are tagged as **image** autofill fields: `sfondo_cover` (p1),
`sfondo_pagina2` (p2), `sfondo_impressum` (p16). Each month the pipeline picks a photo
from a **curated Canva folder** (`CANVA_BACKGROUND_FOLDER_ID`) and passes its asset_id
to autofill (`app/pipelines/workbook/backgrounds.py`). Selection is deterministic per
edition, so regenerating a month reuses the same photo. If the folder is unset/empty,
the template keeps its default backgrounds.

Setup (one-time): create a folder in Canva, add approved background photos, copy its
folder ID into `CANVA_BACKGROUND_FOLDER_ID`. Canva's Connect API can't browse Canva's
stock library, so backgrounds must live in the account (uploaded or added to the folder).
The locked brand textures (mantra page etc.) and the leaf decorations stay fixed.

## Notes / caveats
- Calibration makes pages *visually consistent*, not pixel-perfect — natural language length
  varies, so we target a range and let validation pull outliers back in.
- Font **size/weight/style** are settable via the API; font **family** is not — keep families
  set correctly in the template by hand (brand font).
- Boxes must be sized to span the page area; otherwise text fills the box but not the page.
