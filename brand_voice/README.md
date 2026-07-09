# Brand voice sources

The `generate-workbook` skill reads everything in this folder before drafting, so
the workbook sounds like Giusi — not like generic AI. Add real material here.

## What to put here

| File / folder | Why |
|---|---|
| `tone_guide.md` | The single most useful file — signature phrases, do's/don'ts, what to avoid (see the template) |
| `past-workbooks/` | Exported past workbooks (PDF/text) — structure, rhythm, exercise style |
| `podcast-transcripts/` | Transcripts of recent episodes — her spoken voice and phrasing |
| `social-captions.md` | A handful of strong, on-brand captions |
| Anything else on-voice | Newsletters, landing-page copy, etc. |

## Local vs. connectors

This folder is the **always-available** source. The skill also pulls live material
via MCP connectors (Libsyn, social, Drive) when they're available in the run — but
if a connector isn't there (e.g. a headless run), it falls back to this folder.
So keep at least `tone_guide.md` and a couple of references here.

## Privacy

Transcripts and past material may be private. This folder is committed by default;
if you'd rather not commit the raw material, add `brand_voice/` (or specific
subfolders) to `.gitignore` and keep them local.
