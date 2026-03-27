from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db, MacroPanel
from cache_utils import get_or_set
import yfinance as yf
import FinanceDataReader as fdr
import pandas as pd

router = APIRouter()
TTL_SECONDS = 3600

PRESET_TICKERS = {
    "US10YT=X": "미국 10Y 금리",
    "SP500":    "S&P 500",
    "DX-Y.NYB": "달러 인덱스",
    "CL=F":     "WTI 유가",
    "VIX":      "VIX 지수",
    "QQQ":      "나스닥 100",
    "KS11":     "KOSPI",
    "KQ11":     "KOSDAQ",
    "GC=F":     "금 선물",
    "IXIC":     "나스닥 종합",
    "DJI":      "다우존스",
}
LEGACY_TICKER_MAP = {
    "^TNX": "US10YT=X",
    "^GSPC": "SP500",
    "^VIX": "VIX",
    "^NDX": "QQQ",
    "^KS11": "KS11",
    "^KQ11": "KQ11",
    "^IXIC": "IXIC",
    "^DJI": "DJI",
}


class UpdatePanelRequest(BaseModel):
    ticker: str
    label:  str


@router.get("/panels")
def get_panels(db: Session = Depends(get_db)):
    panels = db.query(MacroPanel).order_by(MacroPanel.slot).all()
    return [{"slot": p.slot, "ticker": p.ticker, "label": p.label} for p in panels]


@router.put("/panels/{slot}")
def update_panel(slot: int, req: UpdatePanelRequest, db: Session = Depends(get_db)):
    panel = db.query(MacroPanel).filter(MacroPanel.slot == slot).first()
    if panel:
        panel.ticker = req.ticker
        panel.label  = req.label
        db.commit()
    return {"ok": True}


@router.get("/presets")
def get_presets():
    return [{"ticker": k, "label": v} for k, v in PRESET_TICKERS.items()]


@router.get("/chart/{ticker}")
def get_macro_chart(ticker: str, period: str = "5y"):
    normalized_ticker = LEGACY_TICKER_MAP.get(ticker, ticker)

    def fetch_chart():
        days = {"1y": 365, "3y": 365 * 3, "5y": 365 * 5}.get(period, 365 * 5)
        start = (pd.Timestamp.today() - pd.Timedelta(days=days)).strftime("%Y-%m-%d")

        try:
            df = fdr.DataReader(normalized_ticker, start)
        except Exception:
            yf_ticker = {
                "SP500": "^GSPC",
                "VIX": "^VIX",
                "QQQ": "QQQ",
                "KS11": "^KS11",
                "KQ11": "^KQ11",
                "IXIC": "^IXIC",
                "DJI": "^DJI",
                "US10YT=X": "^TNX",
            }.get(normalized_ticker, normalized_ticker)
            df = yf.download(yf_ticker, period=period, auto_adjust=True, progress=False)

        if df.empty:
            return {"data": [], "latest": None, "change": None}

        df = df[["Close"]].dropna().reset_index()
        df.columns = ["date", "close"]
        df["date"] = df["date"].astype(str)
        df = df.iloc[::5].reset_index(drop=True)
        latest = float(df["close"].iloc[-1])
        prev   = float(df["close"].iloc[-2]) if len(df) > 1 else latest
        change = round((latest - prev) / prev * 100, 2)
        return {"data": df.to_dict(orient="records"), "latest": round(latest, 4), "change": change}

    return get_or_set(
        key=f"macro:chart:{normalized_ticker}:{period}",
        ttl_seconds=TTL_SECONDS,
        fetcher=fetch_chart,
        fallback={"data": [], "latest": None, "change": None},
    )
