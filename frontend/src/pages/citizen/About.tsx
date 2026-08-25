import {
  ArrowRight,
  CheckCircle2,
  Ear,
  Languages,
  Lightbulb,
  MessageSquareText,
  ShieldCheck,
  Smartphone,
  Users,
} from "lucide-react";
import { Link } from "react-router-dom";

import aboutCommunityConversation from "../../assets/images/about-community-conversation.png";

const principles = [
  {
    icon: Ear,
    number: "01",
    title: "Understand",
    text: "Begin with what a person is actually experiencing, not the legal terminology they may not know.",
  },
  {
    icon: Lightbulb,
    number: "02",
    title: "Act",
    text: "Turn rights information into practical options and understandable next steps.",
  },
  {
    icon: Users,
    number: "03",
    title: "Connect",
    text: "Help people identify appropriate services and support when they need more than information.",
  },
];

const differences = [
  {
    icon: MessageSquareText,
    title: "Plain language",
    text: "Rights information should be understandable without requiring legal training.",
  },
  {
    icon: Smartphone,
    title: "Accessible by design",
    text: "Sauti Yo is designed for smartphones, the web and basic-phone channels.",
  },
  {
    icon: Languages,
    title: "Language matters",
    text: "People should be able to access important information in language that feels familiar.",
  },
  {
    icon: ShieldCheck,
    title: "Responsible guidance",
    text: "The platform supports informed decisions without pretending to replace professional legal advice.",
  },
];

