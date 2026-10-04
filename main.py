"""
EXUR — Atmospheric Intelligence Platform
FastAPI Python Server for Render Deployment
"""

import sys
import os

# If launched with an older system Python (e.g. macOS /usr/bin/python3 which is 3.9),
# auto re-exec with the project's Python 3.12 virtual environment.
project_dir = os.path.dirname(os.path.abspath(__file__))
venv_python = os.path.join(project_dir, ".venv", "bin", "python")
if sys.version_info < (3, 10) and os.path.exists(venv_python):
    os.execv(venv_python, [venv_python] + sys.argv)

import glob
from pathlib import Path

project_root = Path(__file__).resolve().parent
for sp in glob.glob(str(project_root / ".venv" / "lib" / "python*" / "site-packages")):
    if sp not in sys.path:
        sys.path.insert(0, sp)

from dotenv import load_dotenv

# 1. Load Environment Variables (.env.local has precedence)
env_local_path = project_root / ".env.local"
if env_local_path.exists():
    load_dotenv(dotenv_path=env_local_path)
else:
    load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

# Import API Routers
from backend.api.chat import router as chat_router
from backend.api.corridor import router as corridor_router
from backend.api.firms import router as firms_router
from backend.api.gee import router as gee_router
from backend.api.satellite import router as satellite_router
from backend.api.weather import router as weather_router
from backend.api.wind_history import router as wind_history_router
from backend.api.radiometry import router as radiometry_router

app = FastAPI(
    title="Exur Atmospheric Intelligence Platform",
    description="Clean Air & Climate Resilience Platform built for Indian Economic Corridors",
    version="1.0.0",
)

# 2. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Mount Backend API Routers under /api
app.include_router(chat_router, prefix="/api", tags=["Advisor Chat"])
app.include_router(corridor_router, prefix="/api", tags=["Corridor AQI"])
app.include_router(firms_router, prefix="/api", tags=["NASA FIRMS"])
app.include_router(gee_router, prefix="/api", tags=["Google Earth Engine"])
app.include_router(satellite_router, prefix="/api", tags=["ISRO Satellite"])
app.include_router(weather_router, prefix="/api", tags=["Weather"])
app.include_router(wind_history_router, prefix="/api", tags=["Wind History"])
app.include_router(radiometry_router, prefix="/api", tags=["Citizen Radiometry"])

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "Exur Atmospheric Engine",
        "python": "3.12",
        "apis": [
            "/api/chat",
            "/api/corridor",
            "/api/firms",
            "/api/gee",
            "/api/satellite",
            "/api/weather",
            "/api/wind-history",
            "/api/radiometry/openaq",
            "/api/radiometry/vision",
        ],
    }

# 4. Frontend Static Files Serving (Next.js static export in `out/`)
OUT_DIR = Path(__file__).parent / "out"

if (OUT_DIR / "_next").exists():
    app.mount("/_next", StaticFiles(directory=str(OUT_DIR / "_next")), name="next_static")

@app.api_route("/{full_path:path}", methods=["GET", "HEAD"])
async def serve_static_frontend(full_path: str):
    # Don't intercept API or health endpoints
    if full_path.startswith("api/") or full_path == "api" or full_path == "health":
        raise HTTPException(status_code=404, detail="API route not found")

    if not OUT_DIR.exists():
        return JSONResponse(
            status_code=200,
            content={
                "message": "Exur Python API server is running.",
                "note": "Static UI files not found in /out. Run `pnpm build` to compile the frontend.",
            }
        )

    # 1. Exact file match (e.g. favicon.ico, logo.png, robots.txt)
    requested_file = OUT_DIR / full_path
    if requested_file.is_file():
        return FileResponse(str(requested_file))

    # 2. Clean URL match (e.g. /advisor -> out/advisor.html or out/advisor/index.html)
    clean_html_file = OUT_DIR / f"{full_path}.html"
    if clean_html_file.is_file():
        return FileResponse(str(clean_html_file))

    nested_index_file = OUT_DIR / full_path / "index.html"
    if nested_index_file.is_file():
        return FileResponse(str(nested_index_file))

    # 3. Root URL match
    if not full_path or full_path == "/":
        index_file = OUT_DIR / "index.html"
        if index_file.is_file():
            return FileResponse(str(index_file))

    # 4. Fallback to 404 or index.html
    not_found_file = OUT_DIR / "404.html"
    if not_found_file.is_file():
        return FileResponse(str(not_found_file), status_code=404)

    index_fallback = OUT_DIR / "index.html"
    if index_fallback.is_file():
        return FileResponse(str(index_fallback))

    raise HTTPException(status_code=404, detail="Page not found")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
