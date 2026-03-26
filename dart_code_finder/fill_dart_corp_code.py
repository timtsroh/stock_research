"""
DART corp_code 자동 채우기

Google Sheets의 Light/Atom 시트에서 회사명(B열)을 읽고,
D열에 corp_code가 비어 있는 행에 DART corp_code를 자동으로 채운다.

실행:
    python fill_dart_corp_code.py

사전 준비:
    - .env 파일에 DART_API_KEY, GOOGLE_SERVICE_ACCOUNT_JSON, GOOGLE_SHEET_ID 설정
    - 또는 환경 변수로 직접 설정
"""

import io
import json
import os
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

import requests
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv


# ── 설정 ──────────────────────────────────────────────
DART_CORP_CODE_URL = "https://opendart.fss.or.kr/api/corpCode.xml"
CACHE_FILE = os.path.join(os.path.dirname(__file__), "corp_code_cache.json")
CACHE_DAYS = 7  # 캐시 유효 기간 (일)

TARGET_SHEETS = [
    {"sheet_name": "Light", "name_col": 2, "corp_code_col": 4},
    {"sheet_name": "Atom",  "name_col": 2, "corp_code_col": 4},
]
# ──────────────────────────────────────────────────────


def load_dart_corp_codes(api_key: str) -> dict:
    """
    DART 기업 목록을 반환한다.
    캐시 파일이 있고 유효 기간(7일) 이내면 캐시를 사용, 아니면 새로 다운로드.
    """
    # 캐시 확인
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            cache = json.load(f)
        cached_at = datetime.fromisoformat(cache["cached_at"])
        if datetime.now() - cached_at < timedelta(days=CACHE_DAYS):
            print(f"캐시 사용 중 (저장일: {cached_at.strftime('%Y-%m-%d')}, 상장사 {len(cache['data']):,}개)")
            return cache["data"]
        else:
            print(f"캐시 만료 ({cached_at.strftime('%Y-%m-%d')}), 새로 다운로드...")
    else:
        print("캐시 없음, DART 기업 목록 다운로드 중...")

    # 새로 다운로드
    params = {"crtfc_key": api_key}
    resp = requests.get(DART_CORP_CODE_URL, params=params, timeout=30)
    resp.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
        xml_filename = z.namelist()[0]
        with z.open(xml_filename) as f:
            tree = ET.parse(f)

    corp_map = {}
    for item in tree.getroot().findall("list"):
        corp_name = (item.findtext("corp_name") or "").strip()
        corp_code = (item.findtext("corp_code") or "").strip()
        stock_code = (item.findtext("stock_code") or "").strip()
        if corp_name and corp_code and stock_code:
            corp_map[corp_name] = corp_code

    # 캐시 저장
    with open(CACHE_FILE, "w") as f:
        json.dump({"cached_at": datetime.now().isoformat(), "data": corp_map}, f, ensure_ascii=False)

    print(f"  → 상장사 {len(corp_map):,}개 로드 및 캐시 저장 완료")
    return corp_map


def get_gspread_client() -> gspread.Client:
    sa_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if sa_json:
        sa_info = json.loads(sa_json)
    else:
        key_file = os.path.join(os.path.dirname(__file__), "..", "news_kor", "gcp-oauth.keys2.json")
        with open(key_file, "r") as f:
            sa_info = json.load(f)
    creds = Credentials.from_service_account_info(
        sa_info,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    return gspread.authorize(creds)


def fill_corp_codes(sheet_id: str, corp_map: dict):
    client = get_gspread_client()
    spreadsheet = client.open_by_key(sheet_id)

    for target in TARGET_SHEETS:
        sheet_name = target["sheet_name"]
        name_col = target["name_col"]
        code_col = target["corp_code_col"]

        print(f"\n[{sheet_name}] 시트 처리 중...")
        ws = spreadsheet.worksheet(sheet_name)

        names = ws.col_values(name_col)       # B열 전체 (헤더 포함)
        codes = ws.col_values(code_col)       # D열 전체 (헤더 포함)

        filled = 0
        not_found = []

        for i, name in enumerate(names):
            row = i + 1
            if row == 1:
                continue  # 헤더 스킵

            name = name.strip()
            if not name:
                continue

            # D열 값 확인 (비어있으면 채우기)
            current_code = codes[i].strip() if i < len(codes) else ""
            if current_code:
                continue  # 이미 입력되어 있으면 스킵

            corp_code = corp_map.get(name)
            if corp_code:
                ws.update_cell(row, code_col, f"'{corp_code}")
                print(f"  ✓ {name} → {corp_code}")
                filled += 1
            else:
                not_found.append(name)

        print(f"  → {filled}개 채움 완료")
        if not_found:
            print(f"  → corp_code 미발견 ({len(not_found)}개): {', '.join(not_found)}")


def main():
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", "dart", ".env"))

    api_key = os.environ.get("DART_API_KEY")
    if not api_key:
        raise ValueError("DART_API_KEY 환경 변수가 설정되지 않았습니다.")

    sheet_id = os.environ.get("GOOGLE_SHEET_ID", "1sfDjoKbrEbKvA0qwMA1nPdcEu628YgNX0A_JLLOB4WA")

    corp_map = load_dart_corp_codes(api_key)
    fill_corp_codes(sheet_id, corp_map)

    print("\n완료.")


if __name__ == "__main__":
    main()
