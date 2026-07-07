"""
Claude-powered workbook content generation.

Produces a WorkbookContent object that maps to the named autofill fields tagged
in Giusi Valentini's Canva brand template (template id: EAHNaGY-7DM), which has a
**uniform** layout (see WORKBOOK_LAYOUT_SPEC.md):

  - each of the 4 sections = 2 pages: an intro page (2 body columns) + an
    exercises page (one box with 4 exercises, each with 3 answer lines)
  - Cara Homie letter = 1 page (2 columns)
  - fixed font sizes; pages are designed to be filled

34 autofill fields total:
    cover_title, cover_subtitle                         (p1, p2)
    mantra_testo, intenzione_testo                      (p3)
    lettera_testo_1, lettera_testo_2                    (p4)
    toc_1 .. toc_4                                       (p5, section subtitles)
    per section N: sezN_titolo, sezN_citazione,
                   sezN_testo_1, sezN_testo_2, sezN_esercizi
    integrazione_testo_1, integrazione_testo_2          (p14)
    esercizio_finale                                    (p14 block)
    completamenti                                       (p15 block)

"Fills the page" is enforced in two steps: Claude is told target lengths, and
`generate_workbook_content` then validates each body field against FIELD_BUDGETS
and **regenerates** (with targeted expand/trim feedback) until everything fits or
a max-iterations cap is reached.

Fixed (never autofilled): the "Cara Homie," greeting and "Giusi" signature, all
"SEZIONE N" / "Sezione N" labels, the "Contenuti"/"Integrazione finale" headings,
page numbers, © footers, the Impressum (p16).
"""

import json

from pydantic import BaseModel, model_validator

from app.integrations import claude_client

# ---------------------------------------------------------------------------
# Layout constants (uniform across all 4 sections)
# ---------------------------------------------------------------------------

SECTION_BODY_COLUMNS = 2     # intro page: two body columns
EXERCISES_PER_SECTION = 4    # exercises page: four exercises
ANSWER_LINES = 3             # dotted answer lines under each exercise prompt

# One full-width dotted answer line at font size 12 in the ~535px exercise/
# completion boxes. Tunable if the box width changes.
DOTTED_LINE = "." * 150

# Character budgets for the body fields, calibrated from the template's box
# geometry at font size 12 (height available to fill x column width). Only the
# fields whose *length* drives page fill are budgeted; titles, quotes, exercise
# prompts and the scaffolded blocks are naturally bounded. (min, max) inclusive.
# These are deliberately approximate and easy to tune.
FIELD_BUDGETS: dict[str, tuple[int, int]] = {
    "sez1_testo_1": (480, 720), "sez1_testo_2": (480, 720),
    "sez2_testo_1": (480, 720), "sez2_testo_2": (480, 720),
    "sez3_testo_1": (480, 720), "sez3_testo_2": (480, 720),
    "sez4_testo_1": (480, 720), "sez4_testo_2": (480, 720),
    "lettera_testo_1": (470, 700), "lettera_testo_2": (440, 670),
    "integrazione_testo_1": (250, 440), "integrazione_testo_2": (260, 450),
}

# Human-readable (Italian) descriptions for regeneration feedback.
def _field_description_it(field: str) -> str:
    if field.startswith("sez") and "_testo_" in field:
        n, col = field[3], field.split("_testo_")[1]
        return f"il corpo della Sezione {n}, colonna {col}"
    if field.startswith("lettera_testo_"):
        return f"la lettera 'Cara Homie', colonna {field.split('_')[-1]}"
    if field.startswith("integrazione_testo_"):
        return f"l'integrazione finale, colonna {field.split('_')[-1]}"
    return field


