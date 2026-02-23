"""
Pharma Daily Brief を自動生成するスクリプト
RSS から記事を取得し、Gemini API で要約・分類して index.html を生成します。
"""

import html
import json
import os
import re
from datetime import datetime
from pathlib import Path

import feedparser

# .env を読み込む
_env_file = Path(__file__).parent / ".env"
if _env_file.exists():
    with open(_env_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

RSS_FEEDS = [
    ("https://www.biopharmadive.com/feeds/news/", "BioPharma Dive"),
    ("https://www.fiercebiotech.com/rss/xml", "Fierce Biotech"),
    ("https://endpoints.news/feed/", "Endpoints News"),
]

CATEGORIES = ["pipeline", "regulatory", "deals", "earnings"]
REGIONS = ["US", "Europe", "China"]
OUTPUT_FILE = Path(__file__).parent / "index.html"


def fetch_articles(max_per_feed: int = 15) -> list[dict]:
    """RSS から記事を取得"""
    articles = []
    seen_urls = set()

    for url, source in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for i, entry in enumerate(feed.entries):
                if i >= max_per_feed:
                    break
                link = entry.get("link", "").strip()
                if not link or link in seen_urls:
                    continue
                seen_urls.add(link)

                desc = ""
                if entry.get("summary"):
                    desc = re.sub(r"<[^>]+>", "", entry.summary)[:300]
                elif entry.get("description"):
                    desc = re.sub(r"<[^>]+>", "", entry.description)[:300]
                desc = html.unescape(desc).strip()

                articles.append({
                    "title": html.unescape(entry.get("title", "")),
                    "url": link,
                    "description": desc,
                    "source": source,
                })
        except Exception as e:
            print(f"RSS fetch error ({source}): {e}")

    return articles


def summarize_with_gemini(articles: list[dict]) -> list[dict] | None:
    """Gemini API で要約・分類"""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY が未設定のため、RSS のみでフォールバックします。")
        return None

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            "gemini-1.5-flash",
            generation_config={"response_mime_type": "application/json"},
        )
    except ImportError:
        print("google-generativeai がインストールされていません。")
        return None

    article_text = "\n\n".join(
        f"[{i+1}] Title: {a['title']}\nURL: {a['url']}\nDescription: {a['description']}\nSource: {a['source']}"
        for i, a in enumerate(articles[:40])
    )

    prompt = f"""以下の医薬・バイオ業界の英語ニュース記事一覧から、最も重要な記事を最大10本選び、
日本語でサマリーを作成してください。

【対象の重点】
- 約9割は米国: FDA承認・申請、臨床試験、米国企業のM&A・決算
- 欧州: ノボノルディスク、BMS、サノフィ、ロッシュ、バイエルなど大手の重要ニュース
- 中国: 個別企業よりNMPAなど医薬品規制当局の大きな動向

【記事一覧】
{article_text}

【出力形式】以下のJSON形式のみで出力してください。他のテキストは含めないこと。
{{
  "articles": [
    {{
      "category": "pipeline|regulatory|deals|earnings",
      "region": "US|Europe|China",
      "title_ja": "日本語タイトル",
      "summary_ja": "2〜3文の日本語要約",
      "url": "元のURL",
      "source": "出典名",
      "entity": "企業名や組織名",
      "tag": "FDA承認やM&Aなどの短いタグ",
      "importance": 1
    }}
  ]
}}

importance は 1(高)〜3(低)、category は pipeline=臨床・承認、regulatory=規制、deals=M&A・ライセンス、earnings=決算。
"""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        # JSON ブロックを抽出（```で囲まれている場合）
        if "```" in text:
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        data = json.loads(text)
        return data.get("articles", [])[:10]
    except Exception as e:
        print(f"Gemini API error: {e}")
        return None


def build_fallback_articles(articles: list[dict]) -> list[dict]:
    """Gemini 失敗時のフォールバック: RSS の上位10本をそのまま使用"""
    result = []
    for a in articles[:10]:
        result.append({
            "category": "pipeline",
            "region": "US",
            "title_ja": a["title"],
            "summary_ja": a["description"][:200] + "…" if len(a["description"]) > 200 else a["description"],
            "url": a["url"],
            "source": a["source"],
            "entity": "",
            "tag": "",
            "importance": 2,
        })
    return result


