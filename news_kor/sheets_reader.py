import os
import json
import gspread
from google.oauth2.service_account import Credentials


SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


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


def get_companies(sheet_id: str, sheet_name: str, col: int = 2) -> list[str]:
    """지정한 시트의 지정한 열에서 회사명 목록을 반환한다."""
    client = _get_gspread_client()
    worksheet = client.open_by_key(sheet_id).worksheet(sheet_name)
    companies = []
    for v in worksheet.col_values(col)[1:]:  # 첫 행(헤더) 항상 스킵
        name = v.strip()
        if name:
            companies.append(name)
    return companies


def get_companies_with_tickers(sheet_id: str, sheet_name: str, name_col: int = 2, ticker_col: int = 4) -> list[tuple]:
    """지정한 시트에서 (회사명, 티커) 쌍 목록을 반환한다."""
    client = _get_gspread_client()
    worksheet = client.open_by_key(sheet_id).worksheet(sheet_name)
    names = worksheet.col_values(name_col)[1:]
    tickers = worksheet.col_values(ticker_col)[1:]
    result = []
    for name, ticker in zip(names, tickers):
        name, ticker = name.strip(), ticker.strip()
        if name and ticker:
            result.append((name, ticker))
    return result