_SYSTEM_PROMPT = f"""Sei una formatrice esperta di crescita personale femminile che lavora con Giusi Valentini
per il programma Happy Daily Home (HDH). Crei il contenuto di un workbook mensile in italiano,
per donne che vogliono riconnettersi alla propria femminilità, sensualità e forza vitale.

Restituisci SOLO JSON valido secondo lo schema qui sotto — niente markdown, niente commenti.
Il contenuto riempie un layout grafico fisso: rispetta ESATTAMENTE il numero di paragrafi e di
esercizi richiesti. Ogni sezione ha una pagina introduttiva con DUE colonne di corpo e una pagina
di esercizi con QUATTRO esercizi.

LUNGHEZZE (importante per riempire le pagine, a corpo 12):
- Ogni colonna di corpo di sezione: circa 90-120 parole (550-680 caratteri).
- Ogni colonna della lettera 'Cara Homie': circa 85-110 parole.
- Ogni colonna dell'integrazione finale: circa 45-65 parole.

Schema JSON:
{{
  "cover_title": "titolo del tema del mese, MAIUSCOLO (es: COSA VUOI DAVVERO DALLA TUA VITA)",
  "cover_subtitle": "sottotitolo breve che descrive il percorso",
  "mantra_testo": "frase breve in prima persona al presente (es: Abito il mio corpo...)",
  "intenzione_testo": "frase breve in prima persona al presente, complementare al mantra",
  "lettera_corpo": ["paragrafo 1 della lettera personale", "paragrafo 2, che termina con 'Namaste,'"],
  "sezioni": [
    {{
      "numero": 1,
      "titolo": "sottotitolo descrittivo della sezione",
      "citazione": "citazione ispirazionale breve legata al tema della sezione",
      "corpo": ["colonna 1 del corpo (~90-120 parole)", "colonna 2 del corpo (~90-120 parole)"],
      "esercizi_intro": "Esercizi – [nome breve del lavoro della sezione]",
      "esercizi": [
        {{"titolo": "titolo esercizio (es: Che idea ho della femminilita)", "prompt": "domanda o istruzione riflessiva in seconda persona"}}
      ]
    }}
  ],
  "integrazione_corpo": ["colonna 1 (~45-65 parole)", "colonna 2 (~45-65 parole)"],
  "esercizio_finale_titolo": "Esercizio finale – [nome breve]",
  "esercizio_finale_completamenti": ["Oggi scelgo di abitare di piu...", "Sono pronta a lasciare andare..."],
  "completamenti": ["La mia [tema] per me ora e...", "La mia [tema correlato] puo diventare...", "Da oggi mi permetto di..."],
  "completamenti_chiusura": "frase finale di incoraggiamento"
}}

Regole:
- ESATTAMENTE 4 sezioni; ogni sezione ESATTAMENTE {SECTION_BODY_COLUMNS} colonne di corpo e
  ESATTAMENTE {EXERCISES_PER_SECTION} esercizi.
- Ogni esercizio ha un titolo e UN solo prompt riflessivo in seconda persona; NON inserire righe
  di puntini per le risposte (vengono aggiunte automaticamente).
- ESATTAMENTE 2 paragrafi per lettera_corpo e per integrazione_corpo; 2 esercizio_finale_completamenti;
  3 completamenti.
- Tono: caldo, diretto, femminile, incoraggiante — non new age generica. Ogni sezione un tema distinto.
"""


class Esercizio(BaseModel):
    titolo: str
    prompt: str


class Sezione(BaseModel):
    numero: int
    titolo: str
    citazione: str
    corpo: list[str]
    esercizi_intro: str
    esercizi: list[Esercizio]

    @model_validator(mode="after")
    def _check_shape(self) -> "Sezione":
        if self.numero not in (1, 2, 3, 4):
            raise ValueError(f"Sezione numero non valido: {self.numero}")
        if len(self.corpo) != SECTION_BODY_COLUMNS:
            raise ValueError(
                f"Sezione {self.numero}: attese {SECTION_BODY_COLUMNS} colonne di corpo, "
                f"ricevute {len(self.corpo)}"
            )
        if len(self.esercizi) != EXERCISES_PER_SECTION:
            raise ValueError(
                f"Sezione {self.numero}: attesi {EXERCISES_PER_SECTION} esercizi, "
                f"ricevuti {len(self.esercizi)}"
            )
        return self


class WorkbookContent(BaseModel):
    cover_title: str
    cover_subtitle: str
    mantra_testo: str
    intenzione_testo: str
    lettera_corpo: list[str]
    sezioni: list[Sezione]
    integrazione_corpo: list[str]
    esercizio_finale_titolo: str
    esercizio_finale_completamenti: list[str]
    completamenti: list[str]
    completamenti_chiusura: str

    @model_validator(mode="after")
    def _check_shape(self) -> "WorkbookContent":
        if len(self.sezioni) != 4:
            raise ValueError(f"Attese 4 sezioni, ricevute {len(self.sezioni)}")
        if len(self.lettera_corpo) != 2:
            raise ValueError("lettera_corpo deve avere esattamente 2 paragrafi")
        if len(self.integrazione_corpo) != 2:
            raise ValueError("integrazione_corpo deve avere esattamente 2 paragrafi")
        if len(self.esercizio_finale_completamenti) != 2:
            raise ValueError("esercizio_finale_completamenti deve avere esattamente 2 voci")
        if len(self.completamenti) != 3:
            raise ValueError("completamenti deve avere esattamente 3 voci")
        return self


# ---------------------------------------------------------------------------
# Field assembly
# ---------------------------------------------------------------------------

def _answer_lines() -> str:
    return "\n".join([DOTTED_LINE] * ANSWER_LINES)


def _render_exercise_block(sezione: Sezione) -> str:
    parts = [sezione.esercizi_intro]
    for i, ex in enumerate(sezione.esercizi, start=1):
        parts.append(f"{i}. {ex.titolo}\n\n{ex.prompt}\n{_answer_lines()}")
    return "\n\n".join(parts)


