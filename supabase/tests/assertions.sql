-- Behavioural checks run in CI after applying migrations.
do $$
declare
  uid uuid;
  app uuid;
begin
  -- Signing up creates an applicant profile.
  insert into auth.users (email) values ('ci@example.org') returning id into uid;
  perform 1 from public.profiles where id = uid and role = 'applicant';
  if not found then raise exception 'profile trigger did not create an applicant profile'; end if;

  -- Geographic reviewers must have their geography.
  begin
    update public.profiles set role = 'ward', state = 'Kano' where id = uid;
    raise exception 'ward reviewer without lga/ward was accepted';
  exception when check_violation then null;
  end;

  -- Applications: one per user, valid stages only.
  insert into public.applications (reference, user_id, full_name, email, phone, gender, date_of_birth,
    address, state, lga, ward, education, occupation, sector, has_business, business_idea,
    motivation, referral_source)
  values ('ARP-CI00000001', uid, 'CI User', 'ci@example.org', '+2348000000000', 'Female',
    '1999-01-01', 'Somewhere', 'Kano', 'Nassarawa', 'Gama', 'Others', 'Others', 'Others', false,
    'idea', 'motivation', 'Others')
  returning id into app;

  begin
    update public.applications set stage = 'bogus' where id = app;
    raise exception 'invalid stage was accepted';
  exception when check_violation then null;
  end;

  -- LGA/ward keys ignore case, spacing and punctuation.
  update public.applications set lga = ' NASARAWA ', ward = 'Gama-Ward' where id = app;
  perform 1 from public.applications
   where id = app and lga_key = 'nasarawa' and ward_key = 'gamaward';
  if not found then raise exception 'lga_key/ward_key not generated as expected'; end if;

  begin
    update public.applications set returns_to_stage = 'approved' where id = app;
    raise exception 'invalid returns_to_stage was accepted';
  exception when check_violation then null;
  end;

  -- One application per identification number.
  insert into public.application_kyc (application_id, identification_type, identification_number,
    identity_document_path, passport_photograph_path)
  values (app, 'NIN', '12345678901', 'a/b/identity_document.pdf', 'a/b/passport_photograph.jpg');
  insert into auth.users (email) values ('ci2@example.org') returning id into uid;
  insert into public.applications (reference, user_id, full_name, email, phone, gender, date_of_birth,
    address, state, lga, ward, education, occupation, sector, has_business, business_idea,
    motivation, referral_source)
  values ('ARP-CI00000002', uid, 'CI User 2', 'ci2@example.org', '+2348000000001', 'Male',
    '1999-01-01', 'Somewhere', 'Kano', 'Nasarawa', 'Gama', 'Others', 'Others', 'Others', false,
    'idea', 'motivation', 'Others')
  returning id into app;
  begin
    insert into public.application_kyc (application_id, identification_type, identification_number,
      identity_document_path, passport_photograph_path)
    values (app, 'NIN', '12345678901', 'c/d/identity_document.pdf', 'c/d/passport_photograph.jpg');
    raise exception 'duplicate identification number was accepted';
  exception when unique_violation then null;
  end;

  -- Storage bucket is private.
  perform 1 from storage.buckets where id = 'applicant-documents' and public = false;
  if not found then raise exception 'applicant-documents bucket missing or public'; end if;

  -- RLS is enabled everywhere.
  perform 1 from pg_class c join pg_namespace n on n.oid = c.relnamespace
   where n.nspname = 'public' and c.relkind = 'r' and not c.relrowsecurity;
  if found then raise exception 'a public table has RLS disabled'; end if;

  raise notice 'All schema assertions passed';
end $$;
