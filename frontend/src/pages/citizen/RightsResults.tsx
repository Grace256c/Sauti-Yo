import {
  useEffect,
  useState,
} from "react";
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  BookOpen,
  Building2,
  CheckCircle2,
  ClipboardList,
  FileText,
  Info,
  Scale,
} from "lucide-react";
import {
  Link,
  Navigate,
  useParams,
} from "react-router-dom";

import {
  getJourneyStorageKey,
  getRightsCategory,
} from "../../data/rightsData";

import type {
  CategorySlug,
} from "../../data/rightsData";

import {
  getSituation,
} from "../../services/rights";

import type {
  Situation,
} from "../../services/rights";

type JourneyAnswers = Record<string, string>;

type IssueResult = {
  heading: string;
  introduction: string;
  rights: string[];
  actions: string[];
  documents: string[];
};

const issueResults: Record<
  CategorySlug,
  Record<string, IssueResult>
> = {
  "work-employment": {
    unpaid: {
      heading: "Your situation appears to involve a pay problem.",
      introduction:
        "Based on your answers, the main issue appears to involve unpaid wages, delayed payment or another problem with your pay.",
      rights: [
        "It may be important to understand what payment was agreed for the work you performed.",
        "Written and informal work arrangements can both involve important employment questions.",
        "Payment records, agreements and communication with the employer may help clarify what happened.",
      ],
      actions: [
        "Write down the work you completed and the dates you worked.",
        "Record the amount you expected to receive and what, if anything, you were actually paid.",
        "Keep messages or conversations relating to payment.",
        "Where appropriate and safe, ask for a clear explanation of the payment issue.",
        "Consider seeking labour or legal support if the issue remains unresolved.",
      ],
      documents: [
        "Employment contract or agreement",
        "Payslips",
        "Mobile money or bank records",
        "Messages about payment",
        "Attendance or work records",
        "Names of possible witnesses",
      ],
    },

    dismissed: {
      heading: "Your situation appears to involve dismissal or suspension.",
      introduction:
        "Based on your answers, the main issue appears to involve being dismissed, suspended or told to stop working.",
      rights: [
        "Understanding why the employment relationship ended may be important.",
        "Any contract, disciplinary communication or termination notice may help clarify the situation.",
        "The process followed before or during dismissal may be relevant when seeking further guidance.",
      ],
      actions: [
        "Write down when you were told to stop working and who communicated the decision.",
        "Keep any dismissal, suspension or disciplinary letters.",
        "Record any reasons you were given.",
        "Keep your employment and payment records.",
        "Consider seeking labour or legal guidance before making important decisions about the dispute.",
      ],
      documents: [
        "Employment contract",
        "Termination or suspension letter",
        "Disciplinary correspondence",
        "Payslips",
        "Workplace policies",
        "Relevant messages or emails",
      ],
    },

    treatment: {
      heading: "Your situation appears to involve workplace treatment.",
      introduction:
        "Based on your answers, you may be dealing with unfair treatment, harassment, inappropriate conduct or difficult workplace conditions.",
      rights: [
        "It can be important to distinguish a disagreement at work from conduct that may require formal support.",
        "Workplace policies and employment agreements may help explain available internal processes.",
        "Safety should come before confronting someone where raising the issue could put you at risk.",
      ],
      actions: [
        "Write down specific incidents, including dates and what happened.",
        "Keep relevant messages or other records.",
        "Check whether your workplace has a complaint or reporting process.",
        "Identify possible witnesses where appropriate.",
        "Seek outside support if reporting internally feels unsafe or ineffective.",
      ],
      documents: [
        "Employment contract",
        "Workplace policies",
        "Messages or emails",
        "Written complaints",
        "Incident notes",
        "Names of witnesses",
      ],
    },

    contract: {
      heading: "Your situation appears to involve your work agreement.",
      introduction:
        "Based on your answers, you may need help understanding an employment contract, verbal agreement or the conditions under which you work.",
      rights: [
        "Understanding what was agreed between you and the employer is an important starting point.",
        "Written documents are useful, but other records may also help explain an informal work arrangement.",
        "You should avoid signing documents you do not understand.",
      ],
      actions: [
        "Read any employment documents you have carefully.",
        "Identify the particular term or condition you are concerned about.",
        "Keep records showing how the work arrangement has operated in practice.",
        "Ask for clarification where appropriate.",
        "Seek qualified guidance before agreeing to a major change you do not understand.",
      ],
      documents: [
        "Employment contract",
        "Appointment letter",
        "Payslips",
        "Work schedules",
        "Messages with the employer",
        "Relevant workplace policies",
      ],
    },

    other: {
      heading: "Your situation involves another workplace concern.",
      introduction:
        "Your workplace issue does not fit neatly into the common situations listed, but you can still organise the facts and identify appropriate support.",
      rights: [
        "Understanding exactly what happened is an important first step.",
        "Employment records may help another person or organisation understand the situation.",
        "You can seek further support when general information does not address the issue.",
      ],
      actions: [
        "Write a short timeline of what happened.",
        "Identify the people involved.",
        "Keep relevant employment documents and communication.",
        "Record what outcome you are hoping for.",
        "Consider speaking with an appropriate labour or legal support service.",
      ],
      documents: [
        "Employment records",
        "Contracts or agreements",
        "Messages or emails",
        "Payment records",
        "Letters or notices",
        "Incident notes",
      ],
    },
  },

  "safety-protection": {
    violence: {
      heading: "Your situation involves a serious safety concern.",
      introduction:
        "You indicated that someone has physically harmed or attacked you. Your immediate safety should come before collecting evidence or trying to resolve the situation alone.",
      rights: [
        "You can seek appropriate protection and support when you are unsafe.",
        "You do not need to confront the person involved before seeking help.",
        "Health, protection, legal or other specialised services may be relevant depending on what happened.",
      ],
      actions: [
        "Prioritise getting to a safer place where possible.",
        "Contact a trusted person or appropriate support service if it is safe to do so.",
        "Seek medical attention where needed.",
        "Avoid actions that could increase immediate danger.",
        "Preserve relevant information only when it is safe.",
      ],
      documents: [
        "Medical records where relevant",
        "Messages or call records",
        "Previous reports",
        "Photographs where safe and appropriate",
        "Names of witnesses",
        "A timeline of events",
      ],
    },

    threats: {
      heading: "Your situation appears to involve threats or intimidation.",
      introduction:
        "You indicated that someone is threatening or intimidating you. The seriousness and immediacy of those threats should guide what you do next.",
      rights: [
        "Threats to your safety should be taken seriously.",
        "You may seek help without confronting the person making the threats.",
        "Specialised protection or legal support may be appropriate.",
      ],
      actions: [
        "Consider whether you are currently somewhere safe.",
        "Tell a trusted person what is happening where appropriate.",
        "Keep threatening messages or other records if doing so is safe.",
        "Avoid direct confrontation where it could increase risk.",
        "Seek appropriate protection or professional support.",
      ],
      documents: [
        "Threatening messages",
        "Call records",
        "Relevant photographs",
        "Previous reports",
        "Names of witnesses",
        "Incident timeline",
      ],
    },

    harassment: {
      heading: "Your situation appears to involve harassment.",
      introduction:
        "Repeated unwanted behaviour can be difficult to navigate, especially where there is fear, pressure or a power imbalance.",
      rights: [
        "You can seek support when unwanted behaviour is affecting your safety or wellbeing.",
        "You do not need to handle persistent harassment alone.",
        "The appropriate reporting pathway may depend on where the harassment is happening.",
      ],
      actions: [
        "Keep a record of repeated incidents where safe.",
        "Preserve relevant messages or communication.",
        "Consider whether there is a trusted person or organisation you can contact.",
        "Avoid confrontation if it may make the situation more dangerous.",
        "Seek specialised support where needed.",
      ],
      documents: [
        "Messages",
        "Emails",
        "Call records",
        "Incident notes",
        "Previous complaints",
        "Names of witnesses",
      ],
    },

    abuse: {
      heading: "Your situation appears to involve abuse.",
      introduction:
        "Abuse within a personal or family relationship can involve safety, emotional wellbeing, finances, housing and other concerns at the same time.",
      rights: [
        "Your immediate safety is more important than completing an online process.",
        "You can seek confidential and specialised support.",
        "You should not be required to confront the person involved before seeking assistance.",
      ],
      actions: [
        "Consider where you can safely go if the situation becomes dangerous.",
        "Identify a trusted person where possible.",
        "Keep important documents accessible where safe.",
        "Avoid making a plan in a way that could increase danger if discovered.",
        "Seek appropriate specialised support.",
      ],
      documents: [
        "Important identification documents",
        "Relevant messages",
        "Medical records where applicable",
        "Previous reports",
        "Financial or household records where relevant",
        "Incident notes",
      ],
    },

    other: {
      heading: "You have identified another safety concern.",
      introduction:
        "Even if your situation does not fit the listed examples, concerns about personal safety deserve careful attention.",
      rights: [
        "You can seek support when you believe your safety may be at risk.",
        "You do not need to wait until a situation becomes more serious before asking for help.",
        "Different support services may be appropriate depending on what is happening.",
      ],
      actions: [
        "Consider whether you are currently safe.",
        "Identify someone you trust where possible.",
        "Write down what is happening only if doing so is safe.",
        "Avoid confrontation where it could increase danger.",
        "Seek appropriate specialised assistance.",
      ],
      documents: [
        "Relevant messages",
        "Call records",
        "Incident notes",
        "Previous reports",
        "Relevant documents",
        "Names of witnesses",
      ],
    },
  },

  "land-housing": {
    ownership: {
      heading: "Your situation appears to involve land or property ownership.",
      introduction:
        "Ownership disputes can depend heavily on documents, agreements, occupation history and the claims being made by each person involved.",
      rights: [
        "It is important to understand the basis on which each person claims an interest in the property.",
        "Property documents should be reviewed carefully before major decisions are made.",
        "You should avoid signing away an interest you do not fully understand.",
      ],
      actions: [
        "Gather the property documents you already have.",
        "Write down the history of the property and dispute.",
        "Record who is making competing claims.",
        "Avoid signing or surrendering documents you do not understand.",
        "Consider seeking specialised land or legal support.",
      ],
      documents: [
        "Land agreements",
        "Titles or certificates",
        "Receipts",
        "Survey information",
        "Letters or notices",
        "Relevant family or ownership records",
      ],
    },

    eviction: {
      heading: "Your situation appears to involve eviction.",
      introduction:
        "You indicated that you are being evicted or threatened with eviction. The type of property, your relationship to it and any notices or agreements may be important.",
      rights: [
        "Understanding who is seeking to remove you and why is an important starting point.",
        "Any tenancy, ownership or occupation records may be relevant.",
        "You should be cautious about signing documents or leaving important records behind when under pressure.",
      ],
      actions: [
        "Keep any eviction notice or communication you received.",
        "Record when and how you were told to leave.",
        "Gather tenancy, ownership or occupation records.",
        "Avoid physical confrontation.",
        "Seek appropriate land, housing or legal support promptly.",
      ],
      documents: [
        "Eviction notices",
        "Tenancy agreements",
        "Land agreements",
        "Receipts",
        "Property documents",
        "Messages or letters",
      ],
    },

    boundary: {
      heading: "Your situation appears to involve a boundary dispute.",
      introduction:
        "Boundary disputes often require a clear understanding of the property, existing records and what each person believes the boundary to be.",
      rights: [
        "Property records and survey information may be important.",
        "Informal assumptions about boundaries can differ from documented information.",
        "Escalating a boundary disagreement physically can make resolution more difficult.",
      ],
      actions: [
        "Gather available maps, agreements or survey information.",
        "Record the area being disputed.",
        "Keep relevant communication with neighbours or other parties.",
        "Avoid moving markers or escalating the dispute without appropriate guidance.",
        "Seek specialised support where necessary.",
      ],
      documents: [
        "Survey documents",
        "Maps",
        "Titles or certificates",
        "Land agreements",
        "Photographs",
        "Relevant correspondence",
      ],
    },

    tenancy: {
      heading: "Your situation appears to involve a landlord or tenant issue.",
      introduction:
        "Rental disputes may involve payment, property conditions, agreements, notices or the responsibilities of the people involved.",
      rights: [
        "The terms of the rental arrangement are an important starting point.",
        "Receipts and communication may help clarify what was agreed.",
        "You should keep records of notices, payments and major disputes.",
      ],
      actions: [
        "Review your tenancy or rental agreement if you have one.",
        "Keep proof of rent or other payments.",
        "Record the specific problem and when it began.",
        "Keep notices and communication.",
        "Seek support if the issue cannot be resolved safely and reasonably.",
      ],
      documents: [
        "Tenancy agreement",
        "Rent receipts",
        "Mobile money or bank records",
        "Notices",
        "Messages",
        "Photographs where relevant",
      ],
    },

    documents: {
      heading: "Your situation appears to involve property documents.",
      introduction:
        "When a dispute concerns documents, it is important to understand what each document is, who issued it and what it actually says before relying on it.",
      rights: [
        "You should avoid signing property documents you do not understand.",
        "Different property documents may have different purposes.",
        "Qualified assistance may be useful before major property decisions are made.",
      ],
      actions: [
        "Keep the original documents somewhere safe.",
        "Make copies where appropriate.",
        "Write down how and when you received the documents.",
        "Do not alter original records.",
        "Seek qualified help to understand documents that affect important property rights.",
      ],
      documents: [
        "Titles",
        "Certificates",
        "Land agreements",
        "Receipts",
        "Survey records",
        "Letters or notices",
      ],
    },

    other: {
      heading: "Your situation involves another land or housing concern.",
      introduction:
        "Land and housing problems can take many forms. Organising the facts and records can make it easier to identify appropriate help.",
      rights: [
        "You can seek information before making important property decisions.",
        "Documents and occupation history may be relevant.",
        "You should avoid signing documents you do not understand.",
      ],
      actions: [
        "Write down what happened.",
        "Identify the property involved.",
        "Collect available records.",
        "Avoid escalating the dispute physically.",
        "Seek appropriate land or legal support.",
      ],
      documents: [
        "Property records",
        "Agreements",
        "Receipts",
        "Notices",
        "Messages",
        "Relevant photographs",
      ],
    },
  },

  "family-inheritance": {
    inheritance: {
      heading: "Your situation appears to involve inheritance.",
      introduction:
        "Inheritance concerns may involve family relationships, property, documents and decisions made after someone has died.",
      rights: [
        "It is important to identify the property and people involved before major decisions are made.",
        "Wills, succession documents and property records may be important.",
        "You should avoid signing away an interest you do not understand.",
      ],
      actions: [
        "Gather available succession and property documents.",
        "Write down the family relationship of the people involved.",
        "Identify the property or assets in dispute.",
        "Keep records of important family discussions or decisions.",
        "Seek appropriate legal or mediation support where necessary.",
      ],
      documents: [
        "Will where one exists",
        "Death certificate",
        "Succession documents",
        "Property documents",
        "Family records",
        "Relevant correspondence",
      ],
    },

    children: {
      heading: "Your situation appears to involve children or family responsibilities.",
      introduction:
        "Situations involving children can affect several people and should be approached carefully with the child's wellbeing in mind.",
      rights: [
        "Decisions affecting children require careful consideration of their wellbeing.",
        "Family responsibilities may involve both practical and legal questions.",
        "Specialised family, legal or social-support services may sometimes be appropriate.",
      ],
      actions: [
        "Write down the specific issue affecting the child.",
        "Keep important child-related records.",
        "Avoid involving children unnecessarily in adult disputes.",
        "Record existing care or support arrangements.",
        "Seek appropriate family or professional support where needed.",
      ],
      documents: [
        "Birth certificates",
        "School records where relevant",
        "Medical records where relevant",
        "Family agreements",
        "Relevant correspondence",
        "Support or payment records",
      ],
    },

    marriage: {
      heading: "Your situation appears to involve marriage or separation.",
      introduction:
        "Relationship changes can involve family responsibilities, property, finances, children and personal safety.",
      rights: [
        "It can be helpful to understand your situation before making major agreements or property decisions.",
        "Family and property questions may require different forms of support.",
        "Safety should take priority where the relationship involves threats or abuse.",
      ],
      actions: [
        "Identify the specific issues you need help with.",
        "Keep important family and financial documents.",
        "Avoid signing agreements you do not understand.",
        "Consider whether mediation or professional support is appropriate.",
        "Prioritise safety where there is abuse or intimidation.",
      ],
      documents: [
        "Marriage-related documents",
        "Property records",
        "Financial records",
        "Children's documents where relevant",
        "Written agreements",
        "Relevant correspondence",
      ],
    },

    property: {
      heading: "Your situation appears to involve family property or money.",
      introduction:
        "Family property disputes can become complicated when ownership, contributions and informal agreements are unclear.",
      rights: [
        "Understanding who owns or contributed to property is an important starting point.",
        "Documents and payment records may help clarify the history.",
        "You should avoid making irreversible decisions under pressure.",
      ],
      actions: [
        "Identify the property or money involved.",
        "Collect relevant ownership and payment records.",
        "Write down important agreements or discussions.",
        "Avoid signing documents you do not understand.",
        "Seek appropriate family, mediation or legal support.",
      ],
      documents: [
        "Property documents",
        "Payment records",
        "Bank or mobile money records",
        "Family agreements",
        "Receipts",
        "Relevant correspondence",
      ],
    },

    other: {
      heading: "Your situation involves another family concern.",
      introduction:
        "Family situations do not always fit neatly into one category. Organising the issue can still help identify an appropriate next step.",
      rights: [
        "You can seek information before making major family decisions.",
        "Sensitive family issues may require different forms of support.",
        "Safety and privacy should be considered where appropriate.",
      ],
      actions: [
        "Write down the main issue.",
        "Identify the people and decisions involved.",
        "Collect relevant records.",
        "Consider what outcome you are hoping for.",
        "Seek appropriate support where needed.",
      ],
      documents: [
        "Family records",
        "Agreements",
        "Property records",
        "Messages",
        "Financial records",
        "Relevant official documents",
      ],
    },
  },

  "public-services": {
    access: {
      heading: "Your situation appears to involve access to a public service.",
      introduction:
        "You indicated that you are having difficulty accessing a service you need.",
      rights: [
        "Understanding the requirements for the service is an important starting point.",
        "You may ask what documents or steps are required.",
        "Records of applications and visits can help when seeking further assistance.",
      ],
      actions: [
        "Identify the exact service and office involved.",
        "Ask what requirements apply.",
        "Keep copies of forms and documents submitted.",
        "Record visits, calls and reference numbers.",
        "Seek assistance if you cannot identify the appropriate process.",
      ],
      documents: [
        "Application forms",
        "Reference numbers",
        "Receipts",
        "Official letters",
        "Identification documents where relevant",
        "Records of visits or calls",
      ],
    },

    decision: {
      heading: "Your situation appears to involve a public decision.",
      introduction:
        "You indicated that an institution made a decision you do not understand or agree with.",
      rights: [
        "Understanding what decision was made and the reason given is an important starting point.",
        "There may be complaint, review or clarification processes depending on the institution.",
        "Written records can help when asking another person or organisation for assistance.",
      ],
      actions: [
        "Keep the decision or notice you received.",
        "Ask for clarification where appropriate.",
        "Record relevant dates and reference numbers.",
        "Check whether the institution has a complaint or review process.",
        "Seek further support if you cannot navigate the process.",
      ],
      documents: [
        "Decision letters",
        "Notices",
        "Application records",
        "Reference numbers",
        "Emails or messages",
        "Receipts",
      ],
    },

    delay: {
      heading: "Your situation appears to involve a delay or lack of response.",
      introduction:
        "You indicated that a public institution has delayed or has not responded to your matter.",
      rights: [
        "Keeping a record of when you submitted or requested something can be important.",
        "Reference numbers and receipts can help establish the history of the matter.",
        "Escalation or complaint processes may exist depending on the institution.",
      ],
      actions: [
        "Record when the matter was first submitted.",
        "Keep reference numbers and receipts.",
        "Follow up through the official channel where possible.",
        "Record each follow-up attempt.",
        "Consider an appropriate complaint or support pathway if the delay continues.",
      ],
      documents: [
        "Reference numbers",
        "Receipts",
        "Applications",
        "Emails",
        "Letters",
        "Follow-up records",
      ],
    },

    treatment: {
      heading: "Your situation appears to involve unfair treatment by a public institution.",
      introduction:
        "You indicated that you believe you were treated unfairly while dealing with a public service or institution.",
      rights: [
        "It can be useful to distinguish the service decision from the way you were treated.",
        "Complaint processes may be available depending on the institution.",
        "Detailed records can help explain what happened.",
      ],
      actions: [
        "Write down what happened and when.",
        "Record the office or institution involved.",
        "Keep relevant documents.",
        "Identify witnesses where appropriate.",
        "Consider using an appropriate complaint or support process.",
      ],
      documents: [
        "Official documents",
        "Messages",
        "Receipts",
        "Complaint records",
        "Incident notes",
        "Names of witnesses",
      ],
    },

    complaint: {
      heading: "You want to understand how to make a complaint.",
      introduction:
        "The appropriate complaint pathway usually depends on the institution and the decision, service or conduct involved.",
      rights: [
        "It is useful to identify exactly what you are complaining about.",
        "Existing reference numbers and correspondence may help the institution trace the matter.",
        "Keeping a copy of your complaint can help if further follow-up becomes necessary.",
      ],
      actions: [
        "Identify the institution responsible.",
        "Write a short factual summary of the issue.",
        "Include important dates and reference numbers.",
        "Keep a copy of anything you submit.",
        "Record when and where the complaint was submitted.",
      ],
      documents: [
        "Complaint letter",
        "Reference numbers",
        "Receipts",
        "Previous correspondence",
        "Decision notices",
        "Supporting documents",
      ],
    },

    other: {
      heading: "Your situation involves another public-service concern.",
      introduction:
        "Public-service issues can vary widely. Identifying the institution, decision and history of the matter can help clarify what to do next.",
      rights: [
        "You can seek information about the process affecting you.",
        "Records may help when asking for clarification or support.",
        "Different institutions may have different complaint or review processes.",
      ],
      actions: [
        "Identify the institution involved.",
        "Write down what happened.",
        "Keep relevant documents and reference numbers.",
        "Ask what process applies where appropriate.",
        "Seek further support if necessary.",
      ],
      documents: [
        "Official correspondence",
        "Applications",
        "Receipts",
        "Reference numbers",
        "Messages",
        "Incident notes",
      ],
    },
  },

  "community-discrimination": {
    discrimination: {
      heading: "Your situation appears to involve discrimination.",
      introduction:
        "You indicated that you believe you were treated differently or unfairly because of who you are or how you were perceived.",
      rights: [
        "Unfair treatment can raise important rights concerns depending on what happened and where it occurred.",
        "The setting and reason for the treatment may be important.",
        "You can seek appropriate support before deciding whether to report the issue.",
      ],
      actions: [
        "Write down exactly what happened.",
        "Record when and where it occurred.",
        "Keep relevant messages or documents.",
        "Identify witnesses where appropriate.",
        "Consider an appropriate complaint or support pathway.",
      ],
      documents: [
        "Messages",
        "Emails",
        "Relevant policies",
        "Complaint records",
        "Incident notes",
        "Names of witnesses",
      ],
    },

    excluded: {
      heading: "Your situation appears to involve unfair exclusion.",
      introduction:
        "You indicated that you were excluded from something in a way you believe was unfair.",
      rights: [
        "Understanding what you were excluded from and why is an important starting point.",
        "Rules, policies or decisions relating to the exclusion may be relevant.",
        "You can seek clarification or support where appropriate.",
      ],
      actions: [
        "Record what you were excluded from.",
        "Write down any reason you were given.",
        "Keep relevant policies or communication.",
        "Identify who made the decision.",
        "Consider whether a complaint or review process exists.",
      ],
      documents: [
        "Policies",
        "Notices",
        "Messages",
        "Emails",
        "Complaint records",
        "Decision records",
      ],
    },

    harassment: {
      heading: "Your situation appears to involve harassment or degrading treatment.",
      introduction:
        "You indicated that you experienced unwanted, repeated or degrading treatment.",
      rights: [
        "You can seek support where behaviour is affecting your safety, dignity or ability to participate.",
        "You do not necessarily need to confront the person directly before asking for help.",
        "The appropriate pathway may depend on where the behaviour occurred.",
      ],
      actions: [
        "Keep a record of incidents where safe.",
        "Preserve relevant messages or communication.",
        "Identify witnesses where appropriate.",
        "Consider the complaint process in the relevant setting.",
        "Seek support if direct reporting feels unsafe.",
      ],
      documents: [
        "Messages",
        "Emails",
        "Incident notes",
        "Complaint records",
        "Relevant policies",
        "Names of witnesses",
      ],
    },

    community: {
      heading: "Your situation appears to involve a community decision or action.",
      introduction:
        "You indicated that a community decision or action is affecting you in a way you believe is unfair.",
      rights: [
        "Understanding who made the decision and how it affects you is an important first step.",
        "Community processes may sometimes have mechanisms for discussion, review or support.",
        "Safety should be considered where raising the issue directly could cause harm.",
      ],
      actions: [
        "Write down the decision or action affecting you.",
        "Identify who was involved.",
        "Keep relevant notices or communication.",
        "Record any attempts you have made to resolve the issue.",
        "Seek outside support where direct engagement is unsafe or ineffective.",
      ],
      documents: [
        "Community notices",
        "Messages",
        "Meeting records",
        "Complaint records",
        "Relevant policies",
        "Incident notes",
      ],
    },

    other: {
      heading: "Your situation involves another community concern.",
      introduction:
        "Your experience may not fit neatly into the listed examples, but documenting what happened can still help identify appropriate support.",
      rights: [
        "You can seek information and support where you believe you have been treated unfairly.",
        "The setting and people involved may help determine the appropriate pathway.",
        "Safety and privacy should be considered before reporting sensitive concerns.",
      ],
      actions: [
        "Write down what happened.",
        "Record where and when it occurred.",
        "Keep relevant communication.",
        "Identify witnesses where appropriate.",
        "Seek suitable support if needed.",
      ],
      documents: [
        "Messages",
        "Notices",
        "Incident notes",
        "Complaint records",
        "Relevant policies",
        "Names of witnesses",
      ],
    },
  },
};

