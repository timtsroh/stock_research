from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db, EventFilter, WatchlistItem
import yfinance as yf

router = APIRouter()

SCHEDULED_EVENTS = [
    # FOMC 2025
    {"date": "2025-01-29", "key": "fed",          "title": "FOMC Meeting"},
    {"date": "2025-03-19", "key": "fed",          "title": "FOMC Meeting"},
    {"date": "2025-05-07", "key": "fed",          "title": "FOMC Meeting"},
    {"date": "2025-06-18", "key": "fed",          "title": "FOMC Meeting"},
    {"date": "2025-07-30", "key": "fed",          "title": "FOMC Meeting"},
    {"date": "2025-09-17", "key": "fed",          "title": "FOMC Meeting"},
    {"date": "2025-11-05", "key": "fed",          "title": "FOMC Meeting"},
    {"date": "2025-12-17", "key": "fed",          "title": "FOMC Meeting"},
    # FOMC 2026
    {"date": "2026-01-28", "key": "fed",          "title": "FOMC Meeting"},
    {"date": "2026-03-18", "key": "fed",          "title": "FOMC Meeting"},
    {"date": "2026-04-29", "key": "fed",          "title": "FOMC Meeting"},
    {"date": "2026-06-17", "key": "fed",          "title": "FOMC Meeting"},
    # FOMC 의사록 2025
    {"date": "2025-02-19", "key": "fomc_minutes", "title": "FOMC Minutes"},
    {"date": "2025-04-09", "key": "fomc_minutes", "title": "FOMC Minutes"},
    {"date": "2025-05-28", "key": "fomc_minutes", "title": "FOMC Minutes"},
    {"date": "2025-07-09", "key": "fomc_minutes", "title": "FOMC Minutes"},
    {"date": "2025-08-20", "key": "fomc_minutes", "title": "FOMC Minutes"},
    {"date": "2025-10-08", "key": "fomc_minutes", "title": "FOMC Minutes"},
    {"date": "2025-11-26", "key": "fomc_minutes", "title": "FOMC Minutes"},
    {"date": "2026-01-07", "key": "fomc_minutes", "title": "FOMC Minutes"},
    # CPI 2025-2026
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
    {"date": "2026-01-14", "key": "cpi", "title": "CPI"},
    {"date": "2026-02-11", "key": "cpi", "title": "CPI"},
    {"date": "2026-03-11", "key": "cpi", "title": "CPI"},
    {"date": "2026-04-09", "key": "cpi", "title": "CPI"},
    # PPI 2025-2026
    {"date": "2025-01-14", "key": "ppi", "title": "PPI"},
    {"date": "2025-02-13", "key": "ppi", "title": "PPI"},
    {"date": "2025-03-13", "key": "ppi", "title": "PPI"},
    {"date": "2025-04-11", "key": "ppi", "title": "PPI"},
    {"date": "2025-05-15", "key": "ppi", "title": "PPI"},
    {"date": "2025-06-12", "key": "ppi", "title": "PPI"},
    {"date": "2025-07-15", "key": "ppi", "title": "PPI"},
    {"date": "2025-08-14", "key": "ppi", "title": "PPI"},
    {"date": "2025-09-11", "key": "ppi", "title": "PPI"},
    {"date": "2025-10-16", "key": "ppi", "title": "PPI"},
    {"date": "2025-11-13", "key": "ppi", "title": "PPI"},
    {"date": "2025-12-11", "key": "ppi", "title": "PPI"},
    {"date": "2026-01-15", "key": "ppi", "title": "PPI"},
    {"date": "2026-02-12", "key": "ppi", "title": "PPI"},
    {"date": "2026-03-12", "key": "ppi", "title": "PPI"},
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
    {"date": "2025-07-31", "key": "pce", "title": "PCE"},
    {"date": "2025-08-29", "key": "pce", "title": "PCE"},
    {"date": "2025-09-26", "key": "pce", "title": "PCE"},
    {"date": "2025-10-31", "key": "pce", "title": "PCE"},
    {"date": "2025-11-26", "key": "pce", "title": "PCE"},
    {"date": "2025-12-19", "key": "pce", "title": "PCE"},
    {"date": "2026-01-30", "key": "pce", "title": "PCE"},
    {"date": "2026-02-27", "key": "pce", "title": "PCE"},
    {"date": "2026-03-27", "key": "pce", "title": "PCE"},
    # GDP 2025-2026
    {"date": "2025-01-30", "key": "gdp", "title": "GDP (Advance)"},
    {"date": "2025-04-30", "key": "gdp", "title": "GDP (Advance)"},
    {"date": "2025-07-30", "key": "gdp", "title": "GDP (Advance)"},
    {"date": "2025-10-30", "key": "gdp", "title": "GDP (Advance)"},
    {"date": "2026-01-29", "key": "gdp", "title": "GDP (Advance)"},
    {"date": "2026-04-29", "key": "gdp", "title": "GDP (Advance)"},
    # ISM 2025-2026
    {"date": "2025-01-03", "key": "ism", "title": "ISM 제조업 PMI"},
    {"date": "2025-02-03", "key": "ism", "title": "ISM 제조업 PMI"},
    {"date": "2025-03-03", "key": "ism", "title": "ISM 제조업 PMI"},
    {"date": "2025-04-01", "key": "ism", "title": "ISM 제조업 PMI"},
    {"date": "2025-05-01", "key": "ism", "title": "ISM 제조업 PMI"},
    {"date": "2025-06-02", "key": "ism", "title": "ISM 제조업 PMI"},
    {"date": "2025-07-01", "key": "ism", "title": "ISM 제조업 PMI"},
    {"date": "2025-08-01", "key": "ism", "title": "ISM 제조업 PMI"},
    {"date": "2025-09-02", "key": "ism", "title": "ISM 제조업 PMI"},
    {"date": "2025-10-01", "key": "ism", "title": "ISM 제조업 PMI"},
    {"date": "2025-11-03", "key": "ism", "title": "ISM 제조업 PMI"},
    {"date": "2025-12-01", "key": "ism", "title": "ISM 제조업 PMI"},
    {"date": "2026-01-05", "key": "ism", "title": "ISM 제조업 PMI"},
    {"date": "2026-02-02", "key": "ism", "title": "ISM 제조업 PMI"},
    {"date": "2026-03-02", "key": "ism", "title": "ISM 제조업 PMI"},
    # 소비자신뢰지수 2025-2026
    {"date": "2025-01-28", "key": "consumer", "title": "소비자신뢰지수"},
    {"date": "2025-02-25", "key": "consumer", "title": "소비자신뢰지수"},
    {"date": "2025-03-25", "key": "consumer", "title": "소비자신뢰지수"},
    {"date": "2025-04-29", "key": "consumer", "title": "소비자신뢰지수"},
    {"date": "2025-05-27", "key": "consumer", "title": "소비자신뢰지수"},
    {"date": "2025-06-24", "key": "consumer", "title": "소비자신뢰지수"},
    {"date": "2025-07-29", "key": "consumer", "title": "소비자신뢰지수"},
    {"date": "2025-08-26", "key": "consumer", "title": "소비자신뢰지수"},
    {"date": "2025-09-30", "key": "consumer", "title": "소비자신뢰지수"},
    {"date": "2025-10-28", "key": "consumer", "title": "소비자신뢰지수"},
    {"date": "2025-11-25", "key": "consumer", "title": "소비자신뢰지수"},
    {"date": "2025-12-23", "key": "consumer", "title": "소비자신뢰지수"},
    {"date": "2026-01-27", "key": "consumer", "title": "소비자신뢰지수"},
    {"date": "2026-02-24", "key": "consumer", "title": "소비자신뢰지수"},
    {"date": "2026-03-31", "key": "consumer", "title": "소비자신뢰지수"},
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
    filters   = {f.key: f for f in db.query(EventFilter).all()}
    watchlist = db.query(WatchlistItem).all()
    events    = []

    for ev in SCHEDULED_EVENTS:
        f = filters.get(ev["key"])
        if f and f.enabled:
            events.append({"date": ev["date"], "title": ev["title"],
                           "key": ev["key"], "color": f.color})

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
                            events.append({"date": str(d)[:10],
                                           "title": f"{item.name or item.ticker} Earnings",
                                           "key": "earnings", "color": f_earn.color})
                        except Exception:
                            pass
            except Exception:
                pass

    return sorted(events, key=lambda x: x["date"])
