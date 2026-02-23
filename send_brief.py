"""
Pharma Daily Brief をHTMLメールで送信するスクリプト
毎朝実行することで index.html の内容を nzm0302@gmail.com に送信します。
"""

import os
from pathlib import Path

# .env があれば読み込む
_env_file = Path(__file__).parent / ".env"
if _env_file.exists():
    with open(_env_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

import re
import smtplib
from datetime import datetime

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# 設定
RECIPIENT = "nzm0302@gmail.com"
HTML_FILE = Path(__file__).parent / "index.html"


def get_html_with_today_date() -> str:
    """HTMLの日付を今日の日付に更新して返す"""
    html = HTML_FILE.read_text(encoding="utf-8")
    today = datetime.now().strftime("%Y年%m月%d日")
    weekday = ["月", "火", "水", "木", "金", "土", "日"][datetime.now().weekday()]
    date_str = f"{today}（{weekday}）"
    # 日付部分を置換（例: 2025年2月24日（月））
    html = re.sub(
        r"\d{4}年\d{1,2}月\d{1,2}日（[月火水木金土日]）",
        date_str,
        html,
        count=1,
    )
    return html


def send_email(html_body: str) -> None:
    """Gmail SMTPでHTMLメールを送信"""
    sender = os.environ.get("PHARMA_BRIEF_SENDER", RECIPIENT)
    app_password = os.environ.get("PHARMA_BRIEF_APP_PASSWORD")

    if not app_password:
        print("エラー: 環境変数 PHARMA_BRIEF_APP_PASSWORD が設定されていません。")
        print("Gmailのアプリパスワードを設定してください。")
        print("設定方法: https://support.google.com/accounts/answer/185833")
        raise SystemExit(1)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Pharma Daily Brief | {datetime.now().strftime('%Y/%m/%d')}"
    msg["From"] = f"Pharma Daily Brief <{sender}>"
    msg["To"] = RECIPIENT

    text_fallback = "Pharma Daily Brief（HTMLメールが表示されない環境向けのテキスト）"
    msg.attach(MIMEText(text_fallback, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender, app_password)
        server.sendmail(sender, RECIPIENT, msg.as_string())

    print(f"送信完了: {RECIPIENT}")


def main() -> None:
    if not HTML_FILE.exists():
        print(f"エラー: {HTML_FILE} が見つかりません。")
        raise SystemExit(1)

    html = get_html_with_today_date()
    send_email(html)


if __name__ == "__main__":
    main()
