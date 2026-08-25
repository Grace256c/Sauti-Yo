import { createBrowserRouter } from "react-router-dom";

import AppShell from "../components/layout/AppShell";

import Home from "../pages/citizen/Home";
import Rights from "../pages/citizen/Rights";
import HowItWorks from "../pages/citizen/HowItWorks";

function AccessPlaceholder() {
  return (
    <main className="site-container min-h-[70vh] py-20">
      <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold">
        Sauti Yo
      </p>

      <h1 className="heading-serif mt-4 text-4xl font-semibold text-text-primary sm:text-5xl">
        Access Sauti Yo
      </h1>

      <p className="mt-5 max-w-xl leading-7 text-text-secondary">
        Web, USSD, SMS and Voice access will be presented here.
      </p>
    </main>
  );
}

function CommunityPlaceholder() {
  return (
    <main className="site-container min-h-[70vh] py-20">
      <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold">
        Sauti Yo
      </p>

      <h1 className="heading-serif mt-4 text-4xl font-semibold text-text-primary sm:text-5xl">
        Community Voice
      </h1>

      <p className="mt-5 max-w-xl leading-7 text-text-secondary">
        This page is being built next.
      </p>
    </main>
  );
}

function SupportPlaceholder() {
  return (
    <main className="site-container min-h-[70vh] py-20">
      <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold">
        Sauti Yo
      </p>

      <h1 className="heading-serif mt-4 text-4xl font-semibold text-text-primary sm:text-5xl">
        Find Support
      </h1>

      <p className="mt-5 max-w-xl leading-7 text-text-secondary">
        Trusted support services and referral pathways will appear here.
      </p>
    </main>
  );
}

function AboutPlaceholder() {
  return (
    <main className="site-container min-h-[70vh] py-20">
      <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold">
        Sauti Yo
      </p>

      <h1 className="heading-serif mt-4 text-4xl font-semibold text-text-primary sm:text-5xl">
        About Sauti Yo
      </h1>

      <p className="mt-5 max-w-xl leading-7 text-text-secondary">
        Learn about the purpose, mission and approach behind Sauti Yo.
      </p>
    </main>
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
        path: "rights",
        element: <Rights />,
      },
      {
        path: "how-it-works",
        element: <HowItWorks />,
      },
      {
        path: "access",
        element: <AccessPlaceholder />,
      },
      {
        path: "community",
        element: <CommunityPlaceholder />,
      },
      {
        path: "support",
        element: <SupportPlaceholder />,
      },
      {
        path: "about",
        element: <AboutPlaceholder />,
      },
    ],
  },
]);