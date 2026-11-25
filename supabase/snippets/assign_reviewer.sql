-- Assign reviewer roles. Run in the Supabase SQL editor (the user must have signed up first).
-- LGA names must be spelt as in backend/app/lgas.json (case doesn't matter). A misspelt LGA is
-- refused at sign-in to the review workspace rather than silently showing nothing.

-- National reviewer (sees everything, the only role that can open KYC documents)
update public.profiles set role = 'national', state = null, lga = null, ward = null
where email = 'national.reviewer@example.org';

-- State reviewer
update public.profiles set role = 'state', state = 'Kano', lga = null, ward = null
where email = 'kano.reviewer@example.org';

-- LGA reviewer
update public.profiles set role = 'lga', state = 'Kano', lga = 'Nasarawa', ward = null
where email = 'nasarawa.reviewer@example.org';

-- Ward reviewer
update public.profiles set role = 'ward', state = 'Kano', lga = 'Nasarawa', ward = 'Gama'
where email = 'gama.reviewer@example.org';

-- Revoke a reviewer
update public.profiles set role = 'applicant', state = null, lga = null, ward = null
where email = 'former.reviewer@example.org';
