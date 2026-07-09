from datetime import date

from app.pipelines.workbook import content_plan


def _write_plan(tmp_path, body: str):
    p = tmp_path / "content_plan.toml"
    p.write_text(body)
    return p


def test_load_existing_edition(tmp_path):
    plan = _write_plan(
        tmp_path,
        '["2026-07"]\ntema = "un tema"\nobiettivi = "degli obiettivi"\n',
    )
    ed = content_plan.load_edition(date(2026, 7, 15), plan_path=plan)
    assert ed is not None
    assert ed.key == "2026-07"
    assert ed.label == "Luglio 2026"
    assert ed.tema == "un tema"
    assert ed.obiettivi == "degli obiettivi"


def test_missing_edition_returns_none(tmp_path):
    plan = _write_plan(tmp_path, '["2026-07"]\ntema = "x"\n')
    assert content_plan.load_edition(date(2026, 8, 1), plan_path=plan) is None


def test_entry_without_tema_is_ignored(tmp_path):
    plan = _write_plan(tmp_path, '["2026-07"]\nobiettivi = "solo obiettivi"\n')
    assert content_plan.load_edition(date(2026, 7, 1), plan_path=plan) is None


def test_missing_plan_file_returns_none(tmp_path):
    assert content_plan.load_edition(date(2026, 7, 1), plan_path=tmp_path / "nope.toml") is None


def test_edition_label_italian():
    assert content_plan.edition_label(date(2026, 12, 1)) == "Dicembre 2026"
    assert content_plan.edition_label(date(2027, 1, 1)) == "Gennaio 2027"
