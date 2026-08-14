# Filling the HDH workbook Canva template via MCP

Procedure for step 5 of `SKILL.md`. There is no Python pipeline in this repo
anymore (removed — see `SKILL.md`'s Notes section) — this uses the connected
Canva MCP integration (`mcp__Canva__*` tools) only, no OAuth/`.env`/local
service of any kind.

## 1. Get the 34 field values

Assemble them per `references/field_assembly.md` — direct copies for most
fields, fixed scaffolding (numbering, dotted answer lines, connective phrases)
added on top of your drafted text for `sezN_esercizi`, `esercizio_finale`, and
`completamenti`. This is plain text work, no code required. Keep the 34 values
in memory (or jot them to `out/workbook-<YYYY-MM>.json` if that helps you track
state across a long session) — you'll use them directly in the `replace_text`
operations in step 5 below. Check each body field against its budget in
`field_assembly.md` before filling; revise and re-check rather than shipping an
out-of-range field.

## 2. Locate the template

Brand template id: **`EAHNaGY-7DM`** (title shows as "WB HDH \<last-used-month\>").
Confirm with `mcp__Canva__get-brand-template-dataset` if you want to re-verify
field names — the live dataset has **48 fields**, not 34: extra numbered variants
per section (`sez2_testo_3`, `sez2_testo_4`, `sez1_esercizi_1`, `sez1_esercizi_2`,
etc.) and 3 background image fields (`sfondo_cover`, `sfondo_pagina2`,
`sfondo_impressum`) exist in the template but are **not** part of the current
34-field content schema. Leave them untouched — this is a pre-existing template/
pipeline mismatch, not something to "fix" by inventing content for them.

## 3. Create a design instance

```
mcp__Canva__create-design-from-brand-template  brand_template_id: "EAHNaGY-7DM"
```

This returns a `design_id` (starts with `D`) and a 15-page design pre-filled with
the previous edition's sample content (not blank placeholders).

## 4. Map fields to elements

Open one editing transaction and keep reusing its `transaction_id` for every
edit:

```
mcp__Canva__read-design  design_id: <id>  open_transaction: true
  filter.fields: ["design_content"]  filter.page_indices: [1]
```

Read pages one at a time (or in small batches) via `read-design` with the same
`transaction_id`. Text elements that are autofill targets carry a
`dataFieldLabel: "<field_name>"` annotation directly in the markdown — match it
against the field dict from step 1. Page layout (as of the last fill):

| Page | Fields |
|---|---|
| 1 | `cover_subtitle` (no `cover_title` field exists anywhere — see gotcha below) |
| 2 | `mantra_testo`, `intenzione_testo` |
| 3 | `lettera_testo_1`, `lettera_testo_2` |
| 4 (TOC) | `toc_1`–`toc_4` — **see disambiguation gotcha below** |
| 5 | `sez1_titolo`, `sez1_citazione`, `sez1_testo_1`, `sez1_testo_2` |
| 6 | `sez1_esercizi` |
| 7 | `sez2_titolo`, `sez2_citazione`, `sez2_testo_1`, `sez2_testo_2` |
| 8 | `sez2_esercizi` |
| 9 | `sez3_titolo`, `sez3_citazione`, `sez3_testo_1`, `sez3_testo_2` |
| 10 | `sez3_esercizi` |
| 11 | `sez4_titolo`, `sez4_citazione`, `sez4_testo_1`, `sez4_testo_2` |
| 12 | `sez4_esercizi` |
| 13 | `integrazione_testo_1`, `integrazione_testo_2`, `esercizio_finale` |
| 14 | `completamenti` |
| 15 | impressum/colophon — no data fields |

Re-verify this layout rather than trusting it blindly — the template can change.

## 5. Apply edits

For each page, one `mcp__Canva__edit-design` call with `page_index` set and
`operations: [{type: "replace_text", element_id: <locator_id>, text: <value>}, ...]`
for every field on that page, `finalize: "keep_open"`. `element_id` is the
locator id shown in brackets in the `read-design` output, e.g.
`PBhq7xcTvPR0HS9f-LBFYH72pn9PnlXsf` for `[PBhq7xcTvPR0HS9f-LBFYH72pn9PnlXsf]`.

## 6. Known gotchas (hit these on the first fill — check for them every time)

- **`toc_1`..`toc_4` are reused on non-target elements.** On the TOC page, some
  elements tagged `toc_1` etc. hold the actual section subtitle (replace these),
  but *other* elements share the same label while holding fixed structural text
  like "SEZIONE 1" or "Integrazione finale" (do **not** touch these — they're
  static headings, not content slots). Disambiguate by the element's *current*
  text: if it reads as a themed phrase, it's real content; if it's a generic
  structural label, skip it.
- **`cover_title` has no field anywhere.** Confirmed by reading all 15 pages —
  there is no `dataFieldLabel="cover_title"` element in this template. The large
  cover heading is tagged `cover_subtitle`. Don't spend time hunting for it every
  run; just note it in the final report as before.
- **`replace_text` can trigger Canva's autoshrink** on some title-sized text
  boxes, collapsing the font to ~1px even when the new text is *shorter* than the
  old — this happened on `sez2_titolo` and `sez3_titolo` in the first fill.
  Always pull a page thumbnail (`read-design` with `filter.fields: ["thumbnails"]`
  and the transaction_id) after editing each page and eyeball it; if text has
  vanished or shrunk, fix with a `format_text` operation setting an explicit
  `font_size` back to a sane value (title fields on this template render around
  27px).
- **Formatting can leak from the old content.** One body field inherited
  `fontWeight: bold` from the previous edition's multi-run rich text (which had a
  bold opening line). Check thumbnails for stray bold/italic runs and normalize
  with `format_text` if the new text shouldn't have them.
