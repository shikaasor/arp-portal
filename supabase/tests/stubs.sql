-- Minimal stand-ins for objects Supabase provides, so migrations can be validated on plain Postgres.
create role anon nologin;
create role authenticated nologin;
create role service_role nologin;
create schema auth;
create table auth.users (id uuid primary key default gen_random_uuid(), email text);
create schema storage;
create table storage.buckets (
  id text primary key, name text, public boolean, file_size_limit bigint, allowed_mime_types text[]
);
