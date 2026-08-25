import {
  ArrowLeft,
  ArrowRight,
  BriefcaseBusiness,
  HeartHandshake,
  Home,
  Landmark,
  ShieldCheck,
  Users,
} from "lucide-react";
import { Link } from "react-router-dom";

const situations = [
  {
    slug: "work-employment",
    icon: BriefcaseBusiness,
    title: "Something happened at work",
    description:
      "Pay, dismissal, contracts, workplace treatment or working conditions.",
    examples: [
      "I have not been paid.",
      "I was dismissed.",
      "I am being treated unfairly at work.",
    ],
  },
  {
    slug: "safety-protection",
    icon: ShieldCheck,
    title: "I am worried about my safety",
    description:
      "Threats, abuse, violence, harassment or another personal safety concern.",
    examples: [
      "Someone is threatening me.",
      "I have experienced abuse.",
      "I need to understand where I can get help.",
    ],
  },
  {
    slug: "land-housing",
    icon: Home,
    title: "I have a land or housing problem",
    description:
      "Land ownership, tenancy, eviction, boundaries or housing disputes.",
    examples: [
      "There is a dispute about land.",
      "I am being threatened with eviction.",
      "I have a problem with my landlord or tenant.",
    ],
  },
  {
    slug: "family-inheritance",
    icon: HeartHandshake,
    title: "It involves my family",
    description:
      "Marriage, children, family responsibilities or inheritance concerns.",
    examples: [
      "There is an inheritance disagreement.",
      "I have a concern involving children.",
      "A family situation has become difficult.",
    ],
  },
  {
    slug: "public-services",
    icon: Landmark,
    title: "It involves a public institution",
    description:
      "Government services, public institutions or administrative decisions.",
    examples: [
      "I cannot access a public service.",
      "I do not understand a decision that was made.",
      "I need to know where I can make a complaint.",
    ],
  },
  {
    slug: "community-discrimination",
    icon: Users,
    title: "I have been treated unfairly",
    description:
      "Discrimination, exclusion or another community rights concern.",
    examples: [
      "I feel I have been discriminated against.",
      "I have been excluded unfairly.",
      "A community issue is affecting my rights.",
    ],
  },
];

export default function SituationNavigator() {
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
                Help me choose
              </p>
            </div>

            <h1 className="heading-serif text-4xl font-semibold leading-tight text-text-primary sm:text-5xl lg:text-6xl">
              You do not need to know
              <span className="block text-gold-deep dark:text-gold">
                what the legal issue is called.
              </span>
            </h1>

            <p className="mt-6 max-w-2xl text-base leading-7 text-text-secondary sm:text-lg">
              Choose the statement that feels closest to what happened.
              It does not need to be a perfect match.
            </p>
          </div>
        </div>
      </section>

      {/* SITUATION OPTIONS */}
      <section className="section-padding bg-surface">
        <div className="site-container">
          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
            {situations.map((situation) => {
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
                    {situation.title}
                  </h2>

                  <p className="mt-3 text-sm leading-6 text-text-secondary">
                    {situation.description}
                  </p>

                  <div className="mt-5 space-y-2">
                    {situation.examples.map((example) => (
                      <p
                        key={example}
                        className="text-xs leading-5 text-text-secondary"
                      >
                        • {example}
                      </p>
                    ))}
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
              Pick the closest option.
            </h2>

            <p className="mx-auto mt-4 max-w-2xl text-sm leading-6 text-text-secondary sm:text-base">
              Your first choice does not lock you into anything. You can go
              back and explore another situation if the information does not
              feel relevant.
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
                  We’ll connect it to the rights information.
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