import { Link } from "react-router-dom";
import {
  ArrowUp,
  Globe2,
  Headphones,
  MessageSquareText,
  Phone,
  ShieldCheck,
} from "lucide-react";

import footerLogo from "../../assets/branding/sauti-yo-logo-footer.png";

const footerNavigation = [
  { label: "Know Your Rights", href: "/rights" },
  { label: "How It Works", href: "/how-it-works" },
  { label: "Access Sauti Yo", href: "/access" },
  { label: "Community Voice", href: "/community" },
  { label: "Find Support", href: "/support" },
];

const accessChannels = [
  {
    label: "Web",
    icon: Globe2,
    action: null,
  },
  {
    label: "USSD",
    icon: Phone,
    action: "*384*163024#",
  },
  {
    label: "SMS",
    icon: MessageSquareText,
    action: "18275",
  },
  {
    label: "Voice",
    icon: Headphones,
    action: "+256 323 200 924",
  },
];

export default function Footer() {
  const currentYear = new Date().getFullYear();

  const scrollToTop = () => {
    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  return (
    <footer
      className="relative overflow-hidden border-t border-white/10 bg-[#171717] text-white"
      aria-label="Sauti Yo footer"
    >
      {/* Subtle decorative background */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -right-24 -top-28 h-80 w-80 rounded-full bg-gold/5 blur-3xl"
      />

      <div
        aria-hidden="true"
        className="pointer-events-none absolute -bottom-32 -left-24 h-80 w-80 rounded-full bg-white/[0.025] blur-3xl"
      />

      {/* Main footer */}
      <div className="site-container relative py-12 sm:py-14 lg:py-16">
        <div className="grid gap-10 md:grid-cols-2 lg:grid-cols-[1.35fr_0.8fr_0.85fr] lg:gap-14">
          {/* Brand column */}
          <div className="max-w-md">
            <Link
              to="/"
              aria-label="Sauti Yo home"
              className="inline-flex"
            >
              <img
                src={footerLogo}
                alt="Sauti Yo — Know. Act. Be Heard."
                className="h-auto w-[185px] object-contain object-left sm:w-[210px]"
              />
            </Link>

            <p className="mt-5 max-w-sm text-sm leading-7 text-white/65 sm:text-[15px]">
              Helping people understand their rights, identify
              practical next steps and connect with appropriate
              support through accessible digital and feature-phone
              channels.
            </p>

            {/* Trust message */}
            <div className="mt-6 flex max-w-sm items-start gap-3 border-l-2 border-gold pl-4">
              <ShieldCheck
                className="mt-0.5 h-5 w-5 shrink-0 text-gold"
                strokeWidth={1.8}
              />

              <p className="text-sm leading-6 text-white/65">
                Rights information should be clear, responsible and
                accessible to everyone.
              </p>
            </div>
          </div>

          {/* Navigation */}
          <div>
            <p className="mb-5 font-semibold text-white">
              Explore Sauti Yo
            </p>

            <nav
              className="flex flex-col gap-3"
              aria-label="Footer navigation"
            >
              {footerNavigation.map((item) => (
                <Link
                  key={item.href}
                  to={item.href}
                  className="group inline-flex w-fit items-center gap-2 text-sm text-white/60 transition-colors duration-200 hover:text-gold"
                >
                  <span className="h-px w-3 bg-white/25 transition-all duration-200 group-hover:w-5 group-hover:bg-gold" />

                  {item.label}
                </Link>
              ))}
            </nav>
          </div>

          {/* Access channels */}
          <div>
            <p className="mb-2 font-semibold text-white">
              Access Sauti Yo
            </p>

            <p className="mb-5 text-sm leading-6 text-white/55">
              Different ways to reach the same trusted
              Rights-to-Action experience.
            </p>

            <div className="grid grid-cols-2 gap-2">
              {accessChannels.map((channel) => {
                const Icon = channel.icon;

                return (
                  <div
                    key={channel.label}
                    className="flex min-h-11 items-center gap-2.5 rounded-md border border-white/10 bg-white/[0.035] px-3 py-2.5 text-sm text-white/70"
                  >
                    <Icon
                      className="h-4 w-4 shrink-0 text-gold"
                      strokeWidth={1.8}
                    />

                    <div className="min-w-0">
                      <span className="block">{channel.label}</span>

                      {channel.action && (
                        <span className="block text-xs font-semibold text-gold">
                          {channel.action}
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            <Link
              to="/rights"
              className="mt-5 inline-flex min-h-11 items-center justify-center border border-gold px-5 py-2.5 text-sm font-semibold text-gold transition duration-200 hover:bg-gold hover:text-[#171717]"
            >
              Start Here
            </Link>
          </div>
        </div>
      </div>

      {/* Bottom bar */}
      <div className="border-t border-white/10">
        <div className="site-container flex flex-col gap-5 py-5 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-col gap-2 text-xs text-white/45 sm:flex-row sm:items-center sm:gap-4">
            <p>
              © {currentYear} Sauti Yo. All rights reserved.
            </p>

            <span
              aria-hidden="true"
              className="hidden h-3 w-px bg-white/15 sm:block"
            />

            <p>Know. Act. Be Heard.</p>
          </div>

          <button
            type="button"
            onClick={scrollToTop}
            className="flex h-11 w-11 items-center justify-center self-start rounded-full border border-white/15 text-white/65 transition duration-200 hover:border-gold hover:bg-gold hover:text-[#171717] sm:self-auto"
            aria-label="Back to top"
            title="Back to top"
          >
            <ArrowUp
              className="h-4 w-4"
              strokeWidth={1.8}
            />
          </button>
        </div>
      </div>
    </footer>
  );
}