import re
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from . import constants as c
from .geo import canonical_lga, geo_key, tidy

PHONE_RE = re.compile(r"^\+?[0-9][0-9\s\-()]{6,19}$")
NIN_RE = re.compile(r"^\d{11}$")
PASSPORT_RE = re.compile(r"^[A-Z][0-9]{8}$")


def _one_of(value: str, allowed: tuple[str, ...], label: str) -> str:
    if value not in allowed:
        raise ValueError(f"Select a valid {label}.")
    return value


class ApplicationDetails(BaseModel):
    """Applicant-supplied form fields (files are validated separately)."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    full_name: str = Field(min_length=3, max_length=160)
    gender: str
    date_of_birth: date
    phone: str = Field(max_length=30)
    address: str = Field(min_length=5, max_length=300)
    state: str
    lga: str = Field(min_length=2, max_length=100)
    ward: str = Field(min_length=2, max_length=100)
    education: str
    occupation: str
    sector: str
    has_business: bool
    business_idea: str = Field(max_length=5000)
    motivation: str = Field(min_length=20, max_length=5000)
    referral_source: str
    identification_type: str
    identification_number: str = Field(max_length=20)

    @field_validator("gender")
    @classmethod
    def _gender(cls, v: str) -> str:
        return _one_of(v, c.GENDERS, "gender")

    @field_validator("state")
    @classmethod
    def _state(cls, v: str) -> str:
        return _one_of(v, c.NORTHERN_STATES, "state")

    @field_validator("education")
    @classmethod
    def _education(cls, v: str) -> str:
        return _one_of(v, c.EDUCATION_LEVELS, "qualification")

    @field_validator("occupation")
    @classmethod
    def _occupation(cls, v: str) -> str:
        return _one_of(v, c.OCCUPATIONS, "occupation")

    @field_validator("sector")
    @classmethod
    def _sector(cls, v: str) -> str:
        return _one_of(v, c.SECTORS, "sector")

    @field_validator("referral_source")
    @classmethod
    def _referral(cls, v: str) -> str:
        return _one_of(v, c.REFERRAL_SOURCES, "referral source")

    @field_validator("identification_type")
    @classmethod
    def _id_type(cls, v: str) -> str:
        return _one_of(v, c.IDENTIFICATION_TYPES, "identification type")

    @field_validator("phone")
    @classmethod
    def _phone(cls, v: str) -> str:
        if not PHONE_RE.match(v):
            raise ValueError("Enter a valid phone number.")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def _dob(cls, v: date) -> date:
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < c.MIN_APPLICANT_AGE:
            raise ValueError(f"Applicants must be at least {c.MIN_APPLICANT_AGE} years old.")
        if age > 120:
            raise ValueError("Enter a valid date of birth.")
        return v

    @field_validator("business_idea")
    @classmethod
    def _business_idea(cls, v: str) -> str:
        if len(v.split()) < c.MIN_BUSINESS_IDEA_WORDS:
            raise ValueError(
                f"Describe your business in at least {c.MIN_BUSINESS_IDEA_WORDS} words."
            )
        return v

    @model_validator(mode="after")
    def _location(self) -> "ApplicationDetails":
        # Reviewers are matched to applications by LGA and ward, so the LGA must be an official
        # one (stored with its canonical spelling) and the ward must contain real characters.
        lga = canonical_lga(self.state, self.lga)
        if lga is None:
            raise ValueError(f"Select a Local Government Area in {self.state}.")
        self.lga = lga
        self.ward = tidy(self.ward)
        if len(geo_key(self.ward)) < 2:
            raise ValueError("Enter your ward.")
        return self

    @model_validator(mode="after")
    def _identification(self) -> "ApplicationDetails":
        number = self.identification_number.replace(" ", "").upper()
        if self.identification_type == "NIN" and not NIN_RE.match(number):
            raise ValueError("NIN must contain exactly 11 digits.")
        if self.identification_type == "International Passport" and not PASSPORT_RE.match(number):
            raise ValueError("Passport number must be one letter followed by 8 digits.")
        self.identification_number = number
        return self


class ReviewEvent(BaseModel):
    stage: str
    action: str
    note: str | None = None
    created_at: datetime


class ApplicantApplication(BaseModel):
    """What an applicant may see about their own application (no KYC data)."""

    id: str
    reference: str
    full_name: str
    state: str
    lga: str
    ward: str
    stage: str
    feedback: str | None = None
    applicant_response: str | None = None
    created_at: datetime
    history: list[ReviewEvent] = []


class Profile(BaseModel):
    id: str
    email: str | None = None
    role: str = c.ROLE_APPLICANT
    state: str | None = None
    lga: str | None = None
    ward: str | None = None


class MeResponse(BaseModel):
    profile: Profile
    email_verified: bool
    application: ApplicantApplication | None = None


class SubmitResponse(BaseModel):
    id: str
    reference: str
    stage: str


class AdminApplication(BaseModel):
    id: str
    reference: str
    full_name: str
    email: EmailStr | str
    phone: str
    gender: str
    date_of_birth: date
    state: str
    lga: str
    ward: str
    education: str
    occupation: str
    sector: str
    has_business: bool
    business_idea: str
    motivation: str
    referral_source: str
    stage: str
    feedback: str | None = None
    applicant_response: str | None = None
    created_at: datetime


class AdminList(BaseModel):
    items: list[AdminApplication]
    total: int


class ReviewRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    action: Literal["approve", "reject", "request_information"]
    note: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def _note_required(self) -> "ReviewRequest":
        if self.action != "approve" and not self.note:
            raise ValueError("A note is required when rejecting or requesting information.")
        return self


class KycResponse(BaseModel):
    reference: str
    identification_type: str
    identification_number: str
    identity_document_url: str
    passport_photograph_url: str
    expires_in: int


REFERENCE_PATTERN = r"^ARP-[0-9A-F]{10}$"


class DeclaredFile(BaseModel):
    content_type: str = Field(max_length=100)
    size: int = Field(ge=0)


class UploadRequest(BaseModel):
    identity_document: DeclaredFile
    passport_photograph: DeclaredFile


class UploadTicket(BaseModel):
    path: str
    token: str
    signed_url: str


class UploadResponse(BaseModel):
    reference: str
    bucket: str
    uploads: dict[str, UploadTicket]


class SubmitRequest(BaseModel):
    reference: str = Field(pattern=REFERENCE_PATTERN)
    details: ApplicationDetails
    identity_document_path: str = Field(max_length=300)
    passport_photograph_path: str = Field(max_length=300)


class ResponseUploadRequest(BaseModel):
    """Replacement documents an applicant wants to send with a response (each optional)."""

    identity_document: DeclaredFile | None = None
    passport_photograph: DeclaredFile | None = None


class RespondRequest(BaseModel):
    """An applicant's answer to a "request information" review action."""

    model_config = ConfigDict(str_strip_whitespace=True)

    note: str = Field(min_length=5, max_length=2000)
    identity_document_path: str | None = Field(default=None, max_length=300)
    passport_photograph_path: str | None = Field(default=None, max_length=300)