def workbook_to_canva_fields(content: WorkbookContent) -> dict[str, str]:
    """Map WorkbookContent to the 34 named autofill fields of the brand template."""
    fields: dict[str, str] = {
        "cover_title": content.cover_title,
        "cover_subtitle": content.cover_subtitle,
        "mantra_testo": content.mantra_testo,
        "intenzione_testo": content.intenzione_testo,
        "lettera_testo_1": content.lettera_corpo[0],
        "lettera_testo_2": content.lettera_corpo[1],
    }

    for sezione in content.sezioni:
        n = sezione.numero
        fields[f"toc_{n}"] = sezione.titolo                 # TOC subtitle only
        fields[f"sez{n}_titolo"] = sezione.titolo
        fields[f"sez{n}_citazione"] = sezione.citazione
        fields[f"sez{n}_testo_1"] = sezione.corpo[0]
        fields[f"sez{n}_testo_2"] = sezione.corpo[1]
        fields[f"sez{n}_esercizi"] = _render_exercise_block(sezione)

    fields["integrazione_testo_1"] = content.integrazione_corpo[0]
    fields["integrazione_testo_2"] = content.integrazione_corpo[1]

    finale_lines = [
        content.esercizio_finale_titolo,
        "Completa senza pensarci troppo:",
        *[f"{c}\n{_answer_lines()}" for c in content.esercizio_finale_completamenti],
    ]
    fields["esercizio_finale"] = "\n\n".join(finale_lines)

    completamenti_lines = [f"{c}\n{_answer_lines()}" for c in content.completamenti]
    completamenti_lines.append("Porta con te questo:")
    completamenti_lines.append(content.completamenti_chiusura)
    fields["completamenti"] = "\n\n".join(completamenti_lines)

    return fields


# ---------------------------------------------------------------------------
# Length validation (page-fill enforcement)
# ---------------------------------------------------------------------------

def check_budgets(fields: dict[str, str]) -> list[tuple[str, int, int, int]]:
    """Return [(field, length, min, max)] for every budgeted field out of range."""
    violations = []
    for field, (lo, hi) in FIELD_BUDGETS.items():
        length = len(fields.get(field, ""))
        if length < lo or length > hi:
            violations.append((field, length, lo, hi))
    return violations


def _length_feedback(violations: list[tuple[str, int, int, int]]) -> str:
    lines = []
    for field, length, lo, hi in violations:
        desc = _field_description_it(field)
        if length < lo:
            lines.append(f"- {desc}: troppo corto ({length} caratteri), allungalo a circa {lo}-{hi}.")
        else:
            lines.append(f"- {desc}: troppo lungo ({length} caratteri), accorcialo a circa {lo}-{hi}.")
    return (
        "\n\nIMPORTANTE — alcune parti non riempiono o sforano le caselle. "
        "Mantieni lo stesso significato ma correggi le lunghezze:\n" + "\n".join(lines)
    )


def _generate_once(system: str, user: str) -> WorkbookContent:
    raw = claude_client.complete(system=system, user=user, max_tokens=8000).strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return WorkbookContent(**json.loads(raw))


def generate_workbook_content(
    mese: str,
    tema_principale: str,
    obiettivi: str,
    reviewer_feedback: str | None = None,
    max_length_iterations: int = 2,
) -> WorkbookContent:
    """
    Generate a full workbook and validate that body fields fit their boxes.

    If any budgeted field is out of range, regenerate with targeted length
    feedback, up to `max_length_iterations` extra passes, then return the best
    available content.

    Args:
        mese: Month/edition label (e.g. "Giugno 2026")
        tema_principale: Core theme
        obiettivi: Learning objectives / what participants should experience
        reviewer_feedback: If set, Claude revises incorporating this feedback
        max_length_iterations: Extra regeneration passes allowed for length fixes
    """
    base_feedback = ""
    if reviewer_feedback:
        base_feedback = (
            f"\n\nIMPORTANTE — la versione precedente è stata rifiutata con questo feedback:\n"
            f"{reviewer_feedback}\n"
            f"Rivedi il workbook tenendo conto di questo feedback in modo approfondito."
        )

    base_user = (
        f"Mese/edizione: {mese}\n"
        f"Tema principale: {tema_principale}\n"
        f"Obiettivi del percorso: {obiettivi}"
        f"{base_feedback}"
    )

    content = _generate_once(_SYSTEM_PROMPT, base_user)

    for _ in range(max_length_iterations):
        violations = check_budgets(workbook_to_canva_fields(content))
        if not violations:
            break
        retry_user = base_user + _length_feedback(violations)
        content = _generate_once(_SYSTEM_PROMPT, retry_user)

    return content
