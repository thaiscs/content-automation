from unittest.mock import MagicMock, patch

import pytest

from app.integrations import canva_client


def _mock_token_response():
    resp = MagicMock()
    resp.json.return_value = {"access_token": "test_token", "expires_in": 3600}
    resp.raise_for_status = MagicMock()
    return resp


def test_create_design_returns_design_id():
    autofill_resp = MagicMock()
    autofill_resp.json.return_value = {"job": {"id": "job_123"}}
    autofill_resp.raise_for_status = MagicMock()

    poll_resp = MagicMock()
    poll_resp.json.return_value = {
        "job": {"status": "success", "result": {"design": {"id": "design_abc"}}}
    }
    poll_resp.raise_for_status = MagicMock()

    with (
        patch("app.integrations.canva_client.httpx.post", side_effect=[_mock_token_response(), autofill_resp]),
        patch("app.integrations.canva_client.httpx.get", return_value=poll_resp),
        patch("app.integrations.canva_client.time.sleep"),
    ):
        canva_client._token_cache.clear()
        design_id = canva_client.create_design_from_template({"title": "Test", "subtitle": "Sub"})

    assert design_id == "design_abc"


def test_create_design_includes_title_in_payload():
    autofill_resp = MagicMock()
    autofill_resp.json.return_value = {"job": {"id": "job_123"}}
    autofill_resp.raise_for_status = MagicMock()

    poll_resp = MagicMock()
    poll_resp.json.return_value = {
        "job": {"status": "success", "result": {"design": {"id": "design_abc"}}}
    }
    poll_resp.raise_for_status = MagicMock()

    captured = {}

    def fake_post(url, **kwargs):
        if url.endswith("/oauth/token"):
            return _mock_token_response()
        captured["payload"] = kwargs.get("json")
        return autofill_resp

    with (
        patch("app.integrations.canva_client.httpx.post", side_effect=fake_post),
        patch("app.integrations.canva_client.httpx.get", return_value=poll_resp),
        patch("app.integrations.canva_client.time.sleep"),
    ):
        canva_client._token_cache.clear()
        canva_client.create_design_from_template({"title": "T"}, title="WB HDH Luglio 2026")

    assert captured["payload"]["title"] == "WB HDH Luglio 2026"


def test_create_design_omits_title_when_not_given():
    autofill_resp = MagicMock()
    autofill_resp.json.return_value = {"job": {"id": "job_123"}}
    autofill_resp.raise_for_status = MagicMock()

    poll_resp = MagicMock()
    poll_resp.json.return_value = {
        "job": {"status": "success", "result": {"design": {"id": "design_abc"}}}
    }
    poll_resp.raise_for_status = MagicMock()

    captured = {}

    def fake_post(url, **kwargs):
        if url.endswith("/oauth/token"):
            return _mock_token_response()
        captured["payload"] = kwargs.get("json")
        return autofill_resp

    with (
        patch("app.integrations.canva_client.httpx.post", side_effect=fake_post),
        patch("app.integrations.canva_client.httpx.get", return_value=poll_resp),
        patch("app.integrations.canva_client.time.sleep"),
    ):
        canva_client._token_cache.clear()
        canva_client.create_design_from_template({"title": "T"})

    assert "title" not in captured["payload"]


def test_create_design_includes_image_fields_in_payload():
    autofill_resp = MagicMock()
    autofill_resp.json.return_value = {"job": {"id": "job_123"}}
    autofill_resp.raise_for_status = MagicMock()

    poll_resp = MagicMock()
    poll_resp.json.return_value = {
        "job": {"status": "success", "result": {"design": {"id": "design_abc"}}}
    }
    poll_resp.raise_for_status = MagicMock()

    captured = {}

    def fake_post(url, **kwargs):
        if url.endswith("/oauth/token"):
            return _mock_token_response()
        captured["payload"] = kwargs.get("json")
        return autofill_resp

    with (
        patch("app.integrations.canva_client.httpx.post", side_effect=fake_post),
        patch("app.integrations.canva_client.httpx.get", return_value=poll_resp),
        patch("app.integrations.canva_client.time.sleep"),
    ):
        canva_client._token_cache.clear()
        canva_client.create_design_from_template(
            {"cover_title": "T"}, image_fields={"sfondo_cover": "MAxyz123"}
        )

    data = captured["payload"]["data"]
    assert data["cover_title"] == {"type": "text", "text": "T"}
    assert data["sfondo_cover"] == {"type": "image", "asset_id": "MAxyz123"}


def test_export_design_pdf_returns_bytes():
    export_resp = MagicMock()
    export_resp.json.return_value = {"job": {"id": "export_job_1"}}
    export_resp.raise_for_status = MagicMock()

    poll_resp = MagicMock()
    poll_resp.json.return_value = {
        "job": {"status": "success", "urls": ["https://example.com/file.pdf"]}
    }
    poll_resp.raise_for_status = MagicMock()

    pdf_resp = MagicMock()
    pdf_resp.content = b"%PDF-1.4 test"
    pdf_resp.raise_for_status = MagicMock()

    # token already cached from previous test or patch it
    canva_client._token_cache["token"] = "test_token"
    canva_client._token_cache["expires_at"] = 9999999999

    with (
        patch("app.integrations.canva_client.httpx.post", return_value=export_resp),
        patch("app.integrations.canva_client.httpx.get", side_effect=[poll_resp, pdf_resp]),
        patch("app.integrations.canva_client.time.sleep"),
    ):
        pdf = canva_client.export_design_pdf("design_abc")

    assert pdf == b"%PDF-1.4 test"


def test_get_design_edit_url_returns_editable_link():
    canva_client._token_cache["token"] = "test_token"
    canva_client._token_cache["expires_at"] = 9999999999

    design_resp = MagicMock()
    design_resp.json.return_value = {
        "design": {
            "urls": {
                "edit_url": "https://canva.com/design/DAxxxx/edit",
                "view_url": "https://canva.com/design/DAxxxx/view",
            }
        }
    }
    design_resp.raise_for_status = MagicMock()

    with patch("app.integrations.canva_client.httpx.get", return_value=design_resp):
        edit_url = canva_client.get_design_edit_url("DAxxxx")

    # Must return the editable URL, not the read-only view URL
    assert edit_url == "https://canva.com/design/DAxxxx/edit"
