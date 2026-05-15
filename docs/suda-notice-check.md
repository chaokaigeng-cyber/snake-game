# SUDA notice check

This repository hosts a cloud-based daily check for:

- https://yjs.suda.edu.cn/8386/list.htm

Schedule:

- GitHub Actions cron `0 1 * * *`
- Equivalent to `09:00` in `Asia/Shanghai`

Behavior:

- If there are SUDA notices judged to be within the last 24 hours, send them by email.
- If there are none, send `无` for the SUDA section.
- Also include a daily 24-hour hot-topic digest from authoritative sites:
- 3 AI hot topics
- 5 world politics hot topics
- 2 finance hot topics
- Current destination mailbox: `2418656381@qq.com`

Required GitHub repository secrets:

- `GMAIL_USERNAME`: the Gmail address that sends the message
- `GMAIL_APP_PASSWORD`: a Gmail app password for that account

Files:

- `.github/workflows/suda-notice-check.yml`
- `scripts/suda_notice_check.py`
