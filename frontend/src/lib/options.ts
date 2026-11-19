// Keep in sync with backend/app/constants.py (the API validates every value).
export const STATES = [
  "Adamawa", "Bauchi", "Benue", "Borno", "Gombe", "Jigawa", "Kaduna", "Kano", "Katsina",
  "Kebbi", "Kogi", "Kwara", "Nasarawa", "Niger", "Plateau", "Sokoto", "Taraba", "Yobe",
  "Zamfara", "FCT Abuja",
] as const;

export const GENDERS = ["Male", "Female"] as const;

export const EDUCATION_LEVELS = [
  "Primary / Secondary", "NCE / ND", "HND / Bachelor’s Degree", "Master’s Degree",
  "PhD / Doctorate", "Others",
] as const;

export const OCCUPATIONS = [
  "Student", "Unemployed", "Self-employed / Business Owner", "Employed (Private Sector)",
  "Employed (Public / Civil Service)", "Farmer", "Others",
] as const;

export const SECTORS = [
  "Agriculture & Agribusiness", "Technology & Digital Services", "Trade & Commerce",
  "Manufacturing / Production", "Creative Arts & Media", "Education & Training",
  "Health & Wellness", "Fashion & Design", "Renewable Energy", "Others",
] as const;

export const REFERRAL_SOURCES = [
  "WhatsApp / Social Media", "Friend / Family", "Radio / TV",
  "Arewa Revival Project Official Channel", "Community Leader / Political Office", "Others",
] as const;

export const ID_TYPES = ["NIN", "International Passport"] as const;

export const REVIEW_PATH = [
  { stage: "state_review", label: "State review" },
  { stage: "lga_review", label: "LGA review" },
  { stage: "ward_review", label: "Ward review" },
  { stage: "approved", label: "Approved" },
] as const;

export const STAGE_LABELS: Record<string, string> = {
  state_review: "State review",
  lga_review: "LGA review",
  ward_review: "Ward review",
  approved: "Approved",
  rejected: "Not selected",
  needs_information: "More information needed",
};

export const ROLE_STAGE: Record<string, string> = {
  state: "state_review",
  lga: "lga_review",
  ward: "ward_review",
};

export const ACTION_LABELS: Record<string, string> = {
  submitted: "Application submitted",
  approve: "Stage approved",
  reject: "Not selected",
  request_information: "More information requested",
};

export const MAX_FILE_BYTES = 5 * 1024 * 1024;
export const MIN_BUSINESS_WORDS = 30;
export const MIN_AGE = 18;
