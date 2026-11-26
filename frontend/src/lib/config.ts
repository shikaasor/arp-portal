// NEXT_PUBLIC_* values are inlined at build time, so they must be referenced literally.
export const config = {
  supabaseUrl: process.env.NEXT_PUBLIC_SUPABASE_URL ?? "",
  supabaseKey:
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ?? "",
  // Set by next.config.ts on Vercel or when API_ORIGIN is configured. API calls are same-origin `/api/*`.
  apiEnabled: process.env.NEXT_PUBLIC_API_ENABLED === "1",
  // The public address of the site, used for metadata and share links.
  siteUrl: process.env.NEXT_PUBLIC_SITE_URL || "https://arewarevivalproject.org",
  // The programme's official mailbox, shown on the site.
  contactEmail: "info@arewarevivalproject.org",
};

export const isConfigured = Boolean(config.apiEnabled && config.supabaseUrl && config.supabaseKey);
