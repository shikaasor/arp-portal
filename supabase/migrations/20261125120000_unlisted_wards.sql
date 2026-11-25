-- Wards not on the GRID3 list (apply BEFORE deploying the API that reads this column).
--
-- Applicants pick their ward from the GRID3 list for their LGA. If theirs is missing they choose
-- "My ward isn't listed" and type it; the application is flagged so the LGA reviewer handles the
-- ward stage (no ward reviewer can be matched to a ward that isn't on the list).

alter table public.applications
  add column if not exists ward_unlisted boolean not null default false;

-- New columns inherit the table's revoked grants and RLS (anon/authenticated still see nothing).
