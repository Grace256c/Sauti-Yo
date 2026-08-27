import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
} from "lucide-react";

import {
  Link,
  Navigate,
  createBrowserRouter,
  useParams,
} from "react-router-dom";

/* =========================================================
   LAYOUTS
========================================================= */

import AppShell from "../components/layout/AppShell";
import PartnerShell from "../components/partner/PartnerShell";
import PartnerRouteGuard from "../components/partner/PartnerRouteGuard";

/* =========================================================
   CITIZEN PAGES
========================================================= */

import Home from "../pages/citizen/Home";
import About from "../pages/citizen/About";
import Rights from "../pages/citizen/Rights";
import SituationNavigator from "../pages/citizen/SituationNavigator";
import GuidedRightsJourney from "../pages/citizen/GuidedRightsJourney";
import RightsResults from "../pages/citizen/RightsResults";
import HowItWorks from "../pages/citizen/HowItWorks";
import Access from "../pages/citizen/Access";
import Community from "../pages/citizen/Community";
import Support from "../pages/citizen/Support";

/* =========================================================
   PARTNER PAGES
========================================================= */

import PartnerLogin from "../pages/partner/PartnerLogin";
import PartnerDashboard from "../pages/partner/PartnerDashboard";
import PartnerProfile from "../pages/partner/PartnerProfile";
import PartnerServices from "../pages/partner/PartnerServices";
import PartnerVerification from "../pages/partner/PartnerVerification";
import PartnerReferrals from "../pages/partner/PartnerReferrals";
import PartnerReferralDetail from "../pages/partner/PartnerReferralDetail";
import PartnerSettings from "../pages/partner/PartnerSettings";

/* =========================================================
   DATA
========================================================= */

import {
  getRightsCategory,
} from "../data/rightsData";

/* =========================================================
   RIGHTS CATEGORY PAGE
========================================================= */

function RightsCategoryPage() {
  const { category } =
    useParams();

  const selected =
    getRightsCategory(category);

  if (!selected) {
    return (
      <Navigate
        to="/rights"
        replace
      />
    );
  }

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

              <h2 className="heading-serif text-3xl font-semibold leading-tight text-text-primary sm:text-4xl">
                Situations may look different

                <span className="block text-gold-deep dark:text-gold">
                  for different people.
                </span>
              </h2>

              <p className="mt-5 max-w-md text-base leading-7 text-text-secondary">
                These examples are only
                a starting point. Your
                experience does not have
                to match them exactly.
              </p>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              {selected.examples.map(
                (example) => (
                  <article
                    key={example}
                    className="card-surface flex min-h-[150px] items-start gap-4 p-5 sm:p-6"
                  >
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gold/10">
                      <CheckCircle2
                        className="h-4 w-4 text-gold"
                        strokeWidth={1.8}
                      />
                    </div>

                    <p className="pt-1 text-sm leading-6 text-text-secondary">
                      {example}
                    </p>
                  </article>
                ),
              )}
            </div>
          </div>
        </div>
      </section>

      {/* REASSURANCE */}
      <section className="bg-surface-soft">
        <div className="site-container py-12 sm:py-14">
          <div className="grid gap-6 border-y border-border py-8 md:grid-cols-[auto_1fr] md:items-start md:gap-6">
            <div className="flex h-11 w-11 items-center justify-center rounded-full bg-gold/10 text-gold">
              <Icon
                className="h-5 w-5"
                strokeWidth={1.6}
              />
            </div>

            <div className="max-w-3xl">
              <h2 className="text-lg font-semibold text-text-primary">
                You do not need to have everything figured out.
              </h2>

              <p className="mt-2 text-sm leading-6 text-text-secondary sm:text-base">
                The next step asks a few
                simple questions about
                what happened. Your
                answers help organise
                information that may be
                more relevant to your
                situation.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CONTINUE */}
      <section className="bg-[#1c1c1c] text-white">
        <div className="site-container py-16 sm:py-20">
          <div className="grid gap-8 lg:grid-cols-[1fr_auto] lg:items-center">
            <div className="max-w-3xl">
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold">
                Continue your journey
              </p>

              <h2 className="heading-serif mt-4 text-3xl font-semibold leading-tight sm:text-4xl lg:text-5xl">
                Tell us a little more

                <span className="block text-gold">
                  about what happened.
                </span>
              </h2>

              <p className="mt-5 max-w-2xl text-base leading-7 text-white/65">
                Answer a few simple
                questions to receive
                information and
                practical next steps
                organised around your
                situation.
              </p>
            </div>

            <Link
              to={`/rights/${selected.slug}/start`}
              className="group inline-flex min-h-12 w-full items-center justify-center gap-2 border border-gold bg-gold px-7 py-3 font-bold text-[#191919] transition duration-300 hover:bg-transparent hover:text-gold sm:w-auto"
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

/* =========================================================
   ROUTER
========================================================= */

export const router =
  createBrowserRouter([
    /* CITIZEN EXPERIENCE */
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
          element: (
            <SituationNavigator />
          ),
        },

        {
          path: "rights/:category",
          element: (
            <RightsCategoryPage />
          ),
        },

        {
          path: "rights/:category/start",
          element: (
            <GuidedRightsJourney />
          ),
        },

        {
          path: "rights/:category/results",
          element: (
            <RightsResults />
          ),
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

    /* PARTNER LOGIN */
    {
      path: "/partner/login",
      element: <PartnerLogin />,
    },

    /* PARTNER PORTAL */
    {
      element: <PartnerRouteGuard />,

      children: [
        {
          path: "/partner",
          element: <PartnerShell />,

          children: [
        {
          index: true,
          element: (
            <PartnerDashboard />
          ),
        },

        {
          path: "profile",
          element: (
            <PartnerProfile />
          ),
        },

        {
          path: "services",
          element: (
            <PartnerServices />
          ),
        },

        {
          path: "verification",
          element: (
            <PartnerVerification />
          ),
        },

        {
          path: "referrals",
          element: (
            <PartnerReferrals />
          ),
        },

        {
          path: "referrals/:referralId",
          element: (
            <PartnerReferralDetail />
          ),
        },

        {
          path: "settings",
          element: (
            <PartnerSettings />
          ),
        },
          ],
        },
      ],
    },

    /* FALLBACK */
    {
      path: "*",
      element: (
        <Navigate
          to="/"
          replace
        />
      ),
    },
  ]);