"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useAuth } from "@/components/AuthProvider";
import { api, type DocumentKey } from "@/lib/api";
import { ACTION_LABELS, REVIEW_PATH, STAGE_LABELS } from "@/lib/options";
import { getSupabase } from "@/lib/supabase";
import { inspectFile } from "@/lib/validation";
import { PageBanner } from "@/components/PageBanner";

const fmt = (iso: string) =>
  new Date(iso).toLocaleString("en-NG", { dateStyle: "medium", timeStyle: "short" });

const REPLACEABLE: { key: DocumentKey; label: string; allowed: string[]; accept: string }[] = [
  {
    key: "identity_document",
    label: "New identity document",
    allowed: ["application/pdf", "image/jpeg", "image/png"],
    accept: "image/jpeg,image/png,application/pdf",
  },
  { key: "passport_photograph", label: "New passport photograph", allowed: ["image/jpeg", "image/png"], accept: "image/jpeg,image/png" },
];

/** Lets the applicant answer a reviewer's request for information, optionally with new documents. */
function RespondForm({ onDone }: { onDone: () => Promise<void> }) {
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const note = String(form.get("note") ?? "").trim();
    if (note.length < 5) return setMessage("Write a short reply to the reviewer.");

    const files: Partial<Record<DocumentKey, { file: File; type: string }>> = {};
    for (const doc of REPLACEABLE) {
      const file = form.get(doc.key) as File | null;
      if (!file || file.size === 0) continue; // optional
      const check = await inspectFile(file, doc.label, doc.allowed);
      if (!check.ok) return setMessage(check.error);
      files[doc.key] = { file, type: check.type };
    }

    setBusy(true);
    try {
      const paths: Partial<Record<`${DocumentKey}_path`, string>> = {};
      const keys = Object.keys(files) as DocumentKey[];
      if (keys.length) {
        setMessage("Preparing secure upload…");
        const tickets = await api.startResponseUpload(
          Object.fromEntries(keys.map((k) => [k, { content_type: files[k]!.type, size: files[k]!.file.size }])),
        );
        const storage = getSupabase()!.storage.from(tickets.bucket);
        for (const key of keys) {
          const ticket = tickets.uploads[key]!;
          setMessage("Uploading your document…");
          const { error } = await storage.uploadToSignedUrl(ticket.path, ticket.token, files[key]!.file, {
            contentType: files[key]!.type,
          });
          if (error) throw new Error(`Upload failed: ${error.message}`);
          paths[`${key}_path`] = ticket.path;
        }
      }
      setMessage("Sending your response…");
      await api.respond({ note, ...paths });
      setMessage("");
      await onDone();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Unable to send your response.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="respondForm" onSubmit={onSubmit}>
      <h3>Reply to the reviewer</h3>
      <label>
        Your response
        <textarea name="note" required minLength={5} maxLength={2000} rows={4} />
      </label>
      <p className="muted">If the reviewer asked for a new document, attach it here. Otherwise leave these empty.</p>
      {REPLACEABLE.map((doc) => (
        <label key={doc.key}>
          {doc.label} (optional) · max 5 MB
          <input type="file" name={doc.key} accept={doc.accept} />
        </label>
      ))}
      <button className="primary" disabled={busy}>
        {busy ? "Sending…" : "Send response"}
      </button>
      <p role="status" className="formMessage">
        {message}
      </p>
    </form>
  );
}

export default function StatusPage() {
  const { configured, ready, session, me, meError, openAuth, refresh } = useAuth();

  let content: React.ReactNode;
  if (!configured) content = <p>Application tracking becomes available once the portal is connected.</p>;
  else if (!ready) content = <p>Loading…</p>;
  else if (!session)
    content = (
      <p>
        <button className="link" onClick={openAuth}>
          Sign in
        </button>{" "}
        to view your application and review history.
      </p>
    );
  else if (meError) content = <p className="error">{meError}</p>;
  else if (!me) content = <p>Loading your application…</p>;
  else if (!me.application)
    content = (
      <>
        {!me.email_verified && <p className="notice">Please verify your email address before applying.</p>}
        <p>No submitted application yet.</p>
        <Link className="button primary" href="/apply">
          Start your application ↗
        </Link>
      </>
    );
  else {
    const a = me.application;
    const idx = REVIEW_PATH.findIndex((s) => s.stage === a.stage);
    const halted = idx === -1;
    content = (
      <>
        <h2>{a.full_name}</h2>
        <p className="muted">
          Reference <b>{a.reference}</b> · {a.state} / {a.lga} / {a.ward} · Submitted {fmt(a.created_at)}
        </p>
        <span className={`pill stage-${a.stage}`}>{STAGE_LABELS[a.stage] ?? a.stage}</span>
        <ol className="tracker" aria-label="Review progress">
          {REVIEW_PATH.map((s, i) => (
            <li key={s.stage} className={!halted && i < idx ? "done" : !halted && i === idx ? "current" : undefined}>
              {s.label}
            </li>
          ))}
        </ol>
        <p>{a.feedback || (halted ? "" : "Your application is awaiting review.")}</p>
        {a.stage === "needs_information" && <RespondForm onDone={refresh} />}
        <h3>History</h3>
        <ul className="history">
          {a.history.map((h, i) => (
            <li key={i}>
              <b>{ACTION_LABELS[h.action] ?? h.action}</b> · {STAGE_LABELS[h.stage] ?? h.stage} · {fmt(h.created_at)}
              {h.note && <div className="muted">{h.note}</div>}
            </li>
          ))}
        </ul>
      </>
    );
  }

  return (
    <>
    <PageBanner eyebrow="Stay informed" title={<>My application <em>status</em></>} />
    <section className="section narrowSection">
      <div className="panel">{content}</div>
    </section>
    </>
  );
}
