# InsightIQ

> Upload Any Dataset. Get Expert-Level Insights Instantly.

A **Universal AI Data Intelligence Platform** built on React + TypeScript + Vite + FastAPI + Supabase + Google Gemini.

## Quick Start

```bash
# Clone
git clone https://github.com/Sanjayduduka45/Insight-IQ.git
cd Insight-IQ
cp .env.example .env   # Fill in your API keys

# Backend  (http://localhost:8000)
cd apps/backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend  (http://localhost:5173) — new terminal
cd apps/frontend
npm install
npm run dev
```

## Architecture

| Layer | Technology |
|---|---|
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS, ShadCN UI |
| **Backend** | FastAPI (Python 3.11), uvicorn |
| **Database** | Supabase PostgreSQL |
| **Auth** | Supabase Auth (JWT) |
| **AI** | Google Gemini 2.0 Flash |
| **Analytics** | Pandas, Scikit-Learn, XGBoost, DuckDB |

## Project Layout

```
apps/
  backend/     FastAPI API server
  frontend/    React SPA (Vite)
docs/          Architecture & schema documentation
tests/         Pytest test suite
```

## License

MIT
