# EXUR — Atmospheric Intelligence Platform
> **Clean Air & Climate Resilience Platform for Indian Economic Corridors**  
> Deployed on Render with Python (FastAPI + Uvicorn) & Next.js Apple Design System Frontend

---

## 🏛️ System Architecture

Exur has been migrated to a unified **Python FastAPI Web Service** architecture:

- **Backend (Python 3.12 / FastAPI):**
  - High-performance asynchronous API layer with full support for SSE streaming chat, NASA FIRMS processing, Open-Meteo & OpenWeather aggregation, and ISRO MOSDAC satellite telemetry.
  - Complete atmospheric physics & dispersion modeling in Python:
    - `backend/advisor_engine.py`: Grounded citizen respiratory advisor.
    - `backend/attribution.py`: Lagrangian backward kinematic ray-tracing.
    - `backend/earth_engine.py`: Multi-sensor GEE atmospheric harmonization.
    - `backend/aod_to_aqi.py`: Columnar AOD to ground-level PM2.5 converter.
- **Frontend (Apple Design System):**
  - Pre-compiled static React export (`out/`) served directly by FastAPI with zero UI modifications, providing fast loading, interactive Leaflet corridor maps, and smartphone radiometry.

---

## 🚀 Running Locally

### 1. Set Up Python Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy or update `.env.local` (or `.env`):
```bash
cp .env.example .env.local
```
Configure your keys:
- `GEMINI_API_KEY`: Google Gemma 4 / Gemini API key
- `GROQ_API_KEY`: Groq LPU inference key
- `OPENWEATHER_API_KEY`: OpenWeather atmospheric conditions key
- `NASA_FIRMS_KEY`: NASA FIRMS fire telemetry key
- `OPENAQ_API_KEY`: OpenAQ v3 ground sensor key
- `NEXT_PUBLIC_CARTO_KEY`: CartoDB basemap key

### 3. Build Frontend & Start Server
```bash
# Build the static UI export
pnpm build

# Start the unified Python server
python3 main.py
# Or with auto-reload:
uvicorn main:app --reload --port 8000
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

---

## 🌐 Deploying to Render

This repository is pre-configured for **Render** via Blueprint (`render.yaml`), Native Python runtime (`build.sh`), or Docker (`Dockerfile`).

### Option 1: Render Blueprint (Recommended)
1. Push this repository to GitHub or GitLab.
2. In the [Render Dashboard](https://dashboard.render.com), click **New +** → **Blueprint**.
3. Connect your repository. Render will automatically detect `render.yaml`.
4. Fill in your environment variables in the Render settings.
5. Deploy!

### Option 2: Render Web Service (Manual)
1. In Render Dashboard, click **New +** → **Web Service**.
2. Connect your repository.
3. Configure the following settings:
   - **Environment:** `Python 3`
   - **Build Command:** `./build.sh`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add your environment variables under the **Environment** tab.
5. Click **Create Web Service**.

### Option 3: Render Docker Web Service
- If deploying with Docker, Render will detect `Dockerfile` automatically and perform the multi-stage build.

---

## 📡 API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | System health & endpoint registry |
| `/api/chat` | POST | Google Gemma 4 streaming & non-streaming advisory |
| `/api/corridor` | GET | Real-time CPCB + Open-Meteo corridor station air quality |
| `/api/firms` | GET | NASA FIRMS VIIRS active stubble fire hotspots |
| `/api/gee` | GET | Sentinel-5P & MODIS GEE multi-sensor harmonization |
| `/api/satellite` | GET | ISRO MOSDAC INSAT-3DS preview imagery & AOD detector |
| `/api/weather` | GET | Boundary layer height & atmospheric conditions |
| `/api/wind-history` | GET | Hourly historical kinematic wind vectors |
| `/api/radiometry/openaq` | GET | CORS-safe OpenAQ ground truth sensor proxy |
| `/api/radiometry/vision` | POST | Gemma 4 multimodal sky haze & aerosol vision analyzer |
