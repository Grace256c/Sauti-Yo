import {
  apiRequest,
} from "./api";

export interface PartnerMatchResult {
  id: number;
  organisation_name: string;
  organisation_type: string;
  service_description: string;
  public_phone: string;
  public_email: string;
  website: string;
  districts_served: string[];
  nationwide: boolean;
  languages: string[];
  support_channels: string[];
  rights_categories: string[];
  support_types: string[];
  free_services: boolean;
  appointment_required: boolean;
  availability_note: string;
  score: number;
  reasons: string[];
}

export async function findPartnerMatches(
  params: {
    category: string;
    district: string;
    language: string;
    channel: string;
  },
) {
  const query =
    new URLSearchParams(
      params,
    ).toString();

  return apiRequest<
    PartnerMatchResult[]
  >(
    `/api/partners/matches/?${query}`,
  );
}
