import { MAX_FILE_BYTES, MIN_AGE, MIN_BUSINESS_WORDS } from "./options";

export function wordCount(text: string): number {
  const trimmed = text.trim();
  return trimmed ? trimmed.split(/\s+/).length : 0;
}

export function normaliseIdNumber(value: string): string {
  return value.replace(/\s+/g, "").toUpperCase();
}

export function validateIdNumber(type: string, value: string): string | null {
  const v = normaliseIdNumber(value);
  if (type === "NIN" && !/^\d{11}$/.test(v)) return "NIN must contain exactly 11 digits.";
  if (type === "International Passport" && !/^[A-Z]\d{8}$/.test(v))
    return "Passport number must be one letter followed by 8 digits.";
  return null;
}

export function ageOn(dob: string, today = new Date()): number {
  const d = new Date(`${dob}T00:00:00`);
  let age = today.getFullYear() - d.getFullYear();
  const m = today.getMonth() - d.getMonth();
  if (m < 0 || (m === 0 && today.getDate() < d.getDate())) age--;
  return age;
}

export function validatePhone(value: string): string | null {
  return /^\+?[0-9][0-9\s\-()]{6,19}$/.test(value.trim()) ? null : "Enter a valid phone number.";
}

const SIGNATURES: Record<string, number[]> = {
  "application/pdf": [0x25, 0x50, 0x44, 0x46, 0x2d],
  "image/jpeg": [0xff, 0xd8, 0xff],
  "image/png": [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a],
};

export function sniffType(bytes: Uint8Array): string | null {
  for (const [type, sig] of Object.entries(SIGNATURES)) {
    if (sig.every((b, i) => bytes[i] === b)) return type;
  }
  return null;
}

export type FileCheck = { ok: true; type: string } | { ok: false; error: string };

/** Check size and the real file type (from its first bytes, not the browser's guess). */
export async function inspectFile(file: File | null, label: string, allowed: string[]): Promise<FileCheck> {
  if (!file || file.size === 0) return { ok: false, error: `${label} is required.` };
  if (file.size > MAX_FILE_BYTES) return { ok: false, error: `${label} must be 5 MB or smaller.` };
  const head = new Uint8Array(await file.slice(0, 8).arrayBuffer());
  const detected = sniffType(head);
  if (!detected || !allowed.includes(detected)) {
    const kinds = allowed.map((t) => t.split("/")[1].replace("jpeg", "JPG").toUpperCase()).join(", ");
    return { ok: false, error: `${label} must be a ${kinds} file.` };
  }
  return { ok: true, type: detected };
}

export type DetailsInput = Record<string, string>;

/** Client-side checks that mirror the API. Returns the first problem found, or null. */
export function validateDetails(d: DetailsInput, today = new Date()): string | null {
  if (!d.date_of_birth || Number.isNaN(Date.parse(d.date_of_birth))) return "Enter your date of birth.";
  if (ageOn(d.date_of_birth, today) < MIN_AGE) return `Applicants must be at least ${MIN_AGE} years old.`;
  const phone = validatePhone(d.phone ?? "");
  if (phone) return phone;
  if (wordCount(d.business_idea ?? "") < MIN_BUSINESS_WORDS)
    return `Describe your business in at least ${MIN_BUSINESS_WORDS} words.`;
  return validateIdNumber(d.identification_type ?? "", d.identification_number ?? "");
}
