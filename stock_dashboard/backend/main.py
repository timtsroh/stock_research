from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from routers import watchlist, macro, calendar_events
import database
import os

app = FastAPI(title="Stock Research Dashboard API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

database.init_db()

app.include_router(watchlist.router,       prefix="/api/watchlist", tags=["watchlist"])
app.include_router(macro.router,           prefix="/api/macro",     tags=["macro"])
app.include_router(calendar_events.router, prefix="/api/calendar",  tags=["calendar"])


@app.get("/health")
def health():
    return {"status": "ok"}


# Serve React frontend (production build)
_frontend_dist = os.path.join(os.path.dirname(__file__), "../frontend/dist")

if os.path.exists(_frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(_frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        if full_path.startswith("api/"):
            from fastapi import HTTPException
            raise HTTPException(status_code=404)
        return FileResponse(os.path.join(_frontend_dist, "index.html"))
