import {
  apiRequest,
  ensureCsrfToken,
} from "./api";

export interface ReferralStatusHistory {
  id: number;
  from_status: string;
  to_status: string;
  changed_by: number | null;
  changed_by_name: string | null;
  note: string;
  created_at: string;
}

export interface Referral {
  id: number;
  reference: string;
  organisation: number;
  organisation_name?: string;
  rights_topic: number | null;
  summary: string;
  district: string;
  language: string;
  preferred_support_channel: string;
  citizen_consent_to_share: boolean;
  status: string;
  assigned_to?: number | null;
  assigned_to_name?: string | null;
  shared_at?: string | null;
  accepted_at: string | null;
  completed_at: string | null;
  status_history: ReferralStatusHistory[];
  created_at?: string;
  updated_at?: string;
}

export interface ReferralStatusPayload {
  status: string;
  note?: string;
}

export async function getReferrals(
  status?: string,
) {
  const params = new URLSearchParams();

  if (status) {
    params.set(
      "status",
      status,
    );
  }

  const query = params.toString();

  return apiRequest<Referral[]>(
    `/api/referrals/${query ? `?${query}` : ""}`,
  );
}

export async function getReferral(
  referralId: number,
) {
  return apiRequest<Referral>(
    `/api/referrals/${referralId}/`,
  );
}

export async function updateReferralStatus(
  referralId: number,
  payload: ReferralStatusPayload,
) {
  await ensureCsrfToken();

  return apiRequest<Referral>(
    `/api/referrals/${referralId}/status/`,
    {
      method: "POST",
      body: payload,
    },
  );
}
