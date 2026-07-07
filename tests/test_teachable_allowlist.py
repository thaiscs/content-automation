"""
Tests for the Teachable allowlist guard.

No real HTTP calls are made — the guard must fire before any network request.
"""

from unittest.mock import MagicMock, patch

import pytest


def _configure_allowlist(value: str):
    """Patch settings.teachable_allowed_course_ids for the duration of a test."""
    return patch("app.integrations.teachable_client.settings")


@pytest.fixture(autouse=True)
def reset_settings():
    yield


def test_allowed_course_passes():
    mock_settings = MagicMock()
    mock_settings.teachable_allowed_course_ids = "123456,789"
    mock_settings.teachable_api_key = "test_key"

    with patch("app.integrations.teachable_client.settings", mock_settings):
        from app.integrations import teachable_client

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"lesson": {"id": "lesson_1"}}
        mock_resp.raise_for_status = MagicMock()

        with patch("app.integrations.teachable_client.httpx.post", return_value=mock_resp):
            lesson_id = teachable_client.create_draft_lesson("123456", "Test Lesson")

    assert lesson_id == "lesson_1"


def test_disallowed_course_raises_before_network():
    mock_settings = MagicMock()
    mock_settings.teachable_allowed_course_ids = "123456"
    mock_settings.teachable_api_key = "test_key"

    with patch("app.integrations.teachable_client.settings", mock_settings):
        from app.integrations import teachable_client

        with patch("app.integrations.teachable_client.httpx.post") as mock_post:
            with pytest.raises(PermissionError, match="not in TEACHABLE_ALLOWED_COURSE_IDS"):
                teachable_client.create_draft_lesson("999999", "Test Lesson")

            mock_post.assert_not_called()


def test_empty_allowlist_raises():
    mock_settings = MagicMock()
    mock_settings.teachable_allowed_course_ids = ""
    mock_settings.teachable_api_key = "test_key"

    with patch("app.integrations.teachable_client.settings", mock_settings):
        from app.integrations import teachable_client

        with patch("app.integrations.teachable_client.httpx.post") as mock_post:
            with pytest.raises(PermissionError, match="not configured"):
                teachable_client.create_draft_lesson("123456", "Test Lesson")

            mock_post.assert_not_called()


def test_lesson_created_as_draft():
    """Verify the lesson payload always sets is_published: false."""
    mock_settings = MagicMock()
    mock_settings.teachable_allowed_course_ids = "123456"
    mock_settings.teachable_api_key = "test_key"

    with patch("app.integrations.teachable_client.settings", mock_settings):
        from app.integrations import teachable_client

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"lesson": {"id": "lesson_2"}}
        mock_resp.raise_for_status = MagicMock()
        captured = {}

        def capture_post(url, json=None, **kwargs):
            captured["json"] = json
            return mock_resp

        with patch("app.integrations.teachable_client.httpx.post", side_effect=capture_post):
            teachable_client.create_draft_lesson("123456", "My Lesson")

    assert captured["json"]["lesson"]["is_published"] is False
