import {
  apiRequest,
  ensureCsrfToken,
} from "./api";

export interface PartnerUser {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
}

export interface PartnerMembership {
  id: number;
  role: string;
  organisation_id: number;
  organisation_name: string;
}

export interface PartnerSession {
  user: PartnerUser;
  membership: PartnerMembership;
}

export interface SupportService {
  id: number;
  name: string;
  service_type: string;
  description: string;
  phone_number: string;
  alternate_phone_number: string;
  email: string;
  website: string;
  availability: string;
  coverage: string;
  verification_status: string;
  last_verified: string | null;
  next_verification_due: string | null;
  is_emergency_service: boolean;
  is_active: boolean;
}

export interface PartnerMember {
  id: number;
  user_id: number;
  username: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PartnerServiceConfiguration {
  id: number;
  service_description: string;
  rights_categories: string[];
  support_types: string[];
  languages: string[];
  support_channels: string[];
  districts_served: string[];
  nationwide: boolean;
  free_services: boolean;
  appointment_required: boolean;
  accepting_referrals: boolean;
  weekly_referral_limit: number | null;
  availability_note: string;
  created_at: string;
  updated_at: string;
}

export type PartnerVerificationDocumentType =
  | "registration"
  | "organisation_identification"
  | "service_evidence"
  | "authorised_representative"
  | "other";

export interface PartnerVerificationDocument {
  id: number;
  document_type: PartnerVerificationDocumentType;
  title: string;
  file: string;
  uploaded_by: number | null;
  uploaded_by_name?: string | null;
  uploaded_at: string;
  is_active: boolean;
}

export interface PartnerVerification {
  id: number;
  status: string;

  declaration_accurate: boolean;
  declaration_authorised: boolean;
  declaration_consent: boolean;

  submitted_by: number | null;
  submitted_by_name?: string | null;
  submitted_at: string | null;

  reviewed_by: number | null;
  reviewed_by_name?: string | null;
  reviewed_at: string | null;

  review_notes: string;
  documents?: PartnerVerificationDocument[];

  created_at?: string;
  updated_at?: string;
}

export interface PartnerOrganisation {
  id: number;

  support_service: SupportService;

  organisation_type: string;
  registration_number: string;
  year_established: number | null;

  headquarters_district: string;
  physical_address: string;

  public_email: string;
  public_phone: string;

  is_active: boolean;

  service_configuration:
    | PartnerServiceConfiguration
    | null;

  members: PartnerMember[];

  latest_verification:
    | PartnerVerification
    | null;

  created_at: string;
  updated_at: string;
}

export interface PartnerLoginPayload {
  username: string;
  password: string;
}

export interface PartnerOrganisationUpdatePayload {
  support_service?: {
    name?: string;
    service_type?: string;
    description?: string;
    phone_number?: string;
    alternate_phone_number?: string;
    email?: string;
    website?: string;
    availability?: string;
    coverage?: string;
  };

  organisation_type?: string;
  registration_number?: string;
  year_established?: number | null;

  headquarters_district?: string;
  physical_address?: string;

  public_email?: string;
  public_phone?: string;
}

export interface PartnerServiceUpdatePayload {
  service_description?: string;

  rights_categories?: string[];
  support_types?: string[];

  languages?: string[];
  support_channels?: string[];
  districts_served?: string[];

  nationwide?: boolean;
  free_services?: boolean;
  appointment_required?: boolean;
  accepting_referrals?: boolean;

