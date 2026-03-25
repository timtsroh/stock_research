from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db, MacroPanel
import yfinance as yf
import pandas as pd

router = APIRouter()

PRESET_TICKERS = {
    "^TNX":     "미국 10Y 금리",
    "^GSPC":    "S&P 500",
    "DX-Y.NYB": "달러 인덱스",
    "CL=F":     "WTI 유가",
    "^VIX":     "VIX 지수",
    "^NDX":     "나스닥 100",
    "^KS11":    "KOSPI",
    "^KQ11":    "KOSDAQ",
    "GC=F":     "금 선물",
    "^IXIC":    "나스닥 종합",
    "^DJI":     "다우존스",
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
    try:
        df = yf.download(ticker, period=period, auto_adjust=True, progress=False)
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
    except Exception as e:
        return {"data": [], "latest": None, "change": None, "error": str(e)}
