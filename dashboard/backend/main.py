from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import watchlist, macro, calendar_events
import database

app = FastAPI(title="Stock Research Dashboard API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

database.init_db()

app.include_router(watchlist.router,       prefix="/api/watchlist", tags=["watchlist"])
app.include_router(macro.router,           prefix="/api/macro",     tags=["macro"])
app.include_router(calendar_events.router, prefix="/api/calendar",  tags=["calendar"])


@app.get("/")
def root():
    return {"status": "ok", "message": "Stock Research Dashboard API"}
