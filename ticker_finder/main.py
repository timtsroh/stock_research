"""
ticker_finder/main.py

구글 시트에서 D열이 비어있는 기업을 찾아:
- Light/Atom 시트: DART corp_code (8자리) 검색 후 D열에 기록
- ENG 시트: 해외 주식 티커 (예: AAPL) 검색 후 D열에 기록

사용법:
    python main.py            # Light, Atom, ENG 모두 처리
    python main.py Light      # Light 시트만
    python main.py ENG        # ENG 시트만
"""

import io
import json
import os
import sys
import time
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timedelta

import gspread
import requests
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials


SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
DART_CORP_CODE_URL = "https://opendart.fss.or.kr/api/corpCode.xml"
ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"
CACHE_FILE = os.path.join(os.path.dirname(__file__), "corp_code_cache.json")
CACHE_DAYS = 7


# ─── GCP 인증 ────────────────────────────────────────────────────────────────

def _get_gspread_client():
    sa_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not sa_json:
        key_file = os.path.join(os.path.dirname(__file__), "..", "news_kor", "gcp-oauth.keys2.json")
        if os.path.exists(key_file):
            with open(key_file) as f:
                sa_info = json.load(f)
        else:
            raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON 환경 변수 또는 gcp-oauth.keys2.json 파일이 필요합니다.")
    else:
        sa_info = json.loads(sa_json)
    creds = Credentials.from_service_account_info(sa_info, scopes=SCOPES)
    return gspread.authorize(creds)


# ─── DART corp_code 검색 (국내) ───────────────────────────────────────────────

def _load_dart_corp_map(api_key: str) -> dict:
    """
    DART 전체 기업 목록 반환. 7일 캐시 사용.
    반환: {corp_name: {"corp_code": ..., "stock_code": ...}}
    """
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            cache = json.load(f)
        cached_at = datetime.fromisoformat(cache["cached_at"])
        if datetime.now() - cached_at < timedelta(days=CACHE_DAYS):
            print(f"  DART 캐시 사용 (저장일: {cached_at.strftime('%Y-%m-%d')}, {len(cache['data']):,}개)")
            return cache["data"]
        print(f"  DART 캐시 만료, 새로 다운로드 중...")
    else:
        print("  DART 기업 목록 다운로드 중...")

    resp = requests.get(DART_CORP_CODE_URL, params={"crtfc_key": api_key}, timeout=30)
    resp.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
        xml_bytes = z.read(z.namelist()[0])

    corp_map = {}
    for item in ET.fromstring(xml_bytes).findall("list"):
        name = (item.findtext("corp_name") or "").strip()
        code = (item.findtext("corp_code") or "").strip()
        stock = (item.findtext("stock_code") or "").strip()
        if name and code:
            corp_map[name] = {"corp_code": code, "stock_code": stock}

    with open(CACHE_FILE, "w") as f:
        json.dump({"cached_at": datetime.now().isoformat(), "data": corp_map}, f, ensure_ascii=False)

    print(f"  → {len(corp_map):,}개 로드 및 캐시 저장 완료")
    return corp_map


def _find_corp_code(company: str, corp_map: dict) -> str | None:
    """
    1) 완전 일치 → 바로 확인 후 기록
    2) 부분 일치 → 후보 목록 표시 후 선택
    3) 없음 → 직접 입력
    """
    # 1) 완전 일치
    exact = corp_map.get(company)
    if exact:
        stock_info = f"종목코드: {exact['stock_code']}" if exact["stock_code"] else "비상장"
        print(f"  완전 일치: {company} (corp_code: {exact['corp_code']}, {stock_info})")
        confirm = input("    이 기업으로 확정하시겠습니까? (y/n/직접입력): ").strip().lower()
        if confirm == "y":
            return exact["corp_code"]
        elif confirm == "n":
            return None
        else:
            return confirm

    # 2) 부분 일치
    query = company.lower()
    candidates = [
        (name, info) for name, info in corp_map.items()
        if query in name.lower() or name.lower() in query
    ][:10]

    if not candidates:
        print(f"  [{company}] DART에서 일치하는 기업 없음")
        manual = input("    corp_code 직접 입력 (건너뛰려면 Enter): ").strip()
        return manual if manual else None

    print(f"  [{company}] 후보 {len(candidates)}개:")
    for i, (name, info) in enumerate(candidates, 1):
        stock_info = info["stock_code"] if info["stock_code"] else "비상장"
        print(f"    {i}. {name:<20}  corp_code={info['corp_code']}  종목코드={stock_info}")

    choice = input("    번호 선택 (건너뛰려면 Enter, 직접 입력도 가능): ").strip()
    if not choice:
        return None
    if choice.isdigit() and 1 <= int(choice) <= len(candidates):
        return candidates[int(choice) - 1][1]["corp_code"]
    return choice


# ─── Alpha Vantage 티커 검색 (해외) ──────────────────────────────────────────

