import os

import requests

from dart_fetcher import DisclosureItem


TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def build_combined_message(company_disclosures: dict, title: str) -> str:
    """
    전체 회사 공시를 하나의 메시지로 조합.
    company_disclosures: {회사명: [DisclosureItem, ...]}
    """
    lines = [title, ""]

    for company, items in company_disclosures.items():
        if not items:
            continue

        date_str = f"{items[0].rcept_dt[:4]}-{items[0].rcept_dt[4:6]}-{items[0].rcept_dt[6:]}"
        lines.append(f"<b>{company} ({date_str})</b>")

        for item in items:
            report_nm = item.report_nm
            if item.rm:
                report_nm += f" [{item.rm}]"
            lines.append(report_nm)
            lines.append(item.link)
            lines.append(f"제출인: {item.flr_nm}")
            lines.append("")

        lines.append("")

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
