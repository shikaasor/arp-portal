"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { useAuth } from "@/components/AuthProvider";
import { api, type DocumentKey } from "@/lib/api";
import {
  EDUCATION_LEVELS,
  GENDERS,
  ID_TYPES,
  LGAS,
  MIN_BUSINESS_WORDS,
  OCCUPATIONS,
  REFERRAL_SOURCES,
  SECTORS,
  STAGE_LABELS,
  STATES,
} from "@/lib/options";
import { getSupabase } from "@/lib/supabase";
import { inspectFile, normaliseIdNumber, validateDetails, wordCount } from "@/lib/validation";
import { PageBanner } from "@/components/PageBanner";

const DOCUMENTS: { key: DocumentKey; label: string; allowed: string[] }[] = [
  { key: "identity_document", label: "Identity document", allowed: ["application/pdf", "image/jpeg", "image/png"] },
  { key: "passport_photograph", label: "Passport photograph", allowed: ["image/jpeg", "image/png"] },
];

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
  const [state, setState] = useState("");

  if (me?.application) {
    return (
      <>
        <PageBanner eyebrow="Your next chapter" title="Application received" />
        <section className="section narrowSection">
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
      </>
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

    const problem = validateDetails(details);
    if (problem) return setMessage(problem);

    const files = {} as Record<DocumentKey, { file: File; type: string }>;
    for (const doc of DOCUMENTS) {
      const file = form.get(doc.key) as File | null;
      const check = await inspectFile(file, doc.label, doc.allowed);
      if (!check.ok) return setMessage(check.error);
      files[doc.key] = { file: file as File, type: check.type };
    }

    delete details.consent;
    const payload = {
      ...details,
      has_business: details.has_business === "Yes",
      identification_number: normaliseIdNumber(details.identification_number),
    };

    setBusy(true);
    try {
      // 1. Ask the API for one-time upload URLs (it checks eligibility and file metadata).
      setMessage("Preparing secure upload…");
      const tickets = await api.startUpload({
        identity_document: { content_type: files.identity_document.type, size: files.identity_document.file.size },
        passport_photograph: { content_type: files.passport_photograph.type, size: files.passport_photograph.file.size },
      });

      // 2. Upload straight to the private storage bucket (files never pass through the API).
      const storage = getSupabase()!.storage.from(tickets.bucket);
      for (const doc of DOCUMENTS) {
        setMessage(`Uploading ${doc.label.toLowerCase()}…`);
        const ticket = tickets.uploads[doc.key];
        const { error } = await storage.uploadToSignedUrl(ticket.path, ticket.token, files[doc.key].file, {
          contentType: files[doc.key].type,
        });
        if (error) throw new Error(`Upload failed: ${error.message}`);
      }

      // 3. Submit the application; the API verifies the uploaded files before saving.
      setMessage("Submitting your application…");
      const res = await api.submit({
        reference: tickets.reference,
        details: payload,
        identity_document_path: tickets.uploads.identity_document.path,
        passport_photograph_path: tickets.uploads.passport_photograph.path,
      });
      setMessage(`Application submitted. Reference: ${res.reference}`);
      formEl.reset();
      setState("");
      await refresh();
      router.push("/status");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Unable to submit your application.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
    <PageBanner eyebrow="Your next chapter" title={<>Empowerment <em>application</em></>}>
      Complete all sections. Identity documents are seen only by national reviewers.
    </PageBanner>
    <section className="section narrowSection">
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
          <label>
            State of residence
            <select name="state" required value={state} onChange={(e) => setState(e.target.value)}>
              <option value="" disabled>
                Select…
              </option>
              {STATES.map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </label>
          <label>
            Local Government Area
            {/* Reviewers are matched by LGA, so it comes from the official list for the state. */}
            <select name="lga" required defaultValue="" key={state} disabled={!state}>
              <option value="" disabled>
                {state ? "Select…" : "Choose your state first"}
              </option>
              {(LGAS[state] ?? []).map((l) => (
                <option key={l}>{l}</option>
              ))}
            </select>
          </label>
          <Field label="Ward" name="ward" minLength={2} maxLength={100} />
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
    </>
  );
}
