# InsightIQ — Production Deployment Guide

This guide covers deploying **InsightIQ** to production.

| Layer | Platform | Notes |
|---|---|---|
| **Frontend** | [Vercel](https://vercel.com) | React + Vite SPA |
| **Backend** | [Railway](https://railway.app) | FastAPI + uvicorn |
| **Database** | [Supabase](https://supabase.com) | PostgreSQL + Auth |
| **AI** | Google Gemini | `gemini-2.0-flash` |

---

## 1. Database Setup (Supabase)

1. Create a project at [supabase.com](https://supabase.com).
2. Go to **SQL Editor** and run the schema from `docs/supabase_schema.sql`.
3. Note your credentials from **Settings → API**:
   - `SUPABASE_URL` (Project URL)
   - `SUPABASE_ANON_KEY` (anon/public key)
   - `SUPABASE_SERVICE_ROLE_KEY` (service_role key — backend only, keep secret)
4. Note your database connection string from **Settings → Database**:
   - `DATABASE_URL` = `postgresql://postgres:<password>@db.<ref>.supabase.co:5432/postgres`

---

## 2. Backend Deployment (Railway)

1. **Connect GitHub**:
   - Sign in to [Railway Dashboard](https://railway.app).
   - Click **New Project → Deploy from GitHub repo**.
   - Select your `Insight-IQ` repository.

2. **Build & Start**:
   - Railway detects the `Procfile` at the repository root:
     ```
     web: uvicorn app:app --host 0.0.0.0 --port $PORT
     ```
   - `app.py` is a thin shim that exposes the FastAPI application from `apps/backend/main.py`.
   - Dependencies install from root `requirements.txt`.

3. **Environment Variables** (Railway → Variables tab):
   ```env
   ENVIRONMENT=production
   GEMINI_API_KEY=your-gemini-api-key
   GEMINI_MODEL=gemini-2.0-flash
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your-supabase-anon-key
   SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
   DATABASE_URL=postgresql://postgres:<password>@db.<ref>.supabase.co:5432/postgres
   ```

4. **Verify**:
   - Navigate to `https://your-backend.up.railway.app/api/health`
   - Expected:
     ```json
     { "status": "healthy" }
     ```
   - API docs: `https://your-backend.up.railway.app/docs`

---

## 3. Frontend Deployment (Vercel)

1. **Connect GitHub**:
   - Sign in to [Vercel Dashboard](https://vercel.com).
   - Click **Add New → Project**.
   - Import your `Insight-IQ` repository.

2. **Project Configuration**:

   | Setting | Value |
   |---|---|
   | **Framework Preset** | Vite (auto-detected) |
   | **Root Directory** | `apps/frontend` |
   | **Build Command** | `npm run build` |
   | **Output Directory** | `dist` |

3. **Environment Variables** (Vercel → Settings → Environment Variables):
   ```env
   VITE_SUPABASE_URL=https://your-project.supabase.co
   VITE_SUPABASE_ANON_KEY=your-supabase-anon-key
   VITE_API_URL=https://your-backend.up.railway.app
   ```

4. **Routing**:
   - `apps/frontend/vercel.json` rewrites all paths to `index.html` for React Router support — no extra configuration needed.

5. **Deploy**:
   - Click **Deploy**. Vercel builds and serves the frontend globally via CDN.

---

## 4. Local Development

```bash
# Clone
git clone https://github.com/Sanjayduduka45/Insight-IQ.git
cd Insight-IQ
cp .env.example .env   # Fill in your keys

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

---

## 5. Environment Variable Reference

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | ✅ Backend | Google Gemini API key |
| `GEMINI_MODEL` | ✅ Backend | Model name (e.g. `gemini-2.0-flash`) |
| `SUPABASE_URL` | ✅ Both | Supabase project URL |
| `SUPABASE_ANON_KEY` | ✅ Both | Supabase anonymous key |
| `SUPABASE_SERVICE_ROLE_KEY` | ✅ Backend | Service role key (never expose to frontend) |
| `DATABASE_URL` | ✅ Backend | PostgreSQL connection string |
| `ENVIRONMENT` | ✅ Backend | `development` or `production` |
| `VITE_API_URL` | ✅ Frontend | Backend API base URL |
| `VITE_SUPABASE_URL` | ✅ Frontend | Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | ✅ Frontend | Supabase anonymous key |
