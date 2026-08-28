import {
  ArrowRight,
  BookOpen,
  Scale,
  ShieldCheck,
  Users,
} from "lucide-react";
import { Link } from "react-router-dom";

import legalBackground from "../../assets/images/legal-background.png";
import communityRightsSession from "../../assets/images/community-rights-session.png";

const steps = [
  {
    number: "01",
    icon: Users,
    title: "Describe your situation",
    text: "Choose from everyday descriptions like \"my landlord won't return my deposit\" or \"someone at work keeps threatening me\" — no legal terms required.",
  },
  {
    number: "02",
    icon: BookOpen,
    title: "Answer a few short questions",
    text: "A short guided conversation narrows down exactly which rights and protections apply to your specific circumstances.",
  },
  {
    number: "03",
    icon: Scale,
    title: "Review what applies to you",
    text: "See the specific laws that protect you, a clear next action to take, and anything worth being careful about along the way.",
  },
  {
    number: "04",
    icon: ShieldCheck,
    title: "Get connected, if you need it",
    text: "When information alone isn't enough, Sauti Yo can help match you with a verified organisation that can help directly.",
  },
];

export default function HowItWorks() {
  return (
    <>
      <section className="relative isolate overflow-hidden">
        <img
          src={legalBackground}
          alt=""
          aria-hidden="true"
          className="legal-image absolute inset-0 -z-20 h-full w-full object-cover"
        />
        <div className="legal-overlay-light absolute inset-0 -z-10" />

        <div className="site-container py-20 sm:py-24 lg:py-32">
          <div className="max-w-3xl">
            <div className="mb-5 flex items-center gap-3">
              <span className="gold-rule" />
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                How Sauti Yo works
              </p>
            </div>

            <h1 className="heading-serif text-4xl font-semibold text-text-primary sm:text-5xl lg:text-6xl">
              From uncertainty
              <span className="block text-gold-deep dark:text-gold">
                to a practical next step.
              </span>
            </h1>

            <p className="mt-6 max-w-2xl text-base leading-7 text-text-secondary sm:text-lg">
              Sauti Yo turns a real-life situation into clear information,
              practical options and appropriate support.
            </p>
          </div>
        </div>
      </section>

      <section className="section-padding bg-surface">
        <div className="site-container">
          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
            {steps.map((step) => {
              const Icon = step.icon;

              return (
                <article key={step.number} className="card-surface p-6 sm:p-7">
                  <Icon className="h-6 w-6 text-gold" />
                  <p className="mt-5 text-xs font-bold uppercase tracking-[0.15em] text-gold-deep dark:text-gold">
                    Step {step.number}
                  </p>

                  <h2 className="mt-3 text-xl font-semibold text-text-primary">
                    {step.title}
                  </h2>

                  <p className="mt-3 text-sm leading-6 text-text-secondary">
                    {step.text}
                  </p>
                </article>
              );
            })}
          </div>
        </div>
      </section>

      <section className="section-padding bg-background">
        <div className="site-container grid items-center gap-12 lg:grid-cols-2 lg:gap-16">
          <div className="image-frame">
            <img
              src={communityRightsSession}
              alt="Sauti Yo community rights session"
              className="image-soften h-[350px] w-full object-cover sm:h-[450px]"
            />
          </div>

          <div>
            <div className="mb-5 flex items-center gap-3">
              <span className="gold-rule" />
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                Situation first
              </p>
            </div>

            <h2 className="heading-serif text-3xl font-semibold text-text-primary sm:text-4xl">
              Start with the experience, then connect it to the law.
            </h2>

            <p className="mt-6 text-base leading-7 text-text-secondary">
              People should not need to identify the legal doctrine before
              they can get useful guidance.
            </p>

            <Link to="/rights" className="btn-primary mt-8">
              Explore Your Rights
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
