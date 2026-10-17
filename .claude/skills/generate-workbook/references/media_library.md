# Giusi's curated photo library (Canva)

Source for the workbook's two background-photo fields, `sfondo_cover` and
`sfondo_impressum` (see `canva_mcp_fill.md` step 6 — the template's third
image field, `sfondo_pagina2`, is deliberately left unfilled). All access is
via the connected **Canva MCP integration**, read-only — this library lives
in the same Canva account as the brand template, not in this repo.

## Location

Root folder: **"For Claude"** — id `FAHSRkksV60`
(`https://www.canva.com/folder/FAHSRkksV60`). It contains 9 subfolders, each a
curated best-of selection (~4-20 photos) from one photoshoot or era, pulled
out of the account's much larger general Uploads pool specifically so this
skill has a clean, pre-vetted set to pick from instead of wading through
thousands of unrelated screenshots and graphics.

| Subfolder | Folder ID | Mood / context | Good fit for |
|---|---|---|---|
| Giusi - Ritratti 2025 (Laura Hoffmann) | `FAHS6zTBJvY` | Polished, professional, most recent shoot | Default/general-purpose — clean warm portraits, works for almost any theme |
| Giusi - Nov 2021 (Laura Hoffmann) | `FAHS6xo5Vls` | Largest shoot, most variety (garden, indoor, b/w variants) | When you want more options to browse; general-purpose |
| Giusi - Mai 2022 (Laura Hoffmann) | `FAHS65Lrwo8` | Professional portraits, different season/setting from Nov21 | General-purpose alternative to avoid repeating Nov21/2025 every month |
| Giusi - Retreat Maggio 2024 | `FAHS6xi96ZU` | Outdoor, retreat, community energy | Themes about connection, nature, retreats, slowing down |
| Giusi - Casual Dez20 e Journal | `FAHS60_GwB8` | Candid lifestyle: calls, journaling, workouts, everyday moments | Themes about routine, reflection, journaling, daily habits |
| Giusi - Giugno 2019 | `FAHS66ej3hY` | Earlier, more casual portraits | Occasional variety; less polished than the 2021+ shoots |
| Giusi - Selezione 2020 (Finalen) | `FAHS62Dv5vw` | Team's own pre-curated "best of" picks from a 2020 shoot | Safe generic default when no theme-specific folder fits |
| Giusi - Branded Agosto 2025 | `FAHS6-J3b9I` | Category-specific branded shots: business, digital/desk, podcast, phone call, tea+sofa, front portrait | Themes that map to a specific context — e.g. "Digital Detox" → the digital/desk photo (`Giusi_Digital_51.jpg`) |
| Giusi - Varie | `FAHS6xUN308` | Miscellaneous named singles (e.g. a NYC trip photo) | Occasional variety; use sparingly, content is a grab-bag |

Only photos of Giusi Valentini live here — nothing else in the account's
Uploads pool should ever be used for the `sfondo_cover`/`sfondo_impressum`
fields.

## How to browse and pick a photo

1. `mcp__Canva__list-folder-items(folder_id: "<subfolder id>", item_types: ["image"])`
   returns each photo's asset id, filename, and a thumbnail — enough to judge
   fit without opening Canva.
2. Pick the subfolder whose mood/context matches the month's `tema` (see the
   table above). If nothing obviously matches, default to **Selezione 2020
   (Finalen)** or **Ritratti 2025** — both are safe, generically warm choices.
3. Within the chosen subfolder, pick one photo for `sfondo_cover` and one for
   `sfondo_impressum`. You can reuse the same photo for both (simplest,
   consistent look) or pick two different ones from the same subfolder for
   variety — judgment call, no fixed rule. Avoid reusing the *exact same*
   photo two months in a row if you have a way to check (e.g. last month's
   `out/workbook-<YYYY-MM>.json` if one was kept, or the previous design's
   title/thumbnail).
4. Note the asset id (`MA...`) — that's what `update_fill` needs in
   `canva_mcp_fill.md` step 6.

## Maintaining this library

This folder structure was built by a one-time manual curation pass over the
account's full Uploads history (583 raw candidate photos → 88 curated). It
won't grow or refresh itself — if Giusi's team uploads a new shoot, someone
(a person, or a future Claude session asked explicitly) needs to review and
add a new subfolder the same way. Don't treat an empty-feeling subfolder as a
signal to go trawling the general Uploads pool for more — that pool contains
thousands of unrelated files and re-sweeping it is a substantial standalone
task, not something to do inline during a routine workbook run.
