from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db, WatchlistItem
from cache_utils import get_or_set
import yfinance as yf
import FinanceDataReader as fdr
import pandas as pd
from collections import OrderedDict

router = APIRouter()
TTL_SECONDS = 3600
SEARCH_TTL_SECONDS = 3600 * 24


class AddStockRequest(BaseModel):
    ticker: str
    market: str = "US"


def lookup_company_name(ticker: str, market: str) -> str | None:
    universe = get_or_set(
        key="watchlist:search-universe",
        ttl_seconds=SEARCH_TTL_SECONDS,
        fetcher=load_search_universe,
        fallback=[],
    )
    target = ticker.strip().upper()
    for item in universe:
        if item["market"] == market and item["ticker"].upper() == target:
            return item["name"]
    return None


def normalize_listing_row(row: dict, market: str) -> dict | None:
    ticker = row.get("Symbol") or row.get("Code") or row.get("symbol")
    name = row.get("Name") or row.get("name")
    if pd.isna(ticker) or pd.isna(name) or not ticker or not name:
        return None
    return {
        "ticker": str(ticker).strip().upper(),
        "name": str(name).strip(),
        "market": market,
    }


def load_search_universe() -> list[dict]:
    markets = [
        ("KRX", "KR"),
        ("NASDAQ", "US"),
        ("NYSE", "US"),
        ("AMEX", "US"),
    ]
    merged: OrderedDict[str, dict] = OrderedDict()

    for source, market in markets:
        try:
            listing = fdr.StockListing(source)
            records = listing.to_dict(orient="records")
            for row in records:
                normalized = normalize_listing_row(row, market)
                if not normalized:
                    continue
                key = f"{normalized['market']}:{normalized['ticker']}"
                merged.setdefault(key, normalized)
        except Exception:
            continue

    return list(merged.values())


def search_companies(query: str) -> list[dict]:
    keyword = query.strip().upper()
    if not keyword:
        return []

    universe = get_or_set(
        key="watchlist:search-universe",
        ttl_seconds=SEARCH_TTL_SECONDS,
        fetcher=load_search_universe,
        fallback=[],
    )

    results = []
    for item in universe:
        ticker = item["ticker"].upper()
        name = item["name"].upper()
        if keyword in ticker or keyword in name:
            score = 0
            if ticker == keyword:
                score += 100
            elif ticker.startswith(keyword):
                score += 70
            if name == keyword:
                score += 90
            elif name.startswith(keyword):
                score += 60
            if item["market"] == "US":
                score += 5
            results.append({**item, "score": score})

    results.sort(key=lambda item: (-item["score"], item["name"], item["ticker"]))
    return [{k: v for k, v in item.items() if k != "score"} for item in results[:10]]


def fetch_stock_info(ticker: str, market: str) -> dict:
    try:
        if market == "KR":
            df = fdr.DataReader(ticker)
            if df.empty:
                return {}
            latest = df.iloc[-1]
            prev   = df.iloc[-2] if len(df) > 1 else latest
            price  = float(latest["Close"])
            change = (price - float(prev["Close"])) / float(prev["Close"]) * 100
            try:
                info   = yf.Ticker(f"{ticker}.KS").info
                name   = info.get("longName") or info.get("shortName") or lookup_company_name(ticker, market) or ticker
                mktcap = info.get("marketCap")
                per    = info.get("trailingPE")
                pbr    = info.get("priceToBook")
                hi52   = info.get("fiftyTwoWeekHigh")
                lo52   = info.get("fiftyTwoWeekLow")
            except Exception:
                name = lookup_company_name(ticker, market) or ticker
                mktcap = per = pbr = hi52 = lo52 = None
            return dict(ticker=ticker, name=name, market=market,
                        price=price, change_pct=round(change, 2),
                        market_cap=mktcap, per=per, pbr=pbr,
                        week52_high=hi52, week52_low=lo52)
        else:
            info   = yf.Ticker(ticker).info
            price  = info.get("currentPrice") or info.get("regularMarketPrice") or 0
            prev   = info.get("regularMarketPreviousClose") or price
            change = (price - prev) / prev * 100 if prev else 0
            return dict(ticker=ticker,
                        name=info.get("longName") or info.get("shortName") or lookup_company_name(ticker, market) or ticker,
                        market=market, price=price,
                        change_pct=round(change, 2),
                        market_cap=info.get("marketCap"),
                        per=info.get("trailingPE"),
                        pbr=info.get("priceToBook"),
                        week52_high=info.get("fiftyTwoWeekHigh"),
                        week52_low=info.get("fiftyTwoWeekLow"))
    except Exception as e:
        return {
            "ticker": ticker,
            "name": lookup_company_name(ticker, market) or ticker,
            "market": market,
            "error": str(e),
        }


