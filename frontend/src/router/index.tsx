import {
  ArrowLeft,
  ArrowRight,
  BriefcaseBusiness,
  CheckCircle2,
  HeartHandshake,
  Home as HomeIcon,
  Landmark,
  ShieldCheck,
  Users,
} from "lucide-react";

import {
  Link,
  Navigate,
  createBrowserRouter,
  useParams,
} from "react-router-dom";

import AppShell from "../components/layout/AppShell";

import Home from "../pages/citizen/Home";
import About from "../pages/citizen/About";
import Rights from "../pages/citizen/Rights";
import SituationNavigator from "../pages/citizen/SituationNavigator";
import GuidedRightsJourney from "../pages/citizen/GuidedRightsJourney";
import HowItWorks from "../pages/citizen/HowItWorks";
import Access from "../pages/citizen/Access";
import Community from "../pages/citizen/Community";
import Support from "../pages/citizen/Support";

const categoryData = {
  "work-employment": {
    icon: BriefcaseBusiness,
    title: "Work & Employment",
    description:
      "Explore rights and practical next steps related to employment, workplace treatment, contracts, dismissal and pay.",
    examples: [
      "You have not been paid for work you completed.",
      "You were dismissed and are unsure what your options are.",
      "You are concerned about treatment or conditions at work.",
      "You have questions about your employment agreement.",
    ],
  },

  "safety-protection": {
    icon: ShieldCheck,
    title: "Safety & Protection",
    description:
      "Explore safety-conscious information and support options where there may be threats, violence, abuse or harassment.",
    examples: [
      "Someone has threatened or harmed you.",
      "You are worried about your immediate safety.",
      "You are experiencing harassment or abuse.",
      "You need to understand possible protection or support options.",
    ],
  },

  "land-housing": {
    icon: HomeIcon,
    title: "Land & Housing",
    description:
      "Explore rights and next steps related to land, ownership, tenancy, eviction and housing disputes.",
    examples: [
      "There is a disagreement about land ownership.",
      "You are facing eviction or removal from a property.",
      "You have a dispute with a landlord or tenant.",
      "You need to understand documents or decisions affecting property.",
    ],
  },

  "family-inheritance": {
    icon: HeartHandshake,
    title: "Family & Inheritance",
    description:
      "Explore common rights questions involving family responsibilities, marriage, children and inheritance.",
    examples: [
      "There is a disagreement about inheritance.",
      "You have questions about responsibilities toward children.",
      "A family matter has created a legal or practical concern.",
      "You need to understand your options before taking action.",
    ],
  },

  "public-services": {
    icon: Landmark,
    title: "Public Services",
    description:
      "Explore concerns involving public institutions, government services and administrative decisions.",
    examples: [
      "You are having difficulty accessing a public service.",
      "A public institution made a decision you do not understand.",
      "You need to know where to raise a complaint.",
      "You want to understand what steps may be available.",
    ],
  },

  "community-discrimination": {
    icon: Users,
    title: "Community & Discrimination",
    description:
      "Explore situations involving unfair treatment, exclusion, discrimination or community rights concerns.",
    examples: [
      "You believe you have been treated unfairly.",
      "You have experienced exclusion or discrimination.",
      "A community issue is affecting your rights or wellbeing.",
      "You need to understand where appropriate support may exist.",
    ],
  },
};

type CategorySlug = keyof typeof categoryData;

function RightsCategoryPage() {
  const { category } = useParams();

  if (!category || !(category in categoryData)) {
    return <Navigate to="/rights" replace />;
  }

  const selected = categoryData[category as CategorySlug];
  const Icon = selected.icon;

  return (
    <>
      {/* CATEGORY HERO */}
      <section className="bg-background py-16 sm:py-20 lg:py-24">
        <div className="site-container">
          <Link
            to="/rights"
            className="inline-flex items-center gap-2 text-sm font-semibold text-text-secondary transition hover:text-gold"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to all situations
          </Link>

          <div className="mt-10 grid gap-10 lg:grid-cols-[0.8fr_1.2fr] lg:items-end lg:gap-16">
            <div>
              <div className="flex h-14 w-14 items-center justify-center rounded-full bg-gold/10 text-gold">
                <Icon
                  className="h-7 w-7"
                  strokeWidth={1.6}
                />
              </div>

              <div className="mt-7 flex items-center gap-3">
                <span className="gold-rule" />

                <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                  Know your rights
                </p>
              </div>

              <h1 className="heading-serif mt-5 text-4xl font-semibold leading-tight text-text-primary sm:text-5xl lg:text-6xl">
                {selected.title}
              </h1>
            </div>

            <p className="max-w-xl text-base leading-7 text-text-secondary sm:text-lg">
              {selected.description}
            </p>
          </div>
        </div>
      </section>

      {/* EXAMPLES */}
      <section className="section-padding bg-surface">
        <div className="site-container">
          <div className="grid gap-12 lg:grid-cols-[0.75fr_1.25fr] lg:gap-16">
            <div>
              <div className="mb-5 flex items-center gap-3">
                <span className="gold-rule" />

                <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-deep dark:text-gold">
                  Does this sound familiar?
                </p>
              </div>

              <h2 className="heading-serif text-3xl font-semibold text-text-primary sm:text-4xl">
                Situations may look different for different people.
              </h2>

              <p className="mt-5 max-w-md text-base leading-7 text-text-secondary">
                These examples are only a starting point. Your
                experience does not have to match them exactly.
              </p>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              {selected.examples.map((example) => (
                <div
                  key={example}
                  className="card-surface flex items-start gap-3 p-5 sm:p-6"
                >
                  <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-gold" />

                  <p className="text-sm leading-6 text-text-secondary">
                    {example}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* CONTINUE */}
      <section className="bg-[#191919] text-white">
        <div className="site-container py-16 sm:py-20">
          <div className="grid gap-8 lg:grid-cols-[1fr_auto] lg:items-center">
            <div className="max-w-3xl">
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold">
                Continue your journey
              </p>

              <h2 className="heading-serif mt-4 text-3xl font-semibold sm:text-4xl lg:text-5xl">
                Tell us a little more
                <span className="block text-gold">
                  about what happened.
                </span>
              </h2>

              <p className="mt-5 max-w-2xl text-base leading-7 text-white/65">
                The next step guides you through a few simple questions
                so Sauti Yo can organise more relevant information and
                support pathways.
              </p>
            </div>

            <Link
              to={`/rights/${category}/start`}
              className="group inline-flex min-h-12 w-full items-center justify-center gap-2 border border-gold bg-gold px-7 py-3 font-bold text-[#191919] transition hover:bg-transparent hover:text-gold sm:w-auto"
            >
              Continue

              <ArrowRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-1" />
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      {
        index: true,
        element: <Home />,
      },
      {
        path: "about",
        element: <About />,
      },
      {
        path: "rights",
        element: <Rights />,
      },
      {
        path: "rights/navigator",
        element: <SituationNavigator />,
      },
      {
        path: "rights/:category",
        element: <RightsCategoryPage />,
      },
      {
        path: "rights/:category/start",
        element: <GuidedRightsJourney />,
      },
      {
        path: "how-it-works",
        element: <HowItWorks />,
      },
      {
        path: "access",
        element: <Access />,
      },
      {
        path: "community",
        element: <Community />,
      },
      {
        path: "support",
        element: <Support />,
      },
    ],
  },
]);