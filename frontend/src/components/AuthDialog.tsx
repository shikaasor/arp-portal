"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { getSupabase } from "@/lib/supabase";
import { useAuth } from "./AuthProvider";

export function AuthDialog() {
  const { dialogOpen, closeAuth, configured } = useAuth();
  const ref = useRef<HTMLDialogElement>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (dialogOpen && !dialog.open) dialog.showModal();
    if (!dialogOpen && dialog.open) dialog.close();
  }, [dialogOpen]);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const mode = ((e.nativeEvent as SubmitEvent).submitter as HTMLButtonElement | null)?.value;
    const supabase = getSupabase();
    if (!supabase) {
      setMessage("Accounts will be available once the portal is connected to Supabase.");
      return;
    }
    setBusy(true);
    setMessage("");
    try {
      if (mode === "signup") {
        const { data, error } = await supabase.auth.signUp({
          email,
          password,
          options: { emailRedirectTo: `${window.location.origin}/status` },
        });
        if (error) throw error;
        setMessage(
          data.session
            ? "Account created. You are signed in."
            : "Account created. Check your email and click the verification link, then sign in.",
        );
      } else {
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
        setPassword("");
      }
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Unable to sign in.");
    } finally {
      setBusy(false);
    }
  }

  async function onReset() {
    const supabase = getSupabase();
    if (!supabase) return setMessage("Connect the portal to Supabase first.");
    if (!email) return setMessage("Enter your email address above first.");
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/reset-password`,
    });
    setMessage(error ? error.message : "If an account exists for that email, a reset link is on its way.");
  }

  return (
    <dialog ref={ref} className="authDialog" onClose={closeAuth} aria-labelledby="auth-title">
      <form onSubmit={onSubmit}>
        <button type="button" className="close" onClick={closeAuth} aria-label="Close">
          ×
        </button>
        <h2 id="auth-title">Welcome to ARP</h2>
        <p className="muted">Your application, all in one place.</p>
        {!configured && <p className="notice small">Preview mode: sign-in is disabled until Supabase is connected.</p>}
        <label>
          Email
          <input type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>
        <label>
          Password
          <input
            type="password"
            autoComplete="current-password"
            minLength={8}
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        <div className="actions">
          <button className="primary" name="mode" value="signin" disabled={busy}>
            Sign in
          </button>
          <button name="mode" value="signup" disabled={busy}>
            Create account
          </button>
        </div>
        <button type="button" className="link" onClick={onReset}>
          Forgot your password?
        </button>
        <p role="status" className="formMessage">
          {message}
        </p>
      </form>
    </dialog>
  );
}
