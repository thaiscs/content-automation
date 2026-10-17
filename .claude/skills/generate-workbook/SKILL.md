---
name: generate-workbook
description: Generate the monthly HDH workbook in Giusi Valentini's voice and render it in Canva. Use when the user runs /generate-workbook, or asks to create/generate this month's (or a given month's) workbook. Draws on brand-voice sources, produces the 34-field content, and fills the Canva brand template.
---

# Generate the monthly HDH workbook

You generate the content for Giusi Valentini's monthly "Happy Daily Home" (HDH)
workbook — in Italian, in her voice — then fill the Canva brand template
directly via the connected Canva MCP integration.

You are the **content generator** (this replaces the old Anthropic-API call, so it
runs on the Claude subscription). Canva filling is also done by you, via MCP —
there is no Python/API step left in this workflow (see step 5).

## Inputs

- Optional month argument like `--month 2026-07`. If absent, use the current month.
- The theme comes from `content_plan.toml` (keys are `YYYY-MM`), cross-checked
  against the "Temi mensili" list in the onboarding Google Doc (see step 1).
  **Never invent a theme** — if neither source has an entry for the target month,
  stop and tell the user to add one (and, if email is set up, note that
  `run_monthly.py` would send a heads-up).

## Steps

1. **Absorb the brand voice — this is what makes the output sound like Giusi.**
   The primary source is the pair of live Google Docs listed in
   `brand_voice/sources.md`; local files in `brand_voice/` are the always-available
   supplement and fallback. Do this first, since step 2 (resolving the edition)
   needs the second Doc's content.
   - **Fetch the Docs (primary):** for each URL in `brand_voice/sources.md`, use
     the Google Drive connector to get its title (`get_file_metadata`) and body
     (`read_file_content` / `download_file_content`). Write each as a markdown
     snapshot to `brand_voice/google_docs/<slugified-title>.md`, overwriting any
     previous snapshot, with a header noting the source URL and fetch time (UTC).
     These snapshots are generated files — don't hand-edit them.
   - **Fallback:** if the Drive connector isn't available, or a fetch fails, skip
     that doc, note it in your final report, and use whatever snapshot already
     exists in `brand_voice/google_docs/` from the last successful run instead.
     Never fail the whole run over a fetch failure.
   - **Local supplement:** also read every other file in `brand_voice/` (tone
     guide, past workbooks, transcripts, sample captions) for extra texture.
   - **Other connectors (if available):** pull recent, relevant material via MCP —
     podcast transcripts (Libsyn), social captions. Skip if unavailable.
   - **Snapshot commit:** after writing snapshots, if `git status --porcelain
     brand_voice/google_docs/` shows changes, commit them on their own (`git add
     brand_voice/google_docs/ && git commit -m "chore: refresh brand voice
     snapshot for <month>"`) — keep this separate from the workbook-content
     commit/PR so the voice-source history stays easy to audit.
   Extract: her recurring phrases, sentence rhythm, warmth, directness, the topics
   she returns to, and what she avoids. Mirror that voice — do not write generic
   "AI wellness" prose.

2. **Resolve the edition.** Determine the target `YYYY-MM`.
   - Read the entry from `content_plan.toml` (fields: `tema`, `obiettivi`) — this
     remains the source for the full creative brief, since it carries a real thesis
     and stated objectives, not just a label.
   - **Cross-check against the Google Doc.** The snapshot you just wrote for the
     second Doc ("CLAUDE Skill - Onboarding_Giusis Business") contains a "Temi
     mensili 2026" line (short `Mese = Tema` labels, e.g. "Agosto = Digital
     Detox"). Find the target month's label there.
     - If `content_plan.toml` has an entry and the Doc's label for that month is a
       recognizably different concept (not just a wording variance) — STOP and
       report the conflict instead of silently picking one. Show both versions and
       ask which is authoritative before generating anything.
     - If `content_plan.toml` has no entry for the month but the Doc does, you may
       proceed using the Doc's short label as `tema` (with `obiettivi` left to your
       best judgement from context) — but flag in your final report that only a
       terse label was available, not a full brief, so Giusi can review more
       closely than usual.
     - If neither source has an entry, STOP and report (existing "never invent a
       theme" rule).
   - Compute the Italian edition label (e.g. `2026-07` → "Luglio 2026").

3. **Draft the content** to the exact schema below. Match lengths (the layout is
   fixed; text must fill the boxes without overflowing) — see
   `references/field_assembly.md` for the exact character budgets per field.

4. **Assemble the 34 Canva field values** from the drafted JSON, following the
   assembly rules in `references/field_assembly.md` (direct copies for most
   fields; the exercises/completamenti/esercizio_finale blocks need their fixed
   scaffolding — numbering, dotted answer lines, connective phrases — added on
   top of your drafted text). Optionally save the JSON to
   `out/workbook-<YYYY-MM>.json` for your own reference during the run.

5. **Fill Canva via MCP.** There's no Python/API step — fill the brand template
   directly using the connected Canva MCP tools. Follow
   `references/canva_mcp_fill.md` for the exact procedure (locating the template,
   mapping fields to elements, selecting and placing background photos, the
   known gotchas, and the stable edit-URL format). In short: create a design
   from brand template `EAHNaGY-7DM`, map the 34 assembled field values to
   their `dataFieldLabel`-tagged text elements page by page, replace their
   text, pick a themed photo from the curated library (`references/media_library.md`)
   for the `sfondo_cover` and `sfondo_impressum` background-image fields (the
   third such field, `sfondo_pagina2`, is left unfilled), verify via
   thumbnails, rename the design to `WB HDH <Label>`, and commit.
   Three things to get right on every body-text page (don't treat any of
   these as optional polish — they're part of the fill, not a follow-up
   pass): normalize every `testo` box to plain, non-italic weight/style
   before applying any deliberate bold spans; run the per-page
   verify-and-fix loop (thumbnail → judge fill → redraft/refill if
   over/underfilled) before moving to the next page; and on page 4 (TOC),
   explicitly capture and reapply each title's original font size/alignment
   so all four match the brand template instead of drifting. All three are
   spelled out in `references/canva_mcp_fill.md` and
   `references/field_assembly.md`.
   Two standing tooling limitations to note in the report every run, not
   chase as new bugs: bold spans within a text box aren't achievable
   (confirmed — see `field_assembly.md`), and font family can silently
   differ between the two columns of a body-text pair because
   `create-design-from-brand-template` duplicates the previous edition's
   drifted formatting, not a clean template — check each page's two
   columns visually match in typeface, and name any field that doesn't in
   the report (see `canva_mcp_fill.md`'s font-family gotcha). The durable
   fix for the font drift is a human resetting the brand template's
   body-text boxes to one font family in Canva directly — worth flagging
   to Giusi as a standalone action item, not something a fill can correct.

6. **Report** the Canva edit URL (`https://www.canva.com/design/<design_id>/edit`),
   so Giusi can finalize it. Don't send an approval email unless explicitly asked —
   notification is no longer automatic now that the Python fill script is retired.

## Content schema (34 fields — must match exactly)

Return/write JSON with this shape:

```json
{
  "cover_title": "TITOLO DEL TEMA, MAIUSCOLO",
  "cover_subtitle": "sottotitolo breve del percorso",
  "mantra_testo": "frase breve, prima persona, presente",
  "intenzione_testo": "frase breve complementare al mantra",
  "lettera_corpo": ["paragrafo 1 (~85-110 parole)", "paragrafo 2, termina con 'Namaste,'"],
  "sezioni": [
    {
      "numero": 1,
      "titolo": "sottotitolo della sezione",
      "citazione": "citazione ispirazionale breve",
      "corpo": ["colonna 1 (~90-120 parole)", "colonna 2 (~90-120 parole)"],
      "esercizi_intro": "Esercizi – [nome breve]",
      "esercizi": [
        {"titolo": "titolo esercizio", "prompt": "domanda/istruzione riflessiva, seconda persona"}
      ]
    }
  ],
  "integrazione_corpo": ["colonna 1 (~45-65 parole)", "colonna 2 (~45-65 parole)"],
  "esercizio_finale_titolo": "Esercizio finale – [nome breve]",
  "esercizio_finale_completamenti": ["Oggi scelgo di abitare di piu...", "Sono pronta a lasciare andare..."],
  "completamenti": ["La mia [tema] per me ora e...", "La mia [tema correlato] puo diventare...", "Da oggi mi permetto di..."],
  "completamenti_chiusura": "frase finale di incoraggiamento"
}
```

Rules — getting them wrong makes the boxes overflow or leaves fields unmapped:
- EXACTLY 4 sezioni; each with EXACTLY 2 `corpo` columns and EXACTLY 4 `esercizi`.
- EXACTLY 2 paragraphs in `lettera_corpo` and in `integrazione_corpo`.
- Every `corpo` column, and every `lettera_corpo`/`integrazione_corpo`
  string, is itself written as 3 short paragraphs (blank-line-separated,
  falling back to 2 or 1 for the short `integrazione` field when a 3-way
  split would leave a paragraph too thin — see `field_assembly.md`) — this
  is what makes each page read as a filled, breathable page instead of one
  dense block. Don't skip this or leave it for the Canva-filling step
  to patch on; draft it in from the start. On top of that, still mark
  **exactly 2 or 3 paragraphs per page** (not every paragraph) with a
  `**bolded phrase**` of just 3-5 words flagging that paragraph's core idea
  — but be aware this markup currently ships as plain text: the connected
  Canva tooling can't render partial bold within a text box (confirmed,
  not a maybe), so the markers get stripped rather than turned into actual
  bold formatting. Draft them anyway (cheap, self-documenting, forward
  compatible), just don't expect them to render. Exact rules, word counts,
  which paragraphs count as "the same page", and the current bold
  limitation: see `references/field_assembly.md`, "Paragraph rhythm & bold
  emphasis".
- EXACTLY 2 `esercizio_finale_completamenti`; EXACTLY 3 `completamenti`.
- Each esercizio has one `titolo` and one reflective `prompt` (second person). Do
  NOT add answer lines — the template adds them.
- Tone: warm, direct, feminine, encouraging — never generic. Each section a
  distinct theme that builds on the previous.
- Character budgets per body field, and how the drafted JSON turns into the 34
  literal Canva field values (fixed scaffolding for exercises/completamenti/
  esercizio_finale) — see `references/field_assembly.md`.

## Notes

- This is a pure Claude Code + MCP workflow — no local server, database, or API
  keys. Canva access is via the connected **Canva MCP integration**; theme and
  brand-voice sources come via the **Google Drive MCP integration**. There is no
  Python pipeline anymore (it was removed — the old FastAPI/Celery/Postgres/
  SendGrid/Anthropic-API/Canva-OAuth stack is gone from the repo; see git
  history before this skill's Canva-MCP rewrite if you ever need to reference
  the old implementation).
- Known template gap: the brand template (`EAHNaGY-7DM`) has no `cover_title`
  data field anywhere — `cover_title` in the JSON schema currently has nowhere to
  go in Canva. Mention this in your final report rather than silently dropping
  it; if it matters, ask Giusi to tag a cover-title text element in Canva.
- Background photos: the template's `sfondo_cover` and `sfondo_impressum`
  image fields are filled from a curated Canva folder of Giusi's photos, not
  generated or drafted — see `references/media_library.md` for where they
  live and how to pick one, and `references/canva_mcp_fill.md` step 6 for the
  placement mechanics. The third image field, `sfondo_pagina2`, is left
  unfilled on purpose.
