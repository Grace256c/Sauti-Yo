import {
  BriefcaseBusiness,
  HeartHandshake,
  Home,
  Landmark,
  Scale,
  ShieldCheck,
  Users,
} from "lucide-react";

import type { CategorySlug } from "./rightsData";

/* =========================================================
   SUPPORT DATA

   This file describes TYPES OF SUPPORT.

   It does not contain partner organisations.

   Partner profiles, verification and matching belong in:
   src/data/partnerData.ts
========================================================= */

export type SupportType =
  | "legal-aid"
  | "labour-support"
  | "protection"
  | "land-housing"
  | "family-support"
  | "public-services"
  | "community-rights";

export type SupportPathway = {
  id: SupportType;
  title: string;
  description: string;
  icon: typeof Scale;
  categories: CategorySlug[];
  examples: string[];
};

/* =========================================================
   SUPPORT PATHWAYS
========================================================= */

export const supportPathways: SupportPathway[] = [
  {
    id: "labour-support",
    title: "Work & Labour Support",
    description:
      "Support for workplace concerns involving pay, dismissal, employment agreements, treatment or working conditions.",
    icon: BriefcaseBusiness,
    categories: ["work-employment"],
    examples: [
      "Unpaid or delayed wages",
      "Dismissal or suspension",
      "Employment agreements",
      "Workplace treatment",
    ],
  },

  {
    id: "protection",
    title: "Safety & Protection Support",
    description:
      "Support pathways for situations involving violence, abuse, threats, harassment or concerns about personal safety.",
    icon: ShieldCheck,
    categories: [
      "safety-protection",
      "community-discrimination",
    ],
    examples: [
      "Threats or intimidation",
      "Violence or abuse",
      "Harassment",
      "Personal safety concerns",
    ],
  },

  {
    id: "land-housing",
    title: "Land & Housing Support",
    description:
      "Support for land ownership, tenancy, eviction, boundary and other property-related concerns.",
    icon: Home,
    categories: ["land-housing"],
    examples: [
      "Land ownership disputes",
      "Eviction concerns",
      "Landlord or tenant issues",
      "Property documentation",
    ],
  },

  {
    id: "family-support",
    title: "Family & Inheritance Support",
    description:
      "Support for family matters involving inheritance, children, relationships, family responsibilities or property.",
    icon: HeartHandshake,
    categories: ["family-inheritance"],
    examples: [
      "Inheritance concerns",
      "Children and family responsibilities",
      "Marriage or separation",
      "Family property disputes",
    ],
  },

  {
    id: "public-services",
    title: "Public Service Support",
    description:
      "Support for difficulties involving public institutions, administrative decisions, complaints or access to services.",
    icon: Landmark,
    categories: ["public-services"],
    examples: [
      "Difficulty accessing services",
      "Administrative decisions",
      "Delayed responses",
      "Complaints about public institutions",
    ],
  },

  {
    id: "community-rights",
    title: "Community & Rights Support",
    description:
      "Support where a person is experiencing discrimination, exclusion, harassment or another community rights concern.",
    icon: Users,
    categories: ["community-discrimination"],
    examples: [
      "Discrimination",
      "Unfair exclusion",
      "Community disputes",
      "Harassment or degrading treatment",
    ],
  },

  {
    id: "legal-aid",
    title: "General Legal Support",
    description:
      "A broader pathway for situations that may require legal information, advice or representation beyond one specific category.",
    icon: Scale,
    categories: [
      "work-employment",
      "safety-protection",
      "land-housing",
      "family-inheritance",
      "public-services",
      "community-discrimination",
    ],
    examples: [
      "Understanding legal options",
      "Complex or overlapping issues",
      "Help understanding documents",
      "Situations requiring professional legal support",
    ],
  },
];

/* =========================================================
   HELPERS
========================================================= */

export function getSupportPathwaysForCategory(
  category: CategorySlug,
) {
  return supportPathways.filter((pathway) =>
    pathway.categories.includes(category),
  );
}

export function getSupportPathway(
  id: string | undefined,
) {
  if (!id) {
    return null;
  }

  return (
    supportPathways.find(
      (pathway) => pathway.id === id,
    ) ?? null
  );
}