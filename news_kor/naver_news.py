import os
import re
import time
import requests
from dataclasses import dataclass
from urllib.parse import urlparse


NAVER_API_URL = "https://openapi.naver.com/v1/search/news.json"
FETCH_COUNT = 10   # 필터링 여유분을 위해 많이 가져옴
MAX_PER_COMPANY = 3
DELAY = 0.5  # 초

# 주요 언론사 도메인 → 한글 이름 매핑
MEDIA_NAME_MAP = {
    "hankyung.com": "한국경제",
    "mk.co.kr": "매일경제",
    "chosun.com": "조선일보",
    "joongang.co.kr": "중앙일보",
    "donga.com": "동아일보",
    "hani.co.kr": "한겨레",
    "khan.co.kr": "경향신문",
    "yna.co.kr": "연합뉴스",
    "newsis.com": "뉴시스",
    "news1.kr": "뉴스1",
    "edaily.co.kr": "이데일리",
    "etnews.com": "전자신문",
    "zdnet.co.kr": "ZDNet Korea",
    "mt.co.kr": "머니투데이",
    "sedaily.com": "서울경제",
    "thebell.co.kr": "더벨",
    "businesspost.co.kr": "비즈니스포스트",
    "bizwatch.co.kr": "비즈워치",
    "investchosun.com": "투자조선",
    "infostock.co.kr": "인포스탁",
    "news.naver.com": "네이버뉴스",
}


@dataclass
class NewsItem:
    title: str
    link: str
    pub_date: str
    media: str


def _strip_html(text: str) -> str:
    """HTML 태그 및 엔티티 제거."""
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " ")
    return text.strip()


def _extract_media(url: str) -> str:
    """URL 도메인에서 언론사 이름 추출."""
    try:
        domain = urlparse(url).netloc.lower().lstrip("www.")
        for key, name in MEDIA_NAME_MAP.items():
            if key in domain:
                return name
        domain = re.sub(r"\.(com|co\.kr|kr|net|org)$", "", domain)
        return domain
    except Exception:
        return ""


def _is_relevant(company: str, title: str, description: str) -> bool:
    """
    회사명이 제목+본문에 2회 이상 등장하면 관련 기사로 판단.
    단순히 1회만 언급된 기사는 제외.
    """
    combined = (title + " " + description).lower()
    count = combined.count(company.lower())
    return count >= 2


def search_news(company: str, seen_urls: set) -> list[NewsItem]:
    """
    회사명으로 Naver 뉴스 검색 후 필터링된 NewsItem 리스트 반환 (최대 3건).
    seen_urls: 이번 실행에서 이미 처리한 URL 집합 (중복 방지).
    """
    client_id = os.environ.get("NAVER_CLIENT_ID")
    client_secret = os.environ.get("NAVER_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise ValueError("NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 환경 변수가 설정되지 않았습니다.")

    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
    }
    params = {
        "query": company,
        "display": FETCH_COUNT,
        "sort": "date",
    }

    try:
        resp = requests.get(NAVER_API_URL, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  [WARN] {company} 뉴스 검색 실패: {e}")
        return []

    items = resp.json().get("items", [])
    results = []

    for item in items:
        if len(results) >= MAX_PER_COMPANY:
            break

        url = item.get("originallink") or item.get("link", "")
        if url in seen_urls:
            continue

        title = _strip_html(item.get("title", ""))
        description = _strip_html(item.get("description", ""))

        if not _is_relevant(company, title, description):
            continue

        seen_urls.add(url)
        results.append(NewsItem(
            title=title,
            link=url,
            pub_date=item.get("pubDate", ""),
            media=_extract_media(url),
        ))

    time.sleep(DELAY)
    return results
