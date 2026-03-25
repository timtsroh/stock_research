from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db, WatchlistItem
import yfinance as yf
import FinanceDataReader as fdr
import pandas as pd

router = APIRouter()


class AddStockRequest(BaseModel):
    ticker: str
    market: str = "US"


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
                name   = info.get("longName") or info.get("shortName") or ticker
                mktcap = info.get("marketCap")
                per    = info.get("trailingPE")
                pbr    = info.get("priceToBook")
                hi52   = info.get("fiftyTwoWeekHigh")
                lo52   = info.get("fiftyTwoWeekLow")
            except Exception:
                name = ticker; mktcap = per = pbr = hi52 = lo52 = None
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
                        name=info.get("longName") or info.get("shortName") or ticker,
                        market=market, price=price,
                        change_pct=round(change, 2),
                        market_cap=info.get("marketCap"),
                        per=info.get("trailingPE"),
                        pbr=info.get("priceToBook"),
                        week52_high=info.get("fiftyTwoWeekHigh"),
                        week52_low=info.get("fiftyTwoWeekLow"))
    except Exception as e:
        return {"ticker": ticker, "market": market, "error": str(e)}


def fetch_financials(ticker: str, market: str) -> dict:
    try:
        sym = f"{ticker}.KS" if market == "KR" else ticker
        t   = yf.Ticker(sym)
        inc = t.quarterly_income_stmt
        if inc is None or inc.empty:
            return {"quarters": [], "revenue": [], "operating_income": [], "net_income": []}
        cols     = list(inc.columns[:8])
        quarters = [str(c)[:10] for c in cols]

        def safe_row(row_name):
            for k in inc.index:
                if row_name.lower() in str(k).lower():
                    return [round(inc.loc[k, c] / 1e9, 2) if pd.notna(inc.loc[k, c]) else None for c in cols]
            return [None] * len(cols)

        return dict(quarters=quarters,
                    revenue=safe_row("total revenue"),
                    operating_income=safe_row("operating income"),
                    net_income=safe_row("net income"))
    except Exception:
        return {"quarters": [], "revenue": [], "operating_income": [], "net_income": []}


@router.get("/")
def get_watchlist(db: Session = Depends(get_db)):
    items  = db.query(WatchlistItem).all()
    return [fetch_stock_info(item.ticker, item.market) for item in items]


@router.post("/")
def add_stock(req: AddStockRequest, db: Session = Depends(get_db)):
    if db.query(WatchlistItem).filter(WatchlistItem.ticker == req.ticker).first():
        raise HTTPException(status_code=400, detail="Already in watchlist")
    info = fetch_stock_info(req.ticker, req.market)
    item = WatchlistItem(ticker=req.ticker, name=info.get("name", req.ticker), market=req.market)
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
    return fetch_financials(ticker, item.market)


@router.get("/{ticker}/chart")
def get_chart(ticker: str, period: str = "1y", db: Session = Depends(get_db)):
    item   = db.query(WatchlistItem).filter(WatchlistItem.ticker == ticker).first()
    market = item.market if item else "US"
    try:
        if market == "KR":
            days  = {"1y": 365, "3y": 1095, "5y": 1825}.get(period, 365)
            end   = pd.Timestamp.today()
            start = end - pd.Timedelta(days=days)
            df    = fdr.DataReader(ticker, start.strftime("%Y-%m-%d"))
        else:
            df = yf.download(ticker, period=period, auto_adjust=True, progress=False)
        df = df[["Close"]].dropna().reset_index()
        df.columns = ["date", "close"]
        df["date"] = df["date"].astype(str)
        return df.to_dict(orient="records")
    except Exception:
        return []
