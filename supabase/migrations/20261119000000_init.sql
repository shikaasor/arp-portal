-- Arewa Revival Project portal: initial schema.
-- Apply with `supabase db push` (CI does this on main) or paste into the Supabase SQL editor.
--
-- Security model
--   * The browser only talks to Supabase Auth (anon key). All data access goes through the
--     FastAPI backend using the service-role key, which bypasses RLS.
--   * RLS is enabled on every table with NO anon/authenticated policies, so the public anon key
--     cannot read or write application data even if someone calls PostgREST directly.
--   * Identity numbers and document paths live in a separate table (application_kyc) that only
--     national reviewers can reach through the API.

create extension if not exists pgcrypto;

-- ---------------------------------------------------------------------------------------------
-- Profiles & reviewer roles
-- ---------------------------------------------------------------------------------------------
create table if not exists public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  email text,
  role text not null default 'applicant'
    check (role in ('applicant', 'ward', 'lga', 'state', 'national')),
  state text,
  lga text,
  ward text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint profiles_geography_for_role check (
    role in ('applicant', 'national')
    or (role = 'state' and state is not null)
    or (role = 'lga' and state is not null and lga is not null)
    or (role = 'ward' and state is not null and lga is not null and ward is not null)
  )
);

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  insert into public.profiles (id, email) values (new.id, new.email)
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- Backfill profiles for users that existed before this migration.
insert into public.profiles (id, email)
select id, email from auth.users
on conflict (id) do nothing;

-- ---------------------------------------------------------------------------------------------
-- Applications
-- ---------------------------------------------------------------------------------------------
create table if not exists public.applications (
  id uuid primary key default gen_random_uuid(),
  reference text not null unique,
  user_id uuid not null unique references auth.users (id) on delete restrict,
  full_name text not null,
  email text not null,
  phone text not null,
  gender text not null,
  date_of_birth date not null,
  address text not null,
  state text not null,
  lga text not null,
  ward text not null,
  education text not null,
  occupation text not null,
  sector text not null,
  has_business boolean not null,
  business_idea text not null,
  motivation text not null,
  referral_source text not null,
  stage text not null default 'state_review'
    check (stage in ('state_review', 'lga_review', 'ward_review', 'approved', 'rejected',
                     'needs_information')),
  feedback text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists applications_created_at_idx on public.applications (created_at desc);
create index if not exists applications_geo_idx on public.applications (state, lga, ward);
create index if not exists applications_stage_idx on public.applications (stage);

create table if not exists public.application_kyc (
  application_id uuid primary key references public.applications (id) on delete cascade,
  identification_type text not null check (identification_type in ('NIN', 'International Passport')),
  identification_number text not null,
  identity_document_path text not null,
  passport_photograph_path text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.application_events (
  id bigint generated always as identity primary key,
  application_id uuid not null references public.applications (id) on delete cascade,
  stage text not null,
  action text not null,
  note text,
  actor_id uuid references auth.users (id) on delete set null,
  visible_to_applicant boolean not null default true,
  created_at timestamptz not null default now()
);

create index if not exists application_events_app_idx
  on public.application_events (application_id, created_at);

-- Keep updated_at honest.
create or replace function public.touch_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists applications_touch on public.applications;
create trigger applications_touch before update on public.applications
  for each row execute function public.touch_updated_at();

drop trigger if exists profiles_touch on public.profiles;
create trigger profiles_touch before update on public.profiles
  for each row execute function public.touch_updated_at();

-- ---------------------------------------------------------------------------------------------
-- Row level security: deny everything to anon/authenticated; the API uses the service role.
-- ---------------------------------------------------------------------------------------------
alter table public.profiles enable row level security;
alter table public.applications enable row level security;
alter table public.application_kyc enable row level security;
alter table public.application_events enable row level security;

revoke all on public.profiles, public.applications, public.application_kyc,
  public.application_events from anon, authenticated;

-- ---------------------------------------------------------------------------------------------
-- Private storage bucket for identity documents and passport photographs.
-- ---------------------------------------------------------------------------------------------
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('applicant-documents', 'applicant-documents', false, 5242880,
        array['application/pdf', 'image/jpeg', 'image/png'])
on conflict (id) do update set
  public = false,
  file_size_limit = excluded.file_size_limit,
  allowed_mime_types = excluded.allowed_mime_types;
-- No storage.objects policies are created: uploads and short-lived signed download URLs are
-- issued exclusively by the backend.
