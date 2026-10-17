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
`sfondo_impressum`). Only `sfondo_cover` and `sfondo_impressum` get a photo —
see step 6 below and `references/media_library.md` for where the photos live.
`sfondo_pagina2` is deliberately left untouched (keeps the template's default
image); don't fill it.

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
| 1 | `cover_subtitle`, `sfondo_cover` (image) (no `cover_title` field exists anywhere — see gotcha below) |
| 2 | `mantra_testo`, `intenzione_testo` (`sfondo_pagina2` also lives here but is left unfilled — see step 6) |
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
| 15 | impressum/colophon — `sfondo_impressum` (image) |

Re-verify this layout rather than trusting it blindly — the template can change.
The two image fields actually filled (`sfondo_cover` on page 1, `sfondo_impressum`
on page 15, as of the last fill) show up as **image** elements carrying the
same `dataFieldLabel` annotation as text fields — spot them in the `read-design`
output by `type: "image"` rather than `type: "text"`. Note their `locator_id`s
alongside the text fields' while you're reading each page; you'll need them in
step 6. (`sfondo_pagina2` on page 2 is the same kind of element but is skipped
— see step 6.)

**Page 4 (TOC / "Contenuti") — capture original title styling before you
touch it.** The four section titles below their numbers (the real-content
`toc_1`..`toc_4` elements — see the disambiguation gotcha in step 7) have
come back with inconsistent font sizes and alignments across the four
entries after filling. The template's own authored values are correct and
identical across all four (same size, same weight, same alignment) — the
drift is introduced by the fill, not present in the template. So:

1. While reading page 4 in this step, for each of the four real-content
   `toc_N` elements (not the "SEZIONE N" structural ones), record its
   *current* `font_size`, `text_align`, `font_weight`, and `color` straight
   from the `read-design` output, before any edit. These four elements
   should already show matching values to each other — if they don't even
   before you touch anything, that's the template itself out of sync; flag
   it rather than trying to invent a "correct" value.
2. After `replace_text` on each `toc_N`, immediately follow with one
   `format_text` call re-applying that captured `font_size`/`text_align`/
   `font_weight`/`color` explicitly — don't assume `replace_text` preserves
   them; the observed symptom is exactly that it doesn't, consistently.
3. Pull the page 4 thumbnail and confirm all four titles now render at the
   same size, weight, and alignment as each other, matching how they looked
   pre-edit (i.e. matching the brand template) — not just individually
   readable, but visually uniform as a set.

## 5. Apply edits

For each page, one `mcp__Canva__edit-design` call with `page_index` set and
`operations: [{type: "replace_text", element_id: <locator_id>, text: <value>}, ...]`
for every field on that page, `finalize: "keep_open"`. `element_id` is the
locator id shown in brackets in the `read-design` output, e.g.
`PBhq7xcTvPR0HS9f-LBFYH72pn9PnlXsf` for `[PBhq7xcTvPR0HS9f-LBFYH72pn9PnlXsf]`.

For the body-text fields (`lettera_testo_*`, `sezN_testo_*`,
`integrazione_testo_*`), immediately follow each `replace_text` with the
normalize + bold-span `format_text` calls from `field_assembly.md`'s
"Paragraph rhythm & bold emphasis" — same page, same still-open transaction,
before moving to the next page. Don't defer this to a separate pass; do it
field-by-field right after each `replace_text` so a page's thumbnail check
reflects the final formatted state. Then run `field_assembly.md`'s
"Verify-and-fix loop" for that page before advancing — pull the thumbnail,
check both boxes actually look filled (not overflowing, not sparse) and
formatted correctly (no stray italic or full-block bold), and redraft/refill
in place if not. This applies to pages 3, 5, 7, 9, 11, and 13.

For page 4 (TOC), see the dedicated procedure below the field-mapping table
in step 4 above and the `toc_1`..`toc_4` gotchas below — its title styling
needs an explicit capture-and-reapply step, not just replace-and-check.

## 6. Select and place the background photos

Do this after step 5's text edits (same open transaction is fine). Only
`sfondo_cover` (page 1) and `sfondo_impressum` (page 15) get filled —
`sfondo_pagina2` (page 2) is deliberately left alone, keeping the template's
default image.

