-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- ── 1. DATASETS ──────────────────────────────────────────────────────────
create table public.datasets (
    id text not null primary key,
    user_id uuid references auth.users(id) on delete cascade,
    name text not null,
    row_count integer not null,
    column_count integer not null,
    domain text not null,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable Row Level Security
alter table public.datasets enable row level security;

-- RLS Policies
create policy "Users can view their own datasets" on public.datasets
    for select using (auth.uid() = user_id);

create policy "Users can insert their own datasets" on public.datasets
    for insert with check (auth.uid() = user_id);

create policy "Users can delete their own datasets" on public.datasets
    for delete using (auth.uid() = user_id);


-- ── 2. CHAT LOGS ──────────────────────────────────────────────────────────
create table public.chat_logs (
    id uuid default gen_random_uuid() primary key,
    user_id uuid references auth.users(id) on delete cascade,
    dataset_id text not null,
    message text not null,
    response text not null,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable Row Level Security
alter table public.chat_logs enable row level security;

-- RLS Policies
create policy "Users can view their own chat logs" on public.chat_logs
    for select using (auth.uid() = user_id);

create policy "Users can insert their own chat logs" on public.chat_logs
    for insert with check (auth.uid() = user_id);


-- ── 3. REPORTS ───────────────────────────────────────────────────────────
create table public.reports (
    id uuid default gen_random_uuid() primary key,
    user_id uuid references auth.users(id) on delete cascade,
    dataset_id text not null,
    name text not null,
    format text not null,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable Row Level Security
alter table public.reports enable row level security;

-- RLS Policies
create policy "Users can view their own reports" on public.reports
    for select using (auth.uid() = user_id);

create policy "Users can insert their own reports" on public.reports
    for insert with check (auth.uid() = user_id);

create policy "Users can delete their own reports" on public.reports
    for delete using (auth.uid() = user_id);
