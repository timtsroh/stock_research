import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta

import requests
from zoneinfo import ZoneInfo


KST = ZoneInfo("Asia/Seoul")
DART_LIST_URL = "https://opendart.fss.or.kr/api/list.json"
MAX_PER_COMPANY = 3
DELAY = 0.5


@dataclass
class DisclosureItem:
    rcept_no: str     # 접수번호 (상세 링크 키)
    corp_name: str    # 회사명
    report_nm: str    # 보고서명
    rcept_dt: str     # 접수일자 (YYYYMMDD)
    flr_nm: str       # 공시 제출인
    rm: str           # 비고 (정정/첨부 등)

    @property
    def link(self) -> str:
        return f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={self.rcept_no}"


def _get_api_key() -> str:
    key = os.environ.get("DART_API_KEY")
    if not key:
        raise ValueError("DART_API_KEY 환경 변수가 설정되지 않았습니다.")
    return key


def _get_query_date() -> str:
    """전날 날짜(YYYYMMDD)를 반환. 매일 오전 6시 실행 기준으로 전날 공시를 조회."""
    return (datetime.now(KST) - timedelta(days=1)).strftime("%Y%m%d")


def fetch_disclosures(
    corp_code: str,
    seen_rcept_nos: set,
) -> list[DisclosureItem]:
    """
    DART API로 해당 기업의 공시 목록을 조회하고 DisclosureItem 리스트를 반환.
    seen_rcept_nos: 동일 실행 내 중복 접수번호 필터용 set (in-place 업데이트).
    """
    api_key = _get_api_key()
    target_date = _get_query_date()

    params = {
        "crtfc_key": api_key,
        "corp_code": corp_code,
        "bgn_de": target_date,
        "end_de": target_date,
        "last_reprt_at": "N",
        "page_count": 10,
    }

    try:
        resp = requests.get(DART_LIST_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        print(f"  [WARN] DART API 호출 실패 (corp_code={corp_code}): {e}")
        return []

    if data.get("status") != "000":
        # status 013: 조회된 데이터 없음 (정상)
        if data.get("status") != "013":
            print(f"  [WARN] DART API 응답 오류 (corp_code={corp_code}): {data.get('status')} {data.get('message')}")
        return []

    items = []
    for row in data.get("list", []):
        rcept_no = row.get("rcept_no", "")

        if rcept_no in seen_rcept_nos:
            continue

        seen_rcept_nos.add(rcept_no)
        items.append(
            DisclosureItem(
                rcept_no=rcept_no,
                corp_name=row.get("corp_name", ""),
                report_nm=row.get("report_nm", ""),
                rcept_dt=row.get("rcept_dt", ""),
                flr_nm=row.get("flr_nm", ""),
                rm=row.get("rm", ""),
            )
        )
        if len(items) >= MAX_PER_COMPANY:
            break

    time.sleep(DELAY)
    return items
