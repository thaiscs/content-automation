# Running the monthly workbook job on macOS

The monthly job is a single script — `scripts/run_monthly.py` — scheduled with
**launchd** (macOS's native scheduler; more reliable than cron for this).

## What the job does

On the 1st of each month it: looks up the month's theme in `content_plan.toml`,
has Claude generate the workbook, autofills the Canva template, and emails Giusi
the Canva edit link. If no theme is planned for the month, it emails a heads-up
and stops.

## Prerequisites (one-time)

1. Fill these in `.env`:
   - `ANTHROPIC_API_KEY`
   - `SENDGRID_API_KEY`, `REVIEWER_EMAIL`, and `EMAIL_FROM` (a **verified sender** in SendGrid)
   - Canva vars (already set) — and run `scripts/canva_auth.py` once
2. Add upcoming months to `content_plan.toml`
3. Confirm a manual run works end-to-end:
   ```bash
   .venv/bin/python scripts/run_monthly.py --month 2026-07
   ```

## Install the schedule

Create `~/Library/LaunchAgents/com.hdh.workbook.monthly.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.hdh.workbook.monthly</string>

  <key>ProgramArguments</key>
  <array>
    <string>/Users/niklasvanlunteren/thais/giusi-valentini/content-automation/.venv/bin/python</string>
    <string>/Users/niklasvanlunteren/thais/giusi-valentini/content-automation/scripts/run_monthly.py</string>
  </array>

  <!-- Critical: relative paths (.env, content_plan.toml, secrets/) resolve from here -->
  <key>WorkingDirectory</key>
  <string>/Users/niklasvanlunteren/thais/giusi-valentini/content-automation</string>

  <!-- 1st of every month at 09:00 -->
  <key>StartCalendarInterval</key>
  <dict>
    <key>Day</key><integer>1</integer>
    <key>Hour</key><integer>9</integer>
    <key>Minute</key><integer>0</integer>
  </dict>

  <key>StandardOutPath</key>
  <string>/Users/niklasvanlunteren/thais/giusi-valentini/content-automation/logs/monthly.out.log</string>
  <key>StandardErrorPath</key>
  <string>/Users/niklasvanlunteren/thais/giusi-valentini/content-automation/logs/monthly.err.log</string>
</dict>
</plist>
```

Then:

```bash
mkdir -p logs
launchctl load ~/Library/LaunchAgents/com.hdh.workbook.monthly.plist
```

## Test it fires (without waiting for the 1st)

```bash
launchctl start com.hdh.workbook.monthly     # run it now
cat logs/monthly.out.log logs/monthly.err.log
```

## Manage it

```bash
launchctl list | grep hdh                     # is it registered?
launchctl unload ~/Library/LaunchAgents/com.hdh.workbook.monthly.plist   # disable
```

## Important caveats for a Mac

- **The Mac must be awake at 09:00 on the 1st.** If it's asleep, launchd runs the
  job at the next wake (it won't be skipped, just delayed). If the Mac is fully
  shut down, the run is missed until next boot. For reliability, either keep the
  Mac awake (Energy Saver → prevent sleep, or `caffeinate`) or move to an
  always-on Linux host later.
- **The refresh token rotates** each run and is rewritten to
  `secrets/canva_refresh_token`. Keep that file writable and backed up.
- **Failures surface in the logs** (`logs/monthly.err.log`) and, for the
  no-theme case, as an email. Check the logs after the first scheduled run.
