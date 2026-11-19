## Summary

<!-- What does this change and why? -->

## Checklist

- [ ] CI is green (frontend, backend, migrations)
- [ ] New/changed form fields are mirrored in `frontend/src/lib/options.ts` **and** `backend/app/constants.py`
- [ ] Schema changes are a **new** file in `supabase/migrations/` (never edit an applied migration)
- [ ] No secrets, service-role keys, NIN/passport numbers or real applicant data committed
- [ ] Checked the Netlify/Vercel deploy preview
