import os
import json
from datetime import datetime
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo

import gspread
from google.oauth2.service_account import Credentials


SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
KST = ZoneInfo("Asia/Seoul")


def _get_gspread_client():
    sa_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not sa_json:
        key_file = os.path.join(os.path.dirname(__file__), "gcp-oauth.keys2.json")
        if os.path.exists(key_file):
            with open(key_file, "r") as f:
                sa_info = json.load(f)
        else:
            raise ValueError(
                "GOOGLE_SERVICE_ACCOUNT_JSON 환경 변수 또는 gcp-oauth.keys2.json 파일이 필요합니다."
            )
    else:
        sa_info = json.loads(sa_json)
    creds = Credentials.from_service_account_info(sa_info, scopes=SCOPES)
    return gspread.authorize(creds)


def _parse_pub_date(pub_date: str) -> tuple[str, str]:
    """pub_date를 (날짜 YYYY-MM-DD, 시간 HH:MM) KST로 파싱."""
    try:
        dt = datetime.fromisoformat(pub_date.replace("Z", "+00:00")).astimezone(KST)
        return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M")
    except Exception:
        pass
    try:
        dt = parsedate_to_datetime(pub_date).astimezone(KST)
        return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M")
    except Exception:
        pass
    return pub_date, ""


def write_news_to_sheet(
    sheet_id: str,
    target_sheet_name: str,
    company_news: dict,
) -> int:
    """
    수집된 뉴스를 지정한 시트의 2번째 행부터 삽입.
    company_news: {회사명: [NewsItem, ...]}
    반환값: 기록된 행 수
    """
    rows = []
    for company, items in company_news.items():
        for item in items:
            date_str, time_str = _parse_pub_date(item.pub_date)
            rows.append([date_str, time_str, item.media, item.link, company, item.title])

    if not rows:
        return 0

    try:
        client = _get_gspread_client()
        worksheet = client.open_by_key(sheet_id).worksheet(target_sheet_name)
        # 2번째 행에 삽입 (기존 데이터 밀어내기)
        worksheet.insert_rows(rows, row=2)
        print(f"  → [{target_sheet_name}] 시트에 {len(rows)}행 기록 완료")
    except Exception as e:
        print(f"  [WARN] [{target_sheet_name}] 시트 기록 실패: {e}")
        return 0

    return len(rows)
