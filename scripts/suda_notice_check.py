from __future__ import annotations

import os
import re
import smtplib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from html import unescape
from typing import List
from urllib.parse import urljoin
from urllib.request import urlopen

LIST_URL = "https://yjs.suda.edu.cn/8386/list.htm"
DEFAULT_RECIPIENT = "2418656381@qq.com"
TZ = timezone(timedelta(hours=8))


@dataclass
class Notice:
    title: str
    url: str
    date: str


def fetch_html(url: str) -> str:
    with urlopen(url, timeout=20) as response:
        return response.read().decode("utf-8", "replace")


def parse_list(html: str) -> List[Notice]:
    pattern = re.compile(
        r'<li class="news-list-item">\s*<a href="(?P<href>[^"]+)" title="(?P<title>[^"]+)">.*?'
        r'<div class="date">\s*<span>(?P<day>\d{1,2})</span>\s*<b>(?P<year_month>\d{4}\.\d{2})</b>',
        re.S,
    )
    notices: List[Notice] = []
    for match in pattern.finditer(html):
        year_month = match.group("year_month")
        day = match.group("day").zfill(2)
        notices.append(
            Notice(
                title=unescape(match.group("title")).strip(),
                url=urljoin(LIST_URL, match.group("href")),
                date=f"{year_month}.{day}",
            )
        )
    return notices


def filter_recent(notices: List[Notice], now: datetime) -> List[Notice]:
    cutoff = now - timedelta(hours=24)
    recent: List[Notice] = []
    for notice in notices:
        notice_dt = datetime.strptime(notice.date, "%Y.%m.%d").replace(tzinfo=TZ)
        # The source page exposes only date precision. Use local midnight for a
        # deterministic approximation of the user's 24-hour rule.
        if notice_dt >= cutoff.replace(hour=0, minute=0, second=0, microsecond=0):
            recent.append(notice)
    return recent


def build_body(now: datetime, recent: List[Notice]) -> str:
    if not recent:
        return "无"

    lines = [f"检查时间：{now.strftime('%Y-%m-%d %H:%M:%S %z')}", "", "24小时内新通知：", ""]
    for index, notice in enumerate(recent, start=1):
        lines.append(f"{index}. {notice.title}")
        lines.append(f"日期：{notice.date}")
        lines.append(f"链接：{notice.url}")
        lines.append("")
    return "\n".join(lines).strip()


def send_email(subject: str, body: str) -> None:
    sender = os.environ["GMAIL_USERNAME"]
    password = os.environ["GMAIL_APP_PASSWORD"]
    recipient = os.environ.get("RECIPIENT_EMAIL", DEFAULT_RECIPIENT)

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
        smtp.login(sender, password)
        smtp.send_message(msg)


def main() -> None:
    now = datetime.now(TZ)
    html = fetch_html(LIST_URL)
    notices = parse_list(html)
    recent = filter_recent(notices, now)
    body = build_body(now, recent)
    send_email("苏大消息检查", body)
    print(body)


if __name__ == "__main__":
    main()
