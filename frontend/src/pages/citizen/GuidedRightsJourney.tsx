import {
  ArrowLeft,
  ArrowRight,
  Check,
} from "lucide-react";
import { useMemo, useState } from "react";
import {
  Link,
  Navigate,
  useNavigate,
  useParams,
} from "react-router-dom";

import {
  getJourneyStorageKey,
  getRightsCategory,
} from "../../data/rightsData";

export default function GuidedRightsJourney() {
  const { category } = useParams();
  const navigate = useNavigate();

  const journey = getRightsCategory(category);

  if (!journey) {
    return <Navigate to="/rights" replace />;
  }

  const Icon = journey.icon;

  const [currentQuestion, setCurrentQuestion] = useState(0);

  const [answers, setAnswers] = useState<Record<string, string>>(
    () => {
      try {
        const saved = sessionStorage.getItem(
          getJourneyStorageKey(journey.slug),
        );

        return saved ? JSON.parse(saved) : {};
      } catch {
        return {};
      }
    },
  );

  const question = journey.questions[currentQuestion];

  const selectedAnswer = answers[question.id];

  const progress = useMemo(() => {
    return Math.round(
      ((currentQuestion + 1) / journey.questions.length) * 100,
    );
  }, [currentQuestion, journey.questions.length]);

  const saveAnswers = (
    updatedAnswers: Record<string, string>,
  ) => {
    sessionStorage.setItem(
      getJourneyStorageKey(journey.slug),
      JSON.stringify(updatedAnswers),
    );
  };

  const handleAnswer = (answerId: string) => {
    const updatedAnswers = {
      ...answers,
      [question.id]: answerId,
    };

    setAnswers(updatedAnswers);
    saveAnswers(updatedAnswers);
  };

  const handleContinue = () => {
    if (!selectedAnswer) {
      return;
    }

    if (
      currentQuestion ===
      journey.questions.length - 1
    ) {
      saveAnswers(answers);

      navigate(
        `/rights/${journey.slug}/results`,
      );

      return;
    }

    setCurrentQuestion((current) => current + 1);

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  const handleBack = () => {
    if (currentQuestion === 0) {
      return;
    }

    setCurrentQuestion((current) => current - 1);

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  return (
    <>
      {/* =========================================================
          JOURNEY HEADER
      ========================================================= */}
      <section className="border-b border-border bg-background">
        <div className="site-container py-8 sm:py-10">
          <div className="flex flex-wrap items-center justify-between gap-5">
            <Link
              to={`/rights/${journey.slug}`}
              className="inline-flex items-center gap-2 text-sm font-semibold text-text-secondary transition hover:text-gold"
            >
              <ArrowLeft className="h-4 w-4" />

              Back to {journey.title}
            </Link>

            <div className="flex items-center gap-3">
              <div className="hidden h-1.5 w-32 overflow-hidden rounded-full bg-border sm:block">
                <div
                  className="h-full rounded-full bg-gold transition-all duration-500"
                  style={{
                    width: `${progress}%`,
                  }}
                />
              </div>

              <span className="text-xs font-semibold text-text-secondary">
                {currentQuestion + 1} of{" "}
                {journey.questions.length}
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================
          QUESTION
      ========================================================= */}
      <main className="min-h-[70vh] bg-background">
        <div className="site-container py-12 sm:py-16 lg:py-20">
          <div className="mx-auto max-w-3xl">

            {/* CATEGORY */}
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gold/10 text-gold">
                <Icon
                  className="h-5 w-5"
                  strokeWidth={1.6}
                />
              </div>

              <p className="text-sm font-semibold text-text-secondary">
                {journey.title}
              </p>
            </div>

            {/* INTRO */}
            {currentQuestion === 0 && (
              <p className="mt-6 max-w-2xl text-sm leading-6 text-text-secondary">
                Start with the option that feels closest
                to your situation. You can go back and
                change an answer before viewing your next
                steps.
              </p>
            )}

            {/* QUESTION TITLE */}
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

            {/* =====================================================
                ANSWERS
            ===================================================== */}
            <div className="mt-9 space-y-3">
              {question.answers.map((answer) => {
                const active =
                  selectedAnswer === answer.id;

                return (
                  <button
                    key={answer.id}
                    type="button"
                    onClick={() =>
                      handleAnswer(answer.id)
                    }
                    className={[
                      "group flex w-full items-start gap-4 border p-5 text-left transition-all duration-200 sm:p-6",

                      active
                        ? "border-gold bg-gold/5 shadow-[var(--shadow-soft)]"
                        : "border-border bg-surface hover:border-gold/60",
                    ].join(" ")}
                  >
                    {/* RADIO INDICATOR */}
                    <span
                      className={[
                        "mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border transition",

                        active
                          ? "border-gold bg-gold text-[#1f1f1f]"
                          : "border-border bg-background",
                      ].join(" ")}
                    >
                      {active && (
                        <Check className="h-3 w-3" />
                      )}
                    </span>

                    {/* ANSWER TEXT */}
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

            {/* =====================================================
                NAVIGATION CONTROLS
            ===================================================== */}
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
                {currentQuestion ===
                journey.questions.length - 1
                  ? "See My Next Steps"
                  : "Continue"}

                <ArrowRight className="h-4 w-4" />
              </button>
            </div>

            {/* PRIVACY NOTE */}
            <p className="mt-6 text-xs leading-5 text-text-secondary">
              You do not need to share names,
              identification numbers or other unnecessary
              personal details to use this guide.
            </p>
          </div>
        </div>
      </main>
    </>
  );
}