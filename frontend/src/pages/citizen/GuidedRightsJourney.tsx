import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  BriefcaseBusiness,
  Check,
  HeartHandshake,
  Home,
  Landmark,
  ShieldCheck,
  Users,
} from "lucide-react";
import { useMemo, useState } from "react";
import { Link, Navigate, useParams } from "react-router-dom";

type CategorySlug =
  | "work-employment"
  | "safety-protection"
  | "land-housing"
  | "family-inheritance"
  | "public-services"
  | "community-discrimination";

type Answer = {
  id: string;
  label: string;
};

type Question = {
  id: string;
  eyebrow: string;
  title: string;
  description?: string;
  answers: Answer[];
};

type CategoryJourney = {
  title: string;
  icon: typeof BriefcaseBusiness;
  intro: string;
  questions: Question[];
};

const journeys: Record<CategorySlug, CategoryJourney> = {
  "work-employment": {
    title: "Work & Employment",
    icon: BriefcaseBusiness,
    intro:
      "A few simple questions can help us understand what kind of workplace situation you are dealing with.",
    questions: [
      {
        id: "work-issue",
        eyebrow: "Your situation",
        title: "What happened at work?",
        description: "Choose the option that feels closest.",
        answers: [
          {
            id: "unpaid",
            label: "I have not been paid or there is a problem with my pay.",
          },
          {
            id: "dismissed",
            label: "I was dismissed, suspended or told to stop working.",
          },
          {
            id: "treatment",
            label: "I am being treated unfairly or badly at work.",
          },
          {
            id: "contract",
            label: "I have a question or problem involving my contract.",
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
            label: "I am not sure how my work arrangement is classified.",
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
            label: "Yes, I spoke to my employer or supervisor.",
          },
          {
            id: "organisation",
            label: "Yes, I contacted another organisation or authority.",
          },
          {
            id: "nothing",
            label: "No, I have not taken any action yet.",
          },
          {
            id: "unsafe",
            label: "I do not feel safe raising the issue directly.",
          },
        ],
      },
    ],
  },

  "safety-protection": {
    title: "Safety & Protection",
    icon: ShieldCheck,
    intro:
      "We will begin with safety before looking at other information or possible next steps.",
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
            label: "I am not sure, but I am worried about my safety.",
          },
          {
            id: "no",
            label: "No, I am not in immediate danger right now.",
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
            label: "Someone has physically harmed or attacked me.",
          },
          {
            id: "threats",
            label: "Someone is threatening or intimidating me.",
          },
          {
            id: "harassment",
            label: "I am experiencing harassment or repeated unwanted behaviour.",
          },
          {
            id: "abuse",
            label: "I am experiencing abuse in a personal or family situation.",
          },
          {
            id: "other",
            label: "It is another kind of safety concern.",
          },
        ],
      },
      {
        id: "safety-support",
        eyebrow: "Support",
        title: "Do you have someone or somewhere you trust for support?",
        answers: [
          {
            id: "person",
            label: "Yes, there is someone I trust.",
          },
          {
            id: "organisation",
            label: "Yes, I know an organisation or service I can contact.",
          },
          {
            id: "no",
            label: "No, I am not sure who I can turn to.",
          },
        ],
      },
    ],
  },

  "land-housing": {
    title: "Land & Housing",
    icon: Home,
    intro:
      "Tell us a little about the land or housing situation so we can organise the information more clearly.",
    questions: [
      {
        id: "land-issue",
        eyebrow: "Your situation",
        title: "What is the main issue?",
        answers: [
          {
            id: "ownership",
            label: "There is a disagreement about ownership.",
          },
          {
            id: "eviction",
            label: "I am being evicted or threatened with eviction.",
          },
          {
            id: "boundary",
            label: "There is a boundary or neighbouring land dispute.",
          },
          {
            id: "tenancy",
            label: "The issue involves a landlord, tenant or rental arrangement.",
          },
          {
            id: "documents",
            label: "The issue involves land or property documents.",
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
        title: "What is your relationship to the property?",
        answers: [
          {
            id: "owner",
            label: "I believe I own or have rights to the property.",
          },
          {
            id: "tenant",
            label: "I am a tenant or renter.",
          },
          {
            id: "family",
            label: "The property belongs to or is shared within my family.",
          },
          {
            id: "occupant",
            label: "I live or work there but ownership is unclear.",
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
        title: "Do you have documents related to the property?",
        answers: [
          {
            id: "yes",
            label: "Yes, I have documents.",
          },
          {
            id: "some",
            label: "I have some documents, but I am not sure what they mean.",
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

  "family-inheritance": {
    title: "Family & Inheritance",
    icon: HeartHandshake,
    intro:
      "Family situations can be sensitive. These questions help organise the issue without asking you to share unnecessary personal details.",
    questions: [
      {
        id: "family-issue",
        eyebrow: "Your situation",
        title: "What does the issue mainly involve?",
        answers: [
          {
            id: "inheritance",
            label: "Inheritance or property after someone has died.",
          },
          {
            id: "children",
            label: "Children, care or family responsibilities.",
          },
          {
            id: "marriage",
            label: "Marriage, separation or another relationship issue.",
          },
          {
            id: "property",
            label: "Property or money within the family.",
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
        title: "Is there currently a disagreement or dispute?",
        answers: [
          {
            id: "yes",
            label: "Yes, there is an active disagreement.",
          },
          {
            id: "starting",
            label: "A disagreement may be developing.",
          },
          {
            id: "no",
            label: "No, I mainly want to understand my rights.",
          },
        ],
      },
      {
        id: "family-support",
        eyebrow: "Support",
        title: "Have you already asked anyone for help?",
        answers: [
          {
            id: "family",
            label: "Yes, I have spoken with family or community members.",
          },
          {
            id: "professional",
            label: "Yes, I have contacted a professional or organisation.",
          },
          {
            id: "no",
            label: "No, I have not asked for help yet.",
          },
        ],
      },
    ],
  },

  "public-services": {
    title: "Public Services",
    icon: Landmark,
    intro:
      "Tell us what happened when you tried to access or deal with a public institution or service.",
    questions: [
      {
        id: "service-issue",
        eyebrow: "Your situation",
        title: "What best describes the problem?",
        answers: [
          {
            id: "access",
            label: "I cannot access a service I need.",
          },
          {
            id: "decision",
            label: "A decision was made that I do not understand or agree with.",
          },
          {
            id: "delay",
            label: "There has been an unreasonable delay or no response.",
          },
          {
            id: "treatment",
            label: "I believe I was treated unfairly.",
          },
          {
            id: "complaint",
            label: "I want to know how or where to make a complaint.",
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
        title: "Have you contacted the institution about the problem?",
        answers: [
          {
            id: "yes-response",
            label: "Yes, and I received a response.",
          },
          {
            id: "yes-no-response",
            label: "Yes, but I have not received a useful response.",
          },
          {
            id: "no",
            label: "No, I have not contacted them yet.",
          },
        ],
      },
      {
        id: "service-records",
        eyebrow: "Information available",
        title: "Do you have any records related to the issue?",
        answers: [
          {
            id: "yes",
            label: "Yes, I have letters, messages, receipts or other records.",
          },
          {
            id: "some",
            label: "I have some information but not everything.",
          },
          {
            id: "no",
            label: "No, I do not have records.",
          },
        ],
      },
    ],
  },

  "community-discrimination": {
    title: "Community & Discrimination",
    icon: Users,
    intro:
      "These questions help identify the type of unfair treatment or community issue you may be experiencing.",
    questions: [
      {
        id: "community-issue",
        eyebrow: "Your situation",
        title: "What best describes what happened?",
        answers: [
          {
            id: "discrimination",
            label: "I believe I was discriminated against.",
          },
          {
            id: "excluded",
            label: "I was unfairly excluded from something.",
          },
          {
            id: "harassment",
            label: "I experienced harassment or degrading treatment.",
          },
          {
            id: "community",
            label: "A community decision or action is affecting me unfairly.",
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
        title: "Where did this mainly happen?",
        answers: [
          {
            id: "community",
            label: "Within my local community.",
          },
          {
            id: "service",
            label: "While accessing a service.",
          },
          {
            id: "organisation",
            label: "Within an organisation or institution.",
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
        title: "Have you already raised the issue?",
        answers: [
          {
            id: "yes",
            label: "Yes, I have reported or raised it.",
          },
          {
            id: "no",
            label: "No, I have not raised it yet.",
          },
          {
            id: "unsafe",
            label: "I do not feel comfortable or safe raising it directly.",
          },
        ],
      },
    ],
  },
};

export default function GuidedRightsJourney() {
  const { category } = useParams();

  if (!category || !(category in journeys)) {
    return <Navigate to="/rights" replace />;
  }

  const selectedCategory = category as CategorySlug;
  const journey = journeys[selectedCategory];
  const Icon = journey.icon;

  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [completed, setCompleted] = useState(false);

  const question = journey.questions[currentQuestion];

  const selectedAnswer = answers[question?.id];

  const progress = useMemo(() => {
    if (completed) return 100;

    return Math.round(
      ((currentQuestion + 1) / journey.questions.length) * 100,
    );
  }, [completed, currentQuestion, journey.questions.length]);

  const handleAnswer = (answerId: string) => {
    setAnswers((current) => ({
      ...current,
      [question.id]: answerId,
    }));
  };

  const handleContinue = () => {
    if (!selectedAnswer) return;

    if (currentQuestion === journey.questions.length - 1) {
      setCompleted(true);
      return;
    }

    setCurrentQuestion((current) => current + 1);

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  const handleBack = () => {
    if (completed) {
      setCompleted(false);
      return;
    }

    if (currentQuestion > 0) {
      setCurrentQuestion((current) => current - 1);

      window.scrollTo({
        top: 0,
        behavior: "smooth",
      });
    }
  };

  const safetyConcern =
    selectedCategory === "safety-protection" &&
    (answers["safety-now"] === "yes" ||
      answers["safety-now"] === "maybe");

  if (completed) {
    return (
      <>
        <section className="min-h-[70vh] bg-background">
          <div className="site-container py-16 sm:py-20 lg:py-24">
            <Link
              to={`/rights/${selectedCategory}`}
              className="inline-flex items-center gap-2 text-sm font-semibold text-text-secondary transition hover:text-gold"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to {journey.title}
            </Link>

            <div className="mx-auto mt-12 max-w-3xl">
              <div className="border border-border bg-surface p-7 shadow-[var(--shadow-soft)] sm:p-10 lg:p-12">
                <div className="flex h-14 w-14 items-center justify-center rounded-full bg-gold/10 text-gold">
                  <Check className="h-7 w-7" />
                </div>

                <p className="mt-7 text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                  Your guided journey
                </p>

                <h1 className="heading-serif mt-4 text-3xl font-semibold leading-tight text-text-primary sm:text-4xl lg:text-5xl">
                  We have a clearer picture
                  <span className="block text-gold-deep dark:text-gold">
                    of your situation.
                  </span>
                </h1>

                <p className="mt-6 max-w-2xl text-base leading-7 text-text-secondary">
                  Your answers can now be used to organise relevant rights
                  information, practical considerations and possible next
                  steps.
                </p>

                {safetyConcern && (
                  <div className="mt-8 border-l-2 border-gold bg-gold/5 p-5">
                    <div className="flex gap-4">
                      <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-gold" />

                      <div>
                        <h2 className="font-semibold text-text-primary">
                          Your safety comes first
                        </h2>

                        <p className="mt-2 text-sm leading-6 text-text-secondary">
                          You indicated that you may currently be unsafe.
                          Prioritise reaching a safe place or trusted person
                          where possible. Sauti Yo should not delay urgent
                          assistance.
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                <div className="mt-8 border-y border-border py-6">
                  <div className="flex items-center gap-4">
                    <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-gold/10 text-gold">
                      <Icon className="h-5 w-5" strokeWidth={1.6} />
                    </div>

                    <div>
                      <p className="text-xs font-bold uppercase tracking-[0.14em] text-text-secondary">
                        Selected category
                      </p>

                      <p className="mt-1 font-semibold text-text-primary">
                        {journey.title}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="mt-8 grid gap-3 sm:grid-cols-2">
                  <Link
                    to="/support"
                    className="btn-primary w-full"
                  >
                    Find Relevant Support
                    <ArrowRight className="h-4 w-4" />
                  </Link>

                  <Link
                    to={`/rights/${selectedCategory}`}
                    className="btn-secondary w-full"
                  >
                    Review Rights Information
                  </Link>
                </div>

                <p className="mt-6 text-xs leading-5 text-text-secondary">
                  Sauti Yo provides general rights information and guidance.
                  It does not replace advice from a qualified legal or support
                  professional.
                </p>
              </div>
            </div>
          </div>
        </section>
      </>
    );
  }

  return (
    <>
      {/* HEADER */}
      <section className="border-b border-border bg-background">
        <div className="site-container py-10 sm:py-12">
          <div className="flex flex-wrap items-center justify-between gap-5">
            <Link
              to={`/rights/${selectedCategory}`}
              className="inline-flex items-center gap-2 text-sm font-semibold text-text-secondary transition hover:text-gold"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to {journey.title}
            </Link>

            <div className="flex items-center gap-3">
              <div className="hidden h-1.5 w-32 overflow-hidden rounded-full bg-border sm:block">
                <div
                  className="h-full rounded-full bg-gold transition-all duration-500"
                  style={{ width: `${progress}%` }}
                />
              </div>

              <span className="text-xs font-semibold text-text-secondary">
                {currentQuestion + 1} of {journey.questions.length}
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* QUESTION */}
      <main className="min-h-[70vh] bg-background">
        <div className="site-container py-12 sm:py-16 lg:py-20">
          <div className="mx-auto max-w-3xl">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gold/10 text-gold">
                <Icon className="h-5 w-5" strokeWidth={1.6} />
              </div>

              <p className="text-sm font-semibold text-text-secondary">
                {journey.title}
              </p>
            </div>

            {currentQuestion === 0 && (
              <p className="mt-6 max-w-2xl text-sm leading-6 text-text-secondary">
                {journey.intro}
              </p>
            )}

            <div className="mt-9">
              <div className="mb-4 flex items-center gap-3">
                <span className="gold-rule" />

                <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                  {question.eyebrow}
                </p>
              </div>

              <h1 className="heading-serif text-3xl font-semibold leading-tight text-text-primary sm:text-4xl lg:text-5xl">
                {question.title}
              </h1>

              {question.description && (
                <p className="mt-4 text-base leading-7 text-text-secondary">
                  {question.description}
                </p>
              )}
            </div>

            {/* ANSWERS */}
            <div className="mt-9 space-y-3">
              {question.answers.map((answer) => {
                const active = selectedAnswer === answer.id;

                return (
                  <button
                    key={answer.id}
                    type="button"
                    onClick={() => handleAnswer(answer.id)}
                    className={[
                      "group flex w-full items-start gap-4 border p-5 text-left transition-all duration-200 sm:p-6",
                      active
                        ? "border-gold bg-gold/5 shadow-[var(--shadow-soft)]"
                        : "border-border bg-surface hover:border-gold/60",
                    ].join(" ")}
                  >
                    <span
                      className={[
                        "mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border transition",
                        active
                          ? "border-gold bg-gold text-[#1f1f1f]"
                          : "border-border bg-background",
                      ].join(" ")}
                    >
                      {active && <Check className="h-3 w-3" />}
                    </span>

                    <span
                      className={[
                        "text-sm leading-6 sm:text-base",
                        active
                          ? "font-semibold text-text-primary"
                          : "text-text-secondary",
                      ].join(" ")}
                    >
                      {answer.label}
                    </span>
                  </button>
                );
              })}
            </div>

            {/* CONTROLS */}
            <div className="mt-10 flex flex-col-reverse gap-3 border-t border-border pt-7 sm:flex-row sm:items-center sm:justify-between">
              {currentQuestion > 0 ? (
                <button
                  type="button"
                  onClick={handleBack}
                  className="btn-secondary w-full sm:w-auto"
                >
                  <ArrowLeft className="h-4 w-4" />
                  Previous
                </button>
              ) : (
                <div />
              )}

              <button
                type="button"
                disabled={!selectedAnswer}
                onClick={handleContinue}
                className={[
                  "inline-flex min-h-12 w-full items-center justify-center gap-2 px-6 py-3 font-bold transition sm:w-auto",
                  selectedAnswer
                    ? "bg-gold text-[#191919] hover:-translate-y-0.5"
                    : "cursor-not-allowed bg-border text-text-secondary opacity-60",
                ].join(" ")}
              >
                {currentQuestion === journey.questions.length - 1
                  ? "See My Next Steps"
                  : "Continue"}

                <ArrowRight className="h-4 w-4" />
              </button>
            </div>

            <p className="mt-6 text-xs leading-5 text-text-secondary">
              You do not need to share names, identification numbers or other
              unnecessary personal details to use this guide.
            </p>
          </div>
        </div>
      </main>
    </>
  );
}