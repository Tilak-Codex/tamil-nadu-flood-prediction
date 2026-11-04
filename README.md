# AI-Based Flood Prediction and Decision Support System
### Tamil Nadu — LSTM River Water-Level Forecasting

> **Final-Year Engineering Project** | Tamil Nadu CWC Dataset | Python 3.13 · React 19 · FastAPI · LSTM

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     React Frontend (Vite)                       │
│  Overview · Station Map · Hydrographs · Predictions · Risk      │
│  Alerts · Model Evaluation · Data Sources                       │
│               http://localhost:5173                             │
└──────────────────────────┬──────────────────────────────────────┘
                           │  /api proxy
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   FastAPI Backend                               │
│  /api/stations · /api/observations · /api/predictions          │
│  /api/risk · /api/alerts · /api/dashboard · /api/data-sources  │
│               http://localhost:8000                             │
└──────────────────────────┬──────────────────────────────────────┘
                           │  SQLAlchemy ORM
                           ▼
┌──────────────────────┐  ┌──────────────────────────────────────┐
│   SQLite (dev)       │  │   PostgreSQL (prod via Docker)       │
│  data/flood_system.db│  │   tn_flood_db                        │
└──────────────────────┘  └──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│               LSTM Prediction Service                           │
│  Input: 24-hour window [water_level, rainfall, temp, pressure] │
│  Output: next-hour water level + flood risk category           │
│  Saved: models/lstm/model.keras · scalers.pkl · metadata.json  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19 + Vite · Tailwind CSS · Leaflet + React-Leaflet · Recharts · Lucide React |
| Backend | Python 3.13 · FastAPI · Uvicorn · SQLAlchemy · Pydantic |
| ML | TensorFlow/Keras · LSTM · Scikit-learn · Pandas · NumPy |
| Database | SQLite (dev) · PostgreSQL (prod via Docker) |
| Testing | Pytest · FastAPI TestClient |

---

## Dataset

- **Source:** Central Water Commission (CWC) historical telemetry exports
- **Coverage:** Jan 2021 – Jul 2026 (906,971 records)
- **Stations:** 35 Tamil Nadu stations across Cauvery, Adyar, Gundar river basins
- **Features:** `water_level`, `rainfall` (simulated), `temperature` (simulated), `pressure` (simulated)
- **Note:** Meteorological features are physically coupled simulations derived from water-level dynamics — CWC CSV exports do not include raw weather fields.

> ⚠ **All data is HISTORICAL / SIMULATED. This system does not display live telemetry.**

---

## ML Model Performance

| Model | MAE (m) | RMSE (m) | R² | NSE |
|-------|---------|----------|-----|-----|
| Persistence Baseline | 5.75 | 39.89 | 0.9863 | — |
| Moving Average | 22.65 | 87.71 | 0.9337 | — |
| Ridge Regression | 8.53 | 39.20 | 0.9868 | — |
| **LSTM (Our Model)** | **14.24** | **41.05** | **0.9855** | **0.9855** |

Evaluated on 128,991 test sequences (chronological split — no data leakage).  
Trained for 10 epochs; early stopping triggered at epoch 6.

---

## Setup Instructions

### Prerequisites

- Python 3.10+ (tested on 3.13.12)
- Node.js 18+ (tested on 22.22.3)
- Git

### 1. Clone & Create Python Virtual Environment

```bash
git clone <repo-url>
cd demo1
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

```bash
cp .env.example .env
# Edit .env as needed (DATABASE_URL, etc.)
```

### 4. Initialize Database

```bash
python scripts/init_database.py
```

Creates `data/flood_system.db` with 35 stations, CWC flood thresholds, and 1,680 seed observations.

### 5. (Optional) Train ML Model

The trained model is included in `models/lstm/`. To retrain:

```bash
# Prepare dataset
python scripts/prepare_dataset.py

# Train baselines
python scripts/train_baselines.py

# Train LSTM
python scripts/train_lstm.py

# Evaluate all models
python scripts/evaluate_all.py

# Generate predictions CSV
python scripts/generate_predictions.py
```

### 6. Start Backend

```bash
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
```

API docs: http://localhost:8000/docs  
Health check: http://localhost:8000/health

### 7. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:5173

---

## Production Setup (PostgreSQL via Docker)

```bash
# Start PostgreSQL
docker-compose up -d

# Set DATABASE_URL
export DATABASE_URL=postgresql://postgres:postgres123@localhost:5432/tn_flood_db

# Initialize database
python scripts/init_database.py

