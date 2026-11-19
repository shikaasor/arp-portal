-- Assign reviewer roles. Run in the Supabase SQL editor (the user must have signed up first).

-- National reviewer (sees everything, the only role that can open KYC documents)
update public.profiles set role = 'national', state = null, lga = null, ward = null
where email = 'national.reviewer@example.org';

-- State reviewer
update public.profiles set role = 'state', state = 'Kano', lga = null, ward = null
where email = 'kano.reviewer@example.org';

-- LGA reviewer
update public.profiles set role = 'lga', state = 'Kano', lga = 'Nassarawa', ward = null
where email = 'nassarawa.reviewer@example.org';

-- Ward reviewer
update public.profiles set role = 'ward', state = 'Kano', lga = 'Nassarawa', ward = 'Gama'
where email = 'gama.reviewer@example.org';

-- Revoke a reviewer
update public.profiles set role = 'applicant', state = null, lga = null, ward = null
where email = 'former.reviewer@example.org';
