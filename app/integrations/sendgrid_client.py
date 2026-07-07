import sendgrid
from sendgrid.helpers.mail import Mail

from app.config import settings

_client: sendgrid.SendGridAPIClient | None = None


def _get_client() -> sendgrid.SendGridAPIClient:
    global _client
    if _client is None:
        _client = sendgrid.SendGridAPIClient(api_key=settings.sendgrid_api_key)
    return _client


def send_email(to: str, subject: str, html_body: str) -> None:
    message = Mail(
        from_email="noreply@giusi-valentini.com",
        to_emails=to,
        subject=subject,
        html_content=html_body,
    )
    _get_client().send(message)


# Placeholder stubs for future integrations
class LibsynClient:
    """Fetch podcast episodes and transcripts from Libsyn. (Epic 2)"""
    pass


class MetaClient:
    """Publish posts to Meta Business Suite. (Epic 2)"""
    pass


class ManyChatClient:
    """Trigger ManyChat flows. (Future epic)"""
    pass


class FlodeskClient:
    """Add subscribers and send campaigns via Flodesk. (Future epic)"""
    pass