  weekly_referral_limit?: number | null;
  availability_note?: string;
}

export interface VerificationSubmissionPayload {
  declaration_accurate: boolean;
  declaration_authorised: boolean;
  declaration_consent: boolean;
}

/* =========================================================
   AUTH
========================================================= */

export async function getPartnerSession() {
  return apiRequest<PartnerSession>(
    "/api/auth/session/",
  );
}

export async function loginPartner(
  payload: PartnerLoginPayload,
) {
  const csrfToken =
    await ensureCsrfToken();

  return apiRequest<PartnerSession>(
    "/api/auth/login/",
    {
      method: "POST",

      headers: {
        "X-CSRFToken": csrfToken,
      },

      body: payload,
    },
  );
}

export async function logoutPartner() {
  const csrfToken =
    await ensureCsrfToken();

  return apiRequest<{
    detail: string;
  }>(
    "/api/auth/logout/",
    {
      method: "POST",

      headers: {
        "X-CSRFToken": csrfToken,
      },
    },
  );
}

/* =========================================================
   ORGANISATION
========================================================= */

export async function getPartnerOrganisation(
  organisationId: number,
) {
  return apiRequest<PartnerOrganisation>(
    `/api/partners/${organisationId}/`,
  );
}

export async function updatePartnerOrganisation(
  organisationId: number,
  payload: PartnerOrganisationUpdatePayload,
) {
  const csrfToken =
    await ensureCsrfToken();

  return apiRequest<PartnerOrganisation>(
    `/api/partners/${organisationId}/`,
    {
      method: "PATCH",

      headers: {
        "X-CSRFToken": csrfToken,
      },

      body: payload,
    },
  );
}

/* =========================================================
   SERVICES
========================================================= */

export async function getPartnerServices(
  organisationId: number,
) {
  return apiRequest<PartnerServiceConfiguration>(
    `/api/partners/${organisationId}/services/`,
  );
}

export async function updatePartnerServices(
  organisationId: number,
  payload: PartnerServiceUpdatePayload,
) {
  const csrfToken =
    await ensureCsrfToken();

  return apiRequest<PartnerServiceConfiguration>(
    `/api/partners/${organisationId}/services/`,
    {
      method: "PATCH",

      headers: {
        "X-CSRFToken": csrfToken,
      },

      body: payload,
    },
  );
}

/* =========================================================
   VERIFICATION
========================================================= */

export async function getPartnerVerification(
  organisationId: number,
) {
  return apiRequest<PartnerVerification | null>(
    `/api/partners/${organisationId}/verification/`,
  );
}

export async function submitPartnerVerification(
  organisationId: number,
  payload: VerificationSubmissionPayload,
) {
  const csrfToken =
    await ensureCsrfToken();

  return apiRequest<PartnerVerification>(
    `/api/partners/${organisationId}/verification/`,
    {
      method: "POST",

      headers: {
        "X-CSRFToken": csrfToken,
      },

      body: payload,
    },
  );
}

/* =========================================================
   VERIFICATION DOCUMENTS
========================================================= */

export async function uploadPartnerVerificationDocument(
  organisationId: number,
  documentType: PartnerVerificationDocumentType,
  file: File,
  title?: string,
) {
  const csrfToken =
    await ensureCsrfToken();

  const formData =
    new FormData();

  formData.append(
    "document_type",
    documentType,
  );

  formData.append(
    "file",
    file,
  );

  formData.append(
    "title",
    title?.trim() || file.name,
  );

  return apiRequest<PartnerVerificationDocument>(
    `/api/partners/${organisationId}/verification/documents/`,
    {
      method: "POST",

      headers: {
        "X-CSRFToken": csrfToken,
      },

      body: formData,
    },
  );
}

export async function deletePartnerVerificationDocument(
  organisationId: number,
  documentId: number,
) {
  const csrfToken =
    await ensureCsrfToken();

  return apiRequest<null>(
    `/api/partners/${organisationId}/verification/documents/${documentId}/`,
    {
      method: "DELETE",

      headers: {
        "X-CSRFToken": csrfToken,
      },
    },
  );
}



/* =========================================================
   PARTNER PREFERENCES
========================================================= */

export interface PartnerPreferences {
  id: number;

  email_notifications: boolean;
  sms_notifications: boolean;

  referral_notifications: boolean;
  verification_notifications: boolean;

  product_updates: boolean;

  show_public_phone: boolean;
  show_public_email: boolean;

  allow_remote_referrals: boolean;

  created_at: string;
  updated_at: string;
}

export type PartnerPreferencesUpdatePayload =
  Partial<
    Pick<
      PartnerPreferences,
      | "email_notifications"
      | "sms_notifications"
      | "referral_notifications"
      | "verification_notifications"
      | "product_updates"
      | "show_public_phone"
      | "show_public_email"
      | "allow_remote_referrals"
    >
  >;

export async function getPartnerPreferences(
  organisationId: number,
) {
  return apiRequest<PartnerPreferences>(
    `/api/partners/${organisationId}/preferences/`,
  );
}

export async function updatePartnerPreferences(
  organisationId: number,
  payload: PartnerPreferencesUpdatePayload,
) {
  await ensureCsrfToken();

  return apiRequest<PartnerPreferences>(
    `/api/partners/${organisationId}/preferences/`,
    {
      method: "PATCH",
      body: payload,
    },
  );
}
