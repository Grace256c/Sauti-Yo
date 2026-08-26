import {
  ArrowLeft,
  ArrowRight,
  Building2,
  Check,
  Globe2,
  Languages,
  MapPin,
  Phone,
  ShieldCheck,
  Users,
} from "lucide-react";
import { useMemo, useState } from "react";
import {
  Link,
  useSearchParams,
} from "react-router-dom";

import {
  getRightsCategory,
  isCategorySlug,
} from "../../data/rightsData";

import {
  getSupportPathwaysForCategory,
  supportPathways,
} from "../../data/supportData";

import {
  matchPartners,
  partnerProfiles,
} from "../../data/partnerData";

import type {
  PartnerMatch,
  SupportChannel,
} from "../../data/partnerData";

/* =========================================================
   SUPPORT OPTIONS
========================================================= */

const supportMethods: {
  id: SupportChannel;
  title: string;
  description: string;
  icon: typeof Building2;
}[] = [
  {
    id: "in-person",
    title: "In person",
    description:
      "I would prefer to visit an organisation or support provider.",
    icon: Building2,
  },
  {
    id: "phone",
    title: "By phone",
    description:
      "I would prefer to speak with someone by telephone.",
    icon: Phone,
  },
  {
    id: "remote",
    title: "Online or remote",
    description:
      "I would prefer support that does not require travelling.",
    icon: Globe2,
  },
];

const districtOptions = [
  "Kampala",
  "Wakiso",
  "Mukono",
  "Jinja",
  "Masaka",
  "Mbarara",
  "Gulu",
  "Lira",
  "Mbale",
  "Fort Portal",
  "Other",
];

const languageOptions = [
  "English",
  "Luganda",
  "Runyankole",
  "Lusoga",
  "Acholi",
  "Ateso",
  "Langi",
  "Other",
];

