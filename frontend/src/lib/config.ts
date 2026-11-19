// NEXT_PUBLIC_* values are inlined at build time, so they must be referenced literally.
export const config = {
  apiBaseUrl: (process.env.NEXT_PUBLIC_API_BASE_URL ?? "").replace(/\/+$/, ""),
  supabaseUrl: process.env.NEXT_PUBLIC_SUPABASE_URL ?? "",
  supabaseKey:
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ?? "",
};

export const isConfigured = Boolean(config.apiBaseUrl && config.supabaseUrl && config.supabaseKey);
