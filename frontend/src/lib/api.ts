import { getSupabase } from "./supabase";

export type ReviewEvent = { stage: string; action: string; note?: string | null; created_at: string };

export type MyApplication = {
  id: string;
  reference: string;
  full_name: string;
  state: string;
  lga: string;
  ward: string;
  ward_unlisted?: boolean;
  stage: string;
  feedback?: string | null;
  applicant_response?: string | null;
  created_at: string;
  history: ReviewEvent[];
};

export type Profile = {
  id: string;
  email?: string | null;
  role: "applicant" | "ward" | "lga" | "state" | "national";
  state?: string | null;
  lga?: string | null;
  ward?: string | null;
};

export type Me = { profile: Profile; email_verified: boolean; application: MyApplication | null };

export type AdminApplication = {
  id: string;
  reference: string;
  full_name: string;
  email: string;
  phone: string;
  gender: string;
  date_of_birth: string;
  state: string;
  lga: string;
  ward: string;
  /** The applicant's ward isn't on the official list; they typed it. */
  ward_unlisted?: boolean;
  education: string;
  occupation: string;
  sector: string;
  has_business: boolean;
  business_idea: string;
  motivation: string;
  referral_source: string;
  stage: string;
  feedback?: string | null;
  applicant_response?: string | null;
  created_at: string;
};

export type Kyc = {
  reference: string;
  identification_type: string;
  identification_number: string;
  identity_document_url: string;
  passport_photograph_url: string;
  expires_in: number;
};

export type DocumentKey = "identity_document" | "passport_photograph";

export type UploadTicket = { path: string; token: string; signed_url: string };
export type UploadTickets = {
  reference: string;
  bucket: string;
  uploads: Record<DocumentKey, UploadTicket>;
};

export class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message);
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const supabase = getSupabase();
  const token = supabase ? (await supabase.auth.getSession()).data.session?.access_token : undefined;
  const headers = new Headers(init.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  let res: Response;
  try {
    // Same-origin: /api/* is the FastAPI service (vercel.json, or the API_ORIGIN proxy locally).
    res = await fetch(path, { ...init, headers });
  } catch {
    throw new ApiError("Unable to reach the application service. Check your connection.", 0);
  }
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = typeof body.detail === "string" ? body.detail : "Something went wrong. Please try again.";
    throw new ApiError(detail, res.status);
  }
  return body as T;
}

function json(body: unknown): RequestInit {
  return { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
}

export const api = {
  me: () => request<Me>("/api/me"),
  startUpload: (files: Record<DocumentKey, { content_type: string; size: number }>) =>
    request<UploadTickets>("/api/applications/uploads", json(files)),
  submit: (body: {
    reference: string;
    details: Record<string, unknown>;
    identity_document_path: string;
    passport_photograph_path: string;
  }) => request<{ id: string; reference: string; stage: string }>("/api/applications", json(body)),
  /** Upload URLs for replacement documents sent with a response (only the ones requested). */
  startResponseUpload: (files: Partial<Record<DocumentKey, { content_type: string; size: number }>>) =>
    request<{ reference: string; bucket: string; uploads: Partial<Record<DocumentKey, UploadTicket>> }>(
      "/api/applications/me/uploads",
      json(files),
    ),
  respond: (body: { note: string; identity_document_path?: string; passport_photograph_path?: string }) =>
    request<MyApplication>("/api/applications/me/respond", json(body)),
  listApplications: (params: Record<string, string>) => {
    const qs = new URLSearchParams(Object.entries(params).filter(([, v]) => v)).toString();
    return request<{ items: AdminApplication[]; total: number }>(`/api/admin/applications?${qs}`);
  },
  review: (id: string, action: "approve" | "reject" | "request_information", note?: string) =>
    request<AdminApplication>(
      `/api/admin/applications/${encodeURIComponent(id)}/review`,
      json({ action, note: note || null }),
    ),
  kyc: (id: string) => request<Kyc>(`/api/admin/applications/${encodeURIComponent(id)}/kyc`),
};