def fetch_financials(ticker: str, market: str) -> dict:
    try:
        sym = f"{ticker}.KS" if market == "KR" else ticker
        t = yf.Ticker(sym)
        info = t.info or {}
        inc = t.quarterly_income_stmt
        cash = t.quarterly_cashflow
        if inc is None or inc.empty:
            return {
                "quarters": [],
                "revenue": [],
                "operating_income": [],
                "net_income": [],
                "free_cash_flow": [],
                "metrics": {
                    "per": info.get("trailingPE"),
                    "pbr": info.get("priceToBook"),
                    "roe": info.get("returnOnEquity"),
                },
            }

        cols = list(inc.columns[:8])
        quarters = [str(c)[:10] for c in cols]

        def safe_row(row_name):
            for k in inc.index:
                if row_name.lower() in str(k).lower():
                    return [round(inc.loc[k, c] / 1e9, 2) if pd.notna(inc.loc[k, c]) else None for c in cols]
            return [None] * len(cols)

        def safe_cash_row(*row_names):
            if cash is None or cash.empty:
                return [None] * len(cols)
            for row_name in row_names:
                for k in cash.index:
                    if row_name.lower() in str(k).lower():
                        values = []
                        for c in cols:
                            if c in cash.columns and pd.notna(cash.loc[k, c]):
                                values.append(round(cash.loc[k, c] / 1e9, 2))
                            else:
                                values.append(None)
                        return values
            return [None] * len(cols)

        return dict(
            quarters=quarters,
            revenue=safe_row("total revenue"),
            operating_income=safe_row("operating income"),
            net_income=safe_row("net income"),
            free_cash_flow=safe_cash_row("free cash flow", "operating cash flow"),
            metrics={
                "per": info.get("trailingPE"),
                "pbr": info.get("priceToBook"),
                "roe": info.get("returnOnEquity"),
            },
        )
    except Exception:
        return {
            "quarters": [],
            "revenue": [],
            "operating_income": [],
            "net_income": [],
            "free_cash_flow": [],
            "metrics": {"per": None, "pbr": None, "roe": None},
        }


@router.get("/")
def get_watchlist(db: Session = Depends(get_db)):
    items = db.query(WatchlistItem).all()
    result = []
    for item in items:
        payload = get_or_set(
            key=f"watchlist:quote:{item.market}:{item.ticker}",
            ttl_seconds=TTL_SECONDS,
            fetcher=lambda item=item: fetch_stock_info(item.ticker, item.market),
            fallback={"ticker": item.ticker, "market": item.market, "name": item.name},
        )
        if not payload.get("name") or payload.get("name") == payload.get("ticker"):
            payload["name"] = item.name or lookup_company_name(item.ticker, item.market) or item.ticker
        result.append(payload)
    return result


@router.get("/search")
def autocomplete_stocks(q: str):
    return search_companies(q)


@router.post("/")
def add_stock(req: AddStockRequest, db: Session = Depends(get_db)):
    if db.query(WatchlistItem).filter(WatchlistItem.ticker == req.ticker).first():
        raise HTTPException(status_code=400, detail="Already in watchlist")
    info = fetch_stock_info(req.ticker, req.market)
    item = WatchlistItem(
        ticker=req.ticker,
        name=info.get("name") or lookup_company_name(req.ticker, req.market) or req.ticker,
        market=req.market,
    )
    db.add(item); db.commit()
    return info


@router.delete("/{ticker}")
def remove_stock(ticker: str, db: Session = Depends(get_db)):
    item = db.query(WatchlistItem).filter(WatchlistItem.ticker == ticker).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(item); db.commit()
    return {"ok": True}


@router.get("/{ticker}/financials")
def get_financials(ticker: str, db: Session = Depends(get_db)):
    item = db.query(WatchlistItem).filter(WatchlistItem.ticker == ticker).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return get_or_set(
        key=f"watchlist:financials:{item.market}:{ticker}",
        ttl_seconds=TTL_SECONDS,
        fetcher=lambda: fetch_financials(ticker, item.market),
        fallback={
            "quarters": [],
            "revenue": [],
            "operating_income": [],
            "net_income": [],
            "free_cash_flow": [],
            "metrics": {"per": None, "pbr": None, "roe": None},
        },
    )


@router.get("/{ticker}/chart")
def get_chart(ticker: str, period: str = "1y", db: Session = Depends(get_db)):
    item   = db.query(WatchlistItem).filter(WatchlistItem.ticker == ticker).first()
    market = item.market if item else "US"
    def fetch_chart():
        if market == "KR":
            days = {"1y": 365, "3y": 1095, "5y": 1825}.get(period, 365)
            end = pd.Timestamp.today()
            start = end - pd.Timedelta(days=days)
            df = fdr.DataReader(ticker, start.strftime("%Y-%m-%d"))
        else:
            df = yf.download(ticker, period=period, auto_adjust=True, progress=False)
        df = df[["Close"]].dropna().reset_index()
        df.columns = ["date", "close"]
        df["date"] = df["date"].astype(str)
        return df.to_dict(orient="records")

    return get_or_set(
        key=f"watchlist:chart:{market}:{ticker}:{period}",
        ttl_seconds=TTL_SECONDS,
        fetcher=fetch_chart,
        fallback=[],
    )
