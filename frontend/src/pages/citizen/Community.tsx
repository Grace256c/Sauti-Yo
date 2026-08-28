import {
  ArrowRight,
  BarChart3,
  LockKeyhole,
  MessageSquareText,
  ShieldCheck,
  Users,
} from "lucide-react";
import { Link } from "react-router-dom";

import communityRightsSession from "../../assets/images/community-rights-session.png";

const principles = [
  {
    icon: LockKeyhole,
    title: "Privacy-conscious",
    text: "Sensitive experiences should not become public personal profiles.",
  },
  {
    icon: Users,
    title: "Community insight",
    text: "Anonymous patterns can reveal recurring issues affecting communities.",
  },
  {
    icon: BarChart3,
    title: "Evidence for action",
    text: "Aggregated insights can help shape advocacy, services and responses.",
  },
];

export default function Community() {
  return (
    <>
      <section className="section-padding bg-background">
        <div className="site-container grid items-center gap-12 lg:grid-cols-[0.9fr_1.1fr] lg:gap-16">
          <div>
            <div className="mb-5 flex items-center gap-3">
              <span className="gold-rule" />
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                Community Voice
              </p>
            </div>

            <h1 className="heading-serif text-4xl font-semibold text-text-primary sm:text-5xl lg:text-6xl">
              Individual experiences
              <span className="block text-gold-deep dark:text-gold">
                can reveal bigger patterns.
              </span>
            </h1>

            <p className="mt-6 max-w-xl text-base leading-7 text-text-secondary sm:text-lg">
              Community Voice helps transform anonymous, aggregated
              experiences into useful insight while protecting individual
              privacy.
            </p>
          </div>

          <div className="image-frame">
            <img
              src={communityRightsSession}
              alt="Community rights session"
              className="image-soften h-[350px] w-full object-cover sm:h-[460px]"
            />
          </div>
        </div>
      </section>

      <section className="section-padding bg-surface">
        <div className="site-container grid gap-5 md:grid-cols-3">
          {principles.map((item) => {
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

      <section className="border-y border-border bg-surface-soft py-6">
        <div className="site-container flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm font-semibold text-text-primary">
            No smartphone? Sauti Yo is also reachable by:
          </p>

          <div className="flex flex-wrap gap-x-6 gap-y-2 text-sm">
            <span className="font-bold text-gold-deep dark:text-gold">
              USSD *384*163024#
            </span>

            <span className="font-bold text-gold-deep dark:text-gold">
              SMS 18275
            </span>

            <span className="font-bold text-gold-deep dark:text-gold">
              Call +256 323 200 924
            </span>
          </div>
        </div>
      </section>

      <section className="section-padding bg-background">
        <div className="site-container grid gap-10 lg:grid-cols-[0.8fr_1.2fr] lg:gap-16">
          <div>
            <MessageSquareText className="h-7 w-7 text-gold" />
            <h2 className="heading-serif mt-5 text-3xl font-semibold text-text-primary sm:text-4xl">
              Your voice can contribute without exposing your identity.
            </h2>
          </div>

          <div>
            <p className="text-base leading-7 text-text-secondary">
              Feedback can be collected in privacy-conscious ways and
              analysed in aggregate to identify common rights concerns,
              service gaps and recurring community challenges.
            </p>

            <div className="mt-7 flex items-start gap-3">
              <ShieldCheck className="mt-0.5 h-5 w-5 text-gold" />
              <p className="text-sm leading-6 text-text-secondary">
                Personal privacy should remain central to how community
                information is collected and presented.
              </p>
            </div>

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
