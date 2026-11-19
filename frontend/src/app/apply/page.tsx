"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { useAuth } from "@/components/AuthProvider";
import { api } from "@/lib/api";
import {
  EDUCATION_LEVELS,
  GENDERS,
  ID_TYPES,
  MIN_BUSINESS_WORDS,
  OCCUPATIONS,
  REFERRAL_SOURCES,
  SECTORS,
  STAGE_LABELS,
  STATES,
} from "@/lib/options";
import { normaliseIdNumber, validateDetails, validateFile, wordCount } from "@/lib/validation";

function Select({ label, name, options }: { label: string; name: string; options: readonly string[] }) {
  return (
    <label>
      {label}
      <select name={name} required defaultValue="">
        <option value="" disabled>
          Select…
        </option>
        {options.map((o) => (
          <option key={o}>{o}</option>
        ))}
      </select>
    </label>
  );
}

function Field({ label, name, type = "text", ...rest }: { label: string; name: string; type?: string } & React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <label>
      {label}
      <input name={name} type={type} maxLength={200} required {...rest} />
    </label>
  );
}

export default function ApplyPage() {
  const router = useRouter();
  const { configured, session, me, openAuth, refresh } = useAuth();
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [words, setWords] = useState(0);

  if (me?.application) {
    return (
      <section>
        <div className="eyebrow">YOUR NEXT CHAPTER</div>
        <h1>Application received</h1>
        <div className="panel">
          <p>
            You have already applied. Reference <b>{me.application.reference}</b> ·{" "}
            <span className="pill">{STAGE_LABELS[me.application.stage] ?? me.application.stage}</span>
          </p>
          <Link className="button primary" href="/status">
            Track your application →
          </Link>
        </div>
      </section>
    );
  }

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const formEl = e.currentTarget;
    if (!configured) return setMessage("Applications open once the portal is connected to its secure backend.");
    if (!session) {
      setMessage("Sign in or create an account to submit your application.");
      return openAuth();
    }
    if (me && !me.email_verified) return setMessage("Verify your email address (check your inbox), then sign in again.");

    const form = new FormData(formEl);
    const details: Record<string, string> = {};
    for (const [k, v] of form.entries()) if (typeof v === "string") details[k] = v.trim();

    const problem =
      validateDetails(details) ??
      (await validateFile(form.get("identity_document") as File, "Identity document", ["application/pdf", "image/jpeg", "image/png"])) ??
      (await validateFile(form.get("passport_photograph") as File, "Passport photograph", ["image/jpeg", "image/png"]));
    if (problem) return setMessage(problem);

    const payload = {
      ...details,
      has_business: details.has_business === "Yes",
      identification_number: normaliseIdNumber(details.identification_number),
    };
    delete (payload as Record<string, unknown>).consent;

    const body = new FormData();
    body.set("details", JSON.stringify(payload));
    body.set("identity_document", form.get("identity_document") as File);
    body.set("passport_photograph", form.get("passport_photograph") as File);

    setBusy(true);
    setMessage("Uploading your documents and submitting…");
    try {
      const res = await api.submit(body);
      setMessage(`Application submitted. Reference: ${res.reference}`);
      formEl.reset();
      await refresh();
      router.push("/status");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Unable to submit your application.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section>
      <div className="eyebrow">YOUR NEXT CHAPTER</div>
      <h1>Empowerment application</h1>
      <p className="muted">Complete all sections. Identity documents are restricted to national reviewers.</p>
      {configured && !session && (
        <p className="notice">
          You’ll need an account to submit.{" "}
          <button type="button" className="link" onClick={openAuth}>
            Sign in or create one
          </button>{" "}
          before you start.
        </p>
      )}
      <form className="applicationForm" onSubmit={onSubmit} noValidate={false}>
        <h2>Personal information</h2>
        <div className="grid">
          <Field label="Full name (as on ID)" name="full_name" autoComplete="name" minLength={3} />
          <Select label="Gender" name="gender" options={GENDERS} />
          <Field label="Date of birth" name="date_of_birth" type="date" autoComplete="bday" />
          <Field label="Phone / WhatsApp" name="phone" type="tel" autoComplete="tel" placeholder="+234…" />
          <Field label="Residential address" name="address" autoComplete="street-address" />
        </div>

        <h2>Your location</h2>
        <div className="grid">
          <Select label="State of residence" name="state" options={STATES} />
          <Field label="Local Government Area" name="lga" />
          <Field label="Ward" name="ward" />
        </div>

        <h2>Education &amp; enterprise</h2>
        <div className="grid">
          <Select label="Highest qualification" name="education" options={EDUCATION_LEVELS} />
          <Select label="Current occupation" name="occupation" options={OCCUPATIONS} />
          <Select label="Sector of interest" name="sector" options={SECTORS} />
          <Select label="Existing business?" name="has_business" options={["Yes", "No"]} />
          <label className="full">
            Business idea / existing business (at least {MIN_BUSINESS_WORDS} words)
            <textarea name="business_idea" required maxLength={5000} onChange={(e) => setWords(wordCount(e.target.value))} />
            <small className={words >= MIN_BUSINESS_WORDS ? "ok" : "muted"}>{words} words</small>
          </label>
          <label className="full">
            Why do you want to participate?
            <textarea name="motivation" required minLength={20} maxLength={5000} />
          </label>
          <Select label="How did you hear about us?" name="referral_source" options={REFERRAL_SOURCES} />
        </div>

        <h2>Identity verification</h2>
        <div className="grid">
          <label>
            Identification type
            <select name="identification_type" required defaultValue="NIN">
              {ID_TYPES.map((t) => (
                <option key={t}>{t}</option>
              ))}
            </select>
          </label>
          <Field label="NIN / Passport number" name="identification_number" autoComplete="off" maxLength={20} />
          <label>
            Identity document · PDF, JPG or PNG, max 5 MB
            <input type="file" name="identity_document" accept="image/jpeg,image/png,application/pdf" required />
          </label>
          <label>
            Passport photograph · JPG or PNG, max 5 MB
            <input type="file" name="passport_photograph" accept="image/jpeg,image/png" required />
          </label>
        </div>

        <label className="check">
          <input type="checkbox" name="consent" required />I confirm my information is accurate, consent to
          programme-related processing and contact, and understand selection is not guaranteed.
        </label>
        <button className="primary" disabled={busy}>
          {busy ? "Submitting…" : "Submit application ↗"}
        </button>
        <p role="status" className="formMessage">
          {message}
        </p>
      </form>
    </section>
  );
}