def _find_ticker(company: str, av_key: str) -> str | None:
    """Alpha Vantage SYMBOL_SEARCH → 후보 목록 표시 후 선택."""
    try:
        resp = requests.get(
            ALPHA_VANTAGE_URL,
            params={"function": "SYMBOL_SEARCH", "keywords": company, "apikey": av_key},
            timeout=10,
        )
        resp.raise_for_status()
        matches = resp.json().get("bestMatches", [])
    except Exception as e:
        print(f"  [{company}] Alpha Vantage 검색 실패: {e}")
        matches = []

    if not matches:
        print(f"  [{company}] 검색 결과 없음")
        manual = input("    티커 직접 입력 (건너뛰려면 Enter): ").strip()
        return manual if manual else None

    candidates = matches[:8]
    print(f"  [{company}] 후보 {len(candidates)}개:")
    for i, m in enumerate(candidates, 1):
        sym = m.get("1. symbol", "")
        name = m.get("2. name", "")
        region = m.get("4. region", "")
        mtype = m.get("3. type", "")
        print(f"    {i}. {sym:<12} {name:<35} {region} / {mtype}")

    choice = input("    번호 선택 (건너뛰려면 Enter, 직접 입력도 가능): ").strip()
    if not choice:
        return None
    if choice.isdigit() and 1 <= int(choice) <= len(candidates):
        return candidates[int(choice) - 1]["1. symbol"]
    return choice


# ─── 시트 처리 ────────────────────────────────────────────────────────────────

def process_kor_sheet(ws, sheet_name: str, corp_map: dict, name_col: int = 2, code_col: int = 4):
    names = ws.col_values(name_col)
    codes = ws.col_values(code_col)

    filled = skipped = 0
    not_found = []

    for i, name in enumerate(names):
        if i == 0:
            continue
        name = name.strip()
        if not name:
            continue
        current = codes[i].strip() if i < len(codes) else ""
        if current:
            skipped += 1
            continue

        print(f"\n  행 {i+1}: {name}")
        corp_code = _find_corp_code(name, corp_map)
        if corp_code:
            ws.update_cell(i + 1, code_col, f"'{corp_code}")
            print(f"    → {corp_code} 기록 완료")
            filled += 1
            time.sleep(0.5)
        else:
            not_found.append(name)

    print(f"\n[{sheet_name}] {filled}개 채움 / {skipped}개 기존값 스킵", end="")
    if not_found:
        print(f" / 미처리 {len(not_found)}개: {', '.join(not_found)}")
    else:
        print()


def process_eng_sheet(ws, av_key: str, name_col: int = 2, ticker_col: int = 4):
    names = ws.col_values(name_col)
    tickers = ws.col_values(ticker_col)

    filled = skipped = 0

    for i, name in enumerate(names):
        if i == 0:
            continue
        name = name.strip()
        if not name:
            continue
        current = tickers[i].strip() if i < len(tickers) else ""
        if current:
            skipped += 1
            continue

        print(f"\n  행 {i+1}: {name}")
        ticker = _find_ticker(name, av_key)
        if ticker:
            ws.update_cell(i + 1, ticker_col, ticker)
            print(f"    → {ticker} 기록 완료")
            filled += 1
            time.sleep(1.2)

    print(f"\n[ENG] {filled}개 채움 / {skipped}개 기존값 스킵")


# ─── 메인 ─────────────────────────────────────────────────────────────────────

def main():
    for env_path in [
        os.path.join(os.path.dirname(__file__), "..", "dart", ".env"),
        os.path.join(os.path.dirname(__file__), "..", "news_kor", ".env"),
        os.path.join(os.path.dirname(__file__), ".env"),
    ]:
        if os.path.exists(env_path):
            load_dotenv(env_path)

    sheet_id = os.environ.get("GOOGLE_SHEET_ID", "1sfDjoKbrEbKvA0qwMA1nPdcEu628YgNX0A_JLLOB4WA")
    dart_key = os.environ.get("DART_API_KEY")
    av_key = os.environ.get("ALPHA_VANTAGE_API_KEY")

    target_sheets = sys.argv[1:] if len(sys.argv) > 1 else ["Light", "Atom", "ENG"]

    print(f"=== 티커/corp_code 찾기 ===")
    print(f"대상 시트: {', '.join(target_sheets)}\n")

    client = _get_gspread_client()
    spreadsheet = client.open_by_key(sheet_id)

    kor_sheets = [s for s in target_sheets if s in ("Light", "Atom")]
    do_eng = "ENG" in target_sheets

    if kor_sheets:
        if not dart_key:
            print("[ERROR] DART_API_KEY 환경 변수가 없습니다.")
            sys.exit(1)
        corp_map = _load_dart_corp_map(dart_key)
        for sheet_name in kor_sheets:
            print(f"\n{'='*50}")
            print(f"[{sheet_name}] 국내 기업 corp_code 검색")
            print(f"{'='*50}")
            process_kor_sheet(spreadsheet.worksheet(sheet_name), sheet_name, corp_map)

    if do_eng:
        if not av_key:
            print("[ERROR] ALPHA_VANTAGE_API_KEY 환경 변수가 없습니다.")
            sys.exit(1)
        print(f"\n{'='*50}")
        print(f"[ENG] 해외 기업 티커 검색")
        print(f"{'='*50}")
        process_eng_sheet(spreadsheet.worksheet("ENG"), av_key)

    print("\n=== 완료 ===")


if __name__ == "__main__":
    main()
