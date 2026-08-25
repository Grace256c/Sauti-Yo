import {
  ArrowRight,
  Building2,
  HeartHandshake,
  PhoneCall,
  ShieldAlert,
} from "lucide-react";
import { Link } from "react-router-dom";

import legalSupportConsultation from "../../assets/images/legal-support-consultation.png";

const supportTypes = [
  {
    icon: HeartHandshake,
    title: "Legal & Rights Support",
    text: "Find organisations that can provide legal information or assistance.",
  },
  {
    icon: ShieldAlert,
    title: "Safety & Protection",
    text: "Identify services relevant to safety, protection and urgent support.",
  },
  {
    icon: Building2,
    title: "Public & Community Services",
    text: "Find relevant institutions and community organisations.",
  },
  {
    icon: PhoneCall,
    title: "Contact Pathways",
    text: "See available phone, website and alternative contact options.",
  },
];

export default function Support() {
  return (
    <>
      <section className="section-padding bg-background">
        <div className="site-container grid items-center gap-12 lg:grid-cols-2 lg:gap-16">
          <div className="image-frame order-2 lg:order-1">
            <img
              src={legalSupportConsultation}
              alt="Professional support consultation"
              className="image-soften h-[360px] w-full object-cover sm:h-[480px]"
            />
          </div>

          <div className="order-1 lg:order-2">
            <div className="mb-5 flex items-center gap-3">
              <span className="gold-rule" />
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                Find Support
              </p>
            </div>

            <h1 className="heading-serif text-4xl font-semibold text-text-primary sm:text-5xl lg:text-6xl">
              Information helps.
              <span className="block text-gold-deep dark:text-gold">
                Sometimes people need more.
              </span>
            </h1>

            <p className="mt-6 max-w-xl text-base leading-7 text-text-secondary sm:text-lg">
              Sauti Yo helps users identify appropriate organisations,
              services and referral pathways when specialised assistance
              is needed.
            </p>
          </div>
        </div>
      </section>

      <section className="section-padding bg-surface">
        <div className="site-container grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          {supportTypes.map((item) => {
            const Icon = item.icon;

            return (
              <article key={item.title} className="card-surface p-6 sm:p-7">
                <Icon className="h-6 w-6 text-gold" />
                <h2 className="mt-5 text-xl font-semibold text-text-primary">
                  {item.title}
                </h2>
                <p className="mt-3 text-sm leading-6 text-text-secondary">
                  {item.text}
                </p>
              </article>
            );
          })}
        </div>
      </section>

      <section className="bg-[#191919] text-white">
        <div className="site-container py-16 sm:py-20">
          <div className="grid gap-8 lg:grid-cols-[1fr_auto] lg:items-center">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold">
                Start with your situation
              </p>

              <h2 className="heading-serif mt-4 text-3xl font-semibold sm:text-4xl lg:text-5xl">
                Not sure what support you need?
                <span className="block text-gold">
                  Begin with what happened.
                </span>
              </h2>
            </div>

            <Link
              to="/rights"
              className="inline-flex min-h-12 items-center justify-center gap-2 border border-gold bg-gold px-7 py-3 font-bold text-[#191919] transition hover:bg-transparent hover:text-gold"
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
