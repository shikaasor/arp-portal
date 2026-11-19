import { createClient, type SupabaseClient } from "@supabase/supabase-js";
import { config, isConfigured } from "./config";

let client: SupabaseClient | null = null;

/** Browser Supabase client (anon key, auth only). Returns null in preview mode. */
export function getSupabase(): SupabaseClient | null {
  if (!isConfigured || typeof window === "undefined") return null;
  client ??= createClient(config.supabaseUrl, config.supabaseKey, {
    auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true },
  });
  return client;
}
