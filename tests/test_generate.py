import json
from unittest.mock import patch

from app.pipelines.workbook.generate import (
    ANSWER_LINES,
    DOTTED_LINE,
    WorkbookContent,
    check_budgets,
    generate_workbook_content,
    workbook_to_canva_fields,
)


def _body(seed: str, target: int = 560) -> str:
    """A body string padded to ~target chars so it sits within FIELD_BUDGETS."""
    unit = seed.strip() + " "
    out = unit * (target // len(unit) + 1)
    return out[:target].strip()


def _section(n: int) -> dict:
    return {
        "numero": n,
        "titolo": f"Titolo sezione {n}",
        "citazione": f"Citazione della sezione {n}",
        "corpo": [_body(f"Corpo {n} colonna uno."), _body(f"Corpo {n} colonna due.")],
        "esercizi_intro": f"Esercizi – Sezione {n}",
        "esercizi": [
            {"titolo": f"Esercizio {n}.{i}", "prompt": f"Prompt riflessivo {n}.{i}?"}
            for i in range(1, 5)
        ],
    }


def _sample_dict() -> dict:
    return {
        "cover_title": "TORNARE ALLA TUA VOCE",
        "cover_subtitle": "Ritrova fiducia, radici e desiderio",
        "mantra_testo": "Ascolto la mia voce e le do spazio.",
        "intenzione_testo": "Scelgo di esprimere cio che sento.",
        "lettera_corpo": [_body("Cara lettrice, questo mese.", 540), _body("Ti abbraccio. Namaste,", 520)],
        "sezioni": [_section(1), _section(2), _section(3), _section(4)],
        "integrazione_corpo": [_body("Hai fatto un lavoro profondo.", 340), _body("Porta con te questo.", 360)],
        "esercizio_finale_titolo": "Esercizio finale – Il tuo ritorno a te",
        "esercizio_finale_completamenti": ["Oggi scelgo di dare voce a...", "Sono pronta a fidarmi di..."],
        "completamenti": ["La mia voce ora e...", "Il mio desiderio puo diventare...", "Da oggi mi permetto di..."],
        "completamenti_chiusura": "non devi chiedere il permesso per esistere pienamente.",
    }


_SAMPLE_JSON = json.dumps(_sample_dict())


def test_generate_returns_valid_workbook_content():
    with patch("app.integrations.claude_client.complete", return_value=_SAMPLE_JSON):
        content = generate_workbook_content("Giugno 2026", "tema", "obiettivi")
    assert isinstance(content, WorkbookContent)
    assert content.cover_title == "TORNARE ALLA TUA VOCE"
    assert len(content.sezioni) == 4
    assert all(len(s.corpo) == 2 for s in content.sezioni)
    assert all(len(s.esercizi) == 4 for s in content.sezioni)


def test_generate_includes_feedback_when_provided():
    captured = {}

    def mock_complete(system, user, **kwargs):
        captured["user"] = user
        return _SAMPLE_JSON

    with patch("app.integrations.claude_client.complete", side_effect=mock_complete):
        generate_workbook_content(
            mese="Giugno 2026", tema_principale="tema", obiettivi="obiettivi",
            reviewer_feedback="Aggiungere più esercizi pratici",
        )
    assert "Aggiungere più esercizi pratici" in captured["user"]


def test_generate_strips_markdown_fences():
    fenced = f"```json\n{_SAMPLE_JSON}\n```"
    with patch("app.integrations.claude_client.complete", return_value=fenced):
        content = generate_workbook_content("Giugno 2026", "tema", "obiettivi")
    assert content.cover_title == "TORNARE ALLA TUA VOCE"


# The 34 autofill field labels tagged in the rebuilt brand template.
_EXPECTED_FIELDS = {
    "cover_title", "cover_subtitle", "mantra_testo", "intenzione_testo",
    "lettera_testo_1", "lettera_testo_2",
    "toc_1", "toc_2", "toc_3", "toc_4",
    "sez1_titolo", "sez1_citazione", "sez1_testo_1", "sez1_testo_2", "sez1_esercizi",
    "sez2_titolo", "sez2_citazione", "sez2_testo_1", "sez2_testo_2", "sez2_esercizi",
    "sez3_titolo", "sez3_citazione", "sez3_testo_1", "sez3_testo_2", "sez3_esercizi",
    "sez4_titolo", "sez4_citazione", "sez4_testo_1", "sez4_testo_2", "sez4_esercizi",
    "integrazione_testo_1", "integrazione_testo_2", "esercizio_finale", "completamenti",
}


def _fields_from_sample() -> dict:
    with patch("app.integrations.claude_client.complete", return_value=_SAMPLE_JSON):
        content = generate_workbook_content("Giugno 2026", "tema", "obiettivi")
    return workbook_to_canva_fields(content)


def test_workbook_to_canva_fields_matches_template_labels():
    assert set(_fields_from_sample().keys()) == _EXPECTED_FIELDS


def test_canva_fields_total_count():
    assert len(_fields_from_sample()) == 34


def test_toc_is_subtitle_only():
    fields = _fields_from_sample()
    # No "SEZIONE N" prefix anymore — the label is a separate fixed box.
    assert fields["toc_1"] == "Titolo sezione 1"
    assert "SEZIONE" not in fields["toc_1"]


def test_exercise_block_structure():
    fields = _fields_from_sample()
    block = fields["sez1_esercizi"]
    assert block.startswith("Esercizi – Sezione 1")
    for i in range(1, 5):
        assert f"{i}. Esercizio 1.{i}" in block
    # 4 exercises x ANSWER_LINES dotted lines each.
    assert block.count(DOTTED_LINE) == 4 * ANSWER_LINES


def test_check_budgets_flags_out_of_range():
    fields = _fields_from_sample()
    assert check_budgets(fields) == []  # sample is calibrated within budget

    fields["sez1_testo_1"] = "troppo corto"
    violations = check_budgets(fields)
    assert any(v[0] == "sez1_testo_1" for v in violations)


def test_regeneration_triggered_when_too_short():
    short = _sample_dict()
    short["sezioni"][0]["corpo"][0] = "troppo corto"   # well under budget
    short_json = json.dumps(short)

    calls = {"n": 0}

    def mock_complete(system, user, **kwargs):
        calls["n"] += 1
        # First pass returns the too-short version, then the valid one.
        return short_json if calls["n"] == 1 else _SAMPLE_JSON

    with patch("app.integrations.claude_client.complete", side_effect=mock_complete):
        content = generate_workbook_content(
            "Giugno 2026", "tema", "obiettivi", max_length_iterations=2,
        )

    assert calls["n"] == 2  # regenerated once after the short first pass
    assert check_budgets(workbook_to_canva_fields(content)) == []
