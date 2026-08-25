import {
  ArrowRight,
  BookOpen,
  BriefcaseBusiness,
  Building2,
  CheckCircle2,
  HeartHandshake,
  Home,
  Landmark,
  Scale,
  ShieldCheck,
  Users,
} from "lucide-react";

import legalBackground from "../../assets/images/legal-background.png";
import communityRightsSession from "../../assets/images/community-rights-session.png";

const rightsCategories = [
  {
    icon: BriefcaseBusiness,
    title: "Work & Employment",
    text: "Questions about pay, dismissal, workplace treatment, contracts or unfair conditions.",
  },
  {
    icon: ShieldCheck,
    title: "Safety & Protection",
    text: "Situations involving abuse, threats, violence, harassment or personal safety.",
  },
  {
    icon: Home,
    title: "Land & Housing",
    text: "Issues involving land, tenancy, eviction, ownership or housing disputes.",
  },
  {
    icon: HeartHandshake,
    title: "Family & Inheritance",
    text: "Questions affecting marriage, children, family responsibilities or inheritance.",
  },
  {
    icon: Landmark,
    title: "Public Services",
    text: "Concerns involving public institutions, access to services or administrative decisions.",
  },
  {
    icon: Users,
    title: "Community & Discrimination",
    text: "Situations involving unfair treatment, exclusion or rights within the community.",
  },
];

const nextSteps = [
  {
    icon: BookOpen,
    title: "Understand",
    text: "Get clear information in plain language.",
  },
  {
    icon: Scale,
    title: "Decide",
    text: "See practical options and important considerations.",
  },
  {
    icon: Building2,
    title: "Connect",
    text: "Find appropriate support when you need more help.",
  },
];

