import {
  apiRequest,
} from "./api";

export interface VerifiedLegalSource {
  title: string;
  version_date?: string | null;
  jurisdiction?: string | null;
  category?: string | null;
  pages: number[];
}

export interface LegalGuidanceResponse {
  matched: boolean;
  reply?: string;
  message?: string;
  sources?: VerifiedLegalSource[];
  has_verified_sources?: boolean;
  situation?: {
    slug: string;
    title: string;
    risk_level: string;
  } | null;
}

/**
 * Request a source-grounded explanation for a citizen's concern.
 *
 * The deterministic Rights Navigator remains responsible for
 * classification, safety responses, action steps and support services.
 * This service only adds the RAG-backed explanatory layer.
 */
export async function getLegalGuidance(
  concern: string,
  situationSlug?: string | null,
  language = "en",
) {
  return apiRequest<LegalGuidanceResponse>(
    "/api/chat/",
    {
      method: "POST",
      body: {
        message: concern,
        language,
        situation_slug: situationSlug ?? null,
      },
    },
  );
}