def render_html(articles: list[dict]) -> str:
    """HTML を生成"""
    today = datetime.now()
    date_str = today.strftime("%Y年%m月%d日")
    weekday = ["月", "火", "水", "木", "金", "土", "日"][today.weekday()]

    def esc(s: str) -> str:
        return html.escape(str(s))

    def star_html(n: int) -> str:
        return "".join(
            f'<span class="star{" empty" if i >= n else ""}">★</span>'
            for i in range(4)
        )

    # カテゴリ別に記事をグループ化
    by_cat: dict[str, list] = {c: [] for c in CATEGORIES}
    for a in articles:
        cat = (a.get("category") or "pipeline").lower()
        if cat not in by_cat:
            by_cat[cat] = []
        by_cat[cat].append(a)

    cat_names = {
        "pipeline": "Pipeline",
        "regulatory": "Regulatory",
        "deals": "M&A & Licensing",
        "earnings": "Earnings",
    }

    cards_html = []
    for cat in CATEGORIES:
        items = by_cat.get(cat, [])
        if not items:
            continue
        cards_html.append(f'''
    <section class="category-section category-{cat}">
      <h2 class="category-header">
        <span class="badge"></span>
        {cat_names.get(cat, cat)}
      </h2>''')
        for a in items:
            imp = min(3, max(1, int(a.get("importance", 2))))
            region = (a.get("region") or "US").lower().replace(" ", "-")
            region_class = f"region-{region}" if region in ("us", "europe", "china") else "region-us"
            meta_parts = [f'<span class="region {region_class}">{a.get("region", "US")}</span>']
            if a.get("entity"):
                meta_parts.append(f'<span>{esc(a["entity"])}</span>')
            if a.get("tag"):
                meta_parts.append(f'<span>{esc(a["tag"])}</span>')
            meta_parts.append(f'<span class="importance">{star_html(imp)}</span>')

            cards_html.append(f'''
      <article class="article-card {cat}">
        <h3 class="title"><a href="{esc(a["url"])}" target="_blank" rel="noopener">{esc(a["title_ja"])}</a></h3>
        <p class="summary">{esc(a["summary_ja"])}</p>
        <div class="meta">
          {" ".join(meta_parts)}
        </div>
        <div class="link-wrap"><a href="{esc(a["url"])}" target="_blank" rel="noopener">{esc(a.get("source", ""))} </a></div>
      </article>''')
        cards_html.append("    </section>")

    body = "\n".join(cards_html)

    return f'''<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Pharma Daily Brief | PiercePharma 朝刊</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg-main: #0f1419;
      --bg-card: #1a2332;
      --bg-card-hover: #232f42;
      --text-primary: #e8edf4;
      --text-secondary: #94a3b8;
      --text-muted: #64748b;
      --accent-pipeline: #38bdf8;
      --accent-regulatory: #fb923c;
      --accent-deals: #4ade80;
      --accent-earnings: #a78bfa;
      --border: #2d3a4f;
      --link: #7dd3fc;
      --link-hover: #bae6fd;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'IBM Plex Sans', 'Noto Sans JP', sans-serif; background: var(--bg-main); color: var(--text-primary); line-height: 1.6; min-height: 100vh; padding: 24px 16px; }}
    .container {{ max-width: 720px; margin: 0 auto; }}
    .header {{ margin-bottom: 32px; padding-bottom: 20px; border-bottom: 1px solid var(--border); }}
    .header h1 {{ font-size: 1.5rem; font-weight: 700; letter-spacing: -0.02em; }}
    .header .date {{ font-size: 0.875rem; color: var(--text-muted); margin-top: 4px; font-weight: 500; }}
    .header .subtitle {{ font-size: 0.8125rem; color: var(--text-secondary); margin-top: 8px; }}
    .header .scope {{ font-size: 0.75rem; color: var(--text-muted); margin-top: 12px; padding: 10px 12px; background: var(--bg-card); border-radius: 6px; border: 1px solid var(--border); line-height: 1.5; }}
    .header .scope strong {{ color: var(--text-secondary); }}
    .category-section {{ margin-bottom: 28px; }}
    .category-header {{ display: flex; align-items: center; gap: 8px; margin-bottom: 12px; font-size: 0.8125rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }}
    .category-header .badge {{ width: 8px; height: 8px; border-radius: 50%; }}
    .category-pipeline .badge {{ background: var(--accent-pipeline); }} .category-pipeline .category-header {{ color: var(--accent-pipeline); }}
    .category-regulatory .badge {{ background: var(--accent-regulatory); }} .category-regulatory .category-header {{ color: var(--accent-regulatory); }}
    .category-deals .badge {{ background: var(--accent-deals); }} .category-deals .category-header {{ color: var(--accent-deals); }}
    .category-earnings .badge {{ background: var(--accent-earnings); }} .category-earnings .category-header {{ color: var(--accent-earnings); }}
    .article-card {{ background: var(--bg-card); border: 1px solid var(--border); border-left: 3px solid; border-radius: 8px; padding: 16px; margin-bottom: 12px; transition: background 0.2s; }}
    .article-card:hover {{ background: var(--bg-card-hover); }}
    .article-card.pipeline {{ border-left-color: var(--accent-pipeline); }}
    .article-card.regulatory {{ border-left-color: var(--accent-regulatory); }}
    .article-card.deals {{ border-left-color: var(--accent-deals); }}
    .article-card.earnings {{ border-left-color: var(--accent-earnings); }}
    .article-card .title {{ font-size: 1rem; font-weight: 600; margin-bottom: 8px; line-height: 1.4; }}
    .article-card .title a {{ color: var(--text-primary); text-decoration: none; transition: color 0.2s; }}
    .article-card .title a:hover {{ color: var(--link-hover); }}
    .article-card .summary {{ font-size: 0.875rem; color: var(--text-secondary); margin-bottom: 10px; line-height: 1.5; }}
    .article-card .meta {{ display: flex; flex-wrap: wrap; gap: 12px; font-size: 0.75rem; color: var(--text-muted); }}
    .article-card .meta span {{ display: inline-flex; align-items: center; gap: 4px; }}
    .article-card .link-wrap {{ margin-top: 10px; }}
    .article-card .link-wrap a {{ font-size: 0.8125rem; color: var(--link); text-decoration: none; transition: color 0.2s; }}
    .article-card .link-wrap a:hover {{ color: var(--link-hover); text-decoration: underline; }}
    .article-card .link-wrap a::after {{ content: '→'; }}
    .importance {{ display: inline-flex; gap: 2px; }}
    .importance .star {{ color: var(--accent-regulatory); font-size: 0.7rem; }}
    .importance .star.empty {{ color: var(--text-muted); opacity: 0.5; }}
    .article-card .meta .region {{ font-size: 0.7rem; padding: 2px 6px; border-radius: 4px; font-weight: 500; }}
    .region-us {{ background: rgba(56,189,248,0.2); color: var(--accent-pipeline); }}
    .region-europe {{ background: rgba(251,146,60,0.2); color: var(--accent-regulatory); }}
    .region-china {{ background: rgba(74,222,128,0.2); color: var(--accent-deals); }}
    @media (max-width: 480px) {{ body {{ padding: 16px 12px; }} .header h1 {{ font-size: 1.25rem; }} .article-card {{ padding: 14px; }} }}
  </style>
</head>
<body>
  <div class="container">
    <header class="header">
      <h1>Pharma Daily Brief</h1>
      <div class="date">{date_str}（{weekday}）</div>
      <div class="subtitle">パイプライン・規制・M&A・決算｜医薬・バイオ業界の重要ニュース（毎朝更新）</div>
      <div class="scope">
        <strong>対象地域：</strong>約9割は米国。欧州はノボノルディスク、ブリストルマイヤーズスクイーブ、サノフィ、ロッシュ、バイエルなど大手の重要ニュースを追加。中国は個別企業より<strong>医薬品規制当局の動向</strong>（変化が大きい場合）を掲載。
      </div>
    </header>

{body}

    <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid var(--border); font-size: 0.75rem; color: var(--text-muted);">
      Pharma Daily Brief — PiercePharma 朝刊 | 米国中心・欧州大手・中国規制を含む医薬・バイオ業界の重要ニュース
    </footer>
  </div>
</body>
</html>'''


def main() -> None:
    print("RSS を取得中...")
    articles = fetch_articles()
    print(f"取得: {len(articles)} 件")

    summarized = summarize_with_gemini(articles)
    if not summarized:
        print("Gemini スキップ、RSS フォールバックで生成します")
        summarized = build_fallback_articles(articles)

    html_content = render_html(summarized)
    OUTPUT_FILE.write_text(html_content, encoding="utf-8")
    print(f"出力: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