export default function Rights() {
  return (
    <>
      {/* FULL SCREEN HERO */}
      <section className="rights-hero relative isolate flex min-h-[calc(100svh-74px)] overflow-hidden">
        <img
          src={legalBackground}
          alt=""
          aria-hidden="true"
          className="rights-hero-image absolute inset-0 -z-30 h-full w-full object-cover object-[68%_center] lg:object-center"
        />

        <div
          aria-hidden="true"
          className="rights-hero-overlay absolute inset-0 -z-20"
        />

        <div
          aria-hidden="true"
          className="rights-hero-bottom absolute inset-x-0 bottom-0 -z-10 h-32"
        />

        <div className="site-container flex w-full items-center py-16 sm:py-20 lg:py-24">
          <div className="max-w-[720px] animate-fade-up">
            <div className="mb-6 flex items-center gap-3">
              <span className="gold-rule-grow" />

              <p className="text-xs font-bold uppercase tracking-[0.22em] text-gold-deep dark:text-gold">
                Know your rights
              </p>
            </div>

            <h1 className="heading-serif text-balance text-4xl font-semibold leading-[1.03] text-[#242424] dark:text-white sm:text-5xl md:text-6xl lg:text-7xl">
              Start with
              <span className="block">
                your situation,
              </span>

              <span className="block text-gold-deep dark:text-gold">
                not legal jargon.
              </span>
            </h1>

            <p className="mt-7 max-w-[600px] text-base leading-7 text-[#625f59] dark:text-white/72 sm:text-lg sm:leading-8">
              You do not need to know the law before you begin. Choose
              the situation that best describes what is happening and
              Sauti Yo will help you understand relevant rights and
              possible next steps.
            </p>

            <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:gap-x-7">
              {[
                "Plain-language guidance",
                "Practical next steps",
                "Support when needed",
              ].map((item) => (
                <div
                  key={item}
                  className="flex items-center gap-2 text-sm text-[#6b675f] dark:text-white/68"
                >
                  <CheckCircle2 className="h-4 w-4 shrink-0 text-gold" />

                  <span>{item}</span>
                </div>
              ))}
            </div>

            <div className="mt-10 flex flex-col gap-3 sm:flex-row">
              <a
                href="#rights-categories"
                className="group inline-flex min-h-12 w-full items-center justify-center gap-3 border border-gold bg-gold px-6 py-3 text-sm font-bold text-[#1c1c1c] transition-all duration-300 hover:bg-gold-deep hover:shadow-[var(--shadow-gold)] sm:w-auto"
              >
                Explore Your Rights

                <ArrowRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-1" />
              </a>

              <a
                href="#what-happens-next"
                className="inline-flex min-h-12 w-full items-center justify-center border border-black/20 bg-white/35 px-6 py-3 text-sm font-semibold text-[#292929] backdrop-blur-sm transition-all duration-300 hover:border-gold hover:bg-gold/10 hover:text-gold-deep dark:border-white/25 dark:bg-black/10 dark:text-white dark:hover:text-gold sm:w-auto"
              >
                How It Helps
              </a>
            </div>
          </div>
        </div>

        <a
          href="#rights-categories"
          aria-label="Scroll to rights categories"
          className="absolute bottom-7 left-1/2 hidden -translate-x-1/2 flex-col items-center gap-2 text-[#6e695f] transition-colors hover:text-gold dark:text-white/55 md:flex"
        >
          <span className="text-[10px] font-semibold uppercase tracking-[0.22em]">
            Explore
          </span>

          <span className="flex h-9 w-6 justify-center rounded-full border border-black/25 pt-2 dark:border-white/25">
            <span className="h-1.5 w-1.5 rounded-full bg-gold motion-safe:animate-bounce" />
          </span>
        </a>
      </section>

      {/* REAL LIFE INTRO */}
      <section
        id="rights-categories"
        className="scroll-mt-20 bg-surface py-20 sm:py-24 lg:py-28"
      >
        <div className="site-container">
          <div className="grid items-center gap-12 lg:grid-cols-[0.8fr_1.2fr] lg:gap-16">
            <div>
              <div className="mb-5 flex items-center gap-3">
                <span className="gold-rule" />

                <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                  Choose what fits best
                </p>
              </div>

              <h2 className="heading-serif text-balance text-3xl font-semibold leading-tight text-text-primary sm:text-4xl lg:text-5xl">
                Rights make more sense when they begin with real life.
              </h2>

              <p className="mt-6 max-w-xl text-base leading-7 text-text-secondary">
                Sauti Yo begins with situations people recognise in
                everyday life, then guides them toward relevant rights,
                practical options and appropriate support.
              </p>

              <p className="mt-4 max-w-xl text-sm leading-6 text-text-secondary">
                You do not need to identify a legal category perfectly.
                Pick the option that feels closest to what happened.
              </p>
            </div>

            <div className="image-fade image-fade-left min-h-[340px] sm:min-h-[440px] lg:min-h-[540px]">
              <img
                src={communityRightsSession}
                alt="A Sauti Yo community rights session"
                className="image-soften h-full w-full object-cover"
              />
            </div>
          </div>

          <div className="mt-16 grid gap-x-10 gap-y-12 md:grid-cols-2 xl:grid-cols-3">
            {rightsCategories.map((category) => {
              const Icon = category.icon;

              return (
                <button
                  key={category.title}
                  type="button"
                  className="group flex min-h-[230px] flex-col items-start border-t border-border pt-6 text-left transition-all duration-300 hover:border-gold"
                >
                  <div className="flex h-11 w-11 items-center justify-center rounded-full bg-gold/10 text-gold transition-all duration-300 group-hover:-translate-y-1 group-hover:bg-gold group-hover:text-[#1f1f1f]">
                    <Icon
                      className="h-5 w-5"
                      strokeWidth={1.7}
                    />
                  </div>

                  <h3 className="mt-5 text-xl font-semibold text-text-primary">
                    {category.title}
                  </h3>

                  <p className="mt-3 max-w-sm text-sm leading-6 text-text-secondary">
                    {category.text}
                  </p>

                  <div className="mt-auto pt-6">
                    <span className="inline-flex items-center gap-2 text-sm font-semibold text-gold-deep transition-all duration-300 group-hover:gap-3 dark:text-gold">
                      Explore this situation

                      <ArrowRight className="h-4 w-4" />
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </section>

      {/* NEXT STEPS */}
      <section
        id="what-happens-next"
        className="scroll-mt-20 bg-background py-20 sm:py-24 lg:py-28"
      >
        <div className="site-container">
          <div className="grid gap-12 lg:grid-cols-[0.72fr_1.28fr] lg:items-start lg:gap-20">
            <div>
              <div className="mb-5 flex items-center gap-3">
                <span className="gold-rule" />

                <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                  What happens next
                </p>
              </div>

              <h2 className="heading-serif text-balance text-3xl font-semibold leading-tight text-text-primary sm:text-4xl lg:text-5xl">
                Rights information is only useful when it helps you act.
              </h2>

              <p className="mt-5 max-w-md text-base leading-7 text-text-secondary">
                The goal is not simply to show you legal information.
                It is to help turn that information into a clearer,
                safer next step.
              </p>
            </div>

            <div className="grid gap-8 sm:grid-cols-3">
              {nextSteps.map((step) => {
                const Icon = step.icon;

                return (
                  <article key={step.title}>
                    <div className="flex h-11 w-11 items-center justify-center rounded-full bg-gold/10 text-gold">
                      <Icon
                        className="h-5 w-5"
                        strokeWidth={1.6}
                      />
                    </div>

                    <h3 className="mt-5 text-lg font-semibold text-text-primary">
                      {step.title}
                    </h3>

                    <p className="mt-2 text-sm leading-6 text-text-secondary">
                      {step.text}
                    </p>
                  </article>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="relative overflow-hidden bg-[#191919] text-white">
        <div className="site-container relative py-16 sm:py-20 lg:py-24">
          <div className="grid gap-8 lg:grid-cols-[1fr_auto] lg:items-center">
            <div className="max-w-3xl">
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold">
                Not sure which category fits?
              </p>

              <h2 className="heading-serif mt-4 text-balance text-3xl font-semibold leading-tight sm:text-4xl lg:text-5xl">
                Start with what happened.

                <span className="block text-gold">
                  We’ll help you work it out.
                </span>
              </h2>

              <p className="mt-5 max-w-2xl text-base leading-7 text-white/65">
                You should not have to identify the legal issue before
                you can get useful guidance.
              </p>
            </div>

            <button
              type="button"
              className="group inline-flex min-h-12 w-full items-center justify-center gap-2 border border-gold bg-gold px-7 py-3 font-bold text-[#191919] transition-all duration-300 hover:bg-transparent hover:text-gold sm:w-auto"
            >
              Help Me Choose

              <ArrowRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-1" />
            </button>
          </div>
        </div>
      </section>
    </>
  );
}