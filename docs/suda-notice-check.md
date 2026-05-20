# SUDA notice check

This repository hosts a cloud-based check for:

- https://yjs.suda.edu.cn/8386/list.htm

Schedule:

- GitHub Actions workflow: `.github/workflows/suda-notice-check-beijing.yml`
- GitHub Actions cron `0 2,14 * * *`
- Equivalent to `10:00` and `22:00` in `Asia/Shanghai` / Beijing time
- Current effective schedule: twice daily at 10:00 and 22:00 Beijing time

Behavior:

- The SUDA section uses a date-based fallback rule because the source page exposes dates but not precise publish times.
- Notices dated today or yesterday are included, so a newly posted SUDA notice will appear in both daily mailings.
- If there are no such SUDA notices, send `无` for the SUDA section.
- Also include a 12-hour hot-topic digest from authoritative sites:
- 3 AI hot topics
- 5 world politics hot topics
- 2 finance hot topics
- Headlines are translated to Chinese, with original titles retained below each item.
- Current destination mailbox: `2418656381@qq.com`

Operational note:

- GitHub Actions scheduled workflows are cloud-based and do not depend on the local computer being powered on.
- GitHub scheduled workflow start times are not guaranteed to be exact; jobs can be delayed by GitHub queueing after the cron time.
- The previous workflow file `.github/workflows/suda-notice-check.yml` was removed after schedule runs continued near the old 12:00/00:00 times, forcing GitHub to register the refreshed Beijing-time workflow from a new file.

Required GitHub repository secrets:

- `GMAIL_USERNAME`: the Gmail address that sends the message
- `GMAIL_APP_PASSWORD`: a Gmail app password for that account

Files:

- `.github/workflows/suda-notice-check-beijing.yml`
- `scripts/suda_notice_check.py`
