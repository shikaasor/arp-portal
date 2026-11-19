"use client";

import { FormEvent, useState } from "react";
import { useAuth } from "@/components/AuthProvider";
import { getSupabase } from "@/lib/supabase";

export default function ResetPassword() {
  const { session } = useAuth();
  const [message, setMessage] = useState("");

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const password = new FormData(e.currentTarget).get("password") as string;
    const supabase = getSupabase();
    if (!supabase) return;
    const { error } = await supabase.auth.updateUser({ password });
    setMessage(error ? error.message : "Your password has been updated.");
  }

  return (
    <section>
      <div className="eyebrow">ACCOUNT</div>
      <h1>Choose a new password</h1>
      <div className="panel narrow">
        {session ? (
          <form onSubmit={onSubmit}>
            <label>
              New password
              <input type="password" name="password" minLength={8} autoComplete="new-password" required />
            </label>
            <button className="primary">Update password</button>
            <p role="status" className="formMessage">
              {message}
            </p>
          </form>
        ) : (
          <p>Open the reset link from your email to continue.</p>
        )}
      </div>
    </section>
  );
}
