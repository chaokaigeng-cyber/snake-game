# SUDA notice check

Status: disabled on 2026-06-30.

- Both GitHub Actions workflow files are manual-only no-op workflows and contain no scheduled triggers.
- The Python sender exits immediately unless `ENABLE_EMAIL=1` is explicitly set.
- No scheduled emails should be sent to `2418656381@qq.com`.

Disabled workflow files:

- `.github/workflows/suda-notice-check-beijing.yml`
- `.github/workflows/suda-notice-check.yml`

Sender script:

- `scripts/suda_notice_check.py`

To resume in the future, restore the intended schedule and set `ENABLE_EMAIL=1` only in the active sending workflow.
