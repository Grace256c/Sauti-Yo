import {
  ArrowRight,
  BookOpen,
  CheckCircle2,
  Headphones,
  Languages,
  MessageSquareText,
  Phone,
  Scale,
  ShieldCheck,
  Users,
} from "lucide-react";
import { Link } from "react-router-dom";

import legalBackground from "../../assets/images/legal-background.png";
import featurePhoneUssd from "../../assets/images/feature-phone-ussd.png";
import communityRightsSession from "../../assets/images/community-rights-session.png";

const steps = [
  {
    number: "01",
    icon: Users,
    title: "Tell us what happened",
    text: "Begin with the situation you are experiencing. You do not need to know the legal name for the problem.",
  },
  {
    number: "02",
    icon: BookOpen,
    title: "Understand your rights",
    text: "Sauti Yo presents relevant rights information in clear, accessible language.",
  },
  {
    number: "03",
    icon: Scale,
    title: "Explore your options",
    text: "See possible next steps, practical considerations and important safety information.",
  },
  {
    number: "04",
    icon: ShieldCheck,
    title: "Find appropriate support",
    text: "When more help is needed, Sauti Yo can guide you toward relevant support services.",
  },
];

const accessChannels = [
  {
    icon: Phone,
    title: "USSD",
    text: "Use Sauti Yo from a basic feature phone without mobile data.",
  },
  {
    icon: MessageSquareText,
    title: "SMS",
    text: "Receive concise guidance and follow-up information by text.",
  },
  {
    icon: Headphones,
    title: "Voice",
    text: "Listen to guided rights information where reading may be difficult.",
  },
  {
    icon: Languages,
    title: "Web",
    text: "Use the richer experience on a smartphone, tablet or computer.",
  },
];

