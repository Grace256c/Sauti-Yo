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

import legalHeroBackground from "../../assets/images/legal-hero-background.png";
import homeRightsGuidance from "../../assets/images/home-rights-guidance.png";
import featurePhoneUssd from "../../assets/images/feature-phone-ussd.png";
import smartphoneMockup from "../../assets/images/smartphone-app-mockup.png";
import communityRightsSession from "../../assets/images/community-rights-session.png";
import legalSupportConsultation from "../../assets/images/legal-support-consultation.png";

const situations = [
  {
    icon: Users,
    title: "Work & Employment",
    text: "Understand your options when something happens at work.",
  },
  {
    icon: ShieldCheck,
    title: "Safety & Protection",
    text: "Find practical, safety-conscious next steps and support.",
  },
  {
    icon: Scale,
    title: "Land & Housing",
    text: "Explore information related to land, housing and property.",
  },
  {
    icon: BookOpen,
    title: "Family & Inheritance",
    text: "Understand common rights questions affecting families.",
  },
];

const steps = [
  {
    number: "01",
    title: "Share what happened",
    text: "In your own words — no legal terms needed.",
  },
  {
    number: "02",
    title: "Know your rights",
    text: "See exactly what protects you, explained plainly.",
  },
  {
    number: "03",
    title: "Get your next step",
    text: "A clear action to take, not just information.",
  },
  {
    number: "04",
    title: "Reach real support",
    text: "Connect with help when you need more than answers.",
  },
];

const channels = [
  {
    icon: Phone,
    title: "USSD",
    text: "Use a basic feature phone without mobile data.",
    action: "*384*163024#",
  },
  {
    icon: MessageSquareText,
    title: "SMS",
    text: "Receive clear information and follow-up by text.",
    action: "18275",
  },
  {
    icon: Headphones,
    title: "Voice",
    text: "Listen to guided information where reading may be difficult.",
    action: "+256 323 200 924",
  },
  {
    icon: Languages,
    title: "Web",
    text: "Use the richer web experience on a smartphone or computer.",
    action: null,
  },
];

