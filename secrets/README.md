# Production secrets

This directory holds Docker secret files for production. **The secret values themselves are gitignored** — only this README is committed.

Each secret is a single file containing one value, no quotes, no trailing newline. `docker-compose.yml` mounts these at `/run/secrets/<name>`, and `app/config.py` reads them (taking precedence over env vars).

## Files to create

| File | Value |
|---|---|
| `anthropic_api_key` | Anthropic API key |
| `canva_client_id` | Canva Connect integration Client ID |
| `canva_client_secret` | Canva Connect integration Client Secret |
| `canva_template_id` | Canva brand template ID (`DAF...`) |
| `teachable_api_key` | Teachable API key |
| `sendgrid_api_key` | SendGrid API key |
| `reviewer_email` | Email address that receives review requests |

> Note: `TEACHABLE_ALLOWED_COURSE_IDS` is **not** a secret — it's a plain env var in `docker-compose.yml` so the allowlist stays auditable.

## Creating a secret (no trailing newline)

```bash
printf '%s' 'your-value-here' > secrets/canva_client_secret
chmod 600 secrets/canva_client_secret
```

## Local development

For local dev you don't need these files — use the `.env` file in the project root instead. `config.py` falls back to env vars when `/run/secrets/` is absent.