export default function HowItWorks() {
  return (
    <>
      {/* HERO */}
      <section className="relative isolate overflow-hidden bg-background">
        <img
          src={legalBackground}
          alt=""
          aria-hidden="true"
          className="legal-image absolute inset-0 -z-20 h-full w-full object-cover object-[72%_center]"
        />

        <div className="legal-overlay-light absolute inset-0 -z-10" />

        <div className="site-container py-20 sm:py-24 lg:py-32">
          <div className="max-w-3xl animate-fade-up">
            <div className="mb-5 flex items-center gap-3">
              <span className="gold-rule" />

              <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                How Sauti Yo works
              </p>
            </div>

            <h1 className="heading-serif text-balance text-4xl font-semibold leading-[1.05] text-text-primary sm:text-5xl lg:text-6xl">
              From uncertainty
              <span className="block text-gold-deep dark:text-gold">
                to a practical next step.
              </span>
            </h1>

            <p className="mt-7 max-w-2xl text-base leading-7 text-text-secondary sm:text-lg sm:leading-8">
              Sauti Yo is designed to help people move from a real-life
              situation to clear rights information, practical options
              and appropriate support.
            </p>

            <div className="mt-8 flex flex-wrap gap-x-6 gap-y-3">
              {[
                "Situation-first guidance",
                "Plain-language information",
                "Multiple access channels",
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
          </div>
        </div>
      </section>

      {/* FOUR STEPS */}
      <section className="section-padding bg-surface">
        <div className="site-container">
          <div className="mx-auto max-w-3xl text-center">
            <div className="mb-4 flex items-center justify-center gap-3">
              <span className="gold-rule" />

              <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                The journey
              </p>

              <span className="gold-rule" />
            </div>

            <h2 className="heading-serif text-3xl font-semibold text-text-primary sm:text-4xl lg:text-5xl">
              Four simple stages
            </h2>

            <p className="mx-auto mt-5 max-w-2xl text-base leading-7 text-text-secondary">
              The experience is designed to reduce confusion and help a
              person move forward one step at a time.
            </p>
          </div>

          <div className="mt-12 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
            {steps.map((step) => {
              const Icon = step.icon;

              return (
                <article
                  key={step.number}
                  className="card-surface relative overflow-hidden p-6 sm:p-7"
                >
                  <span className="heading-serif absolute right-4 top-1 text-6xl font-bold text-gold/10">
                    {step.number}
                  </span>

                  <div className="relative">
                    <div className="flex h-11 w-11 items-center justify-center rounded-full bg-gold/10 text-gold">
                      <Icon className="h-5 w-5" strokeWidth={1.7} />
                    </div>

                    <p className="mt-5 text-xs font-bold uppercase tracking-[0.15em] text-gold-deep dark:text-gold">
                      Step {step.number}
                    </p>

                    <h3 className="mt-3 text-xl font-semibold text-text-primary">
                      {step.title}
                    </h3>

                    <p className="mt-3 text-sm leading-6 text-text-secondary">
                      {step.text}
                    </p>
                  </div>
                </article>
              );
            })}
          </div>
        </div>
      </section>

      {/* REAL LIFE EXAMPLE */}
      <section className="section-padding bg-background">
        <div className="site-container">
          <div className="grid items-center gap-12 lg:grid-cols-2 lg:gap-16">
            <div className="image-frame">
              <img
                src={communityRightsSession}
                alt="A Sauti Yo community rights session"
                className="image-soften h-[340px] w-full object-cover sm:h-[440px] lg:h-[520px]"
              />
            </div>

            <div>
              <div className="mb-5 flex items-center gap-3">
                <span className="gold-rule" />

                <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                  What this means in practice
                </p>
              </div>

              <h2 className="heading-serif text-3xl font-semibold leading-tight text-text-primary sm:text-4xl lg:text-5xl">
                Start with the experience,
                <span className="block text-gold-deep dark:text-gold">
                  then connect it to the law.
                </span>
              </h2>

              <p className="mt-6 text-base leading-7 text-text-secondary">
                Instead of asking someone to choose a legal doctrine,
                Sauti Yo begins with familiar situations such as a
                workplace problem, a safety concern or a land dispute.
              </p>

              <p className="mt-4 text-base leading-7 text-text-secondary">
                From there, the platform can present relevant rights,
                practical actions and support options in a more useful
                order.
              </p>

              <Link to="/rights" className="btn-primary mt-8">
                Explore Your Rights
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ACCESS CHANNELS */}
      <section className="section-padding bg-surface-soft">
        <div className="site-container">
          <div className="grid items-center gap-12 lg:grid-cols-[0.9fr_1.1fr] lg:gap-16">
            <div>
              <div className="mb-5 flex items-center gap-3">
                <span className="gold-rule" />

                <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                  One experience, different channels
                </p>
              </div>

              <h2 className="heading-serif text-3xl font-semibold text-text-primary sm:text-4xl lg:text-5xl">
                Access should not depend on owning a smartphone.
              </h2>

              <p className="mt-6 max-w-xl text-base leading-7 text-text-secondary">
                Sauti Yo is designed so the same core guidance can be
                delivered through different channels depending on
                connectivity, device and accessibility needs.
              </p>

              <div className="mt-8 grid gap-4 sm:grid-cols-2">
                {accessChannels.map((channel) => {
                  const Icon = channel.icon;

                  return (
                    <div
                      key={channel.title}
                      className="border-l-2 border-gold bg-surface p-4"
                    >
                      <Icon
                        className="h-5 w-5 text-gold"
                        strokeWidth={1.7}
                      />

                      <h3 className="mt-3 font-semibold text-text-primary">
                        {channel.title}
                      </h3>

                      <p className="mt-1 text-sm leading-6 text-text-secondary">
                        {channel.text}
                      </p>
                    </div>
                  );
                })}
              </div>

              <Link to="/access" className="btn-secondary mt-8">
                See Access Options
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>

            <div className="image-frame">
              <img
                src={featurePhoneUssd}
                alt="Sauti Yo access on a feature phone"
                className="image-soften h-full w-full object-cover"
              />
            </div>
          </div>
        </div>
      </section>

      {/* FINAL CTA */}
      <section className="bg-[#191919] text-white">
        <div className="site-container py-16 sm:py-20">
          <div className="grid gap-8 lg:grid-cols-[1fr_auto] lg:items-center">
            <div className="max-w-3xl">
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold">
                Ready to begin?
              </p>

              <h2 className="heading-serif mt-4 text-3xl font-semibold sm:text-4xl lg:text-5xl">
                Start with what happened.
                <span className="block text-gold">
                  Sauti Yo will guide you from there.
                </span>
              </h2>
            </div>

            <Link
              to="/rights"
              className="inline-flex min-h-12 w-full items-center justify-center gap-2 border border-gold bg-gold px-7 py-3 font-bold text-[#191919] transition hover:bg-transparent hover:text-gold sm:w-auto"
            >
              Start Here
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}