# Start backend
uvicorn src.api.app:app --host 0.0.0.0 --port 8000
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | System health check |
| GET | `/api/stations` | List all 35 stations |
| GET | `/api/stations/{id}` | Station details + thresholds |
| GET | `/api/observations/{id}?n=48` | Recent water-level observations |
| GET | `/api/observations/{id}/weather?n=48` | Recent weather observations |
| GET | `/api/forecast/{id}` | LSTM next-hour prediction |
| POST | `/api/predictions/run` | Run prediction for a station |
| GET | `/api/risk/summary` | Risk summary for all stations |
| GET | `/api/risk/{id}` | Risk for specific station |
| GET | `/api/alerts` | Active unacknowledged alerts |
| GET | `/api/alerts/all` | All alerts (history) |
| POST | `/api/alerts/{id}/acknowledge` | Acknowledge an alert |
| GET | `/api/dashboard/stats` | KPI statistics |
| GET | `/api/dashboard/map` | Map view data |
| GET | `/api/data-sources` | Data source status |
| POST | `/api/data-sources/refresh` | Trigger data source refresh |
| GET | `/model/metrics` | ML model evaluation metrics |
| GET | `/model/training-history` | LSTM training history |

Full Swagger UI: http://localhost:8000/docs

---

## Running Tests

```bash
pytest tests/ -v
```

Expected: **25 tests passed**

Test files:
- `tests/test_api.py` — 12 API endpoint tests
- `tests/test_classification.py` — 6 flood risk classification tests
- `tests/test_data_validation.py` — 4 dataset validation tests
- `tests/test_sequence_generation.py` — 3 LSTM sequence tests

---

## Project Structure

```
demo1/
├── data/
│   ├── raw/                    # CWC raw CSV exports
│   ├── processed/              # Cleaned, feature-engineered data
│   └── flood_system.db         # SQLite development database
├── models/
│   └── lstm/
│       ├── model.keras         # Trained LSTM model
│       ├── scalers.pkl         # Per-station MinMaxScalers
│       ├── metadata.json       # Training configuration
│       └── training_history.json
├── results/
│   ├── metrics.csv             # Model comparison metrics
│   ├── predictions.csv         # 128,991 test predictions
│   └── plots/                  # Research visualizations
├── scripts/
│   ├── prepare_dataset.py      # Feature engineering pipeline
│   ├── train_baselines.py      # Baseline model training
│   ├── train_lstm.py           # LSTM training
│   ├── evaluate_all.py         # Model evaluation
│   ├── generate_predictions.py # Prediction CSV generation
│   ├── generate_plots.py       # Research plot generation
│   └── init_database.py        # DB initialization
├── src/
│   ├── api/
│   │   ├── app.py              # FastAPI app + middleware
│   │   ├── schemas.py          # Pydantic request/response models
│   │   └── routes/             # Modular API routers
│   ├── config.py               # Configuration & constants
│   ├── database/
│   │   ├── connection.py       # SQLAlchemy engine setup
│   │   └── models.py           # ORM table definitions
│   ├── models/                 # ML model classes
│   ├── preprocessing/          # Feature engineering
│   ├── repositories/           # DB access layer
│   └── services/               # Business logic (prediction, risk)
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Main orchestrator
│   │   ├── api.js              # Backend API client
│   │   ├── index.css           # Tailwind + Leaflet CSS
│   │   └── components/         # 9 dashboard components
│   ├── vite.config.js          # Vite + Tailwind + API proxy
│   └── package.json
├── tests/                      # pytest test suite
├── docker-compose.yml          # PostgreSQL production
├── requirements.txt
├── .env.example
└── PROJECT_STATUS.md
```

---

## Flood Risk Classification

| Category | Condition | Source |
|----------|-----------|--------|
| Normal | Below Warning Level | CWC Verified |
| Above Normal | Between Warning and Danger Level | CWC Verified |
| Severe | Between Danger and HFL | CWC Verified |
| Extreme | Above Highest Flood Level | CWC Verified |
| **Threshold Unavailable** | No verified CWC thresholds on record | — |

> Never uses arbitrary thresholds. Returns "Threshold Unavailable" when official CWC data is absent.

---

## Data Sources

| Source | Status | Notes |
|--------|--------|-------|
| CWC Telemetry | ✅ Historical CSV | 906,971 records used for training |
| Open-Meteo | ⚠ Simulated | No live API calls; physically coupled simulations |
| IMD | 🔒 Auth Required | Government registration required |
| India-WRIS | 🔒 Auth Required | Government portal, no public API |
| TN-WRD | 🔒 Auth Required | State portal, manual export only |
| NWDP | 🔒 Auth Required | Government portal |

---

## License & Acknowledgements

Final-year engineering project. Dataset courtesy of Central Water Commission (CWC), Government of India.  
Not intended for operational flood forecasting — research and educational use only.
