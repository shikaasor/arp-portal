-- Review workflow fixes (apply BEFORE deploying the API that reads these columns).
--
-- 1. "Request information" no longer strands an application: we remember which stage asked
--    (returns_to_stage) and keep the applicant's answer (applicant_response).
-- 2. LGA/ward reviewer matching ignores case, spacing and punctuation: generated *_key columns
--    hold lowercase letters and digits only (same rule as backend/app/geo.py:geo_key).
-- 3. One application per identification number (NIN or passport).

alter table public.applications
  add column if not exists returns_to_stage text
    check (returns_to_stage in ('state_review', 'lga_review', 'ward_review')),
  add column if not exists applicant_response text,
  add column if not exists lga_key text
    generated always as (regexp_replace(lower(lga), '[^a-z0-9]+', '', 'g')) stored,
  add column if not exists ward_key text
    generated always as (regexp_replace(lower(ward), '[^a-z0-9]+', '', 'g')) stored;

create index if not exists applications_geo_key_idx
  on public.applications (state, lga_key, ward_key);

-- Fails if duplicates already exist: find them first with
--   select identification_type, identification_number, count(*) from public.application_kyc
--   group by 1, 2 having count(*) > 1;
create unique index if not exists application_kyc_identification_unique
  on public.application_kyc (identification_type, identification_number);

-- New columns inherit the table's revoked grants and RLS (anon/authenticated still see nothing).
