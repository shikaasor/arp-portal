"use client";

import Link from "next/link";
import { useAuth } from "@/components/AuthProvider";
import { ACTION_LABELS, REVIEW_PATH, STAGE_LABELS } from "@/lib/options";

const fmt = (iso: string) =>
  new Date(iso).toLocaleString("en-NG", { dateStyle: "medium", timeStyle: "short" });

export default function StatusPage() {
  const { configured, ready, session, me, meError, openAuth } = useAuth();

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
    <section>
      <div className="eyebrow">STAY INFORMED</div>
      <h1>My application status</h1>
      <div className="panel">{content}</div>
    </section>
  );
}
