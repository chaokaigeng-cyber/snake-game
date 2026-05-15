from __future__ import annotations

import os
import re
import smtplib
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import parsedate_to_datetime
from html import unescape
from typing import Iterable, List
from urllib.parse import quote, urljoin
from urllib.request import urlopen

LIST_URL = "https://yjs.suda.edu.cn/8386/list.htm"
NEWS_RSS_URL = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
DEFAULT_RECIPIENT = "2418656381@qq.com"
TZ = timezone(timedelta(hours=8))


@dataclass
class Notice:
    title: str
    url: str
    date: str


@dataclass
class NewsItem:
    title: str
    source: str
    source_url: str
    link: str
    published_at: str


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
        lines.append(f"{index}. {item.title}")
        lines.append(f"来源：{item.source}")
        lines.append(f"时间：{item.published_at}")
        lines.append(f"链接：{item.link}")
        if item.source_url:
            lines.append(f"来源站点：{item.source_url}")
        lines.append("")
    return lines


def build_body(now: datetime) -> str:
    html = fetch_html(LIST_URL)
    notices = parse_list(html)
    recent = filter_recent(notices, now)
    ai_items = parse_google_news_feed(
        '"artificial intelligence" OR "generative AI" OR OpenAI OR Anthropic OR Nvidia when:1d (site:reuters.com OR site:apnews.com OR site:techcrunch.com)',
        3,
    )
    politics_items = parse_google_news_feed(
        'election OR president OR prime minister OR parliament OR sanctions OR summit when:1d (site:reuters.com OR site:apnews.com OR site:bbc.com)',
        5,
    )
    finance_items = parse_google_news_feed(
        'stocks OR inflation OR central bank OR earnings OR tariffs when:1d (site:reuters.com OR site:cnbc.com OR site:bloomberg.com)',
        2,
    )

    lines = [f"检查时间：{now.strftime('%Y-%m-%d %H:%M:%S %z')}", ""]
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

    lines.extend(build_section("二、AI热点（3条）", ai_items))
    lines.extend(build_section("三、世界政治热点（5条）", politics_items))
    lines.extend(build_section("四、财经热点（2条）", finance_items))
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
    body = build_body(now)
    send_email("苏大消息检查", body)
    print(body)


if __name__ == "__main__":
    main()
