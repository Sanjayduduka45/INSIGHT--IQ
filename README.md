# InsightIQ — Enterprise AI Data Analytics Platform

> Upload Any Dataset. Get Expert-Level Insights Instantly.

An **Enterprise AI Data Intelligence Platform** built on **React + TypeScript + FastAPI + Supabase + Google Gemini**. Turn raw tabular business datasets (CSV, Excel, Parquet, JSON) into **board-ready executive dashboards**, **multi-model time-series forecasts**, and **McKinsey-style PDF reports** — powered by zero-config AI reasoning.

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React%20+%20TypeScript-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Bundler-Vite-646CFF?logo=vite&logoColor=white)](https://vite.dev)
[![Tailwind CSS](https://img.shields.io/badge/Styles-Tailwind%20CSS-06B6D4?logo=tailwindcss&logoColor=white)](https://tailwindcss.com)
[![Supabase](https://img.shields.io/badge/Database-Supabase-3ECF8E?logo=supabase&logoColor=white)](https://supabase.com)
[![Gemini](https://img.shields.io/badge/AI-Google%20Gemini-4285F4?logo=google&logoColor=white)](https://ai.google.dev)
[![Pytest](https://img.shields.io/badge/Tests-Pytest-0A9EDC?logo=pytest&logoColor=white)](https://pytest.org)

---

## 🏗️ Architecture

```
                     ┌──────────────────────────────────┐
                     │     React + TypeScript + Vite    │
                     │       (Tailwind CSS / ShadCN)    │
                     │       http://localhost:5173       │
                     └──────────────┬───────────────────┘
                                    │ HTTPS (Supabase JWT Bearer Auth)
                                    ▼
                     ┌──────────────────────────────────┐
                     │     FastAPI Gateway (Python)      │
                     │   Rate Limiting · CORS · Auth    │
                     │       http://localhost:8000       │
                     └────────┬─────────────┬───────────┘
                              │             │
         Supabase PostgreSQL  │             │  LLM Reasoning
                              ▼             ▼
                     ┌──────────────┐  ┌───────────────┐
                     │  Analytics   │  │ Google Gemini │
                     │  Engine      │  │  (2.0-Flash)  │
                     │  Pandas /    │  │               │
                     │  Scikit-Learn│  │  Natural lang │
                     │  XGBoost     │  │  chat & insight│
                     └──────────────┘  └───────────────┘
```

| Layer | Technology |
|---|---|
| **Frontend** | React 19 · TypeScript · Vite · Tailwind CSS · ShadCN UI · Recharts |
| **Backend** | FastAPI · Python 3.11 · uvicorn |
| **Database** | Supabase PostgreSQL |
| **Auth** | Supabase Auth (JWT HS256) |
| **AI** | Google Gemini 2.0 Flash |
| **Analytics** | Pandas · Scikit-Learn · SciPy · XGBoost · DuckDB |
| **Deployment** | Vercel (frontend) · Railway (backend) · Supabase (database) |

---

## ✨ Features

### 1. Robust Dataset Ingestion
- **Multi-Format Support**: CSV, Excel (`.xlsx`, `.xls`), Parquet, and JSON
- **Encoding Auto-Detection**: Handles `utf-8`, `utf-8-sig`, `latin-1`, `cp1252`, `iso-8859-1`
- **Memory Safety**: Supports datasets up to 2 GB via chunk-processing and stream-sampling

### 2. Universal Profiling Engine
- **Auto-Domain Classifier**: Categorises datasets into 15+ domains (Sales, Finance, Healthcare, HR, Logistics, IoT, Cybersecurity, etc.)
- **Dynamic Schema Detection**: Identifies metrics, IDs, categorical dimensions, and datetime indices automatically

### 3. Executive Dashboard
- **KPI Metrics Ribbon**: Health scores, completeness %, unique parameters, and continuous columns
- **Moving Average Trends**: 7-point rolling average trend lines
- **Visual Analytics**: Density histograms, boxplots, Pareto charts, scatter relations, heatmaps
- **Data Quality Panel**: Completeness, Uniqueness, Consistency, Validity, and Timeliness scores

### 4. Advanced Time-Series Forecasting
- **Dynamic Interval Alignment**: Auto-scales forecast horizons based on time resolution (daily → yearly)
- **Multi-Model Forecasting**: Linear + ensemble models with 95% confidence intervals

### 5. Report Exports
- **Board-Ready PDFs**: Cover page, executive summary, high-res plots, statistical tables, strategic recommendations
- **PowerPoint & CSV/Excel**: Formatted data sheets and slide outline statistics

### 6. Authentication & Security
- **Supabase Auth**: Signup, login, password recovery, session persistence
- **JWT Authorization**: Backend routes protected via Supabase HS256 JWT verification
- **Rate Limiting**: 180 requests/min per client
- **Mock Fallback Mode**: Demo mode activates automatically when Supabase env vars are absent

---

## 🛠️ Local Development

### Prerequisites

- Python 3.11+
- Node.js 18+

### 1. Clone & Configure

```bash
git clone https://github.com/Sanjayduduka45/Insight-IQ.git
cd Insight-IQ
cp .env.example .env   # fill in your API keys
```

Key variables in `.env`:

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Google Gemini API key |
| `SUPABASE_URL` | Supabase project API URL |
| `SUPABASE_ANON_KEY` | Supabase anonymous public key |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key (backend only) |

### 2. Start the Backend

```bash
cd apps/backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

- Backend: **http://localhost:8000**
- API Docs: **http://localhost:8000/docs**

### 3. Start the Frontend

```bash
# In a new terminal
cd apps/frontend
npm install
npm run dev
```

- Frontend: **http://localhost:5173**

---

## 🧪 Testing

```bash
# Run non-LLM smoke tests (fast, no API key required)
cd apps/backend
pytest -k "not test_chat" -v

# Full test suite (requires GEMINI_API_KEY)
pytest -v
```

---

## 📁 Project Structure

```
Insight-IQ/
├── apps/
│   ├── backend/                  # FastAPI application
│   │   ├── analytics/            # Trends, charts, feature importance
│   │   ├── anomaly/              # Isolation Forest, Z-score, IQR detectors
│   │   ├── api/                  # Route handlers (datasets, chat, settings, exports)
│   │   ├── core/                 # Settings, JWT verification, security
│   │   ├── export/               # Matplotlib plots & ReportLab PDF generators
│   │   ├── forecasting/          # Time-series forecasting algorithms
│   │   ├── intelligence/         # Domain classifiers & schema auto-detection
│   │   ├── main.py               # FastAPI app entrypoint
│   │   └── requirements.txt      # Python dependencies
│   └── frontend/                 # React SPA
│       ├── src/
│       │   ├── components/       # Reusable UI components
│       │   ├── lib/              # API clients & AuthProviders
│       │   ├── pages/            # Dashboard, Data Quality, Forecast, Chat
│       │   └── App.tsx           # Router & layout
│       ├── package.json          # Node dependencies
│       ├── vite.config.ts        # Vite configuration
│       ├── tsconfig.json         # TypeScript configuration
│       └── vercel.json           # Vercel SPA rewrite rules
├── docs/
│   ├── ARCHITECTURE.md           # System architecture reference
│   └── supabase_schema.sql       # Supabase table definitions
├── supabase/                     # Supabase project config & migrations
├── tests/                        # Pytest test suite
├── .github/workflows/ci.yml      # GitHub Actions CI (lint, test, build)
├── Procfile                      # Railway deployment entrypoint
├── app.py                        # FastAPI app wrapper (sys.path shim for Railway)
├── requirements.txt              # Root-level Python dependencies (Railway)
└── .env.example                  # Environment variable template
```

---

## 🚀 Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for full step-by-step instructions.

| Layer | Platform | Notes |
|---|---|---|
| **Frontend** | [Vercel](https://vercel.com) | Root directory: `apps/frontend`, auto-detects Vite |
| **Backend** | [Railway](https://railway.app) | `Procfile` → uvicorn, port from `$PORT` |
| **Database** | [Supabase](https://supabase.com) | PostgreSQL + Auth + Storage |

---

## 📝 License

Distributed under the MIT License.
