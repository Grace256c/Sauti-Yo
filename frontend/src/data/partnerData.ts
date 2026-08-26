import type { CategorySlug } from "./rightsData";
import type { SupportType } from "./supportData";

/* =========================================================
   PARTNER PORTAL DATA MODEL

   This file defines organisations that may eventually
   participate in the Sauti Yo referral network.

   Registration does NOT automatically make an organisation
   eligible for citizen referrals.

   Referral eligibility requires verification.
========================================================= */

export type PartnerStatus =
  | "draft"
  | "pending-verification"
  | "verified"
  | "suspended"
  | "rejected";

export type OrganisationType =
  | "legal-aid"
  | "ngo"
  | "cbo"
  | "government"
  | "law-firm"
  | "protection-service"
  | "mediation-service"
  | "other";

export type ReferralStatus =
  | "new"
  | "reviewing"
  | "accepted"
  | "declined"
  | "in-progress"
  | "completed"
  | "closed";

export type SupportChannel =
  | "in-person"
  | "phone"
  | "remote";

export type PartnerContact = {
  name: string;
  role: string;
  email: string;
  phone: string;
};

export type PartnerLocation = {
  district: string;
  address?: string;
  directions?: string;
};

export type PartnerCapacity = {
  acceptingReferrals: boolean;
  referralLimit?: number;
  notes?: string;
};

export type PartnerProfile = {
  id: string;

  organisationName: string;

  organisationType: OrganisationType;

  registrationNumber?: string;

  description: string;

  website?: string;

  primaryContact: PartnerContact;

  publicPhone?: string;

  publicEmail?: string;

  supportTypes: SupportType[];

  categories: CategorySlug[];

  serviceDescription: string;

  headquarters?: PartnerLocation;

  districtsServed: string[];

  nationwide: boolean;

  languages: string[];

  supportChannels: SupportChannel[];

  freeServices: boolean;

  appointmentRequired?: boolean;

  accessibilityNotes?: string;

  capacity: PartnerCapacity;

  status: PartnerStatus;

  verifiedAt?: string;

  verifiedBy?: string;

  verificationNotes?: string;

  createdAt: string;

  updatedAt: string;
};

/* =========================================================
   REFERRAL
========================================================= */

export type Referral = {
  id: string;

  partnerId: string;

  category: CategorySlug;

  supportType: SupportType;

  district: string;

  language: string;

  preferredChannel: SupportChannel;

  citizenSummary?: string;

  citizenContact?: {
    name?: string;
    phone?: string;
    email?: string;
  };

  consentToShare: boolean;

  status: ReferralStatus;

  createdAt: string;

  updatedAt: string;
};

/* =========================================================
   MATCHING
========================================================= */

export type PartnerMatchRequest = {
  category: CategorySlug;

  district: string;

  language: string;

  preferredChannel: SupportChannel;

  supportType?: SupportType;
};

export type PartnerMatch = {
  partner: PartnerProfile;

  score: number;

  reasons: string[];
};

/* =========================================================
   CURRENT PARTNER DATA

   Deliberately empty for now.

   Real organisations will eventually come from the Partner
   Portal / backend after verification.
========================================================= */

export const partnerProfiles: PartnerProfile[] = [];

/* =========================================================
   MATCHING LOGIC

   This is frontend prototype logic.

   Later this should move to the backend.
========================================================= */

export function matchPartners(
  partners: PartnerProfile[],
  request: PartnerMatchRequest,
): PartnerMatch[] {
  return partners
    .filter(
      (partner) =>
        partner.status === "verified" &&
        partner.capacity.acceptingReferrals,
    )

    .filter((partner) =>
      partner.categories.includes(request.category),
    )

    .filter(
      (partner) =>
        partner.nationwide ||
        partner.districtsServed.includes(
          request.district,
        ),
    )

    .filter((partner) =>
      partner.languages.includes(request.language),
    )

    .filter((partner) =>
      partner.supportChannels.includes(
        request.preferredChannel,
      ),
    )

    .filter((partner) => {
      if (!request.supportType) {
        return true;
      }

      return partner.supportTypes.includes(
        request.supportType,
      );
    })

    .map((partner) => {
      let score = 0;

      const reasons: string[] = [];

      if (
        partner.categories.includes(
          request.category,
        )
      ) {
        score += 30;

        reasons.push(
          "Supports this type of rights issue",
        );
      }

      if (
        partner.nationwide ||
        partner.districtsServed.includes(
          request.district,
        )
      ) {
        score += 25;

        reasons.push(
          partner.nationwide
            ? "Provides support nationally"
            : `Provides support in ${request.district}`,
        );
      }

      if (
        partner.languages.includes(
          request.language,
        )
      ) {
        score += 20;

        reasons.push(
          `Provides support in ${request.language}`,
        );
      }

      if (
        partner.supportChannels.includes(
          request.preferredChannel,
        )
      ) {
        score += 15;

        reasons.push(
          request.preferredChannel === "remote"
            ? "Offers remote support"
            : request.preferredChannel === "phone"
              ? "Offers telephone support"
              : "Offers in-person support",
        );
      }

      if (
        request.supportType &&
        partner.supportTypes.includes(
          request.supportType,
        )
      ) {
        score += 10;

        reasons.push(
          "Provides the relevant specialised service",
        );
      }

      return {
        partner,
        score,
        reasons,
      };
    })

    .sort((a, b) => b.score - a.score);
}

/* =========================================================
   PORTAL HELPERS
========================================================= */

export function getPartnerById(
  id: string | undefined,
) {
  if (!id) {
    return null;
  }

  return (
    partnerProfiles.find(
      (partner) => partner.id === id,
    ) ?? null
  );
}

export function getVerifiedPartners() {
  return partnerProfiles.filter(
    (partner) =>
      partner.status === "verified",
  );
}

export function getVerifiedPartnersForCategory(
  category: CategorySlug,
): PartnerProfile[] {
  return partnerProfiles.filter(
    (partner) =>
      partner.status === "verified" &&
      partner.capacity.acceptingReferrals &&
      partner.categories.includes(category),
  );
}

export function getPartnersAwaitingVerification() {
  return partnerProfiles.filter(
    (partner) =>
      partner.status ===
      "pending-verification",
  );
}

export function getPartnersAcceptingReferrals() {
  return partnerProfiles.filter(
    (partner) =>
      partner.status === "verified" &&
      partner.capacity.acceptingReferrals,
  );
}