from unittest.mock import patch

from app.pipelines.workbook import backgrounds
from app.pipelines.workbook.backgrounds import BACKGROUND_FIELDS


def test_returns_none_when_no_folder_configured():
    with patch.object(backgrounds.settings, "canva_background_folder_id", ""):
        assert backgrounds.pick_background_fields("Luglio 2026") is None


def test_returns_none_when_folder_empty():
    with (
        patch.object(backgrounds.settings, "canva_background_folder_id", "FOLDER1"),
        patch.object(backgrounds.canva_client, "list_folder_image_assets", return_value=[]),
    ):
        assert backgrounds.pick_background_fields("Luglio 2026") is None


def test_picks_all_three_fields_from_folder():
    assets = ["MA_a", "MA_b", "MA_c"]
    with (
        patch.object(backgrounds.settings, "canva_background_folder_id", "FOLDER1"),
        patch.object(backgrounds.canva_client, "list_folder_image_assets", return_value=assets),
    ):
        result = backgrounds.pick_background_fields("Luglio 2026")

    assert set(result.keys()) == set(BACKGROUND_FIELDS)
    assert all(v in assets for v in result.values())


def test_selection_is_deterministic_per_edition():
    assets = ["MA_a", "MA_b", "MA_c", "MA_d"]
    with (
        patch.object(backgrounds.settings, "canva_background_folder_id", "FOLDER1"),
        patch.object(backgrounds.canva_client, "list_folder_image_assets", return_value=assets),
    ):
        first = backgrounds.pick_background_fields("Luglio 2026")
        again = backgrounds.pick_background_fields("Luglio 2026")
        other = backgrounds.pick_background_fields("Agosto 2026")

    assert first == again                     # same edition -> same choice
    assert first["sfondo_cover"] in assets
    # Different editions generally rotate to a different asset.
    assert other["sfondo_cover"] in assets
