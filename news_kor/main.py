import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from sheets_reader import get_companies
from naver_news import search_news
from telegram_sender import build_combined_message, send_message


KST = ZoneInfo("Asia/Seoul")

FEEDS = [
    {"sheet_name": "Light", "col": 2, "chat_id_env": "TELEGRAM_CHAT_ID_Light"},
    {"sheet_name": "Atom",  "col": 2, "chat_id_env": "TELEGRAM_CHAT_ID_Atom"},
]


def run_feed(sheet_id: str, sheet_name: str, col: int, chat_id_env: str):
    print(f"\n{'='*50}")
    print(f"[{sheet_name}] 피드 시작")
    print(f"{'='*50}")

    # 1. 회사 목록 로드
    print(f"\n[1] {sheet_name} 시트에서 회사 목록 로드 중...")
    try:
        companies = get_companies(sheet_id, sheet_name, col)
    except Exception as e:
        print(f"[ERROR] 회사 목록 로드 실패: {e}")
        return

    print(f"  → {len(companies)}개 회사 로드: {', '.join(companies)}")

    if not companies:
        print("[INFO] 회사 목록이 비어 있어 스킵합니다.")
        return

    # 2. 각 회사별 뉴스 검색
    print(f"\n[2] 뉴스 검색 중...")
    seen_urls: set = set()
    company_news: dict = {}
    total_articles = 0

    for company in companies:
        print(f"  → [{company}] 검색 중...")
        news_items = search_news(company, seen_urls)
        if news_items:
            company_news[company] = news_items
            total_articles += len(news_items)
            print(f"     {len(news_items)}건 수집")
        else:
            print(f"     관련 뉴스 없음, 스킵")

    # 3. 통합 메시지 전송
    print(f"\n[3] Telegram 전송 중... ({chat_id_env} / 총 {total_articles}건)")
    if not company_news:
        print("[INFO] 전송할 뉴스가 없어 스킵합니다.")
        return

    message = build_combined_message(company_news)
    success = send_message(message, chat_id_env)
    print(f"     {'전송 완료' if success else '전송 실패'}")


def main():
    load_dotenv()

    sheet_id = os.environ.get("GOOGLE_SHEET_ID", "1sfDjoKbrEbKvA0qwMA1nPdcEu628YgNX0A_JLLOB4WA")

    start_time = datetime.now(KST)
    print(f"=== 뉴스 피드 시작: {start_time.strftime('%Y-%m-%d %H:%M KST')} ===")

    for feed in FEEDS:
        run_feed(
            sheet_id=sheet_id,
            sheet_name=feed["sheet_name"],
            col=feed["col"],
            chat_id_env=feed["chat_id_env"],
        )

    end_time = datetime.now(KST)
    elapsed = (end_time - start_time).seconds
    print(f"\n=== 전체 완료: {end_time.strftime('%Y-%m-%d %H:%M KST')} | 소요 {elapsed}초 ===")


if __name__ == "__main__":
    main()
