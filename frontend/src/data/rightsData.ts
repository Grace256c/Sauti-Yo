import {
  BriefcaseBusiness,
  HeartHandshake,
  Home,
  Landmark,
  ShieldCheck,
  Users,
} from "lucide-react";

export type CategorySlug =
  | "work-employment"
  | "safety-protection"
  | "land-housing"
  | "family-inheritance"
  | "public-services"
  | "community-discrimination";

export type Answer = {
  id: string;
  label: string;
};

export type Question = {
  id: string;
  eyebrow: string;
  title: string;
  description?: string;
  answers: Answer[];
};

export type RightsCategory = {
  slug: CategorySlug;
  title: string;
  shortDescription: string;
  description: string;
  icon: typeof BriefcaseBusiness;
  examples: string[];
  navigatorTitle: string;
  navigatorDescription: string;
  navigatorExamples: string[];
  questions: Question[];
};

export const rightsCategories: RightsCategory[] = [
  {
    slug: "work-employment",
    title: "Work & Employment",
    icon: BriefcaseBusiness,

    shortDescription:
      "Questions about pay, dismissal, workplace treatment, contracts or unfair conditions.",

    description:
      "Explore rights and practical next steps related to employment, workplace treatment, contracts, dismissal and pay.",

    examples: [
      "You have not been paid for work you completed.",
      "You were dismissed and are unsure what your options are.",
      "You are concerned about treatment or conditions at work.",
      "You have questions about your employment agreement.",
    ],

    navigatorTitle: "Something happened at work",

    navigatorDescription:
      "Pay, dismissal, contracts, workplace treatment or working conditions.",

    navigatorExamples: [
      "I have not been paid.",
      "I was dismissed.",
      "I am being treated unfairly at work.",
    ],

    questions: [
      {
        id: "work-issue",
        eyebrow: "Your situation",
        title: "What happened at work?",
        description: "Choose the option that feels closest.",
        answers: [
          {
            id: "unpaid",
            label:
              "I have not been paid or there is a problem with my pay.",
          },
          {
            id: "dismissed",
            label:
              "I was dismissed, suspended or told to stop working.",
          },
          {
            id: "treatment",
            label:
              "I am being treated unfairly or badly at work.",
          },
          {
            id: "contract",
            label:
              "I have a question or problem involving my contract.",
          },
          {
            id: "other",
            label: "Something else happened at work.",
          },
        ],
      },
      {
        id: "work-status",
        eyebrow: "A little more context",
        title: "Which best describes your work arrangement?",
        answers: [
          {
            id: "written-contract",
            label: "I have a written employment contract.",
          },
          {
            id: "verbal-agreement",
            label: "I work under a verbal or informal agreement.",
          },
          {
            id: "casual",
            label: "I do casual, temporary or short-term work.",
          },
          {
            id: "unsure",
            label:
              "I am not sure how my work arrangement is classified.",
          },
        ],
      },
      {
        id: "work-action",
        eyebrow: "What have you done so far?",
        title: "Have you already raised the issue with anyone?",
        answers: [
          {
            id: "employer",
            label:
              "Yes, I spoke to my employer or supervisor.",
          },
          {
            id: "organisation",
            label:
              "Yes, I contacted another organisation or authority.",
          },
          {
            id: "nothing",
            label: "No, I have not taken any action yet.",
          },
          {
            id: "unsafe",
            label:
              "I do not feel safe raising the issue directly.",
          },
        ],
      },
    ],
  },

  {
    slug: "safety-protection",
    title: "Safety & Protection",
    icon: ShieldCheck,

    shortDescription:
      "Situations involving abuse, threats, violence, harassment or personal safety.",

    description:
      "Explore safety-conscious information and support options where there may be threats, violence, abuse or harassment.",

    examples: [
      "Someone has threatened or harmed you.",
      "You are worried about your immediate safety.",
      "You are experiencing harassment or abuse.",
      "You need to understand possible protection or support options.",
    ],

    navigatorTitle: "I am worried about my safety",

    navigatorDescription:
      "Threats, abuse, violence, harassment or another personal safety concern.",

    navigatorExamples: [
      "Someone is threatening me.",
      "I have experienced abuse.",
      "I need to understand where I can get help.",
    ],

    questions: [
      {
        id: "safety-now",
        eyebrow: "Safety first",
        title: "Are you in immediate danger right now?",
        description:
          "Choose the answer that best describes your situation at this moment.",
        answers: [
          {
            id: "yes",
            label: "Yes, I may be in immediate danger.",
          },
          {
            id: "maybe",
            label:
              "I am not sure, but I am worried about my safety.",
          },
          {
            id: "no",
            label:
              "No, I am not in immediate danger right now.",
          },
        ],
      },
      {
        id: "safety-issue",
        eyebrow: "Your situation",
        title: "What is happening?",
        answers: [
          {
            id: "violence",
            label:
              "Someone has physically harmed or attacked me.",
          },
          {
            id: "threats",
            label:
              "Someone is threatening or intimidating me.",
          },
          {
            id: "harassment",
            label:
              "I am experiencing harassment or repeated unwanted behaviour.",
          },
          {
            id: "abuse",
            label:
              "I am experiencing abuse in a personal or family situation.",
          },
          {
            id: "other",
            label:
              "It is another kind of safety concern.",
          },
        ],
      },
      {
        id: "safety-support",
        eyebrow: "Support",
        title:
          "Do you have someone or somewhere you trust for support?",
        answers: [
          {
            id: "person",
            label: "Yes, there is someone I trust.",
          },
          {
            id: "organisation",
            label:
              "Yes, I know an organisation or service I can contact.",
          },
          {
            id: "no",
            label:
              "No, I am not sure who I can turn to.",
          },
        ],
      },
    ],
  },

  {
    slug: "land-housing",
    title: "Land & Housing",
    icon: Home,

    shortDescription:
      "Issues involving land, tenancy, eviction, ownership or housing disputes.",

    description:
      "Explore rights and next steps related to land, ownership, tenancy, eviction and housing disputes.",

    examples: [
      "There is a disagreement about land ownership.",
      "You are facing eviction or removal from a property.",
      "You have a dispute with a landlord or tenant.",
      "You need to understand documents or decisions affecting property.",
    ],

    navigatorTitle: "I have a land or housing problem",

    navigatorDescription:
      "Land ownership, tenancy, eviction, boundaries or housing disputes.",

    navigatorExamples: [
      "There is a dispute about land.",
      "I am being threatened with eviction.",
      "I have a problem with my landlord or tenant.",
    ],

    questions: [
      {
        id: "land-issue",
        eyebrow: "Your situation",
        title: "What is the main issue?",
        answers: [
          {
            id: "ownership",
            label:
              "There is a disagreement about ownership.",
          },
          {
            id: "eviction",
            label:
              "I am being evicted or threatened with eviction.",
          },
          {
            id: "boundary",
            label:
              "There is a boundary or neighbouring land dispute.",
          },
          {
            id: "tenancy",
            label:
              "The issue involves a landlord, tenant or rental arrangement.",
          },
          {
            id: "documents",
            label:
              "The issue involves land or property documents.",
          },
          {
            id: "other",
            label: "It is another land or housing issue.",
          },
        ],
      },
      {
        id: "land-relationship",
        eyebrow: "Your connection",
        title:
          "What is your relationship to the property?",
        answers: [
          {
            id: "owner",
            label:
              "I believe I own or have rights to the property.",
          },
          {
            id: "tenant",
            label: "I am a tenant or renter.",
          },
          {
            id: "family",
            label:
              "The property belongs to or is shared within my family.",
          },
          {
            id: "occupant",
            label:
              "I live or work there but ownership is unclear.",
          },
          {
            id: "other",
            label: "Another situation applies.",
          },
        ],
      },
      {
        id: "land-documents",
        eyebrow: "Information available",
        title:
          "Do you have documents related to the property?",
        answers: [
          {
            id: "yes",
            label: "Yes, I have documents.",
          },
          {
            id: "some",
            label:
              "I have some documents, but I am not sure what they mean.",
          },
          {
            id: "no",
            label: "No, I do not have documents.",
          },
          {
            id: "unsure",
            label: "I am not sure.",
          },
        ],
      },
    ],
  },

  {
    slug: "family-inheritance",
    title: "Family & Inheritance",
    icon: HeartHandshake,

    shortDescription:
      "Questions affecting marriage, children, family responsibilities or inheritance.",

    description:
      "Explore common rights questions involving family responsibilities, marriage, children and inheritance.",

    examples: [
      "There is a disagreement about inheritance.",
      "You have questions about responsibilities toward children.",
      "A family matter has created a legal or practical concern.",
      "You need to understand your options before taking action.",
    ],

    navigatorTitle: "It involves my family",

    navigatorDescription:
      "Marriage, children, family responsibilities or inheritance concerns.",

    navigatorExamples: [
      "There is an inheritance disagreement.",
      "I have a concern involving children.",
      "A family situation has become difficult.",
    ],

    questions: [
      {
        id: "family-issue",
        eyebrow: "Your situation",
        title:
          "What does the issue mainly involve?",
        answers: [
          {
            id: "inheritance",
            label:
              "Inheritance or property after someone has died.",
          },
          {
            id: "children",
            label:
              "Children, care or family responsibilities.",
          },
          {
            id: "marriage",
            label:
              "Marriage, separation or another relationship issue.",
          },
          {
            id: "property",
            label:
              "Property or money within the family.",
          },
          {
            id: "other",
            label: "Another family issue.",
          },
        ],
      },
      {
        id: "family-dispute",
        eyebrow: "Current situation",
        title:
          "Is there currently a disagreement or dispute?",
        answers: [
          {
            id: "yes",
            label:
              "Yes, there is an active disagreement.",
          },
          {
            id: "starting",
            label:
              "A disagreement may be developing.",
          },
          {
            id: "no",
            label:
              "No, I mainly want to understand my rights.",
          },
        ],
      },
      {
        id: "family-support",
        eyebrow: "Support",
        title:
          "Have you already asked anyone for help?",
        answers: [
          {
            id: "family",
            label:
              "Yes, I have spoken with family or community members.",
          },
          {
            id: "professional",
            label:
              "Yes, I have contacted a professional or organisation.",
          },
          {
            id: "no",
            label:
              "No, I have not asked for help yet.",
          },
        ],
      },
    ],
  },

  {
    slug: "public-services",
    title: "Public Services",
    icon: Landmark,

    shortDescription:
      "Concerns involving public institutions, access to services or administrative decisions.",

    description:
      "Explore concerns involving public institutions, government services and administrative decisions.",

    examples: [
      "You are having difficulty accessing a public service.",
      "A public institution made a decision you do not understand.",
      "You need to know where to raise a complaint.",
      "You want to understand what steps may be available.",
    ],

    navigatorTitle: "It involves a public institution",

    navigatorDescription:
      "Government services, public institutions or administrative decisions.",

    navigatorExamples: [
      "I cannot access a public service.",
      "I do not understand a decision that was made.",
      "I need to know where I can make a complaint.",
    ],

    questions: [
      {
        id: "service-issue",
        eyebrow: "Your situation",
        title:
          "What best describes the problem?",
        answers: [
          {
            id: "access",
            label:
              "I cannot access a service I need.",
          },
          {
            id: "decision",
            label:
              "A decision was made that I do not understand or agree with.",
          },
          {
            id: "delay",
            label:
              "There has been an unreasonable delay or no response.",
          },
          {
            id: "treatment",
            label:
              "I believe I was treated unfairly.",
          },
          {
            id: "complaint",
            label:
              "I want to know how or where to make a complaint.",
          },
          {
            id: "other",
            label: "Another public-service issue.",
          },
        ],
      },
      {
        id: "service-contact",
        eyebrow: "What happened next?",
        title:
          "Have you contacted the institution about the problem?",
        answers: [
          {
            id: "yes-response",
            label:
              "Yes, and I received a response.",
          },
          {
            id: "yes-no-response",
            label:
              "Yes, but I have not received a useful response.",
          },
          {
            id: "no",
            label:
              "No, I have not contacted them yet.",
          },
        ],
      },
      {
        id: "service-records",
        eyebrow: "Information available",
        title:
          "Do you have any records related to the issue?",
        answers: [
          {
            id: "yes",
            label:
              "Yes, I have letters, messages, receipts or other records.",
          },
          {
            id: "some",
            label:
              "I have some information but not everything.",
          },
          {
            id: "no",
            label:
              "No, I do not have records.",
          },
        ],
      },
    ],
  },

  {
    slug: "community-discrimination",
    title: "Community & Discrimination",
    icon: Users,

    shortDescription:
      "Situations involving unfair treatment, exclusion or rights within the community.",

    description:
      "Explore situations involving unfair treatment, exclusion, discrimination or community rights concerns.",

    examples: [
      "You believe you have been treated unfairly.",
      "You have experienced exclusion or discrimination.",
      "A community issue is affecting your rights or wellbeing.",
      "You need to understand where appropriate support may exist.",
    ],

    navigatorTitle: "I have been treated unfairly",

    navigatorDescription:
      "Discrimination, exclusion or another community rights concern.",

    navigatorExamples: [
      "I feel I have been discriminated against.",
      "I have been excluded unfairly.",
      "A community issue is affecting my rights.",
    ],

    questions: [
      {
        id: "community-issue",
        eyebrow: "Your situation",
        title:
          "What best describes what happened?",
        answers: [
          {
            id: "discrimination",
            label:
              "I believe I was discriminated against.",
          },
          {
            id: "excluded",
            label:
              "I was unfairly excluded from something.",
          },
          {
            id: "harassment",
            label:
              "I experienced harassment or degrading treatment.",
          },
          {
            id: "community",
            label:
              "A community decision or action is affecting me unfairly.",
          },
          {
            id: "other",
            label: "Something else happened.",
          },
        ],
      },
      {
        id: "community-setting",
        eyebrow: "Where it happened",
        title:
          "Where did this mainly happen?",
        answers: [
          {
            id: "community",
            label:
              "Within my local community.",
          },
          {
            id: "service",
            label:
              "While accessing a service.",
          },
          {
            id: "organisation",
            label:
              "Within an organisation or institution.",
          },
          {
            id: "other",
            label: "Somewhere else.",
          },
        ],
      },
      {
        id: "community-action",
        eyebrow: "What you have done",
        title:
          "Have you already raised the issue?",
        answers: [
          {
            id: "yes",
            label:
              "Yes, I have reported or raised it.",
          },
          {
            id: "no",
            label:
              "No, I have not raised it yet.",
          },
          {
            id: "unsafe",
            label:
              "I do not feel comfortable or safe raising it directly.",
          },
        ],
      },
    ],
  },
];

export const rightsCategoryMap = Object.fromEntries(
  rightsCategories.map((category) => [
    category.slug,
    category,
  ]),
) as Record<CategorySlug, RightsCategory>;

export function isCategorySlug(
  value: string | undefined,
): value is CategorySlug {
  return Boolean(
    value &&
      Object.prototype.hasOwnProperty.call(
        rightsCategoryMap,
        value,
      ),
  );
}

export function getRightsCategory(
  slug: string | undefined,
) {
  if (!isCategorySlug(slug)) {
    return null;
  }

  return rightsCategoryMap[slug];
}

export function getJourneyStorageKey(
  slug: CategorySlug,
) {
  return `sauti-yo-journey-${slug}`;
}