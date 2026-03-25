import os
import json
import gspread
from google.oauth2.service_account import Credentials


SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


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


def get_companies_with_corp_code(
    sheet_id: str,
    sheet_name: str,
    name_col: int = 2,
    corp_code_col: int = 4,
) -> list[tuple]:
    """지정한 시트의 B열(회사명)과 D열(DART corp_code) 쌍 목록을 반환한다."""
    client = _get_gspread_client()
    worksheet = client.open_by_key(sheet_id).worksheet(sheet_name)
    names = worksheet.col_values(name_col)[1:]       # 헤더 스킵
    corp_codes = worksheet.col_values(corp_code_col)[1:]

    result = []
    for i, (name, corp_code) in enumerate(zip(names, corp_codes), start=2):
        name = name.strip()
        corp_code = corp_code.strip()
        if not name:
            continue
        if not corp_code:
            print(f"  [WARN] {sheet_name} 시트 {i}행 [{name}]: corp_code 없음, 스킵")
            continue
        result.append((name, corp_code))
    return result
