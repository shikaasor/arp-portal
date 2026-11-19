"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/components/AuthProvider";
import { api, type AdminApplication, type Kyc } from "@/lib/api";
import { ROLE_STAGE, STAGE_LABELS, STATES } from "@/lib/options";

const ACTIVE = ["state_review", "lga_review", "ward_review"];

function ReviewControls({ app, onDone }: { app: AdminApplication; onDone: (a: AdminApplication) => void }) {
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function act(action: "approve" | "reject" | "request_information") {
    if (action !== "approve" && !note.trim()) return setError("Add a note for the applicant first.");
    setBusy(true);
    setError("");
    try {
      onDone(await api.review(app.id, action, note.trim()));
      setNote("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Review failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="reviewControls">
      <label>
        Reviewer note (shared with the applicant; required to reject or request information)
        <textarea value={note} onChange={(e) => setNote(e.target.value)} maxLength={2000} rows={2} />
      </label>
      <div className="actions">
        <button className="primary" disabled={busy} onClick={() => act("approve")}>
          Approve stage
        </button>
        <button disabled={busy} onClick={() => act("request_information")}>
          Request information
        </button>
        <button className="danger" disabled={busy} onClick={() => act("reject")}>
          Reject
        </button>
      </div>
      {error && <p className="error">{error}</p>}
    </div>
  );
}

function KycPanel({ id }: { id: string }) {
  const [kyc, setKyc] = useState<Kyc | null>(null);
  const [error, setError] = useState("");
  async function load() {
    setError("");
    try {
      setKyc(await api.kyc(id));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to load KYC data.");
    }
  }
  if (!kyc)
    return (
      <>
        <button onClick={load}>View KYC documents</button>
        {error && <p className="error">{error}</p>}
      </>
    );
  return (
    <div className="kyc">
      <p>
        <b>{kyc.identification_type}:</b> {kyc.identification_number}
      </p>
      <p>
        <a href={kyc.identity_document_url} target="_blank" rel="noopener noreferrer">
          Open identity document ↗
        </a>{" "}
        ·{" "}
        <a href={kyc.passport_photograph_url} target="_blank" rel="noopener noreferrer">
          Open passport photograph ↗
        </a>
      </p>
      <p className="fine">Links expire in {Math.round(kyc.expires_in / 60)} minutes. This access has been logged.</p>
    </div>
  );
}

export default function AdminPage() {
  const { configured, session, me, openAuth } = useAuth();
  const [search, setSearch] = useState("");
  const [state, setState] = useState("");
  const [stage, setStage] = useState("");
  const [rows, setRows] = useState<AdminApplication[]>([]);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const role = me?.profile.role;
  const isReviewer = role && role !== "applicant";

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await api.listApplications({ search, state, stage, limit: "100" });
      setRows(res.items);
      setTotal(res.total);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to load applications.");
    } finally {
      setLoading(false);
    }
  }, [search, state, stage]);

  useEffect(() => {
    if (!isReviewer) return;
    const t = setTimeout(load, 300);
    return () => clearTimeout(t);
  }, [isReviewer, load]);

  const canReview = (a: AdminApplication) =>
    ACTIVE.includes(a.stage) && (role === "national" || ROLE_STAGE[role ?? ""] === a.stage);

  let body: React.ReactNode;
  if (!configured) body = <div className="panel">The review workspace becomes available once the portal is connected.</div>;
  else if (!session)
    body = (
      <div className="panel">
        <button className="link" onClick={openAuth}>
          Sign in
        </button>{" "}
        with an assigned reviewer account to access this workspace.
      </div>
    );
  else if (!me) body = <div className="panel">Loading…</div>;
  else if (!isReviewer) body = <div className="panel">Your account has no reviewer assignment.</div>;
  else
    body = (
      <>
        <p className="muted">
          Signed in as <b>{role}</b> reviewer
          {me.profile.state && ` · ${[me.profile.state, me.profile.lga, me.profile.ward].filter(Boolean).join(" / ")}`}
        </p>
        <div className="filters">
          <input placeholder="Search name or reference" aria-label="Search applications" value={search} onChange={(e) => setSearch(e.target.value)} />
          {role === "national" && (
            <select aria-label="Filter state" value={state} onChange={(e) => setState(e.target.value)}>
              <option value="">All states</option>
              {STATES.map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          )}
          <select aria-label="Filter stage" value={stage} onChange={(e) => setStage(e.target.value)}>
            <option value="">All stages</option>
            {Object.entries(STAGE_LABELS).map(([k, v]) => (
              <option key={k} value={k}>
                {v}
              </option>
            ))}
          </select>
          <button onClick={load} disabled={loading}>
            {loading ? "Loading…" : "Refresh"}
          </button>
        </div>
        <p className="muted">
          {rows.length} shown · {total} matching applications
        </p>
        {error && <p className="error">{error}</p>}
        <div className="panel">
          {rows.length === 0 && !loading && <p>No matching applications.</p>}
          {rows.map((a) => (
            <div className="record" key={a.id}>
              <div className="recordHead">
                <b>{a.full_name}</b> <span className={`pill stage-${a.stage}`}>{STAGE_LABELS[a.stage] ?? a.stage}</span>
              </div>
              <p className="muted">
                {a.reference} · {a.state} / {a.lga} / {a.ward} · {new Date(a.created_at).toLocaleDateString("en-NG")}
              </p>
              <details>
                <summary>Application details</summary>
                <dl>
                  <dt>Contact</dt>
                  <dd>
                    {a.phone} · {a.email}
                  </dd>
                  <dt>Profile</dt>
                  <dd>
                    {a.gender} · born {a.date_of_birth} · {a.education} · {a.occupation}
                  </dd>
                  <dt>Sector</dt>
                  <dd>
                    {a.sector} · {a.has_business ? "Has an existing business" : "New business idea"}
                  </dd>
                  <dt>Business idea</dt>
                  <dd>{a.business_idea}</dd>
                  <dt>Motivation</dt>
                  <dd>{a.motivation}</dd>
                  <dt>Heard via</dt>
                  <dd>{a.referral_source}</dd>
                  {a.feedback && (
                    <>
                      <dt>Latest note</dt>
                      <dd>{a.feedback}</dd>
                    </>
                  )}
                </dl>
              </details>
              {role === "national" && <KycPanel id={a.id} />}
              {canReview(a) && <ReviewControls app={a} onDone={(u) => setRows((rs) => rs.map((r) => (r.id === u.id ? u : r)))} />}
            </div>
          ))}
        </div>
      </>
    );

  return (
    <section>
      <div className="eyebrow">REVIEW WORKSPACE</div>
      <h1>Application dashboard</h1>
      <p className="muted">Reviewers see only their assigned geography. Only national staff can access KYC documents.</p>
      {body}
    </section>
  );
}