export default function Support() {
  const [searchParams] = useSearchParams();

  const categoryParam =
    searchParams.get("category");

  const selectedCategory =
    categoryParam &&
    isCategorySlug(categoryParam)
      ? getRightsCategory(categoryParam)
      : null;

  const relevantPathways = useMemo(() => {
    if (!selectedCategory) {
      return supportPathways;
    }

    return getSupportPathwaysForCategory(
      selectedCategory.slug,
    );
  }, [selectedCategory]);

  const [district, setDistrict] =
    useState("");

  const [language, setLanguage] =
    useState("");

  const [
    supportMethod,
    setSupportMethod,
  ] = useState<SupportChannel | null>(
    null,
  );

  const [
    matchRequested,
    setMatchRequested,
  ] = useState(false);

  const [
    matches,
    setMatches,
  ] = useState<PartnerMatch[]>([]);

  const canSearch =
    Boolean(selectedCategory) &&
    district !== "" &&
    language !== "" &&
    supportMethod !== null;

  const resetMatches = () => {
    setMatchRequested(false);
    setMatches([]);
  };

  const handleFindSupport = () => {
    if (
      !selectedCategory ||
      !supportMethod ||
      !canSearch
    ) {
      return;
    }

    const partnerMatches =
      matchPartners(
        partnerProfiles,
        {
          category:
            selectedCategory.slug,

          district,

          language,

          preferredChannel:
            supportMethod,
        },
      );

    setMatches(partnerMatches);

    setMatchRequested(true);

    window.setTimeout(() => {
      document
        .getElementById(
          "partner-results",
        )
        ?.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
    }, 50);
  };

  return (
    <>
      {/* HERO */}
      <section className="bg-background py-16 sm:py-20 lg:py-24">
        <div className="site-container">
          {selectedCategory ? (
            <Link
              to={`/rights/${selectedCategory.slug}/results`}
              className="inline-flex items-center gap-2 text-sm font-semibold text-text-secondary transition hover:text-gold"
            >
              <ArrowLeft className="h-4 w-4" />

              Back to my results
            </Link>
          ) : (
            <Link
              to="/rights"
              className="inline-flex items-center gap-2 text-sm font-semibold text-text-secondary transition hover:text-gold"
            >
              <ArrowLeft className="h-4 w-4" />

              Explore your rights
            </Link>
          )}

          <div className="mt-10 grid gap-10 lg:grid-cols-[0.78fr_1.22fr] lg:items-end lg:gap-20">
            <div>
              <div className="mb-5 flex items-center gap-3">
                <span className="gold-rule" />

                <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                  Find support
                </p>
              </div>

              <h1 className="heading-serif text-4xl font-semibold leading-tight text-text-primary sm:text-5xl lg:text-6xl">
                {selectedCategory
                  ? "Support for your"
                  : "Find the right"}

                <span className="block text-gold-deep dark:text-gold">
                  {selectedCategory
                    ? `${selectedCategory.title} situation.`
                    : "place to ask for help."}
                </span>
              </h1>
            </div>

            <div className="max-w-2xl">
              <p className="text-base leading-7 text-text-secondary sm:text-lg sm:leading-8">
                {selectedCategory
                  ? `Based on the ${selectedCategory.title} issue you explored, Sauti Yo can help identify the types of support that may be relevant and match you with eligible verified providers.`
                  : "Different organisations provide different kinds of support. Start by exploring your rights so Sauti Yo can understand the type of support that may be relevant."}
              </p>

              {!selectedCategory && (
                <Link
                  to="/rights"
                  className="btn-primary mt-7"
                >
                  Start With My Situation

                  <ArrowRight className="h-4 w-4" />
                </Link>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* SUPPORT PATHWAYS */}
      <section className="section-padding bg-surface">
        <div className="site-container">
          <div className="grid gap-10 lg:grid-cols-[0.72fr_1.28fr] lg:gap-20">
            <div>
              <div className="mb-5 flex items-center gap-3">
                <span className="gold-rule" />

                <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                  Support pathways
                </p>
              </div>

              <h2 className="heading-serif text-3xl font-semibold leading-tight text-text-primary sm:text-4xl">
                What kind of support

                <span className="block text-gold-deep dark:text-gold">
                  may be relevant?
                </span>
              </h2>

              <p className="mt-5 max-w-md text-base leading-7 text-text-secondary">
                These are types of support rather than individual
                organisations. Provider recommendations should only
                come from verified partners.
              </p>
            </div>

            <div className="grid gap-5 md:grid-cols-2">
              {relevantPathways.map(
                (pathway) => {
                  const Icon =
                    pathway.icon;

                  return (
                    <article
                      key={pathway.id}
                      className="card-surface flex min-h-[300px] flex-col p-6 sm:p-7"
                    >
                      <div className="flex h-11 w-11 items-center justify-center rounded-full bg-gold/10 text-gold">
                        <Icon
                          className="h-5 w-5"
                          strokeWidth={1.7}
                        />
                      </div>

                      <h3 className="mt-5 text-xl font-semibold text-text-primary">
                        {pathway.title}
                      </h3>

                      <p className="mt-3 text-sm leading-6 text-text-secondary">
                        {
                          pathway.description
                        }
                      </p>

                      <div className="mt-5 space-y-2">
                        {pathway.examples
                          .slice(0, 3)
                          .map(
                            (
                              example,
                            ) => (
                              <div
                                key={
                                  example
                                }
                                className="flex items-start gap-2"
                              >
                                <Check className="mt-1 h-3.5 w-3.5 shrink-0 text-gold" />

                                <p className="text-xs leading-5 text-text-secondary">
                                  {
                                    example
                                  }
                                </p>
                              </div>
                            ),
                          )}
                      </div>
                    </article>
                  );
                },
              )}
            </div>
          </div>
        </div>
      </section>

      {/* MATCHING FORM */}
      {selectedCategory && (
        <section className="section-padding bg-background">
          <div className="site-container">
            <div className="mx-auto max-w-4xl">
              <div className="max-w-2xl">
                <div className="mb-5 flex items-center gap-3">
                  <span className="gold-rule" />

                  <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                    Refine your support
                  </p>
                </div>

                <h2 className="heading-serif text-3xl font-semibold leading-tight text-text-primary sm:text-4xl lg:text-5xl">
                  Help us understand

                  <span className="block text-gold-deep dark:text-gold">
                    what support works for you.
                  </span>
                </h2>

                <p className="mt-5 text-base leading-7 text-text-secondary">
                  You do not need to describe your legal problem again.
                  These questions help match you with an accessible
                  provider.
                </p>
              </div>

              <div className="mt-10 grid gap-5 md:grid-cols-2">
                {/* DISTRICT */}
                <div className="border border-border bg-surface p-6">
                  <div className="flex items-center gap-3">
                    <MapPin className="h-5 w-5 text-gold" />

                    <label
                      htmlFor="support-district"
                      className="font-semibold text-text-primary"
                    >
                      Where are you located?
                    </label>
                  </div>

                  <p className="mt-2 text-sm leading-6 text-text-secondary">
                    Choose the district closest to where you would
                    normally seek support.
                  </p>

                  <select
                    id="support-district"
                    value={district}
                    onChange={(event) => {
                      setDistrict(
                        event.target.value,
                      );

                      resetMatches();
                    }}
                    className="mt-5 min-h-12 w-full border border-border bg-background px-4 text-sm text-text-primary outline-none transition focus:border-gold"
                  >
                    <option value="">
                      Select a district
                    </option>

                    {districtOptions.map(
                      (option) => (
                        <option
                          key={option}
                          value={option}
                        >
                          {option}
                        </option>
                      ),
                    )}
                  </select>
                </div>

                {/* LANGUAGE */}
                <div className="border border-border bg-surface p-6">
                  <div className="flex items-center gap-3">
                    <Languages className="h-5 w-5 text-gold" />

                    <label
                      htmlFor="support-language"
                      className="font-semibold text-text-primary"
                    >
                      Preferred language
                    </label>
                  </div>

                  <p className="mt-2 text-sm leading-6 text-text-secondary">
                    Choose the language you would prefer to use
                    when receiving support.
                  </p>

                  <select
                    id="support-language"
                    value={language}
                    onChange={(event) => {
                      setLanguage(
                        event.target.value,
                      );

                      resetMatches();
                    }}
                    className="mt-5 min-h-12 w-full border border-border bg-background px-4 text-sm text-text-primary outline-none transition focus:border-gold"
                  >
                    <option value="">
                      Select a language
                    </option>

                    {languageOptions.map(
                      (option) => (
                        <option
                          key={option}
                          value={option}
                        >
                          {option}
                        </option>
                      ),
                    )}
                  </select>
                </div>
              </div>

              {/* SUPPORT METHOD */}
              <div className="mt-8">
                <h3 className="text-lg font-semibold text-text-primary">
                  How would you prefer to receive help?
                </h3>

                <p className="mt-2 text-sm leading-6 text-text-secondary">
                  Choose the option that would be most practical
                  for you.
                </p>

                <div className="mt-5 grid gap-4 md:grid-cols-3">
                  {supportMethods.map(
                    (method) => {
                      const Icon =
                        method.icon;

                      const active =
                        supportMethod ===
                        method.id;

                      return (
                        <button
                          key={
                            method.id
                          }
                          type="button"
                          onClick={() => {
                            setSupportMethod(
                              method.id,
                            );

                            resetMatches();
                          }}
                          className={[
                            "flex min-h-[190px] flex-col items-start border p-5 text-left transition-all duration-200",

                            active
                              ? "border-gold bg-gold/5 shadow-[var(--shadow-soft)]"
                              : "border-border bg-surface hover:border-gold/60",
                          ].join(
                            " ",
                          )}
                        >
                          <div
                            className={[
                              "flex h-10 w-10 items-center justify-center rounded-full transition",

                              active
                                ? "bg-gold text-[#191919]"
                                : "bg-gold/10 text-gold",
                            ].join(
                              " ",
                            )}
                          >
                            <Icon className="h-5 w-5" />
                          </div>

                          <h4 className="mt-4 font-semibold text-text-primary">
                            {
                              method.title
                            }
                          </h4>

                          <p className="mt-2 text-sm leading-6 text-text-secondary">
                            {
                              method.description
                            }
                          </p>
                        </button>
                      );
                    },
                  )}
                </div>
              </div>

              <div className="mt-9 border-t border-border pt-7">
                <button
                  type="button"
                  disabled={!canSearch}
                  onClick={
                    handleFindSupport
                  }
                  className={[
                    "inline-flex min-h-12 w-full items-center justify-center gap-2 px-7 py-3 font-bold transition sm:w-auto",

                    canSearch
                      ? "bg-gold text-[#191919] hover:-translate-y-0.5"
                      : "cursor-not-allowed bg-border text-text-secondary opacity-60",
                  ].join(" ")}
                >
                  Find Matching Support

                  <ArrowRight className="h-4 w-4" />
                </button>

                {!canSearch && (
                  <p className="mt-3 text-xs leading-5 text-text-secondary">
                    Select your location, preferred language and
                    support method to continue.
                  </p>
                )}
              </div>
            </div>
          </div>
        </section>
      )}

      {/* RESULTS */}
      {matchRequested &&
        selectedCategory && (
          <section
            id="partner-results"
            className="scroll-mt-24 section-padding bg-surface-soft"
          >
            <div className="site-container">
              <div className="mx-auto max-w-4xl">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gold/10 text-gold">
                  <Users className="h-6 w-6" />
                </div>

                <div className="mt-6 flex items-center gap-3">
                  <span className="gold-rule" />

                  <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                    Support matches
                  </p>
                </div>

                <h2 className="heading-serif mt-5 text-3xl font-semibold leading-tight text-text-primary sm:text-4xl">
                  {matches.length > 0
                    ? `${matches.length} verified ${
                        matches.length === 1
                          ? "provider matches"
                          : "providers match"
                      } your preferences.`
                    : "No verified matches are available yet."}
                </h2>

                {matches.length > 0 ? (
                  <div className="mt-8 space-y-5">
                    {matches.map(
                      ({
                        partner,
                        score,
                        reasons,
                      }) => (
                        <article
                          key={partner.id}
                          className="card-surface p-6 sm:p-7"
                        >
                          <div className="flex flex-col gap-6 sm:flex-row sm:items-start sm:justify-between">
                            <div className="flex items-start gap-4">
                              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-gold/10 text-gold">
                                <Building2 className="h-5 w-5" />
                              </div>

                              <div>
                                <div className="flex flex-wrap items-center gap-2">
                                  <h3 className="text-xl font-semibold text-text-primary">
                                    {
                                      partner.organisationName
                                    }
                                  </h3>

                                  <span className="inline-flex items-center gap-1 text-xs font-semibold text-gold-deep dark:text-gold">
                                    <ShieldCheck className="h-3.5 w-3.5" />

                                    Verified
                                  </span>
                                </div>

                                <p className="mt-3 max-w-xl text-sm leading-6 text-text-secondary">
                                  {
                                    partner.serviceDescription
                                  }
                                </p>
                              </div>
                            </div>

                            <div className="shrink-0">
                              <p className="text-xs font-bold uppercase tracking-[0.15em] text-text-secondary">
                                Match
                              </p>

                              <p className="mt-1 text-2xl font-semibold text-gold-deep dark:text-gold">
                                {score}%
                              </p>
                            </div>
                          </div>

                          <div className="mt-6 grid gap-3 sm:grid-cols-2">
                            {reasons.map(
                              (
                                reason,
                              ) => (
                                <div
                                  key={
                                    reason
                                  }
                                  className="flex items-start gap-2"
                                >
                                  <Check className="mt-1 h-4 w-4 shrink-0 text-gold" />

                                  <p className="text-sm leading-6 text-text-secondary">
                                    {
                                      reason
                                    }
                                  </p>
                                </div>
                              ),
                            )}
                          </div>

                          <div className="mt-7 border-t border-border pt-6">
                            <button
                              type="button"
                              className="btn-primary"
                            >
                              View Support Option

                              <ArrowRight className="h-4 w-4" />
                            </button>
                          </div>
                        </article>
                      ),
                    )}
                  </div>
                ) : (
                  <div className="mt-8 border border-border bg-surface p-6 sm:p-8">
                    <div className="flex items-start gap-4">
                      <ShieldCheck className="mt-0.5 h-6 w-6 shrink-0 text-gold" />

                      <div>
                        <h3 className="text-lg font-semibold text-text-primary">
                          We’re building the verified partner network.
                        </h3>

                        <p className="mt-3 max-w-2xl text-sm leading-6 text-text-secondary sm:text-base">
                          Sauti Yo will only recommend organisations
                          that meet the matching criteria and have been
                          approved for referrals.
                        </p>

                        <div className="mt-6 grid gap-3 sm:grid-cols-3">
                          <div className="border-t border-border pt-4">
                            <p className="text-xs font-bold uppercase tracking-[0.15em] text-text-secondary">
                              Location
                            </p>

                            <p className="mt-2 text-sm font-semibold text-text-primary">
                              {district}
                            </p>
                          </div>

                          <div className="border-t border-border pt-4">
                            <p className="text-xs font-bold uppercase tracking-[0.15em] text-text-secondary">
                              Language
                            </p>

                            <p className="mt-2 text-sm font-semibold text-text-primary">
                              {language}
                            </p>
                          </div>

                          <div className="border-t border-border pt-4">
                            <p className="text-xs font-bold uppercase tracking-[0.15em] text-text-secondary">
                              Support method
                            </p>

                            <p className="mt-2 text-sm font-semibold text-text-primary">
                              {supportMethod ===
                              "remote"
                                ? "Online / remote"
                                : supportMethod ===
                                    "phone"
                                  ? "Phone"
                                  : "In person"}
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </section>
        )}

      {/* TRUST */}
      <section className="bg-[#1c1c1c] text-white">
        <div className="site-container py-16 sm:py-20">
          <div className="grid gap-10 lg:grid-cols-[0.75fr_1.25fr] lg:items-center lg:gap-20">
            <div>
              <ShieldCheck
                className="h-8 w-8 text-gold"
                strokeWidth={1.5}
              />

              <p className="mt-5 text-xs font-bold uppercase tracking-[0.2em] text-gold">
                Referral with care
              </p>

              <h2 className="heading-serif mt-4 text-3xl font-semibold leading-tight sm:text-4xl">
                A referral should help,

                <span className="block text-gold">
                  not create another risk.
                </span>
              </h2>
            </div>

            <div className="max-w-2xl">
              <p className="text-base leading-7 text-white/65">
                Finding a matching provider does not mean your
                personal information should automatically be sent
                to them. Citizens should remain in control of what
                they choose to share.
              </p>

              <p className="mt-4 text-sm leading-6 text-white/50">
                The next referral stage will include explicit
                consent before identifiable information can be
                shared with a partner.
              </p>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}