"""
구글 뉴스 RSS 수집기 — "LLM의 마법 주문서: Automate Anything" 뉴스 분석 시연용

사용법:
    pip install feedparser
    python google_news_rss.py                      # 기본: "인공지능"
    python google_news_rss.py 생성형AI 반도체        # 키워드 여러 개
    python google_news_rss.py 인공지능 --days 1     # 최근 1일만

결과:
    news_YYYYMMDD_HHMM.csv  (엑셀에서 바로 열림)
    news_YYYYMMDD_HHMM.md   (AI에 그대로 붙여 넣는 용도)
"""
import argparse
import csv
import sys
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

import feedparser

KST = timezone(timedelta(hours=9))


def fetch(keyword: str, days: int):
    url = (
        "https://news.google.com/rss/search?"
        f"q={quote(keyword)}+when:{days}d&hl=ko&gl=KR&ceid=KR:ko"
    )
    feed = feedparser.parse(url)
    rows = []
    for e in feed.entries:
        # 제목 끝의 " - 매체명"을 분리
        title = e.get("title", "")
        source = e.get("source", {}).get("title", "")
        if source and title.endswith(f" - {source}"):
            title = title[: -len(f" - {source}")]
        published = ""
        if e.get("published_parsed"):
            published = (
                datetime(*e.published_parsed[:6], tzinfo=timezone.utc)
                .astimezone(KST)
                .strftime("%Y-%m-%d %H:%M")
            )
        rows.append(
            {
                "keyword": keyword,
                "published_kst": published,
                "source": source,
                "title": title,
                "link": e.get("link", ""),
            }
        )
    return rows


def main():
    p = argparse.ArgumentParser()
    p.add_argument("keywords", nargs="*", default=["인공지능"])
    p.add_argument("--days", type=int, default=1)
    args = p.parse_args()

    all_rows, seen = [], set()
    for kw in args.keywords:
        for r in fetch(kw, args.days):
            if r["title"] in seen:  # 같은 기사 중복 제거
                continue
            seen.add(r["title"])
            all_rows.append(r)

    if not all_rows:
        print("받아온 기사가 없습니다. 네트워크나 키워드를 확인하세요.")
        sys.exit(1)

    all_rows.sort(key=lambda r: r["published_kst"], reverse=True)
    stamp = datetime.now(KST).strftime("%Y%m%d_%H%M")

    csv_path = f"news_{stamp}.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
        w.writeheader()
        w.writerows(all_rows)

    md_path = f"news_{stamp}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# 구글 뉴스 RSS 수집 ({stamp} KST)\n")
        f.write(f"키워드: {', '.join(args.keywords)} / 최근 {args.days}일 / {len(all_rows)}건\n\n")
        for i, r in enumerate(all_rows, 1):
            f.write(f"{i}. [{r['published_kst']}] {r['title']} — {r['source']}\n   {r['link']}\n")

    print(f"{len(all_rows)}건 저장: {csv_path}, {md_path}")


if __name__ == "__main__":
    main()