export default function About() {
  return (
    <>
      {/* =========================================================
          HERO
      ========================================================= */}
      <section className="relative overflow-hidden bg-background">
        <div
          aria-hidden="true"
          className="absolute -right-24 -top-24 h-[420px] w-[420px] rounded-full bg-gold/5 blur-3xl"
        />

        <div className="site-container py-16 sm:py-20 lg:py-24 xl:py-28">
          <div className="grid items-center gap-12 lg:grid-cols-[0.85fr_1.15fr] lg:gap-16">
            {/* COPY */}
            <div className="max-w-xl">
              <div className="mb-6 flex items-center gap-3">
                <span className="gold-rule" />

                <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                  About Sauti Yo
                </p>
              </div>

              <h1 className="heading-serif text-[2.8rem] font-semibold leading-[1.03] text-text-primary sm:text-5xl lg:text-6xl">
                Know.
                <span className="text-gold-deep dark:text-gold"> Act.</span>
                <span className="block">Be Heard.</span>
              </h1>

              <p className="mt-7 text-base leading-7 text-text-secondary sm:text-lg sm:leading-8">
                Sauti Yo is a rights-to-action platform designed to help people
                understand their rights, identify practical next steps and
                connect with appropriate support.
              </p>

              <p className="mt-4 text-base leading-7 text-text-secondary">
                We believe rights information becomes truly useful when people
                can understand what it means for their own lives and know what
                they can do next.
              </p>

              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                <Link to="/rights" className="btn-primary w-full sm:w-auto">
                  Explore Your Rights
                  <ArrowRight className="h-4 w-4" />
                </Link>

                <Link
                  to="/how-it-works"
                  className="btn-secondary w-full sm:w-auto"
                >
                  How It Works
                </Link>
              </div>
            </div>

            {/* UNIQUE ABOUT IMAGE */}
            <div className="relative">
              <div
                aria-hidden="true"
                className="absolute -inset-5 -z-10 bg-gold/5 blur-3xl"
              />

              <div className="image-frame overflow-hidden">
                <img
                  src={aboutCommunityConversation}
                  alt="A Sauti Yo community conversation about rights and practical next steps"
                  className="image-soften h-[360px] w-full object-cover sm:h-[440px] lg:h-[520px]"
                />
              </div>

              <div className="absolute bottom-5 left-5 border border-border bg-surface/95 px-5 py-4 shadow-[var(--shadow-soft)] backdrop-blur-sm sm:bottom-7 sm:left-7">
                <p className="text-xs font-bold uppercase tracking-[0.16em] text-gold-deep dark:text-gold">
                  Rights begin with people
                </p>

                <p className="mt-1 max-w-[230px] text-xs leading-5 text-text-secondary">
                  Real situations. Clear information. Practical next steps.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================
          WHY SAUTI YO
      ========================================================= */}
      <section className="section-padding bg-surface-soft">
        <div className="site-container">
          <div className="grid gap-12 lg:grid-cols-[0.8fr_1.2fr] lg:gap-20">
            <div>
              <div className="mb-5 flex items-center gap-3">
                <span className="gold-rule" />

                <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                  Why Sauti Yo
                </p>
              </div>

              <h2 className="heading-serif text-3xl font-semibold leading-tight text-text-primary sm:text-4xl lg:text-5xl">
                Knowing you have rights
                <span className="block text-gold-deep dark:text-gold">
                  is not always enough.
                </span>
              </h2>
            </div>

            <div className="max-w-2xl lg:pt-8">
              <p className="text-lg leading-8 text-text-primary">
                Rights can exist on paper while still feeling difficult to use
                in everyday life.
              </p>

              <p className="mt-5 text-base leading-7 text-text-secondary">
                Legal information may be difficult to understand, people may
                not know which category their situation belongs to, and the
                right support service may be hard to identify.
              </p>

              <p className="mt-5 text-base leading-7 text-text-secondary">
                Sauti Yo is designed to reduce that gap. Instead of asking
                people to begin with legal vocabulary, the platform begins with
                something much more familiar:
              </p>

              <blockquote className="heading-serif mt-7 border-l-2 border-gold pl-6 text-2xl font-semibold leading-snug text-text-primary sm:text-3xl">
                “What happened?”
              </blockquote>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================
          OUR APPROACH
      ========================================================= */}
      <section className="section-padding bg-background">
        <div className="site-container">
          <div className="mx-auto max-w-3xl text-center">
            <div className="mb-4 flex items-center justify-center gap-3">
              <span className="gold-rule" />

              <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                Our approach
              </p>

              <span className="gold-rule" />
            </div>

            <h2 className="heading-serif text-3xl font-semibold text-text-primary sm:text-4xl lg:text-5xl">
              From information to action.
            </h2>

            <p className="mx-auto mt-5 max-w-2xl text-base leading-7 text-text-secondary">
              Sauti Yo is built around a simple journey that helps people move
              from uncertainty toward a clearer next step.
            </p>
          </div>

          <div className="mt-12 grid gap-5 lg:grid-cols-3">
            {principles.map((principle) => {
              const Icon = principle.icon;

              return (
                <article
                  key={principle.number}
                  className="group relative border-t border-border px-1 pb-4 pt-7"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex h-11 w-11 items-center justify-center rounded-full bg-gold/10">
                      <Icon
                        className="h-5 w-5 text-gold-deep dark:text-gold"
                        strokeWidth={1.6}
                      />
                    </div>

                    <span className="heading-serif text-4xl font-semibold text-gold/20">
                      {principle.number}
                    </span>
                  </div>

                  <h3 className="mt-6 text-xl font-semibold text-text-primary">
                    {principle.title}
                  </h3>

                  <p className="mt-3 max-w-sm text-sm leading-6 text-text-secondary">
                    {principle.text}
                  </p>
                </article>
              );
            })}
          </div>
        </div>
      </section>

      {/* =========================================================
          STATEMENT BAND
      ========================================================= */}
      <section className="bg-[#1c1c1c] text-white">
        <div className="site-container py-16 sm:py-20 lg:py-24">
          <div className="grid gap-10 lg:grid-cols-[1fr_0.8fr] lg:items-end">
            <div className="max-w-3xl">
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold">
                The idea behind Sauti Yo
              </p>

              <h2 className="heading-serif mt-5 text-3xl font-semibold leading-tight sm:text-4xl lg:text-5xl">
                Justice should not depend on
                <span className="text-gold">
                  {" "}
                  understanding legal jargon.
                </span>
              </h2>
            </div>

            <p className="max-w-xl text-sm leading-7 text-white/65 sm:text-base">
              People should be able to recognise their situation, understand
              relevant information and make informed decisions about what to do
              next.
            </p>
          </div>
        </div>
      </section>

      {/* =========================================================
          WHAT MAKES SAUTI YO DIFFERENT
      ========================================================= */}
      <section className="section-padding bg-surface">
        <div className="site-container">
          <div className="grid gap-12 lg:grid-cols-[0.7fr_1.3fr] lg:gap-20">
            <div>
              <div className="mb-5 flex items-center gap-3">
                <span className="gold-rule" />

                <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                  Designed differently
                </p>
              </div>

              <h2 className="heading-serif text-3xl font-semibold leading-tight text-text-primary sm:text-4xl">
                Rights information built around real life.
              </h2>

              <p className="mt-5 text-base leading-7 text-text-secondary">
                The goal is not to make people become lawyers. It is to help
                them understand enough to make a more informed next decision.
              </p>
            </div>

            <div className="grid gap-x-10 gap-y-8 sm:grid-cols-2">
              {differences.map((difference) => {
                const Icon = difference.icon;

                return (
                  <article
                    key={difference.title}
                    className="border-t border-border pt-6"
                  >
                    <Icon
                      className="h-6 w-6 text-gold-deep dark:text-gold"
                      strokeWidth={1.5}
                    />

                    <h3 className="mt-4 text-lg font-semibold text-text-primary">
                      {difference.title}
                    </h3>

                    <p className="mt-2 text-sm leading-6 text-text-secondary">
                      {difference.text}
                    </p>
                  </article>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================
          MISSION + VISION
      ========================================================= */}
      <section className="section-padding bg-background">
        <div className="site-container">
          <div className="grid border-y border-border lg:grid-cols-2">
            <article className="py-10 lg:border-r lg:border-border lg:py-14 lg:pr-14">
              <p className="text-xs font-bold uppercase tracking-[0.18em] text-gold-deep dark:text-gold">
                Our mission
              </p>

              <h2 className="heading-serif mt-5 text-3xl font-semibold leading-tight text-text-primary">
                Make rights easier to understand and easier to act on.
              </h2>

              <p className="mt-5 max-w-xl text-base leading-7 text-text-secondary">
                To provide accessible, practical rights information that helps
                people understand their situations, consider appropriate next
                steps and connect with relevant support.
              </p>
            </article>

            <article className="py-10 lg:py-14 lg:pl-14">
              <p className="text-xs font-bold uppercase tracking-[0.18em] text-gold-deep dark:text-gold">
                Our vision
              </p>

              <h2 className="heading-serif mt-5 text-3xl font-semibold leading-tight text-text-primary">
                A society where people can recognise and exercise their rights.
              </h2>

              <p className="mt-5 max-w-xl text-base leading-7 text-text-secondary">
                A future where access to understandable rights information is
                not limited by legal knowledge, device type, connectivity or
                language.
              </p>
            </article>
          </div>
        </div>
      </section>

      {/* =========================================================
          VALUES / TRUST
      ========================================================= */}
      <section className="section-padding bg-surface-soft">
        <div className="site-container">
          <div className="grid items-start gap-12 lg:grid-cols-[0.85fr_1.15fr] lg:gap-20">
            <div>
              <div className="mb-5 flex items-center gap-3">
                <span className="gold-rule" />

                <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                  What guides us
                </p>
              </div>

              <h2 className="heading-serif text-3xl font-semibold text-text-primary sm:text-4xl">
                Useful. Accessible.
                <span className="block text-gold-deep dark:text-gold">
                  Responsible.
                </span>
              </h2>
            </div>

            <div className="space-y-5">
              {[
                "Information should be clear enough to understand.",
                "Technology should expand access, not create another barrier.",
                "People should remain in control of their own decisions.",
                "Sensitive situations require responsible and safety-conscious guidance.",
                "When information is not enough, people should be able to find appropriate support.",
              ].map((value) => (
                <div
                  key={value}
                  className="flex gap-4 border-b border-border pb-5"
                >
                  <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-gold" />

                  <p className="text-base leading-7 text-text-secondary">
                    {value}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================
          FINAL CTA
      ========================================================= */}
      <section className="bg-[#1c1c1c] text-white">
        <div className="site-container py-16 sm:py-20">
          <div className="grid gap-8 lg:grid-cols-[1fr_auto] lg:items-center">
            <div className="max-w-3xl">
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold">
                Know. Act. Be Heard.
              </p>

              <h2 className="heading-serif mt-4 text-3xl font-semibold leading-tight sm:text-4xl lg:text-5xl">
                You do not need to know the law
                <span className="block text-gold">before you begin.</span>
              </h2>

              <p className="mt-5 max-w-2xl text-base leading-7 text-white/60">
                Start with what happened. Sauti Yo will help you understand
                where to go from there.
              </p>
            </div>

            <Link
              to="/rights"
              className="inline-flex min-h-12 w-full items-center justify-center gap-2 border border-gold bg-gold px-7 py-3 font-bold text-[#191919] transition duration-300 hover:bg-transparent hover:text-gold sm:w-auto"
            >
              Start With Your Situation
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}