function getStoredAnswers(
  category: CategorySlug,
): JourneyAnswers {
  try {
    const stored = sessionStorage.getItem(
      getJourneyStorageKey(category),
    );

    if (!stored) {
      return {};
    }

    return JSON.parse(stored) as JourneyAnswers;
  } catch {
    return {};
  }
}

function getPrimaryIssue(
  category: CategorySlug,
  answers: JourneyAnswers,
) {
  switch (category) {
    case "work-employment":
      return answers["work-issue"];

    case "safety-protection":
      return answers["safety-issue"];

    case "land-housing":
      return answers["land-issue"];

    case "family-inheritance":
      return answers["family-issue"];

    case "public-services":
      return answers["service-issue"];

    case "community-discrimination":
      return answers["community-issue"];
  }
}

function ResultList({
  items,
}: {
  items: string[];
}) {
  return (
    <div className="mt-6 space-y-4">
      {items.map((item) => (
        <div
          key={item}
          className="flex items-start gap-3"
        >
          <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-gold" />

          <p className="text-sm leading-6 text-text-secondary sm:text-base">
            {item}
          </p>
        </div>
      ))}
    </div>
  );
}

export default function RightsResults() {
  const { category } = useParams();

  const [
    backendSituation,
    setBackendSituation,
  ] = useState<Situation | null>(null);

  const [
    backendLoading,
    setBackendLoading,
  ] = useState(false);

  const rightsCategory = getRightsCategory(category);

  const backendAnswers =
    rightsCategory
      ? getStoredAnswers(
          rightsCategory.slug,
        )
      : {};

  const backendPrimaryIssue =
    rightsCategory
      ? getPrimaryIssue(
          rightsCategory.slug,
          backendAnswers,
        )
      : null;

  const backendSituationSlug = (() => {
    if (!rightsCategory) {
      return null;
    }

    if (
      rightsCategory.slug ===
      "work-employment"
    ) {
      return "problem-at-work";
    }

    if (
      rightsCategory.slug ===
        "land-housing" &&
      backendPrimaryIssue ===
        "eviction"
    ) {
      return "facing-eviction";
    }

    if (
      rightsCategory.slug ===
      "safety-protection"
    ) {
      if (
        backendPrimaryIssue ===
        "harassment"
      ) {
        return "sexual-harassment";
      }

      if (
        backendPrimaryIssue ===
          "violence" ||
        backendPrimaryIssue ===
          "abuse"
      ) {
        return "domestic-violence";
      }
    }

    return null;
  })();

  useEffect(() => {
    if (!backendSituationSlug) {
      setBackendSituation(null);
      return;
    }

    const activeSituationSlug =
      backendSituationSlug;

    let active = true;

    async function loadBackendRights() {
      setBackendLoading(true);

      try {
        const situation =
          await getSituation(
            activeSituationSlug,
          );

        if (active) {
          setBackendSituation(
            situation,
          );
        }
      } catch {
        if (active) {
          setBackendSituation(
            null,
          );
        }
      } finally {
        if (active) {
          setBackendLoading(false);
        }
      }
    }

    void loadBackendRights();

    return () => {
      active = false;
    };
  }, [backendSituationSlug]);

  if (!rightsCategory) {
    return <Navigate to="/rights" replace />;
  }

  const answers = getStoredAnswers(
    rightsCategory.slug,
  );

  const primaryIssue = getPrimaryIssue(
    rightsCategory.slug,
    answers,
  );

  if (
    !primaryIssue ||
    !issueResults[rightsCategory.slug][
      primaryIssue
    ]
  ) {
    return (
      <Navigate
        to={`/rights/${rightsCategory.slug}/start`}
        replace
      />
    );
  }

  const result =
    issueResults[rightsCategory.slug][
      primaryIssue
    ];

  const backendTopic =
    backendSituation
      ?.rights_links?.[0]
      ?.rights_topic ?? null;

  const backendActions =
    backendTopic?.action_steps
      ?.filter(
        (step) => step.is_active,
      )
      .map(
        (step) =>
          step.description ||
          step.title,
      ) ?? [];

  const backendSafetyResponses =
    backendTopic?.safety_responses
      ?.filter(
        (response) =>
          response.is_active,
      ) ?? [];


  const backendLegalProvisions =
    backendTopic?.legal_provisions
      ?.filter(
        (provision) =>
          provision.is_active,
      )
      .sort(
        (a, b) =>
          a.order - b.order,
      ) ?? [];

  const Icon = rightsCategory.icon;

  const immediateSafetyConcern =
    rightsCategory.slug ===
      "safety-protection" &&
    (answers["safety-now"] === "yes" ||
      answers["safety-now"] === "maybe");

  const unsafeToRaise =
    answers["work-action"] === "unsafe" ||
    answers["community-action"] === "unsafe";

  return (
    <>
      {/* SAFETY PRIORITY */}
      {immediateSafetyConcern && (
        <section className="bg-[#1c1c1c] text-white">
          <div className="site-container py-8 sm:py-10">
            <div className="flex max-w-4xl items-start gap-4">
              <AlertTriangle className="mt-1 h-6 w-6 shrink-0 text-gold" />

              <div>
                <p className="text-xs font-bold uppercase tracking-[0.18em] text-gold">
                  Safety comes first
                </p>

                <h2 className="heading-serif mt-2 text-2xl font-semibold sm:text-3xl">
                  You told us you may not be safe
                  right now.
                </h2>

                <p className="mt-3 max-w-2xl text-sm leading-6 text-white/70 sm:text-base">
                  Do not delay urgent assistance in
                  order to continue using Sauti Yo.
                  Where possible, prioritise reaching
                  a safer place, trusted person or
                  appropriate emergency or protection
                  service.
                </p>
              </div>
            </div>
          </div>
        </section>
      )}

      {backendTopic && (
        <section className="border-b border-border bg-surface">
          <div className="site-container py-4">
            <div className="flex flex-wrap items-center gap-3 text-xs">
              <span className="font-bold uppercase tracking-[0.14em] text-gold-deep dark:text-gold">
                Backend rights content status
              </span>

              <span className="text-text-secondary">
                {backendTopic.title}
              </span>

              <span className="border border-border px-2 py-1 font-semibold text-text-secondary">
                {backendTopic.verification_status ===
                "verified"
                  ? "Verified"
                  : "Review required"}
              </span>
            </div>

            {backendLoading && (
              <p className="mt-2 text-xs text-text-secondary">
                Loading reviewed rights information...
              </p>
            )}

            {backendSafetyResponses.length > 0 && (
              <div className="mt-3 space-y-2">
                {backendSafetyResponses.map(
                  (response) => (
                    <p
                      key={response.id}
                      className="text-sm leading-6 text-text-secondary"
                    >
                      {response.message}
                    </p>
                  ),
                )}
              </div>
            )}
          </div>
        </section>
      )}

      {/* RESULT HERO */}
      <section className="bg-background py-14 sm:py-16 lg:py-20">
        <div className="site-container">
          <Link
            to={`/rights/${rightsCategory.slug}/start`}
            className="inline-flex items-center gap-2 text-sm font-semibold text-text-secondary transition hover:text-gold"
          >
            <ArrowLeft className="h-4 w-4" />
            Review my answers
          </Link>

          <div className="mt-10 grid gap-10 lg:grid-cols-[0.72fr_1.28fr] lg:items-end lg:gap-16">
            <div>
              <div className="flex h-14 w-14 items-center justify-center rounded-full bg-gold/10 text-gold">
                <Icon
                  className="h-7 w-7"
                  strokeWidth={1.6}
                />
              </div>

              <div className="mt-7 flex items-center gap-3">
                <span className="gold-rule" />

                <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                  Based on your answers
                </p>
              </div>

              <p className="mt-4 text-sm font-semibold text-text-secondary">
                {rightsCategory.title}
              </p>
            </div>

            <div className="max-w-2xl">
              <h1 className="heading-serif text-3xl font-semibold leading-tight text-text-primary sm:text-4xl lg:text-5xl">
                {result.heading}
              </h1>

              <p className="mt-6 text-base leading-7 text-text-secondary sm:text-lg sm:leading-8">
                {result.introduction}
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CONTEXT */}
      <section className="border-y border-border bg-surface-soft">
        <div className="site-container py-7">
          <div className="flex max-w-4xl items-start gap-3">
            <Info className="mt-0.5 h-5 w-5 shrink-0 text-gold" />

            <p className="text-sm leading-6 text-text-secondary">
              This result is based on the answers
              you selected and provides general
              information and practical guidance.
              It is not a legal determination about
              your individual case.
            </p>
          </div>
        </div>
      </section>

      {/* UNSAFE TO RAISE */}
      {unsafeToRaise && (
        <section className="bg-background">
          <div className="site-container pt-10">
            <div className="max-w-4xl border-l-2 border-gold bg-gold/5 p-5 sm:p-6">
              <div className="flex items-start gap-4">
                <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-gold" />

                <div>
                  <h2 className="font-semibold text-text-primary">
                    You told us that raising this
                    directly may not feel safe.
                  </h2>

                  <p className="mt-2 text-sm leading-6 text-text-secondary">
                    Do not put yourself at risk
                    simply to follow a suggested
                    step. An independent support
                    organisation may be a more
                    appropriate starting point.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* UNDERSTAND */}
      <section className="section-padding bg-surface">
        <div className="site-container">
          <div className="grid gap-12 lg:grid-cols-[0.72fr_1.28fr] lg:gap-20">
            <div>
              <BookOpen
                className="h-7 w-7 text-gold"
                strokeWidth={1.6}
              />

              <div className="mt-5 flex items-center gap-3">
                <span className="gold-rule" />

                <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                  Understand
                </p>
              </div>

              <h2 className="heading-serif mt-5 text-3xl font-semibold leading-tight text-text-primary sm:text-4xl">
                Things worth
                <span className="block text-gold-deep dark:text-gold">
                  understanding first.
                </span>
              </h2>

              <p className="mt-5 max-w-md text-base leading-7 text-text-secondary">
                These points can help you organise
                the issue before deciding what to do
                next.
              </p>
            </div>

            <ResultList items={result.rights} />
          </div>
        </div>
      </section>

      {/* LEGAL BASIS */}
      {backendLegalProvisions.length > 0 && (
        <section className="section-padding border-y border-border bg-surface-soft">
          <div className="site-container">
            <div className="grid gap-12 lg:grid-cols-[0.72fr_1.28fr] lg:gap-20">
              <div>
                <BookOpen
                  className="h-7 w-7 text-gold"
                  strokeWidth={1.6}
                />

                <div className="mt-5 flex items-center gap-3">
                  <span className="gold-rule" />

                  <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                    Legal basis
                  </p>
                </div>

                <h2 className="heading-serif mt-5 text-3xl font-semibold leading-tight text-text-primary sm:text-4xl">
                  Where this information
                  <span className="block text-gold-deep dark:text-gold">
                    comes from.
                  </span>
                </h2>

                <p className="mt-5 max-w-md text-base leading-7 text-text-secondary">
                  These references connect the guidance
                  to Ugandan law. Content marked review
                  required has not yet received final
                  legal-review approval.
                </p>
              </div>

              <div className="space-y-5">
                {backendLegalProvisions.map(
                  (provision) => (
                    <article
                      key={provision.id}
                      className="border border-border bg-surface p-5 sm:p-6"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <p className="text-xs font-bold uppercase tracking-[0.14em] text-gold-deep dark:text-gold">
                          {provision.source_type.replace(
                            "_",
                            " ",
                          )}
                        </p>

                        <span className="border border-border px-2 py-1 text-xs font-semibold text-text-secondary">
                          {provision.verification_status ===
                          "verified"
                            ? "Verified"
                            : "Review required"}
                        </span>
                      </div>

                      <h3 className="mt-4 text-lg font-semibold text-text-primary">
                        {provision.law_title}
                      </h3>

                      <p className="mt-1 font-semibold text-gold-deep dark:text-gold">
                        {provision.provision_reference}
                      </p>

                      {provision.provision_heading && (
                        <p className="mt-2 text-sm font-medium text-text-primary">
                          {provision.provision_heading}
                        </p>
                      )}

                      <p className="mt-4 text-sm leading-6 text-text-secondary">
                        {
                          provision.plain_language_explanation
                        }
                      </p>

                      {provision.source_url && (
                        <a
                          href={provision.source_url}
                          target="_blank"
                          rel="noreferrer"
                          className="mt-5 inline-flex text-sm font-semibold text-gold-deep underline underline-offset-4 dark:text-gold"
                        >
                          View legal source
                        </a>
                      )}
                    </article>
                  ),
                )}
              </div>
            </div>
          </div>
        </section>
      )}

      {/* ACT */}
      <section className="section-padding bg-background">
        <div className="site-container">
          <div className="grid gap-12 lg:grid-cols-[0.72fr_1.28fr] lg:gap-20">
            <div>
              <Scale
                className="h-7 w-7 text-gold"
                strokeWidth={1.6}
              />

              <div className="mt-5 flex items-center gap-3">
                <span className="gold-rule" />

                <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                  Act
                </p>
              </div>

              <h2 className="heading-serif mt-5 text-3xl font-semibold leading-tight text-text-primary sm:text-4xl">
                Practical things
                <span className="block text-gold-deep dark:text-gold">
                  to consider next.
                </span>
              </h2>

              <p className="mt-5 max-w-md text-base leading-7 text-text-secondary">
                Not every step will apply to every
                person. Choose only the steps that
                are appropriate and safe for your
                circumstances.
              </p>
            </div>

            <ResultList items={backendActions.length > 0 ? backendActions : result.actions} />
          </div>
        </div>
      </section>

      {/* DOCUMENTS */}
      <section className="section-padding bg-surface-soft">
        <div className="site-container">
          <div className="grid gap-12 lg:grid-cols-[0.72fr_1.28fr] lg:gap-20">
            <div>
              <FileText
                className="h-7 w-7 text-gold"
                strokeWidth={1.6}
              />

              <div className="mt-5 flex items-center gap-3">
                <span className="gold-rule" />

                <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                  Keep useful information
                </p>
              </div>

              <h2 className="heading-serif mt-5 text-3xl font-semibold leading-tight text-text-primary sm:text-4xl">
                Records that may
                <span className="block text-gold-deep dark:text-gold">
                  help explain your situation.
                </span>
              </h2>

              <p className="mt-5 max-w-md text-base leading-7 text-text-secondary">
                You do not need every item listed
                here. Preserve what already exists,
                and never put yourself at risk
                simply to collect evidence.
              </p>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              {result.documents.map((document) => (
                <div
                  key={document}
                  className="flex items-start gap-3 border border-border bg-surface p-5"
                >
                  <ClipboardList className="mt-0.5 h-5 w-5 shrink-0 text-gold" />

                  <p className="text-sm leading-6 text-text-secondary">
                    {document}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* SUPPORT */}
      <section className="section-padding bg-surface">
        <div className="site-container">
          <div className="grid items-center gap-12 border-y border-border py-12 lg:grid-cols-[0.75fr_1.25fr] lg:gap-20 lg:py-16">
            <div>
              <Building2
                className="h-7 w-7 text-gold"
                strokeWidth={1.6}
              />

              <h2 className="heading-serif mt-5 text-3xl font-semibold leading-tight text-text-primary sm:text-4xl">
                Information may not
                <span className="block text-gold-deep dark:text-gold">
                  be enough.
                </span>
              </h2>
            </div>

            <div>
              <p className="max-w-xl text-base leading-7 text-text-secondary">
                If you need more help, Sauti Yo can
                guide you toward an appropriate
                support pathway based on the type of
                issue you selected.
              </p>

              <p className="mt-4 max-w-xl text-sm leading-6 text-text-secondary">
                As the Sauti Yo partner network
                develops, verified organisations can
                become part of this referral pathway.
              </p>

              <Link
                to={`/support?category=${rightsCategory.slug}`}
                className="btn-primary mt-7"
              >
                Find Relevant Support

                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* FINAL CTA */}
      <section className="bg-[#1c1c1c] text-white">
        <div className="site-container py-16 sm:py-20">
          <div className="grid gap-8 lg:grid-cols-[1fr_auto] lg:items-center">
            <div className="max-w-3xl">
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold">
                Know. Act. Be Heard.
              </p>

              <h2 className="heading-serif mt-4 text-3xl font-semibold leading-tight sm:text-4xl lg:text-5xl">
                You now have a clearer
                <span className="block text-gold">
                  place to start.
                </span>
              </h2>

              <p className="mt-5 max-w-2xl text-base leading-7 text-white/65">
                Review the information, choose the
                next step that makes sense for you
                and seek appropriate support where
                needed.
              </p>
            </div>

            <Link
              to="/rights"
              className="inline-flex min-h-12 w-full items-center justify-center gap-2 border border-gold px-7 py-3 font-semibold text-gold transition hover:bg-gold hover:text-[#191919] sm:w-auto"
            >
              Explore Another Situation

              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}