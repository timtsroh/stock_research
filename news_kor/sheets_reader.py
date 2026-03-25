import os
import json
import gspread
from google.oauth2.service_account import Credentials


SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def get_companies(sheet_id: str, sheet_name: str, col: int = 2) -> list[str]:
    """지정한 시트의 지정한 열에서 회사명 목록을 반환한다."""
    sa_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")

    # 환경변수가 없으면 같은 폴더의 JSON 파일에서 직접 로드
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
    client = gspread.authorize(creds)

    spreadsheet = client.open_by_key(sheet_id)
    worksheet = spreadsheet.worksheet(sheet_name)

    values = worksheet.col_values(col)

    companies = []
    for v in values[1:]:  # 첫 행(헤더) 항상 스킵
        name = v.strip()
        if not name:
            continue
        companies.append(name)

    return companies
