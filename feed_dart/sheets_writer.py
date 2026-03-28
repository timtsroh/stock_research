import json
import os

import gspread
from google.oauth2.service_account import Credentials

from dart_fetcher import DisclosureItem

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
HEADER = ["회사", "날짜", "보고자", "공시번호", "링크", "제목"]


def _get_gspread_client():
    sa_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not sa_json:
        key_file = os.path.join(os.path.dirname(__file__), "..", "news_kor", "gcp-oauth.keys2.json")
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


def write_disclosures_to_sheet(sheet_id: str, sheet_name: str, company_disclosures: dict):
    """
    공시 결과를 시트에 기록.
    - 2행: 헤더 (없으면 삽입)
    - 3행~: 데이터 추가
    """
    client = _get_gspread_client()
    ws = client.open_by_key(sheet_id).worksheet(sheet_name)

    # 데이터 행 수집
    rows = []
    for corp_name, items in company_disclosures.items():
        for item in items:
            date_str = f"{item.rcept_dt[:4]}.{item.rcept_dt[4:6]}.{item.rcept_dt[6:]}"
            rows.append([
                corp_name,
                date_str,
                item.flr_nm,
                item.rcept_no,
                item.link,
                item.report_nm,
            ])

    if rows:
        ws.append_rows(rows, value_input_option="USER_ENTERED")
        print(f"  → {len(rows)}행 기록 완료 ({sheet_name})")
