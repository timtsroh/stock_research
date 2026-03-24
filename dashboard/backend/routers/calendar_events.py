from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db, EventFilter, WatchlistItem
import yfinance as yf
from datetime import datetime, timedelta

router = APIRouter()

# 2025-2026 Fed 회의 및 주요 경제지표 일정 (고정)
SCHEDULED_EVENTS = [
    # FOMC 2025
    {"date": "2025-01-29", "key": "fed",    "title": "FOMC Meeting"},
    {"date": "2025-03-19", "key": "fed",    "title": "FOMC Meeting"},
    {"date": "2025-05-07", "key": "fed",    "title": "FOMC Meeting"},
    {"date": "2025-06-18", "key": "fed",    "title": "FOMC Meeting"},
    {"date": "2025-07-30", "key": "fed",    "title": "FOMC Meeting"},
    {"date": "2025-09-17", "key": "fed",    "title": "FOMC Meeting"},
    {"date": "2025-11-05", "key": "fed",    "title": "FOMC Meeting"},
    {"date": "2025-12-17", "key": "fed",    "title": "FOMC Meeting"},
    # FOMC 2026
    {"date": "2026-01-28", "key": "fed",    "title": "FOMC Meeting"},
    {"date": "2026-03-18", "key": "fed",    "title": "FOMC Meeting"},
    {"date": "2026-04-29", "key": "fed",    "title": "FOMC Meeting"},
    {"date": "2026-06-17", "key": "fed",    "title": "FOMC Meeting"},
    # FOMC 의사록 2025
    {"date": "2025-02-19", "key": "fomc_minutes", "title": "FOMC Minutes"},
    {"date": "2025-04-09", "key": "fomc_minutes", "title": "FOMC Minutes"},
    {"date": "2025-05-28", "key": "fomc_minutes", "title": "FOMC Minutes"},
    # CPI 2025
    {"date": "2025-01-15", "key": "cpi", "title": "CPI"},
    {"date": "2025-02-12", "key": "cpi", "title": "CPI"},
    {"date": "2025-03-12", "key": "cpi", "title": "CPI"},
    {"date": "2025-04-10", "key": "cpi", "title": "CPI"},
    {"date": "2025-05-13", "key": "cpi", "title": "CPI"},
    {"date": "2025-06-11", "key": "cpi", "title": "CPI"},
    {"date": "2025-07-15", "key": "cpi", "title": "CPI"},
    {"date": "2025-08-12", "key": "cpi", "title": "CPI"},
    {"date": "2025-09-10", "key": "cpi", "title": "CPI"},
    {"date": "2025-10-14", "key": "cpi", "title": "CPI"},
    {"date": "2025-11-13", "key": "cpi", "title": "CPI"},
    {"date": "2025-12-10", "key": "cpi", "title": "CPI"},
    # CPI 2026
    {"date": "2026-01-14", "key": "cpi", "title": "CPI"},
    {"date": "2026-02-11", "key": "cpi", "title": "CPI"},
    {"date": "2026-03-11", "key": "cpi", "title": "CPI"},
    {"date": "2026-04-09", "key": "cpi", "title": "CPI"},
    # NFP 2025-2026
    {"date": "2025-01-10", "key": "nfp", "title": "Non-Farm Payroll"},
    {"date": "2025-02-07", "key": "nfp", "title": "Non-Farm Payroll"},
    {"date": "2025-03-07", "key": "nfp", "title": "Non-Farm Payroll"},
    {"date": "2025-04-04", "key": "nfp", "title": "Non-Farm Payroll"},
    {"date": "2025-05-02", "key": "nfp", "title": "Non-Farm Payroll"},
    {"date": "2025-06-06", "key": "nfp", "title": "Non-Farm Payroll"},
    {"date": "2025-07-03", "key": "nfp", "title": "Non-Farm Payroll"},
    {"date": "2025-08-01", "key": "nfp", "title": "Non-Farm Payroll"},
    {"date": "2025-09-05", "key": "nfp", "title": "Non-Farm Payroll"},
    {"date": "2025-10-03", "key": "nfp", "title": "Non-Farm Payroll"},
    {"date": "2025-11-07", "key": "nfp", "title": "Non-Farm Payroll"},
    {"date": "2025-12-05", "key": "nfp", "title": "Non-Farm Payroll"},
    {"date": "2026-01-09", "key": "nfp", "title": "Non-Farm Payroll"},
    {"date": "2026-02-06", "key": "nfp", "title": "Non-Farm Payroll"},
    {"date": "2026-03-06", "key": "nfp", "title": "Non-Farm Payroll"},
    # PCE 2025-2026
    {"date": "2025-01-31", "key": "pce", "title": "PCE"},
    {"date": "2025-02-28", "key": "pce", "title": "PCE"},
    {"date": "2025-03-28", "key": "pce", "title": "PCE"},
    {"date": "2025-04-30", "key": "pce", "title": "PCE"},
    {"date": "2025-05-30", "key": "pce", "title": "PCE"},
    {"date": "2025-06-27", "key": "pce", "title": "PCE"},
    {"date": "2026-01-30", "key": "pce", "title": "PCE"},
    {"date": "2026-02-27", "key": "pce", "title": "PCE"},
    {"date": "2026-03-27", "key": "pce", "title": "PCE"},
    # GDP
    {"date": "2025-01-30", "key": "gdp", "title": "GDP (Advance)"},
    {"date": "2025-04-30", "key": "gdp", "title": "GDP (Advance)"},
    {"date": "2025-07-30", "key": "gdp", "title": "GDP (Advance)"},
    {"date": "2025-10-30", "key": "gdp", "title": "GDP (Advance)"},
    {"date": "2026-01-29", "key": "gdp", "title": "GDP (Advance)"},
]


class UpdateFilterRequest(BaseModel):
    enabled: bool


@router.get("/filters")
def get_filters(db: Session = Depends(get_db)):
    filters = db.query(EventFilter).all()
    return [{"key": f.key, "label": f.label, "enabled": f.enabled, "color": f.color}
            for f in filters]


@router.put("/filters/{key}")
def update_filter(key: str, req: UpdateFilterRequest, db: Session = Depends(get_db)):
    f = db.query(EventFilter).filter(EventFilter.key == key).first()
    if f:
        f.enabled = req.enabled
        db.commit()
    return {"ok": True}


@router.get("/events")
def get_events(db: Session = Depends(get_db)):
    filters  = {f.key: f for f in db.query(EventFilter).all()}
    watchlist = db.query(WatchlistItem).all()
    events   = []

    # 고정 경제 이벤트
    for ev in SCHEDULED_EVENTS:
        f = filters.get(ev["key"])
        if f and f.enabled:
            events.append({"date": ev["date"], "title": ev["title"],
                           "key": ev["key"], "color": f.color})

    # 관심종목 Earnings
    f_earn = filters.get("earnings")
    if f_earn and f_earn.enabled:
        for item in watchlist:
            try:
                sym = f"{item.ticker}.KS" if item.market == "KR" else item.ticker
                cal = yf.Ticker(sym).calendar
                if cal is not None and "Earnings Date" in cal:
                    earn_dates = cal["Earnings Date"]
                    if not isinstance(earn_dates, list):
                        earn_dates = [earn_dates]
                    for d in earn_dates:
                        try:
                            date_str = str(d)[:10]
                            events.append({"date": date_str,
                                           "title": f"{item.name or item.ticker} Earnings",
                                           "key": "earnings", "color": f_earn.color})
                        except Exception:
                            pass
            except Exception:
                pass

    return sorted(events, key=lambda x: x["date"])