export default function Home() {
  return (
    <>
      {/* HERO */}
      <section className="relative isolate min-h-[calc(100svh-74px)] overflow-hidden bg-background">
        {/* Legal background */}
        <img
          src={legalHeroBackground}
          alt=""
          aria-hidden="true"
          className="legal-image absolute inset-0 -z-30 h-full w-full object-cover object-[70%_center] sm:object-center"
        />

        {/* Light/dark legal overlay */}
        <div className="legal-overlay-light absolute inset-0 -z-20" />

        {/* Subtle gold atmosphere */}
        <div
          aria-hidden="true"
          className="absolute right-[8%] top-[20%] -z-10 h-72 w-72 rounded-full bg-gold/10 blur-3xl"
        />

        <div className="site-container flex min-h-[calc(100svh-74px)] items-center py-14 sm:py-16 lg:py-20">
          <div className="grid w-full items-center gap-12 lg:grid-cols-[0.9fr_1.1fr] lg:gap-14">
            {/* Hero copy */}
            <div className="max-w-2xl animate-fade-up">
              <div className="mb-6 flex items-center gap-3">
                <span className="gold-rule" />

                <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                  Rights to action
                </p>
              </div>

              <h1 className="heading-serif text-balance text-[2.75rem] font-semibold leading-[1.03] text-text-primary sm:text-5xl md:text-6xl xl:text-[4.4rem]">
                Something happened.
                <span className="mt-2 block text-gold-deep dark:text-gold">
                  Know what you can do next.
                </span>
              </h1>

              <p className="mt-7 max-w-xl text-base leading-7 text-text-secondary sm:text-lg sm:leading-8">
                Sauti Yo helps you understand your rights, explore practical
                next steps and connect with appropriate support — through the
                web or a basic phone.
              </p>

              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                <Link to="/rights" className="btn-primary w-full sm:w-auto">
                  Start Here
                  <ArrowRight className="h-4 w-4" />
                </Link>

                <Link
                  to="/how-it-works"
                  className="btn-secondary w-full sm:w-auto"
                >
                  See How It Works
                </Link>
              </div>

              <div className="mt-8 flex flex-wrap gap-x-6 gap-y-3">
                {[
                  "No app required",
                  "Feature-phone access",
                  "Multiple languages",
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

            {/* Human-centred foreground visual */}
            <div className="relative mx-auto w-full max-w-2xl lg:mx-0">
              <div
                aria-hidden="true"
                className="absolute -inset-5 -z-10 rounded-xl bg-white/20 blur-2xl dark:bg-black/15"
              />

              <div className="image-frame overflow-hidden rounded-sm">
                <img
                  src={homeRightsGuidance}
                  alt="A Sauti Yo guidance conversation using a smartphone"
                  className="image-soften h-[360px] w-full object-cover object-center sm:h-[430px] lg:h-[520px]"
                />
              </div>

              {/* Small trust badge */}
              <div className="absolute -bottom-5 left-4 max-w-[240px] border border-border bg-surface px-4 py-3 shadow-[var(--shadow-soft)] sm:left-6">
                <p className="text-xs font-bold uppercase tracking-[0.14em] text-gold-deep dark:text-gold">
                  Human-centred guidance
                </p>

                <p className="mt-1 text-xs leading-5 text-text-secondary">
                  Start with your real situation, not legal terminology.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* SITUATIONS */}
      <section className="section-padding bg-background">
        <div className="site-container">
          <div className="mx-auto max-w-3xl text-center">
            <div className="mb-4 flex items-center justify-center gap-3">
              <span className="gold-rule" />

              <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                Start with your situation
              </p>

              <span className="gold-rule" />
            </div>

            <h2 className="heading-serif text-3xl font-semibold text-text-primary sm:text-4xl lg:text-5xl">
              What is happening?
            </h2>

            <p className="mx-auto mt-5 max-w-2xl text-base leading-7 text-text-secondary">
              You do not need to know the legal name for your problem. Start
              with the situation you are experiencing.
            </p>
          </div>

          <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {situations.map((situation) => {
              const Icon = situation.icon;

              return (
                <Link
                  key={situation.title}
                  to="/rights"
                  className="card-surface group p-6 sm:p-7"
                >
                  <Icon className="h-7 w-7 text-gold" strokeWidth={1.5} />

                  <h3 className="mt-5 text-lg font-semibold text-text-primary">
                    {situation.title}
                  </h3>

                  <p className="mt-3 text-sm leading-6 text-text-secondary">
                    {situation.text}
                  </p>

                  <div className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-gold-deep transition group-hover:gap-3 dark:text-gold">
                    Explore
                    <ArrowRight className="h-4 w-4" />
                  </div>
                </Link>
              );
            })}
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="section-padding bg-surface-soft">
        <div className="site-container">
          <div className="mx-auto max-w-3xl text-center">
            <div className="mb-4 flex items-center justify-center gap-3">
              <span className="gold-rule" />

              <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                How Sauti Yo works
              </p>

              <span className="gold-rule" />
            </div>

            <h2 className="heading-serif text-3xl font-semibold text-text-primary sm:text-4xl lg:text-5xl">
              Four steps. That's it.
            </h2>

            <p className="mx-auto mt-5 max-w-2xl text-base leading-7 text-text-secondary">
              Here's a quick look at the journey — see how it works for the
              full walkthrough of what each step actually involves.
            </p>
          </div>

          <div className="mt-12 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {steps.map((step) => (
              <article
                key={step.number}
                className="card-surface relative overflow-hidden p-6 sm:p-7"
              >
                <span className="heading-serif absolute right-4 top-2 text-6xl font-bold text-gold/10">
                  {step.number}
                </span>

                <span className="text-xs font-bold tracking-[0.16em] text-gold-deep dark:text-gold">
                  STEP {step.number}
                </span>

                <h3 className="mt-5 text-lg font-semibold text-text-primary">
                  {step.title}
                </h3>

                <p className="mt-3 text-sm leading-6 text-text-secondary">
                  {step.text}
                </p>
              </article>
            ))}
          </div>

          <div className="mt-10 text-center">
            <Link to="/how-it-works" className="btn-secondary">
              Learn More
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* ACCESS */}
      <section className="section-padding bg-surface">
        <div className="site-container">
          <div className="grid items-center gap-12 lg:grid-cols-2 lg:gap-16">
            <div className="image-frame order-2 lg:order-1">
              <img
                src={featurePhoneUssd}
                alt="Sauti Yo on a feature phone"
                className="image-soften h-full w-full object-cover"
              />
            </div>

            <div className="order-1 lg:order-2">
              <div className="mb-5 flex items-center gap-3">
                <span className="gold-rule" />

                <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                  Access without barriers
                </p>
              </div>

              <h2 className="heading-serif text-3xl font-semibold text-text-primary sm:text-4xl lg:text-5xl">
                No smartphone?
                <span className="block text-gold-deep dark:text-gold">
                  You can still use Sauti Yo.
                </span>
              </h2>

              <p className="mt-6 max-w-xl text-base leading-7 text-text-secondary">
                The same Rights-to-Action experience can reach people through
                different channels depending on their device, connectivity and
                accessibility needs.
              </p>

              <div className="mt-8 grid gap-4 sm:grid-cols-2">
                {channels.map((channel) => {
                  const Icon = channel.icon;

                  return (
                    <div
                      key={channel.title}
                      className="border-l-2 border-gold bg-background p-4"
                    >
                      <Icon className="h-5 w-5 text-gold" />

                      <h3 className="mt-3 font-semibold text-text-primary">
                        {channel.title}
                      </h3>

                      <p className="mt-1 text-sm leading-6 text-text-secondary">
                        {channel.text}
                      </p>

                      {channel.action && (
                        <p className="mt-2 text-sm font-bold text-gold-deep dark:text-gold">
                          {channel.action}
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>

              <Link to="/access" className="btn-primary mt-8">
                Explore Access
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* PRODUCT EXPERIENCE */}
      <section className="section-padding bg-background">
        <div className="site-container">
          <div className="grid items-center gap-12 lg:grid-cols-[0.85fr_1.15fr] lg:gap-16">
            <div>
              <div className="mb-5 flex items-center gap-3">
                <span className="gold-rule" />

                <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                  Digital experience
                </p>
              </div>

              <h2 className="heading-serif text-3xl font-semibold text-text-primary sm:text-4xl lg:text-5xl">
                Clear information,
                <span className="block text-gold-deep dark:text-gold">
                  easier to navigate.
                </span>
              </h2>

              <p className="mt-6 max-w-xl text-base leading-7 text-text-secondary">
                On connected devices, Sauti Yo offers a richer interface for
                exploring rights, next steps, support services and community
                information.
              </p>
            </div>

            <div className="image-frame">
              <img
                src={smartphoneMockup}
                alt="Sauti Yo digital experience shown on smartphones"
                className="image-soften w-full object-cover"
              />
            </div>
          </div>
        </div>
      </section>

      {/* COMMUNITY VOICE */}
      <section className="section-padding bg-surface-soft">
        <div className="site-container">
          <div className="grid items-center gap-10 lg:grid-cols-[0.9fr_1.1fr] lg:gap-16">
            <div>
              <div className="mb-5 flex items-center gap-3">
                <span className="gold-rule" />

                <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                  Community Voice
                </p>
              </div>

              <h2 className="heading-serif text-3xl font-semibold text-text-primary sm:text-4xl lg:text-5xl">
                Individual experiences can reveal bigger patterns.
              </h2>

              <p className="mt-6 text-base leading-7 text-text-secondary">
                Community Voice creates a way to learn from anonymous,
                aggregated experiences without turning sensitive personal
                stories into public profiles.
              </p>

              <Link to="/community" className="btn-secondary mt-8">
                Explore Community Voice
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>

            <div className="image-frame">
              <img
                src={communityRightsSession}
                alt="Community rights discussion"
                className="image-soften h-[320px] w-full object-cover sm:h-[420px] lg:h-[500px]"
              />
            </div>
          </div>
        </div>
      </section>

      {/* SUPPORT */}
      <section className="section-padding bg-background">
        <div className="site-container">
          <div className="grid overflow-hidden border border-border bg-surface shadow-[var(--shadow-soft)] lg:grid-cols-2">
            <img
              src={legalSupportConsultation}
              alt="One-to-one support consultation"
              className="image-soften h-full min-h-[340px] w-full object-cover"
            />

            <div className="flex items-center p-7 sm:p-10 lg:p-14">
              <div>
                <div className="mb-5 flex items-center gap-3">
                  <span className="gold-rule" />

                  <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                    Find support
                  </p>
                </div>

                <h2 className="heading-serif text-3xl font-semibold text-text-primary sm:text-4xl">
                  Information helps.
                  <span className="block text-gold-deep dark:text-gold">
                    Sometimes people need more.
                  </span>
                </h2>

                <p className="mt-6 max-w-lg text-base leading-7 text-text-secondary">
                  Sauti Yo can help people identify appropriate support
                  services when specialised, practical or urgent assistance is
                  needed.
                </p>

                <Link to="/support" className="btn-primary mt-8">
                  Explore Support
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
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
                Know. Act. Be Heard.
              </p>

              <h2 className="heading-serif mt-4 text-3xl font-semibold sm:text-4xl lg:text-5xl">
                Start with what happened.
                <span className="block text-gold">
                  We’ll help you understand what comes next.
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