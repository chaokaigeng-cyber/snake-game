# SUDA notice check

This repository hosts a cloud-based daily check for:

- https://yjs.suda.edu.cn/8386/list.htm

Schedule:

- GitHub Actions cron `0 4,16 * * *`
- Equivalent to `00:00` and `12:00` in `Asia/Shanghai`
- Start time: `2026-05-16 12:00 +08:00`

Behavior:

- Check the SUDA page for items within the last 12 hours. If there are none, send `无` for the SUDA section.
- Also include a 12-hour hot-topic digest from authoritative sites:
- 3 AI hot topics
- 5 world politics hot topics
- 2 finance hot topics
- Headlines are translated to Chinese, with original titles retained below each item.
- Current destination mailbox: `2418656381@qq.com`

Known source limitation:

- The SUDA site list and article page expose date but not precise publish time, so the 12-hour judgment for SUDA notices is the narrowest reliable approximation available from the source itself.

Required GitHub repository secrets:

- `GMAIL_USERNAME`: the Gmail address that sends the message
- `GMAIL_APP_PASSWORD`: a Gmail app password for that account

Files:

- `.github/workflows/suda-notice-check.yml`
- `scripts/suda_notice_check.py`
