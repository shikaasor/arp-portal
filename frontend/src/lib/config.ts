// NEXT_PUBLIC_* values are inlined at build time, so they must be referenced literally.
export const config = {
  supabaseUrl: process.env.NEXT_PUBLIC_SUPABASE_URL ?? "",
  supabaseKey:
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ?? "",
  // Set by next.config.ts when API_ORIGIN is configured; API calls are same-origin `/api/*`.
  apiEnabled: process.env.NEXT_PUBLIC_API_PROXY_ENABLED === "1",
};

export const isConfigured = Boolean(config.apiEnabled && config.supabaseUrl && config.supabaseKey);
