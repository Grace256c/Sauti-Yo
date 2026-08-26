import {
  apiRequest,
} from "./api";

export interface RightsActionStep {
  id: number;
  order: number;
  title: string;
  description: string;
  is_safety_critical: boolean;
  is_active: boolean;
}

export interface RightsSafetyResponse {
  id: number;
  trigger_key: string;
  message: string;
  is_active: boolean;
}

export interface RightsSupportService {
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

export interface RightsTopic {
  id: number;
  slug: string;
  title: string;
  risk_level: string;
  summary: string;
  source_name: string;
  source_url: string;
  reviewed_by: string;
  last_reviewed: string | null;
  next_review_due: string | null;
  verification_status: string;
  support_services: RightsSupportService[];
  action_steps: RightsActionStep[];
  safety_responses: RightsSafetyResponse[];
  is_active: boolean;
}

export interface SituationRightsLink {
  id: number;
  rights_topic: RightsTopic;
}

export interface Situation {
  id: number;
  slug: string;
  title: string;
  description: string;
  risk_level: string;
  rights_links: SituationRightsLink[];
  is_active: boolean;
}

export async function getSituations() {
  return apiRequest<Situation[]>(
    "/api/rights/situations/",
  );
}

export async function getSituation(
  slug: string,
) {
  return apiRequest<Situation>(
    `/api/rights/situations/${slug}/`,
  );
}

export async function getRightsTopics() {
  return apiRequest<RightsTopic[]>(
    "/api/rights/topics/",
  );
}

export async function getRightsTopic(
  slug: string,
) {
  return apiRequest<RightsTopic>(
    `/api/rights/topics/${slug}/`,
  );
}
