-- Run in your Supabase project's SQL Editor before using saved history.
-- Matches the fields written by backend/database/supabase_db.py.

create table if not exists public.analyses (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users (id) on delete cascade,
    filename text not null,
    ats_score numeric not null default 0,
    keyword_match numeric not null default 0,
    missing_keywords jsonb not null default '[]'::jsonb,
    created_at timestamptz not null default now(),
    analysis_result jsonb not null default '{}'::jsonb
);

create index if not exists analyses_user_created_at_idx
    on public.analyses (user_id, created_at desc);

alter table public.analyses enable row level security;

grant usage on schema public to authenticated, service_role;
grant select, insert, update, delete on public.analyses to authenticated, service_role;

drop policy if exists analyses_select_own on public.analyses;
create policy analyses_select_own on public.analyses
    for select to authenticated
    using ((select auth.uid()) = user_id);

drop policy if exists analyses_insert_own on public.analyses;
create policy analyses_insert_own on public.analyses
    for insert to authenticated
    with check ((select auth.uid()) = user_id);

drop policy if exists analyses_update_own on public.analyses;
create policy analyses_update_own on public.analyses
    for update to authenticated
    using ((select auth.uid()) = user_id)
    with check ((select auth.uid()) = user_id);

drop policy if exists analyses_delete_own on public.analyses;
create policy analyses_delete_own on public.analyses
    for delete to authenticated
    using ((select auth.uid()) = user_id);

-- The backend uses the service_role key and applies the verified user_id to
-- every history operation. Keep that key secret; it bypasses these policies.
