import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo



KST = ZoneInfo("Asia/Seoul")
TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def _format_pub_date(pub_date: str) -> str:
    """ISO 8601 또는 RFC 2822 형식의 날짜를 KST로 변환해 반환."""
    try:
        # ISO 8601: 2026-03-25T09:00:00Z
        dt = datetime.fromisoformat(pub_date.replace("Z", "+00:00")).astimezone(KST)
        return dt.strftime("%Y-%m-%d %H:%M KST")
    except Exception:
        pass
    try:
        # RFC 2822 fallback
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(pub_date).astimezone(KST)
        return dt.strftime("%Y-%m-%d %H:%M KST")
    except Exception:
        return pub_date


def build_combined_message(company_news: dict, title: str) -> str:
    """
    전체 회사 뉴스를 하나의 메시지로 조합.
    company_news: {회사명: [NewsItem, ...]}
    """
    now_kst = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")
    lines = [title, f"🕐 {now_kst}", ""]

    company_index = 1
    for company, items in company_news.items():
        if not items:
            continue

        lines.append(f"<b>{company_index}. {company}</b>")

        for item in items:
            lines.append(f"{item.title}")
            lines.append(f"{item.link}")
            date_str = _format_pub_date(item.pub_date)
            media_str = f"{item.media} | " if item.media else ""
            lines.append(f"{media_str}{date_str}")
            lines.append("")

        lines.append("")
        company_index += 1

    return "\n".join(lines).rstrip()


def send_message(text: str, chat_id_env: str) -> bool:
    """Telegram 채널로 메시지 전송. chat_id_env: 사용할 환경변수 이름. 성공 시 True 반환."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get(chat_id_env)
    if not token or not chat_id:
        raise ValueError(f"TELEGRAM_BOT_TOKEN / {chat_id_env} 환경 변수가 설정되지 않았습니다.")

    url = TELEGRAM_API.format(token=token)
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        return True
    except requests.RequestException as e:
        print(f"  [WARN] Telegram 전송 실패: {e}")
        return False