- **Font family isn't settable via the API.** `format_text` can set size,
  weight, style, color, alignment, etc., but not the font family — if a text
  element is rendering in the wrong typeface, that has to be fixed by hand in
  Canva's editor, not through MCP. Size/weight/style are fine to fix
  programmatically (as in the autoshrink and stray-bold cases above).
- **`toc_1`'s font family mismatches `toc_2`–`toc_4` on the TOC page** (a
  pre-existing template inconsistency, not something the fill introduces):
  `toc_1`'s content element renders in a different, larger-looking typeface
  (`YAFcf7N4Obg` vs `YACkoA9eHeY` for the other three) and can't be matched via
  the API (see the font-family caveat above). The workaround: set `toc_1`'s
  `font_size` to ~15 (vs the other three's 20) via `format_text` — visually
  closes most of the gap, though the typeface itself stays different. Check
  the page 4 thumbnail after; adjust the size if it still stands out.
- **The `sezN_testo_*` boxes auto-grow — use this, don't fight it.** If a
  section's body text looks short on the page after filling (compare against
  the box filling most of the page height in the thumbnail, roughly matching
  the section title + citation + full column of text reaching close to the
  bottom margin), the fix is to write more content, not to resize the box.
  See `field_assembly.md`'s corrected character budget for these fields.
- **Resized/repositioned boxes only help if they still span the intended text
  area.** This doesn't come up in routine fills (`replace_text` doesn't move or
  resize boxes), but if you ever restructure the template — add a section,
  split a box — a box that's the wrong size will visibly under-fill or overflow
  even with correctly length-budgeted text. Worth remembering if the template
  layout ever changes.

## 7. Finish

1. Rename the design: one `edit-design` operation with `type: "update_title"`,
   `title: "WB HDH <Label>"` (e.g. "WB HDH Agosto 2026").
2. Do a final visual pass — pull thumbnails for a few representative pages.
3. Commit: `edit-design` with empty `operations` and `finalize: "commit"`. This
   is irreversible for this design instance, but the instance itself is a
   disposable copy of the brand template (not the template itself) — a mistake
   here doesn't damage the brand template.
4. **Edit URL:** the `edit_url`/`view_url` fields returned by Canva MCP calls are
   short links that regenerate on every call — don't rely on them as a stable
   reference. Use the canonical, stable form instead:
   `https://www.canva.com/design/<design_id>/edit`.
