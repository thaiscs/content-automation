# HDH Workbook Generator

Generates Giusi Valentini's monthly "Happy Daily Home" (HDH) workbook — in
Italian, in her voice — and fills her Canva brand template with it.

This is a **Claude Code + MCP workflow**, not a hosted service: there's no
server, database, or API key to manage. Everything runs inside a Claude Code
session using the connected **Google Drive** MCP integration (brand voice +
theme) and **Canva** MCP integration (filling the design). This repo holds
the instructions and reference data that workflow runs on — not application
code.

## Quick start

- **Ad hoc:** run the `/generate-workbook` skill in a Claude Code session on
  this repo (optionally `--month YYYY-MM` for a specific edition).
- **Scheduled:** [`Routine_Prompt.md`](Routine_Prompt.md) is the Instructions
  payload for a [claude.ai/code/routines](https://claude.ai/code/routines)
  cloud routine that runs this monthly — see that file for the exact setup
  (which connectors it needs, the cron schedule).

Either path reports back a Canva edit URL
(`https://www.canva.com/design/<design_id>/edit`) for Giusi to review and
finalize by hand in Canva. No email is sent automatically.

- **After approval:** once Giusi has finalized a design in Canva, run the
  `/finalize-workbook` skill (giving it that Canva URL) to turn it into a
  fillable PDF — real form fields over the answer lines, typeable on
  desktop or mobile. This is a separate, explicitly-triggered step; it
  never runs automatically off the back of generation. See
  [`.claude/skills/finalize-workbook/SKILL.md`](.claude/skills/finalize-workbook/SKILL.md).

## How it works

1. **Theme.** [`content_plan.toml`](content_plan.toml) holds each edition's
   `tema` (theme) and `obiettivi` (objectives), keyed by `YYYY-MM`, filled in
   by Giusi a few editions ahead. The skill cross-checks this against the
   "Temi mensili" list in the onboarding brand-voice Google Doc and stops
   rather than guessing if a month has no entry, or if the two sources
   disagree on the concept (not just the wording).
2. **Voice.** [`brand_voice/`](brand_voice/) holds the sources that make the
   output sound like Giusi, not generic AI copy — see
   [`brand_voice/README.md`](brand_voice/README.md) for the live-Doc +
   git-snapshot hybrid model.
3. **Content.** Drafted to a fixed 34-field schema (cover, mantra, a 4-section
   body with exercises, closing completions) documented in
   [`SKILL.md`](.claude/skills/generate-workbook/SKILL.md), with per-field
   length budgets and exact text-assembly rules in
   [`references/field_assembly.md`](.claude/skills/generate-workbook/references/field_assembly.md).
4. **Canva.** Filled directly via the Canva MCP connector into brand template
   `EAHNaGY-7DM` (a fixed 15-page layout) — procedure, known template gaps,
   and gotchas hit in practice (an autoshrink bug, stray inherited
   formatting, dual-use TOC elements) are in
   [`references/canva_mcp_fill.md`](.claude/skills/generate-workbook/references/canva_mcp_fill.md).

## Repository layout

```
content_plan.toml           Monthly theme + objectives (keyed by YYYY-MM)
brand_voice/                Voice sources: live Google Doc snapshots + local supplement
Routine_Prompt.md           Instructions payload for the scheduled cloud routine
.claude/skills/generate-workbook/
  SKILL.md                  The workflow: theme → voice → draft → fill Canva
  references/
    field_assembly.md       Character budgets + how drafted JSON becomes Canva field text
    canva_mcp_fill.md       Canva MCP fill procedure, template layout, known gotchas
.claude/skills/finalize-workbook/
  SKILL.md                  Post-approval workflow: export Canva PDF → add fillable fields
  references/
    coordinate_extraction.md  How to find each answer line's PDF coordinates
  scripts/
    add_form_fields.py      Authors real AcroForm text-field widgets onto a flat PDF
    detect_dotlines.py      Finds each answer's dot-run position(s) in the exported PDF
    check_fields.py         Validates a fields.json before authoring (overlaps, dupes)
    get_page_sizes.py       Prints PDF page sizes in points, for coordinate conversion
    render_with_fields.py   Renders pages with field rects outlined, for visual QA
```

## History note

This repo previously ran on a Python backend (FastAPI + Celery + Postgres +
SendGrid + a direct Anthropic API call + Canva's OAuth Autofill API). That's
been removed: content generation now runs on the Claude subscription via the
skill above, and Canva filling goes through the Canva MCP connector instead
of a REST API call — nothing here was actually using the old stack anymore.
The removed code (and the design rationale that led to the current Canva
template layout) is still available in git history prior to the "Remove the
Python pipeline" commit, if it's ever needed for reference.
