# InsightIQ Production Deployment Guide

This guide provides the complete setup for deploying **InsightIQ** to production using **Vercel** (Frontend), **Railway** (Backend), and **Supabase** (Database & Auth).

---

## ── Supabase (Database & Authentication) ──────────────────────────────────

InsightIQ relies on Supabase for relational data storage, user authentication, and storage buckets.

### 1. Database Schema
Execute the SQL schema in `docs/supabase_schema.sql` inside the Supabase SQL Editor. This initializes:
- `datasets` table for tracking uploaded files.
- Row Level Security (RLS) policies linking datasets to `auth.users`.

### 2. Storage Buckets
Create a private storage bucket named `datasets` in the Supabase Dashboard:
1. Go to **Storage** -> **New Bucket**.
2. Name it `datasets`.
3. Set the bucket to **Private** (RLS enabled).
4. Add policies to allow authenticated users to perform all operations (`read`, `write`, `delete`) only on their own files under `(auth.uid() = owner_id)`.

### 3. JWT Secret Configuration
To verify user JWT tokens in the FastAPI backend, locate your Supabase **JWT Secret**:
1. Go to **Project Settings** -> **API**.
2. Copy the **JWT Secret** (HS256). This will be used as the `SUPABASE_JWT_SECRET` environment variable in the backend.

---

## ── Railway (FastAPI Backend) ─────────────────────────────────────────────

The backend is deployed to Railway and runs via the root-level entrypoint `app.py`.

### 1. Deployment Steps
1. Log in to the [Railway Console](https://railway.app).
2. Click **New Project** -> **Deploy from GitHub repo**.
3. Select the `Insight-IQ` repository.
4. Railway will automatically detect the `Procfile` in the root and run the command:
   ```bash
   web: uvicorn app:app --host 0.0.0.0 --port $PORT
   ```

### 2. Environment Variables
Configure the following Environment Variables in the Railway **Variables** tab:

| Variable | Description |
|---|---|
| `ENVIRONMENT` | Set to `production` |
| `GEMINI_API_KEY` | Your Google Gemini API Key |
| `SUPABASE_URL` | Your Supabase project URL (e.g. `https://xxx.supabase.co`) |
| `SUPABASE_ANON_KEY` | Your Supabase anonymous public key |
| `SUPABASE_SERVICE_ROLE_KEY` | Your Supabase service role key |
| `SUPABASE_JWT_SECRET` | Your Supabase JWT Secret (from API settings) |

---

## ── Vercel (React Frontend) ──────────────────────────────────────────────

The React frontend is compiled using Vite and deployed to Vercel.

### 1. Deployment Steps
1. Log in to the [Vercel Dashboard](https://vercel.com).
2. Click **Add New** -> **Project**.
3. Import the `Insight-IQ` repository.
4. In the Project configuration:
   - **Framework Preset**: `Vite` (automatically detected)
   - **Root Directory**: Change this to `frontend` (Critical!)
   - **Build Command**: `tsc -b && vite build`
   - **Output Directory**: `dist`
5. Click **Deploy**.

### 2. Environment Variables
Add the following Environment Variables in Vercel's **Environment Variables** settings:

| Variable | Value |
|---|---|
| `VITE_SUPABASE_URL` | Your Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | Your Supabase anonymous public key |
| `VITE_API_URL` | Your production Railway backend URL (e.g. `https://insightiq-backend.up.railway.app`) |

---

## ── Verification Checklist ───────────────────────────────────────────────

Once both services are deployed, perform these checks:

1. **Health Check**: Visit `https://your-backend.up.railway.app/health` and verify it returns `{"status":"healthy"}`.
2. **CORS Policies**: Verify the frontend can talk to the backend without CORS errors.
3. **Storage Access**: Verify uploaded datasets are visible in the Supabase Storage console under the user's bucket path.