**Don't trust the `dataFieldLabel` on the page 1/2 background elements —
verify by physical position instead.** As of the October 2026 fill, page 1's
background rect is actually labeled `sfondo_pagina2` (not `sfondo_cover`),
and page 2's background rect carries no `dataFieldLabel` at all — the labels
have drifted from what's documented here, and from what the brand template's
own dataset schema (`get-brand-template-dataset`) implies. This doesn't
block filling: `update_fill` targets by `locator_id`, not by label, so place
the cover photo on **page 1's background rect regardless of its label**, and
leave **page 2's background rect** alone regardless of its label (same
"don't touch it" rule as always). But flag this to Giusi — it means the
brand template's own autofill data model is out of sync with its visual
layout, which will confuse anyone (or anything) that fills this template
through Canva's native autofill UI/API instead of this locator-based MCP
flow. Worth her fixing the label directly in Canva at some point.

1. **Pick photos.** Follow `references/media_library.md` to choose a subfolder
   matching the month's `tema`, then `mcp__Canva__list-folder-items` that
   subfolder and pick one photo for `sfondo_cover` and one for `sfondo_impressum`
   (the same photo for both is fine, or two different ones from the same
   subfolder — see that doc). Note each photo's asset id (`MA...`).
2. **Place each photo** with one `edit-design` operation per field:
   ```
   operations: [{
     type: "update_fill",
     element_id: <locator_id of the sfondo_* image element>,
     asset_type: "image",
     asset_id: <chosen photo's asset id>,
     alt_text: "<short description, e.g. 'Giusi Valentini, ritratto professionale'>"
   }]
   ```
   Target the same `page_index` the element lives on (per the table above) —
   `sfondo_cover` on page 1's call, `sfondo_impressum` on page 15's (its own
   call, since page 15 otherwise has no text edits).
3. **Verify via thumbnail** like any other page edit — pull the page thumbnail
   and check the photo landed, isn't stretched/cropped oddly, and reads well
   under the existing text overlay (title/impressum text sits on top of these
   backgrounds, so a very busy or high-contrast photo can hurt legibility;
   prefer photos with a calmer background area behind where the text sits).
4. If a chosen photo doesn't read well once placed, just pick a different one
   from the same subfolder and redo the `update_fill` — it's a cheap operation
   inside the still-open transaction, nothing is committed yet.

## 7. Known gotchas (hit these on the first fill — check for them every time)

- **`toc_1`..`toc_4` are reused on non-target elements.** On the TOC page, some
  elements tagged `toc_1` etc. hold the actual section subtitle (replace these),
  but *other* elements share the same label while holding fixed structural text
  like "SEZIONE 1" or "Integrazione finale" (do **not** touch these — they're
  static headings, not content slots). Disambiguate by the element's *current*
  text: if it reads as a themed phrase, it's real content; if it's a generic
  structural label, skip it.
- **The four real `toc_N` titles drift to inconsistent font sizes and
  alignments after `replace_text`, even though the template has them
  matching.** Not the same bug as the `sez2_titolo`/`sez3_titolo` autoshrink
  below (that collapses to ~1px; this one just picks slightly different
  sizes/alignments per element), but the same category of "replace_text
  doesn't reliably preserve styling" — treat it as expected every run, not
  a rare fluke. Fix: capture each `toc_N`'s original `font_size`/
  `text_align`/`font_weight`/`color` before editing and explicitly
  re-apply them via `format_text` after `replace_text` — see the dedicated
  procedure in step 4 above. Skipping this is what produces the visibly
  inconsistent "Contenuti" page.
- **`cover_title` has no field anywhere.** Confirmed by reading all 15 pages —
  there is no `dataFieldLabel="cover_title"` element in this template. The large
  cover heading is tagged `cover_subtitle`. Don't spend time hunting for it every
  run; just note it in the final report as before.
- **`replace_text` can trigger Canva's autoshrink** on some title-sized text
  boxes, collapsing the font to ~1px even when the new text is *shorter* than the
  old — this happened on `sez2_titolo` and `sez3_titolo` in the first fill,
  and hit the exact same two fields again in the October 2026 fill. Treat
  this as an expected, deterministic step for `sez2_titolo`/`sez3_titolo`
  specifically, not a rare fluke — always pull a page thumbnail (`read-design`
  with `filter.fields: ["thumbnails"]` and the transaction_id) after editing
  each page and eyeball it; if text has vanished or shrunk, fix with a
  `format_text` operation setting an explicit `font_size` back to a sane
  value (title fields on this template render around 27px).
