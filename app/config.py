from pathlib import Path

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


def _read_secret(name: str) -> str | None:
    path = Path(f"/run/secrets/{name}")
    if path.exists():
        return path.read_text().strip()
    return None


class Settings(BaseSettings):
    # Anthropic
    anthropic_api_key: str = ""

    # Canva
    canva_client_id: str = ""
    canva_client_secret: str = ""
    canva_template_id: str = ""
    # Folder of curated background photos; a new one is picked per edition.
    # Leave empty to keep the template's default backgrounds.
    canva_background_folder_id: str = ""
    # OAuth (authorization-code flow). The refresh token is obtained once via
    # scripts/canva_auth.py and then auto-renews. It is stored in a file (not a
    # plain env var) because Canva rotates it on every use and the app rewrites it.
    # Must match the redirect URI registered in the Canva Developer Portal exactly.
    canva_redirect_uri: str = "http://127.0.0.1:8000/oauth/callback"
    canva_scopes: str = (
        "design:content:read design:content:write design:meta:read "
        "brandtemplate:content:read brandtemplate:meta:read"
    )
    canva_refresh_token_path: str = "secrets/canva_refresh_token"

    # Teachable
    teachable_api_key: str = ""
    # Comma-separated list of course IDs the pipeline is allowed to touch.
    # Start with a test course ID only; add the real course after POC validation.
    teachable_allowed_course_ids: str = ""

    # Email
    sendgrid_api_key: str = ""
    reviewer_email: str = ""
    # Sender address — must be a verified sender/domain in SendGrid.
    email_from: str = "noreply@giusivalentini.com"

    # App
    base_url: str = "http://localhost:8000"
    workbook_schedule_cron: str = "0 9 * * 1"
    max_regeneration_iterations: int = 5

    # Infrastructure
    database_url: str = "postgresql://postgres:postgres@localhost:5432/content_workflow"
    redis_url: str = "redis://localhost:6379/0"

    def model_post_init(self, __context: object) -> None:
        # Docker secrets override env vars when present
        secret_fields = [
            "anthropic_api_key",
            "canva_client_id",
            "canva_client_secret",
            "canva_template_id",
            "teachable_api_key",
            "sendgrid_api_key",
            "reviewer_email",
        ]
        for field in secret_fields:
            secret_value = _read_secret(field)
            if secret_value:
                object.__setattr__(self, field, secret_value)

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
