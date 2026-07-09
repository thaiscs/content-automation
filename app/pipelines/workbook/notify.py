"""
Reviewer notifications for the workbook pipeline.

Single source of truth for the "workbook ready" and "no theme planned" emails,
shared by the monthly cron (run_monthly.py) and the Canva fill script
(fill_canva.py). Falls back to stdout when email isn't configured.
"""

from app.config import settings
from app.integrations import sendgrid_client

_READY_EMAIL = """
<html><body style="font-family:sans-serif;max-width:600px;margin:auto;padding:24px">
  <h2>Il workbook di {label} è pronto ✨</h2>
  <p>Ho generato la bozza di questo mese in Canva. Aprila per rivederla,
     modificarla e finalizzarla.</p>
  <p style="margin:24px 0">
    <a href="{edit_url}"
       style="background:#6366f1;color:#fff;padding:12px 24px;border-radius:6px;text-decoration:none">
      ✏️ Apri e modifica in Canva
    </a>
  </p>
  <p style="color:#6b7280;font-size:13px">Tema del mese: {tema}</p>
</body></html>
"""

_NO_PLAN_EMAIL = """
<html><body style="font-family:sans-serif;max-width:600px;margin:auto;padding:24px">
  <h2>Nessun tema pianificato per {label}</h2>
  <p>Non ho trovato una voce per <strong>{key}</strong> in content_plan.toml,
     quindi non ho generato nessun workbook questo mese.</p>
  <p>Aggiungi il tema e gli obiettivi per {label} nel file di pianificazione,
     poi potrò rigenerarlo.</p>
</body></html>
"""


def _send(subject: str, html: str) -> bool:
    """Send via SendGrid if configured; otherwise print and return False."""
    if settings.sendgrid_api_key and settings.reviewer_email:
        sendgrid_client.send_email(to=settings.reviewer_email, subject=subject, html_body=html)
        return True
    print(f"[email skipped — SENDGRID_API_KEY/REVIEWER_EMAIL not set]\n  subject: {subject}")
    return False


def send_ready(edition_label: str, edit_url: str, tema: str = "") -> bool:
    return _send(
        subject=f"[HDH] Workbook {edition_label} pronto",
        html=_READY_EMAIL.format(label=edition_label, edit_url=edit_url, tema=tema),
    )


def send_no_plan(edition_label: str, key: str) -> bool:
    return _send(
        subject=f"[HDH] Nessun tema per {edition_label}",
        html=_NO_PLAN_EMAIL.format(label=edition_label, key=key),
    )
