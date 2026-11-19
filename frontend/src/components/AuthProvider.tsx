"use client";

import type { Session } from "@supabase/supabase-js";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, type Me } from "@/lib/api";
import { isConfigured } from "@/lib/config";
import { getSupabase } from "@/lib/supabase";

type AuthState = {
  configured: boolean;
  ready: boolean;
  session: Session | null;
  me: Me | null;
  meError: string | null;
  refresh: () => Promise<void>;
  signOut: () => Promise<void>;
  dialogOpen: boolean;
  openAuth: () => void;
  closeAuth: () => void;
};

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [ready, setReady] = useState(!isConfigured);
  const [me, setMe] = useState<Me | null>(null);
  const [meError, setMeError] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  const refresh = useCallback(async () => {
    try {
      setMe(await api.me());
      setMeError(null);
    } catch (e) {
      setMe(null);
      setMeError(e instanceof Error ? e.message : "Unable to load your account.");
    }
  }, []);

  useEffect(() => {
    const supabase = getSupabase();
    if (!supabase) return;
    let lastUserId: string | undefined;
    const apply = (s: Session | null) => {
      setSession(s);
      setReady(true);
      const uid = s?.user.id;
      if (uid === lastUserId) return; // token refreshes don't need a reload
      lastUserId = uid;
      if (uid) {
        setDialogOpen(false);
        void refresh();
      } else {
        setMe(null);
      }
    };
    supabase.auth.getSession().then(({ data }) => apply(data.session));
    const { data } = supabase.auth.onAuthStateChange((_event, s) => apply(s));
    return () => data.subscription.unsubscribe();
  }, [refresh]);

  const signOut = useCallback(async () => {
    await getSupabase()?.auth.signOut();
    setMe(null);
  }, []);

  const value = useMemo<AuthState>(
    () => ({
      configured: isConfigured,
      ready,
      session,
      me,
      meError,
      refresh,
      signOut,
      dialogOpen,
      openAuth: () => setDialogOpen(true),
      closeAuth: () => setDialogOpen(false),
    }),
    [ready, session, me, meError, refresh, signOut, dialogOpen],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
