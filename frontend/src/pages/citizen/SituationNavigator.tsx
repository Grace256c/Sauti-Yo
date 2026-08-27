import {
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  Loader2,
  Scale,
  ShieldAlert,
} from "lucide-react";
import {
  type FormEvent,
  useState,
} from "react";
import { Link } from "react-router-dom";

import {
  rightsCategories,
} from "../../data/rightsData";

import {
  analyseRightsConcern,
} from "../../services/rights";

import type {
  ConcernAnalysisResponse,
} from "../../services/rights";


export default function SituationNavigator() {
  const [concern, setConcern] = useState("");
  const [result, setResult] =
    useState<ConcernAnalysisResponse | null>(null);
  const [analysing, setAnalysing] = useState(false);
  const [error, setError] = useState("");

  const handleAnalyse = async (
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();

    const cleanedConcern = concern.trim();

    if (!cleanedConcern) {
      setError(
        "Please briefly describe what happened before continuing.",
      );
      setResult(null);
      return;
    }

    setAnalysing(true);
    setError("");

    try {
      const response =
        await analyseRightsConcern(cleanedConcern);

      setResult(response);
    } catch {
      setResult(null);
      setError(
        "We could not analyse your concern right now. You can still choose the closest category below.",
      );
    } finally {
      setAnalysing(false);
    }
  };

  const matchedSituation =
    result?.matched
      ? result.situation
      : undefined;

  const matchedTopic =
    matchedSituation?.rights_topics?.[0];

  const legalProvisions =
    matchedTopic?.legal_provisions ?? [];

  const actionSteps =
    matchedTopic?.action_steps ?? [];

  const safetyResponses =
    matchedTopic?.safety_responses ?? [];

  const supportServices =
    matchedTopic?.support_services ?? [];

  return (
    <>
      {/* HERO */}
      <section className="bg-background py-16 sm:py-20 lg:py-24">
        <div className="site-container">
          <Link
            to="/rights"
            className="inline-flex items-center gap-2 text-sm font-semibold text-text-secondary transition hover:text-gold"
          >
            <ArrowLeft className="h-4 w-4" />

            Back to Know Your Rights
          </Link>

          <div className="mt-10 max-w-3xl">
            <div className="mb-5 flex items-center gap-3">
              <span className="gold-rule" />

              <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                Start with what happened
              </p>
            </div>

            <h1 className="heading-serif text-4xl font-semibold leading-tight text-text-primary sm:text-5xl lg:text-6xl">
              You do not need to know
              <span className="block text-gold-deep dark:text-gold">
                what the legal issue is called.
              </span>
            </h1>

            <p className="mt-6 max-w-2xl text-base leading-7 text-text-secondary sm:text-lg">
              Describe what happened in your own words, or choose
              the situation below that feels closest. You do not
              need to use legal language.
            </p>
          </div>
        </div>
      </section>

      {/* FREE-TEXT CONCERN ANALYSIS */}
      <section className="border-y border-border bg-surface py-14 sm:py-16">
        <div className="site-container">
          <div className="grid gap-10 lg:grid-cols-[0.72fr_1.28fr] lg:gap-20">
            <div>
              <div className="flex items-center gap-3">
                <BookOpen
                  className="h-6 w-6 text-gold"
                  strokeWidth={1.6}
                />

                <p className="text-xs font-bold uppercase tracking-[0.18em] text-gold-deep dark:text-gold">
                  Tell us what happened
                </p>
              </div>

              <h2 className="heading-serif mt-5 text-3xl font-semibold leading-tight text-text-primary sm:text-4xl">
                Describe your concern
                <span className="block text-gold-deep dark:text-gold">
                  in your own words.
                </span>
              </h2>

              <p className="mt-5 max-w-md text-sm leading-6 text-text-secondary sm:text-base">
                Sauti Yo will try to connect your concern to
                rights information already stored in our
                reviewed-source knowledge base.
              </p>

              <p className="mt-4 max-w-md text-xs leading-5 text-text-secondary">
                Do not include names, national identification
                numbers, account numbers or other unnecessary
                personal information.
              </p>
            </div>

            <form
              onSubmit={handleAnalyse}
              className="border border-border bg-background p-5 sm:p-7"
            >
              <label
                htmlFor="citizen-concern"
                className="text-sm font-semibold text-text-primary"
              >
                What happened?
              </label>

              <textarea
                id="citizen-concern"
                value={concern}
                onChange={(event) => {
                  setConcern(event.target.value);

                  if (error) {
                    setError("");
                  }
                }}
                rows={6}
                maxLength={2000}
                placeholder="For example: My employer dismissed me after I told them I was pregnant."
                className="mt-3 w-full resize-y border border-border bg-surface px-4 py-3 text-sm leading-6 text-text-primary outline-none transition placeholder:text-text-secondary/60 focus:border-gold"
              />

              <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
                <p className="text-xs text-text-secondary">
                  {concern.length}/2000 characters
                </p>

                <p className="text-xs text-text-secondary">
                  Plain language is enough.
                </p>
              </div>

              {error && (
                <div className="mt-4 flex items-start gap-3 border border-border bg-surface-soft p-4">
                  <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-gold" />

                  <p className="text-sm leading-6 text-text-secondary">
                    {error}
                  </p>
                </div>
              )}

              <button
                type="submit"
                disabled={analysing}
                className={[
                  "mt-6 inline-flex min-h-12 w-full items-center justify-center gap-2 px-6 py-3 font-bold transition sm:w-auto",
                  analysing
                    ? "cursor-wait bg-border text-text-secondary"
                    : "bg-gold text-[#191919] hover:-translate-y-0.5",
                ].join(" ")}
              >
                {analysing ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Checking relevant information
                  </>
                ) : (
                  <>
                    Help Me Understand
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </button>
            </form>
          </div>
        </div>
      </section>

      {/* UNMATCHED RESULT */}
      {result && !result.matched && (
        <section className="bg-background py-12 sm:py-14">
          <div className="site-container">
            <div className="mx-auto max-w-4xl border border-border bg-surface p-6 sm:p-8">
              <div className="flex items-start gap-4">
                <AlertCircle className="mt-1 h-6 w-6 shrink-0 text-gold" />

                <div>
                  <h2 className="text-xl font-semibold text-text-primary">
                    We could not confidently match that concern yet.
                  </h2>

                  <p className="mt-3 text-sm leading-6 text-text-secondary sm:text-base">
                    {result.detail ??
                      "The current Sauti Yo knowledge base may not yet cover this situation."}
                  </p>

                  <p className="mt-3 text-sm leading-6 text-text-secondary">
                    Please choose the closest category below instead.
                    Sauti Yo will not invent legal information when
                    there is not a confident match.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* MATCHED RESULT */}
      {matchedSituation && matchedTopic && (
        <section className="bg-background py-14 sm:py-16 lg:py-20">
          <div className="site-container">
            <div className="mx-auto max-w-5xl">
              <div className="border border-border bg-surface p-6 sm:p-8">
                <div className="flex flex-wrap items-start justify-between gap-5">
                  <div>
                    <p className="text-xs font-bold uppercase tracking-[0.18em] text-gold-deep dark:text-gold">
                      Relevant situation
                    </p>

                    <h2 className="heading-serif mt-3 text-3xl font-semibold text-text-primary sm:text-4xl">
                      {matchedSituation.title}
                    </h2>

                    <p className="mt-4 max-w-3xl text-sm leading-6 text-text-secondary sm:text-base">
                      {matchedSituation.description}
                    </p>
                  </div>

                  <div className="flex items-center gap-2 border border-border px-3 py-2 text-xs font-semibold text-text-secondary">
                    <CheckCircle2 className="h-4 w-4 text-gold" />
                    Grounded match
                  </div>
                </div>
              </div>

              {/* SAFETY */}
              {safetyResponses.length > 0 && (
                <div className="mt-6 border border-gold/40 bg-gold/5 p-6 sm:p-8">
                  <div className="flex items-start gap-4">
                    <ShieldAlert className="mt-1 h-6 w-6 shrink-0 text-gold-deep dark:text-gold" />

                    <div>
                      <p className="text-xs font-bold uppercase tracking-[0.18em] text-gold-deep dark:text-gold">
                        Safety first
                      </p>

                      {safetyResponses.map((response) => (
                        <p
                          key={response.trigger_key}
                          className="mt-3 text-sm leading-6 text-text-primary sm:text-base"
                        >
                          {response.message}
                        </p>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* RIGHTS SUMMARY */}
              <div className="mt-10 grid gap-10 lg:grid-cols-[0.72fr_1.28fr] lg:gap-20">
                <div>
                  <Scale
                    className="h-7 w-7 text-gold"
                    strokeWidth={1.6}
                  />

                  <p className="mt-5 text-xs font-bold uppercase tracking-[0.18em] text-gold-deep dark:text-gold">
                    What may be relevant
                  </p>

                  <h2 className="heading-serif mt-4 text-3xl font-semibold text-text-primary">
                    {matchedTopic.title}
                  </h2>

                  <p className="mt-4 text-sm leading-6 text-text-secondary sm:text-base">
                    {matchedTopic.summary}
                  </p>
                </div>

                {/* LEGAL BASIS */}
                <div>
                  <p className="text-xs font-bold uppercase tracking-[0.18em] text-gold-deep dark:text-gold">
                    Legal basis
                  </p>

                  <div className="mt-4 space-y-4">
                    {legalProvisions.length > 0 ? (
                      legalProvisions.map((provision) => (
                        <article
                          key={`${provision.law_title}-${provision.provision_reference}`}
                          className="border border-border bg-surface p-5 sm:p-6"
                        >
                          <div className="flex flex-wrap items-center justify-between gap-3">
                            <span className="text-xs font-bold uppercase tracking-[0.14em] text-gold-deep dark:text-gold">
                              {provision.source_type.replace(
                                "_",
                                " ",
                              )}
                            </span>

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
                      ))
                    ) : (
                      <p className="text-sm leading-6 text-text-secondary">
                        No structured legal references are available
                        for this topic yet.
                      </p>
                    )}
                  </div>
                </div>
              </div>

              {/* ACTIONS */}
              {actionSteps.length > 0 && (
                <div className="mt-14 border-t border-border pt-10">
                  <p className="text-xs font-bold uppercase tracking-[0.18em] text-gold-deep dark:text-gold">
                    Practical next steps
                  </p>

                  <div className="mt-6 grid gap-4 md:grid-cols-2">
                    {actionSteps.map((step) => (
                      <article
                        key={`${step.order}-${step.title}`}
                        className="border border-border bg-surface p-5"
                      >
                        <div className="flex items-start gap-4">
                          <span className="heading-serif text-2xl font-semibold text-gold">
                            {String(step.order).padStart(
                              2,
                              "0",
                            )}
                          </span>

                          <div>
                            <h3 className="font-semibold text-text-primary">
                              {step.title}
                            </h3>

                            <p className="mt-2 text-sm leading-6 text-text-secondary">
                              {step.description}
                            </p>
                          </div>
                        </div>
                      </article>
                    ))}
                  </div>
                </div>
              )}

              {/* SUPPORT */}
              {supportServices.length > 0 && (
                <div className="mt-14 border-t border-border pt-10">
                  <p className="text-xs font-bold uppercase tracking-[0.18em] text-gold-deep dark:text-gold">
                    Support that may be relevant
                  </p>

                  <div className="mt-6 grid gap-4 md:grid-cols-2">
                    {supportServices.map((service) => (
                      <article
                        key={`${service.name}-${service.phone_number}`}
                        className="border border-border bg-surface p-5"
                      >
                        <h3 className="font-semibold text-text-primary">
                          {service.name}
                        </h3>

                        {service.phone_number && (
                          <p className="mt-2 text-sm font-semibold text-gold-deep dark:text-gold">
                            {service.phone_number}
                          </p>
                        )}

                        {service.is_emergency_service && (
                          <p className="mt-2 text-xs font-semibold uppercase tracking-[0.12em] text-text-secondary">
                            Emergency / urgent support
                          </p>
                        )}
                      </article>
                    ))}
                  </div>

                  <Link
                    to="/support"
                    className="btn-secondary mt-6 inline-flex"
                  >
                    Explore Support Options
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                </div>
              )}

              <div className="mt-12 border-t border-border pt-6">
                <p className="text-xs leading-5 text-text-secondary">
                  Sauti Yo provides general rights information and
                  practical pathways. It is not a substitute for
                  personalised legal advice. Legal content marked
                  “Review required” is awaiting final legal-review
                  approval.
                </p>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* SITUATION OPTIONS */}
      <section className="section-padding bg-surface">
        <div className="site-container">
          <div className="mb-10 max-w-2xl">
            <p className="text-xs font-bold uppercase tracking-[0.18em] text-gold-deep dark:text-gold">
              Prefer the guided route?
            </p>

            <h2 className="heading-serif mt-3 text-3xl font-semibold text-text-primary sm:text-4xl">
              Choose the closest situation.
            </h2>

            <p className="mt-4 text-sm leading-6 text-text-secondary sm:text-base">
              You can still use the existing guided questions if
              you would rather choose from examples.
            </p>
          </div>

          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
            {rightsCategories.map((situation) => {
              const Icon = situation.icon;

              return (
                <Link
                  key={situation.slug}
                  to={`/rights/${situation.slug}`}
                  className="card-surface group flex min-h-[310px] flex-col p-6 sm:p-7"
                >
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gold/10 text-gold transition-all duration-300 group-hover:-translate-y-1 group-hover:bg-gold group-hover:text-[#1f1f1f]">
                    <Icon
                      className="h-5 w-5"
                      strokeWidth={1.7}
                    />
                  </div>

                  <h2 className="mt-5 text-xl font-semibold leading-7 text-text-primary">
                    {situation.navigatorTitle}
                  </h2>

                  <p className="mt-3 text-sm leading-6 text-text-secondary">
                    {situation.navigatorDescription}
                  </p>

                  <div className="mt-5 space-y-2">
                    {situation.navigatorExamples.map(
                      (example) => (
                        <p
                          key={example}
                          className="text-xs leading-5 text-text-secondary"
                        >
                          • {example}
                        </p>
                      ),
                    )}
                  </div>

                  <span className="mt-auto inline-flex items-center gap-2 pt-6 text-sm font-semibold text-gold-deep transition-all duration-300 group-hover:gap-3 dark:text-gold">
                    This sounds closest

                    <ArrowRight className="h-4 w-4" />
                  </span>
                </Link>
              );
            })}
          </div>
        </div>
      </section>

      {/* REASSURANCE */}
      <section className="bg-surface-soft py-14 sm:py-16">
        <div className="site-container">
          <div className="mx-auto max-w-3xl text-center">
            <p className="text-xs font-bold uppercase tracking-[0.18em] text-gold-deep dark:text-gold">
              Still unsure?
            </p>

            <h2 className="heading-serif mt-4 text-2xl font-semibold text-text-primary sm:text-3xl">
              Start with the closest option.
            </h2>

            <p className="mx-auto mt-4 max-w-2xl text-sm leading-6 text-text-secondary sm:text-base">
              Your first choice does not lock you into anything.
              You can change your description, choose another
              situation, or explore another pathway.
            </p>
          </div>
        </div>
      </section>

      {/* FINAL CTA */}
      <section className="bg-[#1c1c1c] text-white">
        <div className="site-container py-14 sm:py-16">
          <div className="grid gap-8 lg:grid-cols-[1fr_auto] lg:items-center">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold">
                Sauti Yo
              </p>

              <h2 className="heading-serif mt-4 text-3xl font-semibold sm:text-4xl">
                Start with your experience.
                <span className="block text-gold">
                  We’ll connect it to rights information.
                </span>
              </h2>
            </div>

            <Link
              to="/rights"
              className="inline-flex min-h-12 w-full items-center justify-center gap-2 border border-gold px-7 py-3 font-semibold text-gold transition hover:bg-gold hover:text-[#191919] sm:w-auto"
            >
              View All Categories

              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
