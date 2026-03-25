import os
import re
import time
import requests
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse
from email.utils import parsedate_to_datetime


NAVER_API_URL = "https://openapi.naver.com/v1/search/news.json"
NEWSAPI_URL = "https://newsapi.org/v2/everything"
MARKETAUX_URL = "https://api.marketaux.com/v1/news/all"
ALPHAVANTAGE_URL = "https://www.alphavantage.co/query"
FINNHUB_URL = "https://finnhub.io/api/v1/company-news"
FETCH_COUNT = 10
MAX_PER_COMPANY = 3
DELAY = 0.5  # 초
HOURS_LIMIT = 12

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


def _is_within_hours(pub_date: str, hours: int = HOURS_LIMIT) -> bool:
    """RFC 2822 또는 ISO 8601 날짜가 현재 기준 hours 시간 이내이면 True."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    try:
        dt = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
        return dt >= cutoff
    except Exception:
        pass
    try:
        dt = parsedate_to_datetime(pub_date)
        return dt >= cutoff
    except Exception:
        return True  # 파싱 실패 시 포함


def _is_relevant(company: str, title: str, description: str, min_count: int = 2) -> bool:
    """회사명이 제목+본문에 min_count회 이상 등장하면 관련 기사로 판단."""
    combined = (title + " " + (description or "")).lower()
    return combined.count(company.lower()) >= min_count


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


def search_naver(company: str, seen_urls: set) -> list[NewsItem]:
    """Naver 뉴스 API로 회사 관련 뉴스 검색 (한국 기업용)."""
    client_id = os.environ.get("NAVER_CLIENT_ID")
    client_secret = os.environ.get("NAVER_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise ValueError("NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 환경 변수가 설정되지 않았습니다.")

    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
    }
    params = {"query": company, "display": FETCH_COUNT, "sort": "date"}

    try:
        resp = requests.get(NAVER_API_URL, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  [WARN] {company} Naver 검색 실패: {e}")
        return []

    results = []
    for item in resp.json().get("items", []):
        if len(results) >= MAX_PER_COMPANY:
            break

        pub_date = item.get("pubDate", "")
        if not _is_within_hours(pub_date):
            continue

        url = item.get("originallink") or item.get("link", "")
        if url in seen_urls:
            continue

        title = _strip_html(item.get("title", ""))
        description = _strip_html(item.get("description", ""))
        if not _is_relevant(company, title, description):
            continue

        seen_urls.add(url)
        results.append(NewsItem(title=title, link=url, pub_date=pub_date, media=_extract_media(url)))

    time.sleep(DELAY)
    return results




def search_marketaux(ticker: str, seen_urls: set) -> list[NewsItem]:
    """Marketaux API로 티커 기반 뉴스 검색 (해외 기업용)."""
    api_token = os.environ.get("MARKETAUX_API_KEY")
    if not api_token:
        raise ValueError("MARKETAUX_API_KEY 환경 변수가 설정되지 않았습니다.")

    cutoff = datetime.now(timezone.utc) - timedelta(hours=HOURS_LIMIT)
    params = {
        "symbols": ticker,
        "api_token": api_token,
        "language": "en",
        "published_after": cutoff.strftime("%Y-%m-%dT%H:%M:%S"),
        "limit": FETCH_COUNT,
    }

    try:
        resp = requests.get(MARKETAUX_URL, params=params, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  [WARN] {ticker} Marketaux 검색 실패: {e}")
        return []

    results = []
    for article in resp.json().get("data", []):
        if len(results) >= MAX_PER_COMPANY:
            break
        url = article.get("url", "")
        if not url or url in seen_urls:
            continue
        title = _strip_html(article.get("title") or "")
        if not title:
            continue
        seen_urls.add(url)
        results.append(NewsItem(
            title=title,
            link=url,
            pub_date=article.get("published_at", ""),
            media=article.get("source", ""),
        ))

    time.sleep(DELAY)
    return results


def search_alphavantage(ticker: str, seen_urls: set) -> list[NewsItem]:
    """Alpha Vantage NEWS_SENTIMENT API로 티커 기반 뉴스 검색 (해외 기업용)."""
    api_key = os.environ.get("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        raise ValueError("ALPHA_VANTAGE_API_KEY 환경 변수가 설정되지 않았습니다.")

    cutoff = datetime.now(timezone.utc) - timedelta(hours=HOURS_LIMIT)
    params = {
        "function": "NEWS_SENTIMENT",
        "tickers": ticker,
        "time_from": cutoff.strftime("%Y%m%dT%H%M"),
        "limit": FETCH_COUNT,
        "apikey": api_key,
    }

    try:
        resp = requests.get(ALPHAVANTAGE_URL, params=params, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  [WARN] {ticker} Alpha Vantage 검색 실패: {e}")
        return []

    data = resp.json()
    if "feed" not in data:
        msg = data.get("Information") or data.get("Note") or ""
        print(f"  [WARN] {ticker} Alpha Vantage 응답 오류: {msg}")
        return []

    results = []
    for article in data.get("feed", []):
        if len(results) >= MAX_PER_COMPANY:
            break
        url = article.get("url", "")
        if not url or url in seen_urls:
            continue
        title = _strip_html(article.get("title") or "")
        if not title:
            continue
        seen_urls.add(url)
        results.append(NewsItem(
            title=title,
            link=url,
            pub_date=article.get("time_published", ""),
            media=article.get("source", ""),
        ))

    time.sleep(DELAY)
    return results


def search_finnhub(ticker: str, seen_urls: set) -> list[NewsItem]:
    """Finnhub API로 티커 기반 뉴스 검색 (해외 기업용)."""
    api_key = os.environ.get("FINNHUB_API_KEY")
    if not api_key:
        raise ValueError("FINNHUB_API_KEY 환경 변수가 설정되지 않았습니다.")

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=HOURS_LIMIT)
    params = {
        "symbol": ticker,
        "from": cutoff.strftime("%Y-%m-%d"),
        "to": now.strftime("%Y-%m-%d"),
        "token": api_key,
    }

    try:
        resp = requests.get(FINNHUB_URL, params=params, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  [WARN] {ticker} Finnhub 검색 실패: {e}")
        return []

    results = []
    for article in resp.json():
        if len(results) >= MAX_PER_COMPANY:
            break
        url = article.get("url", "")
        if not url or url in seen_urls:
            continue
        title = _strip_html(article.get("headline") or "")
        if not title:
            continue
        pub_date = datetime.fromtimestamp(article.get("datetime", 0), tz=timezone.utc).isoformat()
        if not _is_within_hours(pub_date):
            continue
        seen_urls.add(url)
        results.append(NewsItem(
            title=title,
            link=url,
            pub_date=pub_date,
            media=article.get("source", ""),
        ))

    time.sleep(DELAY)
    return results


def search_eng(ticker: str, seen_urls: set) -> list[NewsItem]:
    """Marketaux(주) + Finnhub + Alpha Vantage(보조) 결합 검색 (해외 기업용)."""
    results = search_marketaux(ticker, seen_urls)
    if len(results) < MAX_PER_COMPANY:
        results += search_finnhub(ticker, seen_urls)
    if len(results) < MAX_PER_COMPANY:
        results += search_alphavantage(ticker, seen_urls)
    return results[:MAX_PER_COMPANY]


def search_newsapi(company: str, seen_urls: set) -> list[NewsItem]:
    """NewsAPI로 회사 관련 뉴스 검색 (외국 기업용)."""
    api_key = os.environ.get("NEWSAPI_KEY")
    if not api_key:
        raise ValueError("NEWSAPI_KEY 환경 변수가 설정되지 않았습니다.")

    cutoff = datetime.now(timezone.utc) - timedelta(hours=HOURS_LIMIT)
    params = {
        "q": company,
        "from": cutoff.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sortBy": "publishedAt",
        "pageSize": FETCH_COUNT,
        "apiKey": api_key,
    }

    try:
        resp = requests.get(NEWSAPI_URL, params=params, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  [WARN] {company} NewsAPI 검색 실패: {e}")
        return []

    data = resp.json()
    if data.get("status") != "ok":
        print(f"  [WARN] {company} NewsAPI 오류: {data.get('message', '')}")
        return []

    results = []
    for article in data.get("articles", []):
        if len(results) >= MAX_PER_COMPANY:
            break

        url = article.get("url", "")
        if not url or url in seen_urls:
            continue

        pub_date = article.get("publishedAt", "")
        if not _is_within_hours(pub_date):
            continue

        title = _strip_html(article.get("title") or "")
        description = _strip_html(article.get("description") or "")
        if not title or not _is_relevant(company, title, description, min_count=1):
            continue

        seen_urls.add(url)
        results.append(NewsItem(
            title=title,
            link=url,
            pub_date=pub_date,
            media=article.get("source", {}).get("name", ""),
        ))

    time.sleep(DELAY)
    return results
