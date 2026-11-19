"""Programme reference data shared by validation and the review workflow."""

from typing import Final

NORTHERN_STATES: Final = (
    "Adamawa",
    "Bauchi",
    "Benue",
    "Borno",
    "Gombe",
    "Jigawa",
    "Kaduna",
    "Kano",
    "Katsina",
    "Kebbi",
    "Kogi",
    "Kwara",
    "Nasarawa",
    "Niger",
    "Plateau",
    "Sokoto",
    "Taraba",
    "Yobe",
    "Zamfara",
    "FCT Abuja",
)

GENDERS: Final = ("Male", "Female")

EDUCATION_LEVELS: Final = (
    "Primary / Secondary",
    "NCE / ND",
    "HND / Bachelor’s Degree",
    "Master’s Degree",
    "PhD / Doctorate",
    "Others",
)

OCCUPATIONS: Final = (
    "Student",
    "Unemployed",
    "Self-employed / Business Owner",
    "Employed (Private Sector)",
    "Employed (Public / Civil Service)",
    "Farmer",
    "Others",
)

SECTORS: Final = (
    "Agriculture & Agribusiness",
    "Technology & Digital Services",
    "Trade & Commerce",
    "Manufacturing / Production",
    "Creative Arts & Media",
    "Education & Training",
    "Health & Wellness",
    "Fashion & Design",
    "Renewable Energy",
    "Others",
)

REFERRAL_SOURCES: Final = (
    "WhatsApp / Social Media",
    "Friend / Family",
    "Radio / TV",
    "Arewa Revival Project Official Channel",
    "Community Leader / Political Office",
    "Others",
)

IDENTIFICATION_TYPES: Final = ("NIN", "International Passport")

# Review workflow: State → LGA → Ward → Approved.
STAGE_STATE: Final = "state_review"
STAGE_LGA: Final = "lga_review"
STAGE_WARD: Final = "ward_review"
STAGE_APPROVED: Final = "approved"
STAGE_REJECTED: Final = "rejected"
STAGE_NEEDS_INFO: Final = "needs_information"

STAGES: Final = (
    STAGE_STATE,
    STAGE_LGA,
    STAGE_WARD,
    STAGE_APPROVED,
    STAGE_REJECTED,
    STAGE_NEEDS_INFO,
)
ACTIVE_STAGES: Final = (STAGE_STATE, STAGE_LGA, STAGE_WARD)
NEXT_STAGE: Final = {
    STAGE_STATE: STAGE_LGA,
    STAGE_LGA: STAGE_WARD,
    STAGE_WARD: STAGE_APPROVED,
}

ROLE_APPLICANT: Final = "applicant"
ROLE_WARD: Final = "ward"
ROLE_LGA: Final = "lga"
ROLE_STATE: Final = "state"
ROLE_NATIONAL: Final = "national"
REVIEWER_ROLES: Final = (ROLE_NATIONAL, ROLE_STATE, ROLE_LGA, ROLE_WARD)

# The stage each geographic reviewer is responsible for. National reviewers may act on any
# active stage and are the only role with access to identity (KYC) documents.
ROLE_STAGE: Final = {ROLE_STATE: STAGE_STATE, ROLE_LGA: STAGE_LGA, ROLE_WARD: STAGE_WARD}

MIN_APPLICANT_AGE: Final = 18
MIN_BUSINESS_IDEA_WORDS: Final = 30

DOCUMENT_TYPES: Final = {
    "identity_document": {"application/pdf", "image/jpeg", "image/png"},
    "passport_photograph": {"image/jpeg", "image/png"},
}
