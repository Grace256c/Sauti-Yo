import {
  ArrowRight,
  BookOpen,
  Building2,
  CheckCircle2,
  Scale,
} from "lucide-react";
import { Link } from "react-router-dom";

import legalBackground from "../../assets/images/legal-background.png";
import { rightsCategories } from "../../data/rightsData";

const nextSteps = [
  {
    icon: BookOpen,
    number: "01",
    title: "You'll answer a few questions",
    text: "A short, guided conversation about your specific situation — nothing more than necessary.",
  },
  {
    icon: Scale,
    number: "02",
    title: "You'll see what applies to you",
    text: "Not general information — the specific rights, options and considerations relevant to what you told us.",
  },
  {
    icon: Building2,
    number: "03",
    title: "You'll know what to do",
    text: "A clear next step, plus a way to reach real support if your situation needs more than information.",
  },
];

export default function Rights() {
  return (
    <>
      {/* HERO */}
      <section className="relative isolate overflow-hidden bg-background">
        <img
          src={legalBackground}
          alt=""
          aria-hidden="true"
          className="legal-image absolute inset-0 -z-20 h-full w-full object-cover object-[72%_center] sm:object-center"
        />

        <div className="legal-overlay-light absolute inset-0 -z-10" />

        <div className="site-container py-20 sm:py-24 lg:py-28 xl:py-32">
          <div className="max-w-[720px]">
            <div className="mb-6 flex items-center gap-3">
              <span className="gold-rule" />

              <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                Know your rights
              </p>
            </div>

            <h1 className="heading-serif text-balance text-4xl font-semibold leading-[1.04] text-text-primary sm:text-5xl lg:text-6xl xl:text-[4.3rem]">
              Start with your situation,
              <span className="block text-gold-deep dark:text-gold">
                not legal jargon.
              </span>
            </h1>

            <p className="mt-7 max-w-xl text-base leading-7 text-text-secondary sm:text-lg sm:leading-8">
              You do not need to know the law before you begin. Choose
              the situation that feels closest to what happened and
              Sauti Yo will help you work from there.
            </p>

            <div className="mt-8 flex flex-wrap gap-x-6 gap-y-3">
              {[
                "Plain-language information",
                "Practical next steps",
                "Support when needed",
              ].map((item) => (
                <div
                  key={item}
                  className="flex items-center gap-2 text-sm text-text-secondary"
                >
                  <CheckCircle2 className="h-4 w-4 text-gold" />
                  {item}
                </div>
              ))}
            </div>

            <a
              href="#rights-categories"
              className="btn-primary mt-9"
            >
              Explore Your Rights
              <ArrowRight className="h-4 w-4" />
            </a>
          </div>
        </div>
      </section>

      {/* CATEGORY INTRO */}
      <section
        id="rights-categories"
        className="scroll-mt-24 bg-surface py-16 sm:py-20 lg:py-24"
      >
        <div className="site-container">
          <div className="grid gap-10 lg:grid-cols-[0.75fr_1.25fr] lg:items-end lg:gap-20">
            <div>
              <div className="mb-5 flex items-center gap-3">
                <span className="gold-rule" />

                <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                  Choose what fits best
                </p>
              </div>

              <h2 className="heading-serif text-3xl font-semibold leading-tight text-text-primary sm:text-4xl lg:text-5xl">
                What best describes
                <span className="block text-gold-deep dark:text-gold">
                  what happened?
                </span>
              </h2>
            </div>

            <div className="max-w-2xl">
              <p className="text-base leading-7 text-text-secondary">
                Select the category that feels closest to your experience.
                It does not have to describe your situation perfectly,
                and you can always go back and choose another one.
              </p>
            </div>
          </div>

          {/* RIGHTS CATEGORIES */}
          <div className="mt-12 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
            {rightsCategories.map((category) => {
              const Icon = category.icon;

              return (
                <Link
                  key={category.slug}
                  to={`/rights/${category.slug}`}
                  className="card-surface group flex min-h-[250px] flex-col items-start p-6 text-left sm:p-7"
                >
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gold/10 text-gold transition-all duration-300 group-hover:-translate-y-1 group-hover:bg-gold group-hover:text-[#1f1f1f]">
                    <Icon
                      className="h-5 w-5"
                      strokeWidth={1.7}
                    />
                  </div>

                  <h3 className="mt-5 text-xl font-semibold text-text-primary">
                    {category.title}
                  </h3>

                  <p className="mt-3 text-sm leading-6 text-text-secondary">
                    {category.shortDescription}
                  </p>

                  <span className="mt-auto inline-flex items-center gap-2 pt-6 text-sm font-semibold text-gold-deep transition-all duration-300 group-hover:gap-3 dark:text-gold">
                    Explore this situation

                    <ArrowRight className="h-4 w-4" />
                  </span>
                </Link>
              );
            })}
          </div>
        </div>
      </section>

      {/* HELP ME CHOOSE */}
      <section className="bg-surface-soft py-14 sm:py-16">
        <div className="site-container">
          <div className="grid items-center gap-8 border-y border-border py-10 lg:grid-cols-[1fr_auto]">
            <div className="max-w-2xl">
              <p className="text-xs font-bold uppercase tracking-[0.18em] text-gold-deep dark:text-gold">
                Not sure which category fits?
              </p>

              <h2 className="heading-serif mt-3 text-2xl font-semibold text-text-primary sm:text-3xl">
                Start with what happened.
              </h2>

              <p className="mt-3 text-sm leading-6 text-text-secondary sm:text-base">
                You should not need to identify the legal issue before
                you can get useful information.
              </p>
            </div>

            <Link
              to="/rights/navigator"
              className="btn-secondary w-full lg:w-auto"
            >
              Help Me Choose
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* WHAT HAPPENS NEXT */}
      <section className="section-padding bg-background">
        <div className="site-container">
          <div className="grid gap-12 lg:grid-cols-[0.72fr_1.28fr] lg:gap-20">
            <div>
              <div className="mb-5 flex items-center gap-3">
                <span className="gold-rule" />

                <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                  Once you choose a category
                </p>
              </div>

              <h2 className="heading-serif text-3xl font-semibold leading-tight text-text-primary sm:text-4xl lg:text-5xl">
                Here's exactly
                <span className="block text-gold-deep dark:text-gold">
                  what happens next.
                </span>
              </h2>

              <p className="mt-5 max-w-md text-base leading-7 text-text-secondary">
                Picking a category above starts this guide. It only takes
                a couple of minutes.
              </p>
            </div>

            <div className="grid gap-8 sm:grid-cols-3">
              {nextSteps.map((step) => {
                const Icon = step.icon;

                return (
                  <article
                    key={step.number}
                    className="border-t border-border pt-6"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex h-11 w-11 items-center justify-center rounded-full bg-gold/10 text-gold">
                        <Icon
                          className="h-5 w-5"
                          strokeWidth={1.6}
                        />
                      </div>

                      <span className="heading-serif text-3xl font-semibold text-gold/20">
                        {step.number}
                      </span>
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

      {/* SUPPORT BRIDGE */}
      <section className="bg-[#1c1c1c] text-white">
        <div className="site-container py-16 sm:py-20">
          <div className="grid gap-10 lg:grid-cols-[1fr_0.8fr] lg:items-center">
            <div className="max-w-3xl">
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold">
                When information is not enough
              </p>

              <h2 className="heading-serif mt-4 text-3xl font-semibold leading-tight sm:text-4xl lg:text-5xl">
                Some situations need
                <span className="block text-gold">
                  specialised support.
                </span>
              </h2>

              <p className="mt-5 max-w-2xl text-base leading-7 text-white/65">
                Sauti Yo can help users identify appropriate organisations
                and support services when their situation requires more
                than general rights information.
              </p>
            </div>

            <div className="lg:justify-self-end">
              <Link
                to="/support"
                className="inline-flex min-h-12 w-full items-center justify-center gap-2 border border-gold bg-gold px-7 py-3 font-bold text-[#191919] transition duration-300 hover:bg-transparent hover:text-gold sm:w-auto"
              >
                Find Support
                <ArrowRight className="h-4 w-4" />
              </Link>

              <p className="mt-4 max-w-[290px] text-xs leading-5 text-white/45">
                Support pathways can later connect with approved organisations
                participating through the Sauti Yo partner system.
              </p>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}