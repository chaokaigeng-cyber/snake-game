from __future__ import annotations

import json
import os
import re
import smtplib
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import parsedate_to_datetime
from html import unescape
from typing import Iterable, List
from urllib.parse import quote, urljoin
from urllib.request import urlopen

LIST_URL = "https://yjs.suda.edu.cn/8386/list.htm"
NEWS_RSS_URL = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
TRANSLATE_URL = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=zh-CN&dt=t&q={query}"
DEFAULT_RECIPIENT = "2418656381@qq.com"
WINDOW_HOURS = 12
# Cloud schedule is 10:00 and 22:00 in Asia/Shanghai.
START_AT = datetime(2026, 5, 16, 12, 0, tzinfo=timezone(timedelta(hours=8)))
TZ = timezone(timedelta(hours=8))


@dataclass
class Notice:
    title: str
    url: str
    date: str


@dataclass
class NewsItem:
    title: str
    title_zh: str
    source: str
    source_url: str
    link: str
    published_at: str


def fetch_html(url: str) -> str:
    with urlopen(url, timeout=20) as response:
        return response.read().decode("utf-8", "replace")


def translate_to_zh(text: str) -> str:
    if not text:
        return text
    try:
        url = TRANSLATE_URL.format(query=quote(text))
        payload = json.loads(fetch_html(url))
        return "".join(part[0] for part in payload[0] if part and part[0]).strip() or text
    except Exception:
        return text


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


def filter_recent_notices(notices: List[Notice], now: datetime) -> List[Notice]:
    today = now.date()
    yesterday = today - timedelta(days=1)
    recent: List[Notice] = []
    for notice in notices:
        notice_day = datetime.strptime(notice.date, "%Y.%m.%d").date()
        if notice_day in {today, yesterday}:
            recent.append(notice)
    return recent


def parse_google_news_feed(query: str, limit: int) -> List[NewsItem]:
    url = NEWS_RSS_URL.format(query=quote(query))
    xml_text = fetch_html(url)
    root = ET.fromstring(xml_text)
    items: List[NewsItem] = []
    seen_titles: set[str] = set()
    for node in root.findall("./channel/item"):
        title_text = node.findtext("title", default="").strip()
        if not title_text:
            continue
        source_node = node.find("source")
        source = (source_node.text or "").strip() if source_node is not None else ""
        source_url = source_node.attrib.get("url", "") if source_node is not None else ""
        clean_title = re.sub(r"\s*-\s*[^-]+$", "", title_text).strip()
        if clean_title in seen_titles:
            continue
        seen_titles.add(clean_title)
        published_raw = node.findtext("pubDate", default="")
        published_dt = parsedate_to_datetime(published_raw).astimezone(TZ)
        items.append(
            NewsItem(
                title=clean_title,
                title_zh=translate_to_zh(clean_title),
                source=source,
                source_url=source_url,
                link=node.findtext("link", default="").strip(),
                published_at=published_dt.strftime("%Y-%m-%d %H:%M:%S %z"),
            )
        )
        if len(items) >= limit:
            break
    return items


def build_section(title: str, items: Iterable[NewsItem]) -> list[str]:
    lines = [title]
    for index, item in enumerate(items, start=1):
        lines.append(f"{index}. {item.title_zh}")
        lines.append(f"原题：{item.title}")
        lines.append(f"来源：{item.source}")
        lines.append(f"时间：{item.published_at}")
        lines.append(f"链接：{item.link}")
        if item.source_url:
            lines.append(f"来源站点：{item.source_url}")
        lines.append("")
    return lines


def build_output(now: datetime) -> dict:
    html = fetch_html(LIST_URL)
    notices = parse_list(html)
    recent = filter_recent_notices(notices, now)
    ai_items = parse_google_news_feed(
        '"artificial intelligence" OR "generative AI" OR OpenAI OR Anthropic OR Nvidia when:12h (site:reuters.com OR site:apnews.com OR site:techcrunch.com)',
        3,
    )
    politics_items = parse_google_news_feed(
        'election OR president OR prime minister OR parliament OR sanctions OR summit when:12h (site:reuters.com OR site:apnews.com OR site:bbc.com)',
        5,
    )
    finance_items = parse_google_news_feed(
        'stocks OR inflation OR central bank OR earnings OR tariffs when:12h (site:reuters.com OR site:cnbc.com OR site:bloomberg.com)',
        2,
    )

    lines = [
        f"检查时间：{now.strftime('%Y-%m-%d %H:%M:%S %z')}",
        f"热点统计窗口：近 {WINDOW_HOURS} 小时",
        "苏大消息规则：网站仅提供日期，因此当天和前一天的通知会在北京时间 10:00 和 22:00 两次邮件中重复带出",
        "",
    ]
    lines.append("一、苏大消息")
    if recent:
        for index, notice in enumerate(recent, start=1):
            lines.append(f"{index}. {notice.title}")
            lines.append(f"日期：{notice.date}")
            lines.append(f"链接：{notice.url}")
            lines.append("")
    else:
        lines.append("无")
        lines.append("")

    lines.extend(build_section("二、AI 热点（3条）", ai_items))
    lines.extend(build_section("三、世界政治热点（5条）", politics_items))
    lines.extend(build_section("四、财经热点（2条）", finance_items))
    body = "\n".join(lines).strip()
    return {
        "checked_at": now.isoformat(timespec="seconds"),
        "recent_notices": [asdict(n) for n in recent],
        "ai_items": [asdict(n) for n in ai_items],
        "politics_items": [asdict(n) for n in politics_items],
        "finance_items": [asdict(n) for n in finance_items],
        "body": body,
    }


def should_send(now: datetime) -> bool:
    if os.environ.get("FORCE_SEND") == "1":
        return True
    return now >= START_AT


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
    output = build_output(now)
    if os.environ.get("OUTPUT_MODE") == "body":
        print(output["body"])
        return
    if not should_send(now):
        print(f"Skipped until {START_AT.isoformat()}")
        return
    send_email("苏大消息检查", output["body"])
    print(output["body"])


if __name__ == "__main__":
    main()