- **Formatting leaks from the old content on every `esercizi`/
  `completamenti`/`esercizio_finale` field, not just occasionally.** These
  fields hold multi-run rich text (bold numbered headers, differently-colored
  prompts); `replace_text` collapses the whole block into the first run's
  formatting, so the entire field comes back bold and gold-colored, dots
  included — and sometimes italic too, depending on what the previous
  edition's content happened to carry in that first run. Always follow up
  with a `format_text` call normalizing to `font_weight: "normal"`,
  `font_style: "normal"`, `color: "#000000"` on that same element — see
  `field_assembly.md` for the fuller note. Don't skip this expecting it to be
  fine "most of the time"; it wasn't fine on any of the 6 fields of this type
  in the October 2026 fill.
- **Body-text fields (`lettera_testo_*`, `sezN_testo_*`,
  `integrazione_testo_*`) need the same normalize treatment on BOTH the
  left and right box of every pair, every time — including `font_style`,
  not just `font_weight`.** These boxes have come back rendering fully
  italic as well as fully bold — this is the same first-run-formatting-wins
  leak as the exercizi fields above, it just wasn't being corrected on body
  text until this was added. The *normalize* call (`font_weight: "normal"`
  + `font_style: "normal"`) is unconditional on every one of these fields —
  treat it as a required part of filling these fields, not an optional
  polish step, and don't skip the second box of a pair just because the
  first looked fine.
- **Bold spans within a text run are NOT achievable with this Canva MCP
  surface — confirmed, not a caveat.** Tested directly in the October 2026
  fill: (1) sending `**phrase**` markdown syntax through `replace_text`
  does not get parsed as rich text — it renders as literal asterisk
  characters on the page; (2) `format_text`'s `formatting` object has no
  range/offset/length parameter anywhere in its schema — it can only style
  a whole element, never a sub-string within it. There is no fallback that
  makes `field_assembly.md`'s per-paragraph bold-phrase convention work
  today. Ship body text as plain (marker-stripped) paragraphs and say so in
  the final report — don't re-attempt the markdown trick expecting a
  different result, and don't invent a workaround (e.g. a separate bolded
  text element layered on top) without checking with Giusi first.
- **`cover_subtitle` has no documented character budget but visibly needs
  one.** A longer subtitle (~78 characters) grew the text box tall enough to
  overlap the "GIUSI VALENTINI" byline beneath it — Canva doesn't autoshrink
  this box the way it does section titles, it just lets the box grow and
  collide. Keep `cover_subtitle` close to June's original length (~59
  characters) as a practical ceiling, and check the page 1 thumbnail for
  overlap with the byline before committing.
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
- **Font family can drift silently between the two columns of a body-text
  pair, and normalize doesn't fix it** — confirmed in the October 2026
  fill. `create-design-from-brand-template` doesn't return a pristine copy
  of the blank template; it duplicates the *previous edition's actual
  content*, edit history and all. Somewhere in that history a run got
  assigned a different registered font family (e.g. "Poppins" vs. "Poppins
  Light" as two separate font assets, not weight variants of one font —
  common when the underlying font isn't a variable font). `replace_text`
  collapses a multi-run box to a single run using the *first* old run's
  formatting, including its font family, so the new text silently inherits
  whichever family happened to be first — independently per box, so the
  left and right column of the same section can end up in different
  families even though both read "normal" weight/style. Because
  `format_text` has no font-family parameter, this can't be corrected
  during a fill. Check for it visually (do the two columns' letterforms
  actually match, not just their weight?) and flag any affected field by
  name in the final report rather than silently shipping a mismatch. The
  durable fix is for a human to open the **brand template itself** in
  Canva and reset its body-text boxes to one consistent font family, so
  future editions stop inheriting the drift — worth raising to Giusi
  directly rather than expecting each fill to catch it.
- **Resized/repositioned boxes only help if they still span the intended text
  area.** This doesn't come up in routine fills (`replace_text` doesn't move or
  resize boxes), but if you ever restructure the template — add a section,
  split a box — a box that's the wrong size will visibly under-fill or overflow
  even with correctly length-budgeted text. Worth remembering if the template
  layout ever changes.

## 8. Finish

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
